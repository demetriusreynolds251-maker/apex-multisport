#!/usr/bin/env python3
"""Step 4: test pre-match facts one at a time on the Step 3 picks, plus a Goblin estimate. Backtest only.
Inputs (read only): data/processed/nba_history.sqlite, data/processed/step3_predictions.sqlite, reports/latest_step3_numbers.md
(Fit line), and field goals made from the 2TB raw files, the same way Step 3 gets them.
Output: reports/2026-10-31_step4_facts_numbers.md.
Every fact uses earlier dates only, except teammate-out, which reads this game's box score (see report).
Cut-offs are set on the build half only. No API calls. Does not import win_probability.py, which would rewrite Step 3's output."""
import ast, bisect, collections as C, datetime as DT, glob, gzip, json, math, os, re, sqlite3, statistics as ST
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, 'data', 'processed', 'nba_history.sqlite')
PRED = os.path.join(ROOT, 'data', 'processed', 'step3_predictions.sqlite')
STEP3 = os.path.join(ROOT, 'reports', 'latest_step3_numbers.md')
OUTF = os.path.join(ROOT, 'reports', '2026-10-31_step4_facts_numbers.md')
RAW = '/Volumes/2TB Drive/SportsData/sportsgameodds/events/BASKETBALL/NBA'
STATS = {'points': lambda r: r['points'], 'rebounds': lambda r: r['rebounds'], 'rebounds+assists': lambda r: r['rebounds'] + r['assists'],
         'points+rebounds+assists': lambda r: r['points'] + r['rebounds'] + r['assists'], 'fieldGoalsMade': lambda r: r['fgm']}
SHORT = {'points': 'Points', 'points+rebounds+assists': 'PRA', 'rebounds': 'Rebounds', 'rebounds+assists': 'Reb+Ast', 'fieldGoalsMade': 'FG made', 'ALL': 'All five'}
OFFSETS = {'points': [1, 2, 3, 4], 'points+rebounds+assists': [1, 2, 3, 4], 'rebounds+assists': [1, 1.5, 2, 3], 'rebounds': [.5, 1, 1.5, 2], 'fieldGoalsMade': [.5, 1, 1.5, 2]}
MIN_SIDE = 40; USUAL_MIN = 28.0; BIG_SPREAD = 10.0; TREND = 3.0; BOX_MIN = 235.0
def phi(z): return .5 * math.erfc(-z / math.sqrt(2))
def norm(t): return 'Los Angeles Clippers' if t == 'LA Clippers' else t
def days(a, b): return (DT.date.fromisoformat(b) - DT.date.fromisoformat(a)).days
db = sqlite3.connect('file:%s?mode=ro' % DB, uri=True); db.row_factory = sqlite3.Row
pdb = sqlite3.connect('file:%s?mode=ro' % PRED, uri=True); pdb.row_factory = sqlite3.Row
fit = ast.literal_eval(re.search(r'^Fit: (.*)$', open(STEP3).read(), re.M).group(1))
for s in fit: fit[s]['adj'] = {ast.literal_eval(k): v for k, v in fit[s]['adj'].items()}
CUT = re.search(r'Split at (\S+?)\.', open(STEP3).read()).group(1)
fgm = {}
if os.path.isdir(RAW):
    for f in glob.iglob(RAW + '/*/*/*.json.gz'):
        with gzip.open(f, 'rt') as z: e = json.load(z)
        for pid, r in ((e.get('results') or {}).get('game') or {}).items():
            if isinstance(r, dict) and 'fieldGoalsMade' in r: fgm[(e['eventID'], pid)] = r['fieldGoalsMade']
games = {g['event_id']: dict(g) for g in db.execute('select * from games where final=1')}
# --- Step 3 history, rebuilt the same way, in the same order
H = C.defaultdict(list); Allow = C.defaultdict(lambda: C.defaultdict(float))
for r in (dict(x) for x in db.execute('select * from player_games where minutes>0 and points is not null order by game_date')):
    r['fgm'] = fgm.get((r['event_id'], r['player_id']))
    for k in ('rebounds', 'assists'): r[k] = r[k] or 0
    H[r['player_id']].append(r)
    for s, fn in STATS.items():
        try: Allow[(r['event_id'], r['opponent'])][s] += fn(r)
        except TypeError: pass
