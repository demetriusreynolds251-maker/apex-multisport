#!/usr/bin/env python3
"""ROOM EDGE STUDY (his ask 11/5 6:35 AM CT). Room = PrizePicks line minus the middle (median) sportsbook line before tip.
Side taken = the side PrizePicks made easier (PP lower -> MORE, PP higher -> LESS). No projection needed.
Props: clean (PP line before tip, 1+ book before tip, graded) AND the player played (minutes > 0). Pushes excluded."""
import sqlite3, os, json, statistics as st, datetime as dt
from collections import defaultdict
BASE = os.path.expanduser('~/ApexSports/basketball'); TODAY = dt.date.today().isoformat()
OUT = os.path.join(BASE, 'reports', '%s_room_edge_study.md' % TODAY)
con = sqlite3.connect(os.path.join(BASE, 'data/processed/nba_history.sqlite')); con.row_factory = sqlite3.Row
rows = [dict(r) for r in con.execute("""select p.event_id, p.player_id, g.player, g.team, g.opponent, p.stat, p.game_date, p.season, p.pp_line, p.book_lines_json, p.pinnacle_before_start, p.result, p.more_won, p.less_won
  from prop_lines p join player_games g on g.event_id=p.event_id and g.player_id=p.player_id
  where p.pp_before_start=1 and p.result is not null and p.books_before_start>0 and g.minutes>0""")]
try:
    pc = sqlite3.connect(os.path.join(BASE, 'data/processed/phase3_projections.sqlite')); proj = {(r[0], r[1], r[2]): (r[3], r[4]) for r in pc.execute('select event_id, player_id, stat, side, p_side from projections')}
except Exception: proj = {}
NAME = {'points': 'Points', 'rebounds': 'Rebounds', 'assists': 'Assists', 'points+rebounds+assists': 'PRA', 'points+rebounds': 'PR', 'points+assists': 'PA', 'threePointersMade': '3PM',
        'rebounds+assists': 'RA', 'fieldGoalsMade': 'FG Made', 'freeThrowsMade': 'FT Made', 'freeThrowsAttempted': 'FT Att', 'steals': 'Steals', 'blocks': 'Blocks', 'blocks+steals': 'Blk+Stl', 'turnovers': 'Turnovers'}
ORDER = ['points', 'rebounds', 'assists', 'points+rebounds+assists', 'points+rebounds', 'points+assists', 'threePointersMade', 'rebounds+assists', 'fieldGoalsMade', 'freeThrowsMade', 'freeThrowsAttempted', 'steals', 'blocks', 'blocks+steals', 'turnovers']
for r in rows:
    try: bl = [v[0] for v in json.loads(r['book_lines_json'] or '{}').values() if v and v[0] is not None]
    except Exception: bl = []
    r['nb'] = len(bl); r['bm'] = st.median(bl) if bl else None; r['room'] = (r['pp_line'] - r['bm']) if bl else None
    r['push'] = r['result'] == r['pp_line']
    if r['room'] is None or r['room'] == 0: r['rside'] = None; r['rwon'] = None
    else:
        r['rside'] = 'more' if r['room'] < 0 else 'less'; r['rwon'] = (r['more_won'] if r['rside'] == 'more' else r['less_won'])
    pr = proj.get((r['event_id'], r['player_id'], r['stat'])); r['pside'], r['pconf'] = (pr if pr else (None, None))
