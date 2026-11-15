#!/usr/bin/env python3
"""APEX BASKETBALL - Phase 4 simulation engine (first build) + Phase 5/6/7 walk-forward replay.
Input: data/processed/phase3_projections.sqlite (per-prop box-score projection, book median, facts).
Raw chance: book-anchored projection (0.4 ours + 0.6 book median), Normal for points/combos/rebounds/assists/FGM,
Poisson for threes/steals/blocks/blocks+steals; variance +10% on back-to-back, +15% when spread 10+.
Honest chance: bucket table learned on the OLDER half, applied to the NEWER half.
Boards: gated picks (room agrees 0.5+, not threes), ranked by honest chance, Top 3/5/6 whole-slip days on the NEWER half.
Stdlib only."""
import sqlite3, os, math, datetime as dt, statistics as st
from collections import defaultdict
BASE = os.path.expanduser('~/ApexSports/basketball')
TODAY = dt.date.today().isoformat()
OUT = os.path.join(BASE, 'reports', '%s_phase4_engine.md' % TODAY)
TABLE = os.path.join(BASE, 'calibration', 'honest_table_v1.json')
POISSON = {'threePointersMade', 'steals', 'blocks', 'blocks+steals'}
W_OURS, W_BOOK = 0.4, 0.6

def ncdf(x): return 0.5 * (1 + math.erf(x / math.sqrt(2)))
def pois_cdf(k, lam):
    k = int(math.floor(k)); 
    if k < 0: return 0.0
    s = 0.0; term = math.exp(-lam)
    for i in range(k + 1):
        s += term; term *= lam / (i + 1)
    return min(1.0, s)

def raw_chance(stat, line, proj, sd, book_med, b2b, spread):
    mu = proj if book_med is None else W_OURS * proj + W_BOOK * book_med
    infl = 1.0 + (0.10 if b2b else 0) + (0.15 if spread is not None and abs(spread) >= 10 else 0)
    if stat in POISSON:
        lam = max(mu, 0.05)
        p_less = pois_cdf(line - 0.5, lam) if line != int(line) else pois_cdf(line - 1, lam)
        p_push = 0 if line != int(line) else (pois_cdf(line, lam) - pois_cdf(line - 1, lam))
        p_more = 1 - p_less - p_push
    else:
        s = max(sd, 1.0) * infl
        p_more = 1 - ncdf((line - mu) / s); p_less = 1 - p_more
    side = 'more' if p_more >= p_less else 'less'
    return side, max(p_more, p_less), mu

