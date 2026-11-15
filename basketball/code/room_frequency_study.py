#!/usr/bin/env python3
"""ROOM EDGE FREQUENCY STUDY (his ask 2026-11-05 ~7:07 AM CT).
Can Room Edge 2 + Hot Fade, or Room Edge 2 + Room Edge 1, safely raise how often a Top 3 board posts
without materially cutting profit?  Baseline = Room Edge 2 only.  Fill picks are used ONLY when fewer than
3 Room Edge 2 picks exist, so every baseline board day is identical across variants; the difference is
exactly the ADDED days.  Rules fixed in advance; both halves and both seasons reported.
"""
import sqlite3, os, json, sys, datetime as dt
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import room_edge as RE
BASE = os.path.expanduser('~/ApexSports/basketball'); TODAY = dt.date.today().isoformat()
OUT = os.path.join(BASE, 'reports', '%s_room_frequency_study.md' % TODAY)
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
    r['pside'], r['pconf'], r['form'] = (pr[0].upper(), pr[1], pr[2]) if pr else (None, 0.5, None)
    r['hot'] = r['form'] is not None and r['form'] >= .15
    out.append(r)
rows = out
dates = sorted(r['game_date'] for r in rows); mid = dates[len(dates) // 2]
for r in rows: r['half'] = 'older' if r['game_date'] < mid else 'newer'
SEASONS = sorted(set(r['season'] for r in rows))
def won(r, side): return (r['more_won'] if side == 'MORE' else r['less_won']) == 1
def pct(w, l): return 100.0 * w / (w + l) if w + l else 0
by_day = defaultdict(list)
for r in rows: by_day[r['game_date']].append(r)

# pick kinds.  Each returns (side, tier) or None.  tier 0 = core Room Edge 2, 1+ = fill
def core(r): return (r['rside'], 0) if r['edge'] == 2 else None
def hotfade(r): return (r['pside'], 1) if (r['edge'] != 2 and r['hot'] and r['pside'] == 'LESS') else None
def hotfade_room1(r): return (r['pside'], 1) if (r['edge'] != 2 and r['hot'] and r['pside'] == 'LESS' and (r['room'] or 0) >= 0.5) else None
def edge1(r): return (r['rside'], 1) if r['edge'] == 1 else None
def edge1_agree(r): return (r['rside'], 1) if (r['edge'] == 1 and r['pside'] == r['rside']) else None
def edge1_agree60(r): return (r['rside'], 1) if (r['edge'] == 1 and r['pside'] == r['rside'] and r['pconf'] >= .6) else None
def both(r): return edge1(r) or hotfade(r)
def both_strict(r): return edge1_agree60(r) or hotfade_room1(r)

VARIANTS = [
 ('A. Baseline: Room Edge 2 only (projection ranks)', [core]),
 ('B. Room Edge 2 + Hot Fade fill (hot player, projection LESS, any room)', [core, hotfade]),
 ('B2. Room Edge 2 + Hot Fade fill, only when PP line is not below the books', [core, hotfade_room1]),
 ('C. Room Edge 2 + Room Edge 1 fill (PP line 1 below books, MORE)', [core, edge1]),
 ('C2. Room Edge 2 + Room Edge 1 fill, projection agrees', [core, edge1_agree]),
 ('C3. Room Edge 2 + Room Edge 1 fill, projection agrees 60%+', [core, edge1_agree60]),
 ('D. Room Edge 2 + Edge 1 + Hot Fade fill (both)', [core, both]),
 ('D2. Room Edge 2 + strict Edge 1 (agrees 60%+) + strict Hot Fade (not below books)', [core, both_strict]),
]
N = 3; FULL = 60; STAKE = 10
def build(rs, kinds):
    cands = []
    for r in rs:
        for k in kinds:
            v = k(r)
            if v: cands.append((v[1], -r['pconf'], r['player'], r, v[0])); break
    cands.sort(key=lambda t: t[:3]); c = []; games = set(); players = set()
    for tier, _, _, r, side in cands:
        gk = tuple(sorted((r['team'], r['opponent'])))
        if gk in games or r['player'] in players: continue
        c.append((r, side, tier)); games.add(gk); players.add(r['player'])
        if len(c) == N: break
    return c if len(c) == N else None
L = []
def P(s=''): L.append(s)
P('# Apex Basketball - Room Edge Frequency Study (Top 3)')
P('Date: %s. %d played, graded, non-push props on the 8 board stats, %d slate days. Older half before %s, newer half from %s. Seasons %s. One Top 3 slip a day, one pick per game and per player, ranked by projection chance inside each tier (core Room Edge 2 first, fill second). Fill picks are only used when fewer than 3 Room Edge 2 picks exist, so the baseline days are identical in every variant and the difference is exactly the added days. $%d a day, 6x Power (break-even 1 win in 6 days).' % (TODAY, len(rows), len(by_day), mid, mid, ', '.join(SEASONS), STAKE))
base = {}
for d, rs in sorted(by_day.items()): base[d] = build(rs, [core])
rows_out = []
P(); P('## Whole-board results, every variant')
P(); P('| Variant | Days with board | Older half | Newer half | ' + ' | '.join(SEASONS) + ' | Both | Legs W-L | Fill legs W-L | $ net | $ per board day |'); P('|---|---|---|---|' + '---|' * len(SEASONS) + '---|---|---|---|---|')
added_rows = []
for name, kinds in VARIANTS:
    res = defaultdict(lambda: [0, 0]); lw = ll = fw = fl = 0; add = defaultdict(lambda: [0, 0]); addw = addl = 0
    for d, rs in sorted(by_day.items()):
        c = build(rs, kinds)
        if not c: continue
        wl = sum(1 for r, s, t in c if won(r, s)); full = wl == N
        lw += wl; ll += N - wl
        for r, s, t in c:
            if t: fw += won(r, s); fl += (not won(r, s))
        for k in (rs[0]['half'], rs[0]['season']): res[k][0 if full else 1] += 1
        if base[d] is None:
            for k in (rs[0]['half'], rs[0]['season']): add[k][0 if full else 1] += 1
            addw += full; addl += (not full)
    tw = res['older'][0] + res['newer'][0]; tl = res['older'][1] + res['newer'][1]; days = tw + tl
    money = tw * FULL - days * STAKE
    fmt = lambda x: '%d-%d (%.0f%%)' % (x[0], x[1], pct(*x)) if sum(x) else '-'
    P('| %s | %d of %d (%.0f%%) | %s | %s | %s | %s | %d-%d (%.0f%%) | %s | %+d | %+.1f |' % (name, days, len(by_day), 100.0 * days / len(by_day), fmt(res['older']), fmt(res['newer']), ' | '.join(fmt(res[s]) for s in SEASONS), fmt((tw, tl)), lw, ll, pct(lw, ll), ('%d-%d (%.0f%%)' % (fw, fl, pct(fw, fl)) if fw + fl else '-'), money, money / days if days else 0))
    if kinds != [core]:
        am = addw * FULL - (addw + addl) * STAKE
        added_rows.append('| %s | %d | %s | %s | %s | %s | %+d |' % (name, addw + addl, fmt(add['older']), fmt(add['newer']), ' | '.join(fmt(add[s]) for s in SEASONS), fmt((addw, addl)), am))
P(); P('## The added days only (boards that exist ONLY because of the fill)')
P('Break-even on added days is 1 win in 6 (16.7%). Below that the fill loses money even though total $ may still look fine.')
P(); P('| Variant | Added days | Older half | Newer half | ' + ' | '.join(SEASONS) + ' | Both | $ on added days |'); P('|---|---|---|---|' + '---|' * len(SEASONS) + '---|---|')
for a in added_rows: P(a)
P(); P('## Fill picks as single legs (what each fill pick wins on its own, when it is used)')
P(); P('| Fill pick | Older half | Newer half | Both |'); P('|---|---|---|---|')
for lab, k in [('Hot Fade (hot, projection LESS, not Room Edge 2)', hotfade), ('Hot Fade, PP line not below books', hotfade_room1), ('Room Edge 1 (MORE)', edge1), ('Room Edge 1, projection agrees', edge1_agree), ('Room Edge 1, projection agrees 60%+', edge1_agree60)]:
    cells = []; aw = al = 0
    for h in ('older', 'newer'):
        rs = [(r, k(r)[0]) for r in rows if r['half'] == h and k(r)]; w = sum(1 for r, s in rs if won(r, s)); l = len(rs) - w
        cells.append('%d-%d (%.0f%%)' % (w, l, pct(w, l))); aw += w; al += l
    P('| %s | %s | %d-%d (%.0f%%) |' % (lab, ' | '.join(cells), aw, al, pct(aw, al)))
P(); P('## How many Room Edge 2 picks a day (why fill is needed)')
cov = defaultdict(int)
for d, rs in by_day.items():
    c = build(rs, [core]); n = len({r['player'] for r in rs if r['edge'] == 2}); cov[min(n, 5)] += 1
P(); P('| Room Edge 2 picks (distinct players) | Days |'); P('|---|---|')
for k in sorted(cov): P('| %s | %d |' % ('5+' if k == 5 else k, cov[k]))
open(OUT, 'w').write('\n'.join(L) + '\n'); print('wrote', OUT)
