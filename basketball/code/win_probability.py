#!/usr/bin/env python3
"""Step 3: basketball Win Probability, MORE or LESS than the PrizePicks line, from player stats only (no book lines inside).
Inputs: data/processed/nba_history.sqlite; field goals made read from the raw files on the 2TB drive (read only).
Outputs: data/processed/step3_predictions.sqlite and reports/latest_step3_numbers.md.
Every number for a pick uses only games on earlier dates. Tuned on the first half of the dates; the second half is the check. Offline, no API calls."""
import bisect, collections as C, glob, gzip, json, math, os, sqlite3, statistics as ST
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, 'data', 'processed', 'nba_history.sqlite')
OUT = os.path.join(ROOT, 'data', 'processed', 'step3_predictions.sqlite')
RAW = '/Volumes/2TB Drive/SportsData/sportsgameodds/events/BASKETBALL/NBA'
STATS = {'points': lambda r: r['points'], 'rebounds': lambda r: r['rebounds'], 'rebounds+assists': lambda r: r['rebounds'] + r['assists'],
         'points+rebounds+assists': lambda r: r['points'] + r['rebounds'] + r['assists'], 'fieldGoalsMade': lambda r: r['fgm']}
MIN_GAMES = 10
BANDS = [(50, 55), (55, 60), (60, 65), (65, 70), (70, 75), (75, 80), (80, 101)]
db = sqlite3.connect('file:%s?mode=ro' % DB, uri=True); db.row_factory = sqlite3.Row
fgm = {}
for f in glob.iglob(RAW + '/*/*/*.json.gz'):
    with gzip.open(f, 'rt') as z: e = json.load(z)
    for pid, r in ((e.get('results') or {}).get('game') or {}).items():
        if isinstance(r, dict) and 'fieldGoalsMade' in r: fgm[(e['eventID'], pid)] = r['fieldGoalsMade']
H = C.defaultdict(list); Allow = C.defaultdict(lambda: C.defaultdict(float)); byplayer = {}
rows = [dict(r) for r in db.execute("select * from player_games where minutes>0 and points is not null order by game_date")]
for r in rows:
    r['fgm'] = fgm.get((r['event_id'], r['player_id']))
    for k in ('rebounds', 'assists'):
        r[k] = r[k] or 0
    H[r['player_id']].append(r)
    for s, fn in STATS.items():
        try: Allow[(r['event_id'], r['opponent'])][s] += fn(r)
        except TypeError: pass
games = {g['event_id']: dict(g) for g in db.execute("select * from games where final=1")}
TeamG = C.defaultdict(list)   # defense: what each team allowed, by date
for (eid, team), v in Allow.items():
    g = games.get(eid)
    if g: TeamG[team].append((g['game_date'], dict(v)))
for v in TeamG.values(): v.sort(key=lambda x: x[0])
Lg = C.defaultdict(list)
for t, v in TeamG.items():
    for d, a in v:
        for s, x in a.items(): Lg[s].append((d, x))
for v in Lg.values(): v.sort(key=lambda x: x[0])
def lg_mean(s, d):
    v = Lg[s]; i = bisect.bisect_left(v, (d,)); w = v[max(0, i - 400):i]
    return ST.mean(x for _, x in w) if len(w) >= 50 else None
def opp_factor(s, team, d):
    a = [x[1].get(s) for x in TeamG.get(team, []) if x[0] < d][-15:]
    a = [x for x in a if x is not None]; m = lg_mean(s, d)
    return ST.mean(a) / m if len(a) >= 5 and m else 1.0
def phi(z): return .5 * math.erfc(-z / math.sqrt(2))
props = [dict(r) for r in db.execute("""select event_id, player_id, stat, game_date, season, pp_line, result, more_won, less_won from prop_lines
  where pp_before_start=1 and books_before_start>0 and result is not null and pp_line is not null and stat in (%s)""" % ','.join('?' * len(STATS)), list(STATS))]