con = sqlite3.connect(os.path.join(BASE, 'data/processed/phase3_projections.sqlite')); con.row_factory = sqlite3.Row
rows = [dict(r) for r in con.execute('select * from projections')]
dates = sorted(r['date'] for r in rows); mid = dates[len(dates) // 2]
for r in rows:
    r['half'] = 'older' if r['date'] < mid else 'newer'
    bm = None if r['room_book'] is None else r['line'] - r['room_book']
    side, p, mu = raw_chance(r['stat'], r['line'], r['proj'], r['sd'], bm, r['b2b'] == 1, r['team_spread'])
    r['e_side'], r['e_raw'], r['e_mu'] = side, p, mu
    r['e_won'] = r['won'] if side == r['side'] else 1 - r['won']
    rb = r['room_book']
    r['room_agree'] = rb is not None and rb != 0 and ((rb < 0) == (side == 'more'))
    r['room_abs'] = abs(rb) if rb is not None else 0
    r['gate'] = r['room_agree'] and r['room_abs'] >= 0.5 and r['stat'] != 'threePointersMade'
H = ['older', 'newer']
def pct(w, l): return 100.0 * w / (w + l) if w + l else 0
def rec(rs): w = sum(r['e_won'] for r in rs); return w, len(rs) - w
L = []
def P(s=''): L.append(s)
P('# Apex Basketball - Phase 4: simulation engine, first build, walk-forward replay')
P('Date: %s. %d props. Older half before %s (rules learned here), newer half from %s (judged here).' % (TODAY, len(rows), mid, mid))
P()
P('## Engine')
P('Anchored projection = 0.4 x box-score projection + 0.6 x book median line (ours alone when no book). Normal curve for points, rebounds, assists, FGM and combos (spread = last-10 spread, floor 1, +10% on back-to-back, +15% when spread is 10+). Poisson for threes, steals, blocks, blocks+steals. Raw chance = tail past the line. Gates: room agrees with the side by 0.5+, not threes.')
P()
P('## Raw chance by bucket (engine side)')
P(); P('| Raw chance | Older half | Newer half |'); P('|---|---|---|')
B = [(0.5, .55), (.55, .6), (.6, .65), (.65, .7), (.7, .8), (.8, 1.01)]
for lo, hi in B:
    cells = []
    for h in H:
        rs = [r for r in rows if r['half'] == h and lo <= r['e_raw'] < hi]
        w, l = rec(rs); cells.append('%d-%d (%.0f%%)' % (w, l, pct(w, l)) if rs else '-')
    P('| %d-%d%% | %s |' % (lo * 100, min(hi, 1) * 100, ' | '.join(cells)))
P()
for h in H:
    rs = [r for r in rows if r['half'] == h]
    P('- %s half Brier, raw engine chance: %.4f' % (h, st.mean([(r['e_raw'] - r['e_won']) ** 2 for r in rs])))
P()
# honest table
def bucket(r):
    rb = r['room_abs'] if r['room_agree'] else (-r['room_abs'] if r['room_book'] not in (None, 0) else 0)
    rbk = 'against' if rb < 0 else ('same' if rb == 0 else ('room0.5' if rb < 1 else ('room1' if rb < 2 else 'room2+')))
    pb = 'p<55' if r['e_raw'] < .55 else 'p55-60' if r['e_raw'] < .60 else 'p60-70' if r['e_raw'] < .70 else 'p70+'
    return '%s|%s|%s' % (rbk, pb, r['e_side'])
hon = defaultdict(lambda: [0, 0])
for r in rows:
    if r['half'] == 'older':
        hon[bucket(r)][0] += r['e_won']; hon[bucket(r)][1] += 1
def honest(r):
    w, n = hon.get(bucket(r), [0, 0]); return (w + 5 * 0.52) / (n + 5) if n else 0.52
for r in rows: r['e_hon'] = honest(r)
newer = [r for r in rows if r['half'] == 'newer']
P('## Honest chance (table learned on the older half) checked on the newer half')
P('- Newer Brier raw: %.4f | honest: %.4f | flat 52%%: %.4f' % (
    st.mean([(r['e_raw'] - r['e_won']) ** 2 for r in newer]), st.mean([(r['e_hon'] - r['e_won']) ** 2 for r in newer]), st.mean([(0.52 - r['e_won']) ** 2 for r in newer])))
P(); P('| Bucket (room / raw / side) | Older W-L (honest) | Newer W-L (actual) |'); P('|---|---|---|')
nr = defaultdict(lambda: [0, 0])
for r in newer: nr[bucket(r)][0] += r['e_won']; nr[bucket(r)][1] += 1
for b in sorted(hon):
    w, n = hon[b]
    if n < 60: continue
    nw, nn = nr.get(b, [0, 0])
    P('| %s | %d-%d (%.0f%%) | %d-%d (%.0f%%) |' % (b, w, n - w, pct(w, n - w), nw, nn - nw, pct(nw, nn - nw)))
P()
import json
os.makedirs(os.path.dirname(TABLE), exist_ok=True)
json.dump({'trained_before': mid, 'shrink_to': 0.52, 'shrink_n': 5, 'buckets': {b: {'won': v[0], 'n': v[1]} for b, v in hon.items()}}, open(TABLE, 'w'), indent=1)
P('Table saved to calibration/honest_table_v1.json.')
P()
# gated picks
P('## Gated picks (room agrees 0.5+, not threes), engine side')
P(); P('| Picks | Older half | Newer half |'); P('|---|---|---|')
for lab, fn in [('All gated', lambda r: r['gate']), ('Gated, honest 55%+', lambda r: r['gate'] and r['e_hon'] >= .55),
                ('Gated, honest 58%+', lambda r: r['gate'] and r['e_hon'] >= .58), ('Gated, LESS', lambda r: r['gate'] and r['e_side'] == 'less'),
                ('Gated, MORE', lambda r: r['gate'] and r['e_side'] == 'more'), ('Gated, room 1+', lambda r: r['gate'] and r['room_abs'] >= 1),
                ('Not gated (for contrast)', lambda r: not r['gate'])]:
    cells = []
    for h in H:
        rs = [r for r in rows if r['half'] == h and fn(r)]; w, l = rec(rs); cells.append('%d-%d (%.0f%%)' % (w, l, pct(w, l)) if rs else '-')
    P('| %s | %s |' % (lab, ' | '.join(cells)))
P()
# boards, newer half only (walk-forward)
P('## Boards on the NEWER half only (rules and table fixed on the older half): one slip per day')
by_day = defaultdict(list)
for r in newer: by_day[r['date']].append(r)
RANKS = {'Honest chance order, gated': (lambda r: r['gate'], lambda r: (-r['e_hon'], -r['room_abs'])),
         'Room size order, gated': (lambda r: r['gate'], lambda r: (-r['room_abs'], -r['e_hon'])),
         'Honest order, gated, honest 55%+ only': (lambda r: r['gate'] and r['e_hon'] >= .55, lambda r: (-r['e_hon'], -r['room_abs'])),
         'Raw engine chance order, ALL props (baseline)': (lambda r: True, lambda r: -r['e_raw'])}
P(); P('| Ranking | Top 3 days W-L | Top 5 days W-L (4 of 5) | Top 6 days W-L (5 of 6) | Days with no board (under 3 picks) | $10/day result Top 3 at 6x |'); P('|---|---|---|---|---|---|')
for name, (filt, key) in RANKS.items():
    res = {}; nob = 0
    for n in (3, 5, 6):
        w = l = near = 0
        for d, rs in sorted(by_day.items()):
            c = sorted([r for r in rs if filt(r)], key=key)[:n]
            if len(c) < n:
                if n == 3: nob += 1
                continue
            legs = sum(r['e_won'] for r in c)
            if legs == n: w += 1
            else: l += 1
            if legs == n - 1: near += 1
        res[n] = (w, l, near)
    w3, l3, _ = res[3]
    money = w3 * 60 - (w3 + l3) * 10
    P('| %s | %d-%d (%.0f%%) | %d-%d (%d) | %d-%d (%d) | %d | %+d over %d days |' % (name, w3, l3, pct(w3, l3), res[5][0], res[5][1], res[5][2], res[6][0], res[6][1], res[6][2], nob, money, w3 + l3))
P()
P('Break-even for Top 3 Power at 6x is 1 win in 6 days (17%).')
P()
# per-day example of the last 5 newer days
P('## Sample: last 5 days of the newer half, Top 3 by honest order (gated)')
for d in sorted(by_day)[-5:]:
    c = sorted([r for r in by_day[d] if r['gate']], key=lambda r: (-r['e_hon'], -r['room_abs']))[:3]
    if len(c) < 3: P('- %s: no board (%d gated picks)' % (d, len(c))); continue
    P('- %s: ' % d + '; '.join('%s %s %s %.1f %s (honest %.0f%%, room %.1f) %s' % (r['player'], r['team'], r['stat'], r['line'], r['e_side'].upper(), r['e_hon'] * 100, r['room_abs'], '✅' if r['e_won'] else '❌') for r in c))
P()
open(OUT, 'w').write('\n'.join(L) + '\n'); print('wrote', OUT)