rows = [r for r in rows if not r['push']]
dates = sorted(r['game_date'] for r in rows); mid = dates[len(dates) // 2]
for r in rows: r['half'] = 'older' if r['game_date'] < mid else 'newer'
SEASONS = sorted(set(r['season'] for r in rows))
def pct(w, l): return 100.0 * w / (w + l) if w + l else 0
def rec(rs): w = sum(1 for r in rs if r['rwon'] == 1); return w, len(rs) - w
def ev3(p): return 6 * p ** 3 - 1          # 3-pick Power at 6x, $[amount] slip, all three legs at this win rate
def ev_leg(p): return (6 ** (1 / 3)) * p - 1  # the per-leg way to say it: what $[amount] on this leg is worth inside a 6x three-leg slip
L = []
def P(s=''): L.append(s)
P('# Apex Basketball - Room Edge Study')
P('Date: %s. %d played, graded, non-push clean props. Room = PrizePicks line minus the middle sportsbook line before tip. Side taken = the side PrizePicks made easier. Older half before %s, newer half from %s. Seasons on file: %s.' % (TODAY, len(rows), mid, mid, ', '.join(SEASONS)))
P('Break-even: 55.0%% per leg on a 3-pick Power at 6x (all three legs alike). "EV per $1" = 6 x (win rate)^3 - 1 for a $1 three-leg slip at that leg rate; 0 is break-even.')
P()
LEVELS = [('PP lower by 0.5', lambda r: -1 < r['room'] < 0), ('PP lower by 1', lambda r: -2 < r['room'] <= -1), ('PP lower by 2+', lambda r: r['room'] <= -2),
          ('PP higher by 0.5', lambda r: 0 < r['room'] < 1), ('PP higher by 1', lambda r: 1 <= r['room'] < 2), ('PP higher by 2+', lambda r: r['room'] >= 2)]
def level_table(title, rs):
    P('### %s (%d props, %d with a room)' % (title, len(rs), sum(1 for r in rs if r['rside'])))
    P(); P('| Room | Side | Win-loss | Win % | EV per $1 (3-pick 6x) | Older half | Newer half | ' + ' | '.join(SEASONS) + ' | Verdict |'); P('|---|---|---|---|---|---|---|' + '---|' * len(SEASONS) + '---|')
    for lab, fn in LEVELS:
        sel = [r for r in rs if r['rside'] and fn(r)]
        if not sel: P('| %s | %s | - | | | | | %s | none |' % (lab, 'MORE' if 'lower' in lab else 'LESS', ' | '.join('-' * len(SEASONS)))); continue
        w, l = rec(sel); halves = []; ok = True
        for h in ('older', 'newer'):
            hw, hl = rec([r for r in sel if r['half'] == h]); halves.append('%d-%d (%.0f%%)' % (hw, hl, pct(hw, hl)) if hw + hl else '-')
            if hw + hl < 40 or pct(hw, hl) < 55: ok = False
        seas = []
        for s in SEASONS:
            sw, sl = rec([r for r in sel if r['season'] == s]); seas.append('%d-%d (%.0f%%)' % (sw, sl, pct(sw, sl)) if sw + sl else '-')
        p = w / (w + l)
        P('| %s | %s | %d-%d | %.1f%% | %+.2f | %s | %s | %s |' % (lab, 'MORE' if 'lower' in lab else 'LESS', w, l, 100 * p, ev3(p), ' | '.join(halves), ' | '.join(seas), 'PASS' if ok else ('small' if w + l < 80 else 'fail')))
    P()
P('## 1-3. Every prop type, every gap size')
level_table('ALL PROP TYPES', rows)
for s in ORDER:
    rs = [r for r in rows if r['stat'] == s]
    if rs: level_table(NAME.get(s, s), rs)
P('### Fantasy Score')
P('No Fantasy Score lines in the history (the archive has box-score stats only). The saver has been recording PrizePicks Fantasy lines since 2026-11-04; this table fills in after a few weeks of real lines.')
P()
P('## How many books stand behind the middle line?')
P(); P('| Books | Room 1+ props | Win-loss (book side) | Win % |'); P('|---|---|---|---|')
for lab, fn in [('1 book', lambda r: r['nb'] == 1), ('2 books', lambda r: r['nb'] == 2), ('3+ books', lambda r: r['nb'] >= 3)]:
    sel = [r for r in rows if r['rside'] and abs(r['room']) >= 1 and fn(r)]; w, l = rec(sel); P('| %s | %d | %d-%d | %.1f%% |' % (lab, len(sel), w, l, pct(w, l)))
P()
# ---------------- Room Edge Score
def lvl(r):
    a = abs(r['room']); return '0.5' if a < 1 else ('1' if a < 2 else '2+')
def grp(stat): return stat if stat in ('points', 'rebounds', 'assists', 'points+rebounds+assists', 'points+rebounds', 'points+assists', 'rebounds+assists', 'fieldGoalsMade') else 'other'
def bucket(r): return (grp(r['stat']), lvl(r), r['rside'])
train = defaultdict(lambda: [0, 0])
for r in rows:
    if r['rside'] and r['half'] == 'older':
        train[bucket(r)][0] += (r['rwon'] == 1); train[bucket(r)][1] += 1
def score(r):
    """Room Edge Score 0-100 = won-lost rate of the same bucket (stat, gap, side) in the OLDER half, shrunk toward 52 with 20 pretend picks."""
    w, n = train.get(bucket(r), [0, 0]); return round(100 * (w + 20 * .52) / (n + 20), 1)
for r in rows: r['res'] = score(r) if r['rside'] else None
P('## 5. Room Edge Score')
P('Score = the won-lost rate of the same kind of pick (prop type, gap size, side) in the OLDER half, shrunk toward 52 with 20 pretend picks. Learned on the older half only, then checked on the newer half. 55 = break-even.')
P(); P('| Prop type | Gap | Side | Older W-L (the score) | Newer W-L (did it hold?) |'); P('|---|---|---|---|---|')
newer_rec = defaultdict(lambda: [0, 0])
for r in rows:
    if r['rside'] and r['half'] == 'newer': newer_rec[bucket(r)][0] += (r['rwon'] == 1); newer_rec[bucket(r)][1] += 1
for b in sorted(train, key=lambda b: -train[b][1]):
    w, n = train[b]
    if n < 30: continue
    nw, nn = newer_rec.get(b, [0, 0]); P('| %s | %s | %s | %d-%d (%.0f) | %d-%d (%.0f%%) |' % (NAME.get(b[0], b[0]), b[1], b[2].upper(), w, n - w, pct(w, n - w), nw, nn - nw, pct(nw, nn - nw)))
P()
P('### Does the score sort picks? (newer half only, score learned on the older half)')
P(); P('| Room Edge Score | Newer W-L | Win % | EV per $1 |'); P('|---|---|---|---|')
for lo, hi in [(0, 52), (52, 55), (55, 58), (58, 62), (62, 101)]:
    sel = [r for r in rows if r['rside'] and r['half'] == 'newer' and lo <= r['res'] < hi]
    if sel: w, l = rec(sel); P('| %s-%s | %d-%d | %.1f%% | %+.2f |' % (lo, hi if hi < 101 else '', w, l, pct(w, l), ev3(w / (w + l)) if w + l else 0))
P()
# ---------------- boards
P('## 4 and 6. Can room alone carry a board? Top 3 / Elite 6 / Top 10, one slip a day, every leg must win')
by_day = defaultdict(list)
for r in rows: by_day[r['game_date']].append(r)
def pick_key(r): return (-(r['res'] or 0), -abs(r['room'] or 0), r['player'])
V = {
 'A. Room REQUIRED (1+), ranked by Room Edge Score, no 3PM': (lambda r: r['rside'] and abs(r['room']) >= 1 and r['stat'] != 'threePointersMade', pick_key),
 'B. Room REQUIRED (0.5+), ranked by Room Edge Score, no 3PM': (lambda r: r['rside'] and r['stat'] != 'threePointersMade', pick_key),
 'C. Room 1+ as QUALIFIER, ranked by projection chance': (lambda r: r['rside'] and abs(r['room']) >= 1 and r['stat'] != 'threePointersMade' and r['pconf'] is not None and r['pside'] == r['rside'], lambda r: (-r['pconf'], r['player'])),
 'D. Room 1+ LESS side only, ranked by score': (lambda r: r['rside'] == 'less' and abs(r['room']) >= 1 and r['stat'] != 'threePointersMade', pick_key),
 'E. Room 1+, score 57+ only, ranked by score': (lambda r: r['rside'] and abs(r['room']) >= 1 and r['stat'] != 'threePointersMade' and r['res'] >= 57, pick_key),
 'F. No room needed: projection chance ranking (baseline)': (lambda r: r['pconf'] is not None, lambda r: (-r['pconf'], r['player'])),
}
PAY = {3: (60, 0), 6: (250, 20), 10: (0, 0)}
P(); P('| Board rule | Size | Older half days W-L | Newer half days W-L | ' + ' | '.join(SEASONS) + ' | Both | Near miss | Days no board | Legs W-L | $10/day |'); P('|---|---|---|---|' + '---|' * len(SEASONS) + '---|---|---|---|---|')
for name, (filt, key) in V.items():
    for n in (3, 6, 10):
        res = {'older': [0, 0], 'newer': [0, 0]}; seas = {s: [0, 0] for s in SEASONS}; near = nob = lw = ll = 0
        for d, rs in sorted(by_day.items()):
            c = []; games = set(); players = set()
            for r in sorted([r for r in rs if filt(r)], key=key):
                gk = tuple(sorted((r['team'], r['opponent'])))
                if gk in games or r['player'] in players: continue
                c.append(r); games.add(gk); players.add(r['player'])
                if len(c) == n: break
            if len(c) < n: nob += 1; continue
            won_legs = sum(1 for r in c if (r['rwon'] == 1) if r['rside']) if filt is not V['F. No room needed: projection chance ranking (baseline)'][0] else sum(1 for r in c if ((r['pside'] == 'more') == (r['more_won'] == 1)))
            lw += won_legs; ll += n - won_legs; h = rs[0]['half']; s = rs[0]['season']
            if won_legs == n: res[h][0] += 1; seas[s][0] += 1
            else: res[h][1] += 1; seas[s][1] += 1
            if won_legs == n - 1: near += 1
        tw = res['older'][0] + res['newer'][0]; tl = res['older'][1] + res['newer'][1]; full, part = PAY[n]
        money = tw * full + (near * part if n == 6 else 0) - (tw + tl) * 10 if n != 10 else 0
        fmt = lambda x: '%d-%d (%.0f%%)' % (x[0], x[1], pct(*x)) if sum(x) else '-'
        P('| %s | %s | %s | %s | %s | %s | %d | %d | %d-%d (%.0f%%) | %s |' % (name, {3: 'Top 3', 6: 'Elite 6', 10: 'Top 10'}[n], fmt(res['older']), fmt(res['newer']), ' | '.join(fmt(seas[s]) for s in SEASONS), fmt((tw, tl)), near, nob, lw, ll, pct(lw, ll), ('%+d over %d days' % (money, tw + tl)) if n != 10 else 'no PP slip'))
P()
P('Payouts: Top 3 Power 6x; Elite 6 Flex 25x full, 2x at 5 of 6 (4 of 6 refund not counted). Break-even Top 3 = 1 win in 6 days (17%); Elite 6 needs about 1 full win in 25 days plus the 5-of-6 days.')
P()
# per-day coverage
cov = defaultdict(int)
for d, rs in by_day.items(): cov[min(len([r for r in rs if r['rside'] and abs(r['room']) >= 1 and r['stat'] != 'threePointersMade']), 10)] += 1
P('### How many room-1+ picks a day (no 3PM)?')
P(); P('| Picks available | Days |'); P('|---|---|')
for k in sorted(cov): P('| %s | %d |' % ('10+' if k == 10 else k, cov[k]))
P()
open(OUT, 'w').write('\n'.join(L) + '\n'); print('wrote', OUT)