def build_def(keyfn):
    T = C.defaultdict(list)
    for (eid, team), v in Allow.items():
        g = games.get(eid)
        if g: T[keyfn(team)].append((g['game_date'], dict(v)))
    for v in T.values(): v.sort(key=lambda x: x[0])
    return T
T3 = build_def(lambda t: t); TN = build_def(norm)   # T3 = exactly Step 3; TN = Clippers names merged, for the opponent fact
Lg = C.defaultdict(list)
for v in T3.values():
    for d, a in v:
        for s, x in a.items(): Lg[s].append((d, x))
for v in Lg.values(): v.sort(key=lambda x: x[0])
def lg_mean(s, d):
    v = Lg[s]; i = bisect.bisect_left(v, (d,)); w = v[max(0, i - 400):i]
    return ST.mean(x for _, x in w) if len(w) >= 50 else None
def opp_factor(T, s, team, d):
    a = [x[1].get(s) for x in T.get(team, []) if x[0] < d][-15:]
    a = [x for x in a if x is not None]; m = lg_mean(s, d)
    return ST.mean(a) / m if len(a) >= 5 and m else 1.0
# --- box scores by real team, using games.home/away and the home flag (the team column says 'home'/'away' on 109 events in Jan-Feb 2025)
Box = C.defaultdict(dict)
for r in db.execute('select event_id, player_id, home, minutes from player_games'):
    g = games.get(r['event_id'])
    if not g: continue
    t = norm(g['home'] if r['home'] else g['away'])
    if r['minutes'] and r['minutes'] > 0: Box[(r['event_id'], t)][r['player_id']] = r['minutes']
Sched = C.defaultdict(list)   # team -> complete-box games, deduped per date (some games exist under several event ids)
Complete = {}
for (eid, t), b in Box.items():
    Complete[(eid, t)] = sum(b.values()) >= BOX_MIN and len(b) >= 8
byday = C.defaultdict(dict)
for (eid, t), b in Box.items():
    if Complete[(eid, t)]: byday[t].setdefault(games[eid]['game_date'], b)
for t, dd in byday.items(): Sched[t] = sorted(dd.items())
def teammate_out(pid, team, eid, date):
    if not Complete.get((eid, team)): return None, 'box incomplete'
    v = Sched[team]; i = bisect.bisect_left(v, (date,)); w = [x for x in v[max(0, i - 5):i] if days(x[0], date) <= 30]
    if len(w) < 3: return None, 'under 3 recent team games'
    cnt = C.defaultdict(list)
    for _, b in w:
        for q, m in b.items(): cnt[q].append(m)
    now = Box[(eid, team)]
    usual = [q for q, m in cnt.items() if q != pid and len(m) >= 3 and ST.mean(m) >= USUAL_MIN]
    return ('out' if any(q not in now for q in usual) else 'none'), None
