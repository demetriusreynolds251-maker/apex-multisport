#!/usr/bin/env python3
"""ROOM EDGE BOARD REPLAY (his point 6 and 10, 2026-11-05). Top 3 / Elite 6 / Top 10 x {room only, projection only, room + projection, room + projection + hot fade}.
Played, graded, non-push clean props on the 8 prioritized stats. One slip a day, one pick per game and per player. Rules fixed in advance (nothing learned), so both halves and all seasons are honest tests."""
import sqlite3, os, json, sys, statistics as st, datetime as dt
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import room_edge as RE
BASE = os.path.expanduser('~/ApexSports/basketball'); TODAY = dt.date.today().isoformat()
OUT = os.path.join(BASE, 'reports', '%s_room_board_replay.md' % TODAY)
con = sqlite3.connect(os.path.join(BASE, 'data/processed/nba_history.sqlite')); con.row_factory = sqlite3.Row
rows = [dict(r) for r in con.execute("""select p.event_id, p.player_id, g.player, g.team, g.opponent, p.stat, p.game_date, p.season, p.pp_line, p.book_lines_json, p.result, p.more_won, p.less_won
  from prop_lines p join player_games g on g.event_id=p.event_id and g.player_id=p.player_id
  where p.pp_before_start=1 and p.result is not null and p.books_before_start>0 and g.minutes>0 and p.result<>p.pp_line""")]
pc = sqlite3.connect(os.path.join(BASE, 'data/processed/phase3_projections.sqlite'))
proj = {(a, b, c): (side, p, form) for a, b, c, side, p, form in pc.execute('select event_id, player_id, stat, side, p_side, form from projections')}
out = []
for r in rows:
    if not RE.stat_allowed(r['stat']): continue
    try: bl = [v[0] for v in json.loads(r['book_lines_json'] or '{}').values() if v and v[0] is not None]
    except Exception: bl = []
    e = RE.room_edge(r['pp_line'], bl); r.update(edge=e['edge'], rside=e['side'], room=e['room'])
    pr = proj.get((r['event_id'], r['player_id'], r['stat']))
    r['pside'], r['pconf'], r['form'] = (pr[0].upper(), pr[1], pr[2]) if pr else (None, None, None)
    r['hot'] = r['form'] is not None and r['form'] >= .15
    out.append(r)