dates = sorted(p['game_date'] for p in props); CUT = dates[len(dates) // 2]
F = []; skip = C.Counter()
for p in props:
    hist = H.get(p['player_id'], []); dd = [h['game_date'] for h in hist]; i = bisect.bisect_left(dd, p['game_date'])
    me = next((h for h in hist[i:i + 3] if h['event_id'] == p['event_id']), None)
    if me is None: skip['did not play'] += 1; continue
    fn = STATS[p['stat']]
    past = [h for h in hist[:i] if fn(h) is not None] if p['stat'] == 'fieldGoalsMade' else hist[:i]
    if len(past) < MIN_GAMES: skip['under 10 earlier games'] += 1; continue
    rate = lambda L: sum(fn(h) for h in L) / max(1.0, sum(h['minutes'] for h in L))
    l5, l10 = past[-5:], past[-10:]; sea = [h for h in past if h['season'] == p['season']] or past[-30:]
    mins = .6 * ST.mean(h['minutes'] for h in l5) + .4 * ST.mean(h['minutes'] for h in l10)
    r = .4 * rate(l5) + .35 * rate(l10) + .25 * rate(sea)
    resid = [fn(h) - r * h['minutes'] for h in past[-20:]]
    F.append(dict(p, base=r * mins, sd=max(ST.pstdev(resid), 1.0), of=opp_factor(p['stat'], me['opponent'], p['game_date']), b2b=me['back_to_back'] or 0, home=me['home'], player=me['player'],
                  mins=mins, min_trend=ST.mean(h['minutes'] for h in l5) - ST.mean(h['minutes'] for h in past[-20:])))
Tr = [x for x in F if x['game_date'] < CUT]; Ck = [x for x in F if x['game_date'] >= CUT]
# tuned on the first half only, per prop type
FIT = {}
for s in STATS:
    T = [x for x in Tr if x['stat'] == s]
    if not T: continue
    pred = lambda x, o, adj: x['base'] * (1 + o * (x['of'] - 1)) * adj.get((x['b2b'], x['home']), 1.0)
    o = .5; adj = {}
    for key in {(x['b2b'], x['home']) for x in T}:
        K = [x for x in T if (x['b2b'], x['home']) == key]
        a, b = sum(x['result'] for x in K), sum(pred(x, o, {}) for x in K)
        n = len(K); adj[key] = (a + 50) / (b + 50 * b / max(a, 1)) if n >= 30 and b else 1.0
    best = None
    for sc10 in range(8, 41):
        k = sc10 / 10.0; ll = 0
        for x in T:
            q = phi((pred(x, o, adj) - x['pp_line']) / (x['sd'] * k)); q = min(max(q, .02), .98)
            if x['result'] != x['pp_line']: ll -= math.log(q if x['more_won'] else 1 - q)
        if best is None or ll < best[0]: best = (ll, k)
    FIT[s] = dict(o=o, adj=adj, k=best[1])
for x in F:
    f = FIT.get(x['stat'])
    if not f: x['p'] = None; continue
    m = x['base'] * (1 + f['o'] * (x['of'] - 1)) * f['adj'].get((x['b2b'], x['home']), 1.0)
    pm = phi((m - x['pp_line']) / (x['sd'] * f['k'])); x['proj'] = m; x['p_more'] = pm
    x['side'] = 'MORE' if pm >= .5 else 'LESS'; x['p'] = 100 * max(pm, 1 - pm)
    x['win'] = None if x['result'] == x['pp_line'] else int((x['result'] > x['pp_line']) == (x['side'] == 'MORE'))
F = [x for x in F if x.get('p') is not None and x['win'] is not None]
L = ['# Step 3 numbers', '', 'Split at %s. Tuned on dates before it; dates from it on are the check.' % CUT, 'Skipped: %s' % dict(skip), 'Fit: %s' % {s: dict(k=FIT[s]['k'], adj={str(a): round(b, 3) for a, b in FIT[s]['adj'].items()}) for s in FIT}, '']
def rec(X): return '%d won, %d lost' % (sum(x['win'] for x in X), sum(1 - x['win'] for x in X))
for lab, lo, hi in (('TUNING HALF', '0', CUT), ('CHECK HALF', CUT, '9')):
    Y = [x for x in F if lo <= x['game_date'] < hi]; L += ['## %s: %d picks, %s to %s, %s' % (lab, len(Y), min(x['game_date'] for x in Y), max(x['game_date'] for x in Y), rec(Y))]
    for s in ['ALL'] + list(STATS):
        Z = Y if s == 'ALL' else [x for x in Y if x['stat'] == s]
        L.append('%s: %s | ' % (s, rec(Z)) + ' | '.join('%d-%d: %s' % (a, b - 1 if b < 101 else 100, rec([x for x in Z if a <= x['p'] < b])) for a, b in BANDS if any(a <= x['p'] < b for x in Z)))
    hi70 = [x for x in Y if x['p'] >= 70]; days = {x['game_date'] for x in Y}; dh = {x['game_date'] for x in hi70}
    L.append('70+ picks: %d, %s. Days with props %d, days with a 70+ pick %d, about %.1f per day with props. MORE %s, LESS %s' % (len(hi70), rec(hi70), len(days), len(dh), len(hi70) / max(1, len(days)), rec([x for x in hi70 if x['side'] == 'MORE']), rec([x for x in hi70 if x['side'] == 'LESS'])))
    L.append('By side, all: MORE %s, LESS %s' % (rec([x for x in Y if x['side'] == 'MORE']), rec([x for x in Y if x['side'] == 'LESS'])))
    L.append('By month: ' + ' | '.join('%s %s' % (m, rec([x for x in Y if x['game_date'][:7] == m and x['p'] >= 60])) for m in sorted({x['game_date'][:7] for x in Y})) + ' (60+ picks)')
    L.append('')
if os.path.exists(OUT): os.remove(OUT)
o = sqlite3.connect(OUT); o.execute('create table predictions(event_id,player_id,player,stat,game_date,season,half,pp_line,projected,win_prob,side,result,won)')
o.executemany('insert into predictions values(?,?,?,?,?,?,?,?,?,?,?,?,?)', [(x['event_id'], x['player_id'], x['player'], x['stat'], x['game_date'], x['season'], 'tune' if x['game_date'] < CUT else 'check', x['pp_line'], round(x['proj'], 2), round(x['p'], 1), x['side'], x['result'], x['win']) for x in F]); o.commit()
open(os.path.join(ROOT, 'reports', 'latest_step3_numbers.md'), 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