# --- prop line details
PL = {(r['event_id'], r['player_id'], r['stat']): (r['book_lines_json'], r['pinnacle_before_start']) for r in db.execute('select event_id, player_id, stat, book_lines_json, pinnacle_before_start from prop_lines where pp_before_start=1 and books_before_start>0')}
P = []; why = C.Counter(); diffs = []; diffp = []
for r in pdb.execute('select * from predictions'):
    x = dict(r); hist = H[x['player_id']]; dd = [h['game_date'] for h in hist]; i = bisect.bisect_left(dd, x['game_date'])
    me = next(h for h in hist[i:i + 3] if h['event_id'] == x['event_id']); fn = STATS[x['stat']]
    past = [h for h in hist[:i] if fn(h) is not None] if x['stat'] == 'fieldGoalsMade' else hist[:i]
    rate = lambda L: sum(fn(h) for h in L) / max(1.0, sum(h['minutes'] for h in L))
    l5, l10 = past[-5:], past[-10:]; sea = [h for h in past if h['season'] == x['season']] or past[-30:]
    mins = .6 * ST.mean(h['minutes'] for h in l5) + .4 * ST.mean(h['minutes'] for h in l10)
    rr = .4 * rate(l5) + .35 * rate(l10) + .25 * rate(sea); sd = max(ST.pstdev([fn(h) - rr * h['minutes'] for h in past[-20:]]), 1.0)
    f = fit[x['stat']]; o3 = opp_factor(T3, x['stat'], me['opponent'], x['game_date'])
    m = rr * mins * (1 + .5 * (o3 - 1)) * f['adj'].get((me['back_to_back'] or 0, me['home']), 1.0)
    x['m3'] = m; x['s3'] = sd * f['k']; pm = phi((m - x['pp_line']) / x['s3']); diffs.append(abs(m - x['projected'])); diffp.append(abs(100 * max(pm, 1 - pm) - x['win_prob']))
    F = {}
    # minutes: full earlier history of games played, whatever the stat
    pm_ = hist[:i]; mn = [h['minutes'] for h in pm_]
    if len(mn) >= 13:
        t = ST.mean(mn[-3:]) - ST.mean(mn[-13:-3]); F['trend'] = 'up' if t >= TREND else 'down' if t <= -TREND else 'flat'; x['msd'] = ST.pstdev(mn[-10:])
    else: x['msd'] = None; why['minutes: under 13 earlier games'] += 1
    # spread: open only
    g = games[x['event_id']]; sp = g['open_spread_home']; team = norm(g['home'] if me['home'] else g['away'])
    if sp is not None:
        F['big'] = 'big' if abs(sp) >= BIG_SPREAD else 'small'
        mine = sp if me['home'] else -sp
        if mine != 0: F['fav'] = 'fav' if mine < 0 else 'dog'
    # rest: days between this player's games, from earlier rows; schedule check by team
    if pm_:
        rest = days(pm_[-1]['game_date'], x['game_date']) - 1
        F['b2b'] = 'yes' if rest == 0 else 'no'; F['rest'] = '2+' if rest >= 2 else '0-1'
    # opponent, Clippers names merged
    x['of'] = opp_factor(TN, x['stat'], norm(me['opponent']), x['game_date'])
    # teammate
    tm, w = teammate_out(x['player_id'], team, x['event_id'], x['game_date'])
    if tm: F['mate'] = tm
    else: why['teammate: ' + w] += 1
    # room, for the side we picked: + means the book line leaves room for this pick
    bj, pin = PL[(x['event_id'], x['player_id'], x['stat'])]; b = json.loads(bj or '{}')
    lines = [v2[0] for v2 in b.values() if v2 and v2[0] is not None]; sgn = 1 if x['side'] == 'MORE' else -1
    x['book'] = ST.median(lines) if lines else None
    if lines:
        rm = sgn * (x['book'] - x['pp_line']); F['room'] = 'room' if rm > 0 else 'against' if rm < 0 else 'same'
        F['room1'] = 'room' if rm >= 1 else 'against' if rm <= -1 else None
    if 'bet365' in b:
        rm = sgn * (b['bet365'][0] - x['pp_line']); F['r365'] = 'room' if rm > 0 else 'against' if rm < 0 else 'same'
    if pin is not None:
        rm = sgn * (pin - x['pp_line']); F['rpin'] = 'room' if rm > 0 else 'against' if rm < 0 else 'same'
    x['F'] = F; P.append(x)