rows = out
dates = sorted(r['game_date'] for r in rows); mid = dates[len(dates) // 2]
for r in rows: r['half'] = 'older' if r['game_date'] < mid else 'newer'
SEASONS = sorted(set(r['season'] for r in rows))
def won(r, side): return (r['more_won'] if side == 'MORE' else r['less_won']) == 1
def pct(w, l): return 100.0 * w / (w + l) if w + l else 0
L = []
def P(s=''): L.append(s)
P('# Apex Basketball - Room Edge Board Replay')
P('Date: %s. %d played, graded, non-push props on the 8 board stats (points, rebounds, assists, PRA, PR, PA, RA, FG made). Older half before %s, newer half from %s. Seasons: %s. Rules fixed in advance; nothing learned from the data.' % (TODAY, len(rows), mid, mid, ', '.join(SEASONS)))
P()
P('## Per pick: what each layer does on its own and together')
P(); P('| Picks | Side taken | Older half | Newer half | ' + ' | '.join(SEASONS) + ' | Both |'); P('|---|---|---|---|' + '---|' * len(SEASONS) + '---|')
def side_room(r): return r['rside']
def side_proj(r): return r['pside']
PICKS = [
 ('Room Edge 2 only', lambda r: r['edge'] == 2, side_room),
 ('Room Edge 1 only', lambda r: r['edge'] == 1, side_room),
 ('Room Edge 0 (same line / half point), book side n/a: blind LESS', lambda r: r['edge'] == 0, lambda r: 'LESS'),
 ('Projection only, 60%+ sure, any room', lambda r: r['pconf'] is not None and r['pconf'] >= .6, side_proj),
 ('Projection only, 70%+ sure, any room', lambda r: r['pconf'] is not None and r['pconf'] >= .7, side_proj),
 ('Room Edge 2 + projection agrees (confirmation)', lambda r: r['edge'] == 2 and r['pside'] == r['rside'], side_room),
 ('Room Edge 2 + projection DISAGREES', lambda r: r['edge'] == 2 and r['pside'] is not None and r['pside'] != r['rside'], side_room),
 ('Room Edge 2 + projection agrees 60%+', lambda r: r['edge'] == 2 and r['pside'] == r['rside'] and r['pconf'] >= .6, side_room),
 ('Room Edge 2 LESS + hot player (fade)', lambda r: r['edge'] == 2 and r['rside'] == 'LESS' and r['hot'], side_room),
 ('Room Edge 2 LESS, not hot', lambda r: r['edge'] == 2 and r['rside'] == 'LESS' and not r['hot'], side_room),
 ('Hot fade alone (hot + projection LESS), no room needed', lambda r: r['hot'] and r['pside'] == 'LESS', side_proj),
 ('Room Edge 2 + projection agrees + hot fade', lambda r: r['edge'] == 2 and r['pside'] == r['rside'] == 'LESS' and r['hot'], side_room),
]
for lab, fn, sf in PICKS:
    cells = []; aw = al = 0
    for grpname, key in [('older', 'half'), ('newer', 'half')] + [(s, 'season') for s in SEASONS]:
        rs = [r for r in rows if r[key] == grpname and fn(r) and sf(r)]; w = sum(1 for r in rs if won(r, sf(r))); l = len(rs) - w
        cells.append('%d-%d (%.0f%%)' % (w, l, pct(w, l)) if rs else '-')
        if key == 'half': aw += w; al += l
    P('| %s | %s | %s | %d-%d (%.0f%%) |' % (lab, 'book side' if sf is side_room else ('projection' if sf is side_proj else 'LESS'), ' | '.join(cells), aw, al, pct(aw, al)))
P()
# ---- boards
P('## Boards: one slip a day, every leg must win, one pick per game and per player')
P('Payouts: Top 3 Power 6x (break-even 1 win in 6 days); Elite 6 Flex 25x full, 2x at 5 of 6, 0.4x at 4 of 6; Top 10 has no PrizePicks slip (shown as legs only). Volume = days with a full board out of %d days with props.' % len(set(dates)))
by_day = defaultdict(list)
for r in rows: by_day[r['game_date']].append(r)
def hotboost(r): return 1 if (r['hot'] and r['rside'] == 'LESS') else 0
BOARDS = {
 '1. Room only: Edge 2 required, ranked by gap size': (lambda r: r['edge'] == 2, lambda r: (-abs(r['room']), r['player']), side_room),
 '2. Projection only: no room, ranked by projection chance': (lambda r: r['pconf'] is not None, lambda r: (-r['pconf'], r['player']), side_proj),
 '3. Room + Projection: Edge 2, projection agrees, ranked by projection chance': (lambda r: r['edge'] == 2 and r['pside'] == r['rside'], lambda r: (-r['pconf'], r['player']), side_room),
 '3b. Room + Projection: Edge 2, projection ranks (agree or not)': (lambda r: r['edge'] == 2 and r['pconf'] is not None, lambda r: (-r['pconf'], r['player']), side_room),
 '4. Room + Projection + Hot Fade: as 3, hot LESS picks ranked first': (lambda r: r['edge'] == 2 and r['pside'] == r['rside'], lambda r: (-hotboost(r), -r['pconf'], r['player']), side_room),
 '4b. Room + Projection, then Hot Fade picks fill empty spots': (lambda r: (r['edge'] == 2 and r['pside'] == r['rside']) or (r['hot'] and r['pside'] == 'LESS' and r['edge'] != 2), lambda r: (0 if r['edge'] == 2 else 1, -r['pconf'], r['player']), lambda r: r['rside'] if r['edge'] == 2 else r['pside']),
 '5. Room Edge 2 + Edge 1 as fill, ranked by projection chance': (lambda r: r['edge'] >= 1 and r['pside'] == r['rside'], lambda r: (-r['edge'], -r['pconf'], r['player']), side_room),
}
P(); P('| Board | Size | Older half | Newer half | ' + ' | '.join(SEASONS) + ' | Both | Near miss | Volume (days with board) | Legs W-L | $10 a day |'); P('|---|---|---|---|' + '---|' * len(SEASONS) + '---|---|---|---|---|')
PAY = {3: (60, 0, 0), 6: (250, 20, 4), 10: (0, 0, 0)}
for name, (filt, key, sf) in BOARDS.items():
    for n in (3, 6, 10):
        res = defaultdict(lambda: [0, 0]); near = near2 = nob = lw = ll = 0
        for d, rs in sorted(by_day.items()):
            c = []; games = set(); players = set()
            for r in sorted([r for r in rs if filt(r) and sf(r)], key=key):
                gk = tuple(sorted((r['team'], r['opponent'])))
                if gk in games or r['player'] in players: continue
                c.append(r); games.add(gk); players.add(r['player'])
                if len(c) == n: break
            if len(c) < n: nob += 1; continue
            wl = sum(1 for r in c if won(r, sf(r))); lw += wl; ll += n - wl
            for k in (rs[0]['half'], rs[0]['season']): res[k][0 if wl == n else 1] += 1
            if wl == n - 1: near += 1
            if wl == n - 2: near2 += 1
        tw = res['older'][0] + res['newer'][0]; tl = res['older'][1] + res['newer'][1]; full, p1, p2 = PAY[n]
        money = tw * full + near * p1 + near2 * p2 - (tw + tl) * 10
        fmt = lambda x: '%d-%d (%.0f%%)' % (x[0], x[1], pct(*x)) if sum(x) else '-'
        P('| %s | %s | %s | %s | %s | %s | %d | %d of %d | %d-%d (%.0f%%) | %s |' % (name, {3: 'Top 3', 6: 'Elite 6', 10: 'Top 10'}[n], fmt(res['older']), fmt(res['newer']), ' | '.join(fmt(res[s]) for s in SEASONS), fmt((tw, tl)), near, tw + tl, len(by_day), lw, ll, pct(lw, ll), ('%+d' % money) if n != 10 else 'no slip'))
P()
cov = defaultdict(int)
for d, rs in by_day.items():
    c = [r for r in rs if r['edge'] == 2 and r['pside'] == r['rside']]; cov[min(len({r['player'] for r in c}), 10)] += 1
P('### Expected board volume: Room Edge 2 picks with projection agreeing, per day')
P(); P('| Picks a day | Days |'); P('|---|---|')
for k in sorted(cov): P('| %s | %d |' % ('10+' if k == 10 else k, cov[k]))
P()
open(OUT, 'w').write('\n'.join(L) + '\n'); print('wrote', OUT)