Bld = [x for x in P if x['half'] == 'tune']
med_sd = ST.median(x['msd'] for x in Bld if x['msd'] is not None)
oc = {}
for s in STATS:
    v = sorted(x['of'] for x in Bld if x['stat'] == s); oc[s] = (v[len(v) // 3], v[2 * len(v) // 3])
for x in P:
    if x['msd'] is not None: x['F']['steady'] = 'steady' if x['msd'] <= med_sd else 'moved'
    a, b = oc[x['stat']]; x['F']['opp'] = 'lot' if x['of'] >= b else 'little' if x['of'] <= a else 'middle'
TESTS = [('mate', 'Teammate out', 'out', 'none', 'a usual teammate is out', 'nobody usual is out'), ('trend', 'Minutes trend (up vs down)', 'up', 'down', 'minutes up 3+', 'minutes down 3+'),
         ('steady', 'Minutes steady vs moved around', 'steady', 'moved', 'steady', 'moved around'), ('big', 'Spread size', 'big', 'small', 'spread 10+', 'spread under 10'),
         ('fav', "Player's team favored vs underdog", 'fav', 'dog', 'favored', 'underdog'), ('b2b', 'Back-to-back', 'yes', 'no', 'played yesterday', 'did not'),
         ('rest', 'Rest days', '2+', '0-1', '2+ days off', '0-1 days off'), ('opp', 'Opponent allows', 'lot', 'little', 'allows a lot', 'allows little'),
         ('room', 'Room vs book median (any gap)', 'room', 'against', 'book line favors pick', 'book line against pick'), ('room1', 'Room vs book median (1+ gap)', 'room', 'against', '1+ in favor', '1+ against'),
         ('r365', 'Room vs bet365 only', 'room', 'against', 'bet365 favors pick', 'bet365 against pick'), ('rpin', 'Room vs Pinnacle only', 'room', 'against', 'Pinnacle favors pick', 'Pinnacle against pick')]
def rec(X): return (sum(x['won'] for x in X), sum(1 - x['won'] for x in X))
def rs(t): return '%d won, %d lost' % t
def pct(t): return t[0] / sum(t) if sum(t) else None
def zz(a, b):
    na, nb = sum(a), sum(b)
    if not na or not nb: return 0.0
    p = (a[0] + b[0]) / (na + nb); s = math.sqrt(p * (1 - p) * (1 / na + 1 / nb)) if 0 < p < 1 else 0
    return (a[0] / na - b[0] / nb) / s if s else 0.0
def judge(a1, b1, a2, b2):
    enough = min(sum(a1), sum(b1), sum(a2), sum(b2)) >= MIN_SIDE
    d1, d2 = pct(a1), pct(a2)
    if None in (pct(a1), pct(b1), pct(a2), pct(b2)): return 'too few', None
    g1, g2 = d1 - pct(b1), d2 - pct(b2); same = g1 * g2 > 0
    if enough: return ('HELPS' if same else 'flips'), (g1, g2)
    return ('same way, too few' if same else 'flips, too few'), (g1, g2)
CELLS = ['points', 'points+rebounds+assists', 'rebounds', 'rebounds+assists', 'fieldGoalsMade', 'ALL']
def table(key, A, B, halves, floor_list=(60, 70, 50)):
    out = []; res = []
    for fl in floor_list:
        for cell in CELLS:
            for side in ('MORE', 'LESS'):
                Z = [x for x in P if x['win_prob'] >= fl and x['side'] == side and (cell == 'ALL' or x['stat'] == cell)]
                H1, H2 = [x for x in Z if halves(x) == 1], [x for x in Z if halves(x) == 2]
                a1, b1, a2, b2 = [rec([x for x in H if x['F'].get(key) == v]) for H in (H1, H2) for v in (A, B)]
                v, gaps = judge(a1, b1, a2, b2)
                z = (zz(a1, b1) + zz(a2, b2)) / math.sqrt(2)
                res.append(dict(fl=fl, cell=cell, side=side, v=v, gaps=gaps, z=z, a1=a1, b1=b1, a2=a2, b2=b2))
                g = ('%+.0f, %+.0f pts, z %+.1f' % (gaps[0] * 100, gaps[1] * 100, z)) if gaps else '-'
                out.append('| %s | %s | %s | %s | %s | %s | %s | %s | %s |' % ('%d+' % fl if fl != 50 else 'all (extra)', SHORT[cell], side, rs(a1), rs(b1), rs(a2), rs(b2), g, v))
    return out, res
half3 = lambda x: 1 if x['half'] == 'tune' else 2
L = ['# Step 4 facts: numbers, 2026-10-31', '', 'Backtest only, on the %d Step 3 picks. Build half: dates before %s. Check half: %s on. A pick won if it beat the PrizePicks line; ties are out, as in Step 3.' % (len(P), CUT, CUT), '']
# --- checks
L += ['## Data checks', '']
L.append('- Step 3 picks reproduced from history: projection off by %.3f on average (largest %.2f), Win Prob off by %.3f on average (largest %.2f). Raw field goals read for %d player-games.' % (ST.mean(diffs), max(diffs), ST.mean(diffp), max(diffp), len(fgm)))
for lab, lo, hi in (('before Feb 2025', '0', '2025-02-01'), ('Feb 2025 to Jan 2026', '2025-02-01', '2026-02-01'), ('Feb 2026 on', '2026-02-01', '9')):
    G = [g for g in games.values() if lo <= g['game_date'] < hi and g['home_pts'] is not None]
    c = [abs(g['close_spread_home'] + g['home_pts'] - g['away_pts']) for g in G if g['close_spread_home'] is not None]
    o = [abs(g['open_spread_home'] + g['home_pts'] - g['away_pts']) for g in G if g['open_spread_home'] is not None]
    L.append('- Average miss of spread vs final margin, %s: close %s on %d games, open %s on %d games. A fair spread misses by about 11-12.' % (lab, '%.1f' % ST.mean(c) if c else 'n/a', len(c), '%.1f' % ST.mean(o) if o else 'n/a', len(o)))
ow = sorted(g['game_date'] for g in games.values() if g['open_spread_home'] is not None)
L.append('- Spread used: open_spread_home only, first on %s, so **none of the build half has it**. Closes were not used. Picks with an open spread: %d (build %d, check %d).' % (ow[0], sum('big' in x['F'] for x in P), sum('big' in x['F'] for x in Bld), sum('big' in x['F'] and x['half'] == 'check' for x in P)))
n1 = C.Counter(json.loads(PL[(x['event_id'], x['player_id'], x['stat'])][0] or '{}').__len__() for x in P)
ae = [abs(x['book'] - x['result']) for x in P if x['book'] is not None]; ap = [abs(x['pp_line'] - x['result']) for x in P if x['book'] is not None]
L.append('- Book lines used: book_lines_json, the books last updated before the start, for picks with pp_before_start=1. Picks with a usable book line %d of %d, %d of them with only 1 book, bet365 on %d, Pinnacle on %d. Average miss vs result: book median %.2f, PrizePicks %.2f; about equal, so nothing like an in-game line showing up. No timestamps are kept, so the PP and book lines may come from different moments before the start: a book that moved late on news against a PP line last touched hours earlier looks like room, and PP may have moved its line before lock.' % (sum(x['book'] is not None for x in P), len(P), n1[1], sum('r365' in x['F'] for x in P), sum('rpin' in x['F'] for x in P), ST.mean(ae), ST.mean(ap)))
for hl, lab in (('tune', 'build'), ('check', 'check')):
    D = [x for x in P if x['half'] == hl and x['book'] is not None and x['book'] != x['pp_line'] and x['result'] != x['pp_line']]
    w = sum((x['result'] > x['pp_line']) == (x['book'] > x['pp_line']) for x in D)
    L.append('- Book alone, ignoring our guess, %s half: when the book median differs from the PP line, going the way the book points went %d won, %d lost. Book miss %.2f, PP miss %.2f on those rows.' % (lab, w, len(D) - w, ST.mean(abs(x['book'] - x['result']) for x in D), ST.mean(abs(x['pp_line'] - x['result']) for x in D)))
tc = C.Counter((x['half'], x['F'].get('mate', 'unknown')) for x in P)
L.append('- Teammate out counts: build out %d, none %d, unknown %d; check out %d, none %d, unknown %d. Unknown reasons, with minutes: %s.' % (tc[('tune', 'out')], tc[('tune', 'none')], tc[('tune', 'unknown')], tc[('check', 'out')], tc[('check', 'none')], tc[('check', 'unknown')], dict(why)))
bad = C.Counter(); tot = C.Counter()
for k, b in Box.items():
    m = games[k[0]]['game_date'][:7]; tot[m] += 1; bad[m] += not Complete[k]
L.append('- Team box scores missing players (under %d minutes or under 8 players): %d of %d overall; by month from 2025-02: %s.' % (BOX_MIN, sum(bad.values()), sum(tot.values()), ', '.join('%s %d/%d' % (m, bad[m], tot[m]) for m in sorted(tot) if m >= '2025-02')))
dup = C.Counter((x['player_id'], x['game_date'], x['stat']) for x in P)
dg = C.Counter((g['game_date'], norm(g['home']), norm(g['away'])) for g in games.values())
L.append('- Duplicates: %d same matchup/date games stored under more than one event id (%d of them from 2025-02 on); %d Step 3 picks repeat a player, date and stat. Step 3 did not remove these from player history. Same-game picks are not independent, so z numbers run a bit high.' % (sum(v > 1 for v in dg.values()), sum(v > 1 and k[0] >= '2025-02' for k, v in dg.items()), sum(v - 1 for v in dup.values() if v > 1)))
L.append("- Names: games and opponents carry both 'LA Clippers' and 'Los Angeles Clippers', and the team column says 'home'/'away' on some Jan-Feb 2025 rows. Step 3's opponent factor treats the Clippers as two teams (small error in Step 3, left as is so Win Prob stays the same); the facts here merge them.")
L.append('- Cut-offs from the build half: minutes moved-around line %.2f (spread of last 10 games; at or under = steady). Opponent factor, bottom/top third: %s.' % (med_sd, {SHORT[s]: (round(v[0], 3), round(v[1], 3)) for s, v in oc.items()}))
L += ['', '## How each fact is decided', '',
 '- **Teammate out:** "usual" = another player on the team who played in at least 3 of the team\'s last 5 complete-box games (within 30 days) and averaged %d+ minutes in them. "Out" = no row with minutes above 0 in this game\'s box. Games with an incomplete box are left out so missing data is not read as out. **This fact reads this game\'s box score**, so it is the only one that is not strictly pre-match: late scratches count as known, and a real board would need an injury report at lock.' % USUAL_MIN,
 '- **Minutes trend:** average of last 3 games minus average of the 10 before them. Up = +%d or more, down = -%d or less; flat is left out of the comparison. Needs 13 earlier games.' % (TREND, TREND),
 '- **Steady vs moved around:** spread of minutes over the last 10 games, cut at the build-half median.',
 '- **Spread:** absolute open spread %d+ vs under %d. Favored vs underdog from the same open spread.' % (BIG_SPREAD, BIG_SPREAD),
 '- **Back-to-back / rest:** days between this player\'s earlier games and this one. A skipped game or a missing box row counts as rest.',
 '- **Opponent:** Step 3\'s measure, what the team allowed in its last 15 earlier games vs league, cut at the build-half thirds. Team total only: there is no position data. Step 3 already includes half of this, plus back-to-back, so these are tests of what is left over.',
 '- **Room:** book line minus PP line, flipped for LESS, so plus always means the book leaves room for the pick.', '']
# --- baseline
L += ['## Baseline, no fact', '', '| Win Prob | Stat | Side | Build half | Check half |', '|---|---|---|---|---|']
for fl in (60, 70, 50):
    for cell in CELLS:
        for side in ('MORE', 'LESS'):
            Z = [x for x in P if x['win_prob'] >= fl and x['side'] == side and (cell == 'ALL' or x['stat'] == cell)]
            L.append('| %s | %s | %s | %s | %s |' % ('%d+' % fl if fl != 50 else 'all', SHORT[cell], side, rs(rec([x for x in Z if x['half'] == 'tune'])), rs(rec([x for x in Z if x['half'] == 'check']))))
tb = {}; summ = []
for key, name, A, B, la, lb in TESTS:
    t, res = table(key, A, B, half3); tb[key] = (name, la, lb, t, res)
real = [r for k in tb for r in tb[k][4] if r['fl'] != 50]; extra = [r for k in tb for r in tb[k][4] if r['fl'] == 50]
def lst(rows, key=None):
    out = []
    for k in tb:
        for r in tb[k][4]:
            if r in rows and r['v'] == 'HELPS':
                n, la, lb = tb[k][:3]; bet = la if r['gaps'][0] > 0 else lb
                x, y = (r['a1'], r['a2']) if r['gaps'][0] > 0 else (r['b1'], r['b2']); u, w = (r['b1'], r['b2']) if r['gaps'][0] > 0 else (r['a1'], r['a2'])
                out.append('- %s, %s %s %s: better side "%s". Build %s vs %s. Check %s vs %s. Gap %+.0f and %+.0f points, combined z %+.1f.' % (n, SHORT[r['cell']], r['side'], '%d+' % r['fl'] if r['fl'] != 50 else 'all picks', bet, rs(x), rs(u), rs(y), rs(w), abs(r['gaps'][0]) * 100, abs(r['gaps'][1]) * 100, abs(r['z'])))
    return out
big = [r for r in real if min(sum(r['a1']), sum(r['b1']), sum(r['a2']), sum(r['b2'])) >= MIN_SIDE]
VS = len(L) + 1
L += ['', '## Verdicts', '', '"Helps" means same direction in both halves with %d+ picks on each side in each half.' % MIN_SIDE, '',
      '**At Win Prob 60+ and 70+:** %d comparisons tested, %d had enough picks. %d pass:' % (len(real), len(big), sum(r['v'] == 'HELPS' for r in real))] + (lst(real) or ['- None.'])
n70 = max((min(sum(r['a1']), sum(r['b1']), sum(r['a2']), sum(r['b2'])) for r in real if r['fl'] == 70), default=0)
L += ['', 'At 70+ the smallest side of the fullest comparison held %d picks, so no fact can pass at 70+ under this rule.' % n70, '']
bigx = [r for r in extra if min(sum(r['a1']), sum(r['b1']), sum(r['a2']), sum(r['b2'])) >= MIN_SIDE]
L += ['**Extra, all picks regardless of Win Prob (not what was asked to count; same rule, to show if a fact does anything at all):** %d comparisons had enough picks, %d same direction, %d flip. Same direction happens about half the time by luck. Those passing with combined z of 2 or more are below; about %d would be expected by luck, and the room rows share the same picks, so they are not separate proofs:' % (len(bigx), sum(r['v'] == 'HELPS' for r in bigx), sum(r['v'] == 'flips' for r in bigx), round(len(bigx) * .046))]
strong = [r for r in extra if r['v'] == 'HELPS' and abs(r['z']) >= 2]
L += lst(strong) or ['- None.']
L += ['', 'Spread cannot pass on Step 3\'s halves: the build half has no open spread. See the inner split below.', '']
VE = len(L)
# --- inner split for spread
G = sorted(x['game_date'] for x in P if 'big' in x['F']); IC = G[len(G) // 2]
half_in = lambda x: 1 if x['game_date'] < IC else 2
L += ['## Spread, split inside the dates that have it', '', 'Picks with an open spread only, split at %s. This is a split of the check half, so it is weaker evidence.' % IC, '']
for key in ('big', 'fav'):
    n, _, _, _, _ = tb[key]; la, lb = [t for t in TESTS if t[0] == key][0][4:6]; A, B = [t for t in TESTS if t[0] == key][0][2:4]
    t, res = table(key, A, B, half_in)
    L += ['### %s' % n, '', '| Win Prob | Stat | Side | Early: %s | Early: %s | Late: %s | Late: %s | Gap | Verdict |' % (la, lb, la, lb), '|---|---|---|---|---|---|---|---|---|'] + t + ['']
    L += ['Passing inside this split: ' + ('; '.join('%s %s %s' % (SHORT[r['cell']], r['side'], '%d+' % r['fl'] if r['fl'] != 50 else 'all picks') for r in res if r['v'] == 'HELPS') or 'none') + '.', '']
# --- full tables
L += ['## Every comparison, Step 3 halves', '', 'Gap = first side minus second side, win rate, build then check. "all (extra)" rows are context only.', '']
for key, (n, la, lb, t, res) in tb.items():
    L += ['### %s' % n, '', '| Win Prob | Stat | Side | Build: %s | Build: %s | Check: %s | Check: %s | Gap | Verdict |' % (la, lb, la, lb), '|---|---|---|---|---|---|---|---|---|'] + t + ['']
# --- Goblin
GB = [(70, 75, '70-74'), (75, 80, '75-79'), (80, 101, '80+')]
def gob(X, s, off):
    out = []
    for x in X:
        if x['stat'] != s: continue
        l2 = x['pp_line'] - off
        if l2 <= 0: continue
        wp = 100 * phi((x['m3'] - l2) / x['s3'])
        if x['result'] == l2: out.append((x['half'], wp, None)); continue
        out.append((x['half'], wp, int(x['result'] > l2)))
    return out
def grec(v, a=0, b=999, half=None):
    w = [y for y in v if a <= y[1] < b and y[2] is not None and (half is None or y[0] == half)]
    return (sum(y[2] for y in w), len(w) - sum(y[2] for y in w))
MORE = [x for x in P if x['side'] == 'MORE']
L += ['## Goblin estimate', '', '**This is an estimate. The data has no Goblin labels.** Lines were lowered by a fixed amount; real Goblins are set by PrizePicks, pay less and may sit at other distances. Records count only players who played.', '',
      'Offsets tried: Points and PRA 1, 2, 3, 4. Reb+Ast 1, 1.5, 2, 3. Rebounds and FG made 0.5, 1, 1.5, 2. Ties on the lowered line are left out.', '',
      'Win Prob is recomputed at each lower line with the Step 3 method: same projection, same spread, same confidence setting (k = 4.0 on all five, tuned on the original lines only, not re-tuned), MORE side only. Inputs were rebuilt from history and checked against the stored Step 3 picks (see Data checks).', '',
      '### Step 3 MORE picks', '', '| Stat | Lower by | Picks | All picks | Under 70 | 70-74 | 75-79 | 80+ | 70+ build half | 70+ check half |', '|---|---|---|---|---|---|---|---|---|---|']
def grow(X, s, off):
    v = gob(X, s, off)
    return '| %s | %s | %d | %s | %s | %s | %s | %s | %s | %s |' % (SHORT[s], off, len(v), rs(grec(v)), rs(grec(v, 0, 70)), rs(grec(v, 70, 75)), rs(grec(v, 75, 80)), rs(grec(v, 80, 999)), rs(grec(v, 70, 999, 'tune')), rs(grec(v, 70, 999, 'check')))
for s in OFFSETS:
    for off in OFFSETS[s]: L.append(grow(MORE, s, off))
L += ['', '### Same, every Step 3 row whatever side it picked at the original line (real Goblins are MORE-only and do not need our MORE first)', '', '| Stat | Lower by | Picks | All picks | Under 70 | 70-74 | 75-79 | 80+ | 70+ build half | 70+ check half |', '|---|---|---|---|---|---|---|---|---|---|']
for s in OFFSETS:
    for off in OFFSETS[s]: L.append(grow(P, s, off))
L += ['', '### Pooled, all five stats, by rung (1st to 4th offset)', '', '| Rows | Rung | All picks | 70-74 | 75-79 | 80+ |', '|---|---|---|---|---|---|']
for lab, X in (('MORE picks', MORE), ('Every row', P)):
    for i in range(4):
        v = sum((gob(X, s, OFFSETS[s][i]) for s in OFFSETS), [])
        L.append('| %s | %d | %s | %s | %s | %s |' % (lab, i + 1, rs(grec(v)), rs(grec(v, 70, 75)), rs(grec(v, 75, 80)), rs(grec(v, 80, 999))))
L.append('')
L = L[:4] + L[VS:VE] + L[4:VS] + L[VE:]
open(OUTF, 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
