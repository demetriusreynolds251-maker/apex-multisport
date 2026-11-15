#!/usr/bin/env python3
"""APEX BASKETBALL - Phase 3b/5/6/7: combos, ranking choices, board sizes, honest probability.
Reads data/processed/phase3_projections.sqlite written by phase3_edges.py. Stdlib only."""
import sqlite3, os, datetime as dt, statistics as st
from collections import defaultdict
BASE = os.path.expanduser('~/ApexSports/basketball')
DB = os.path.join(BASE, 'data/processed/phase3_projections.sqlite')
TODAY = dt.date.today().isoformat()
OUT = os.path.join(BASE, 'reports', '%s_phase3b_boards.md' % TODAY)
con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
rows = [dict(r) for r in con.execute('select * from projections')]
dates = sorted(r['date'] for r in rows); mid = dates[len(dates)//2]
for r in rows:
    r['half'] = 'older' if r['date'] < mid else 'newer'
    rb = r['room_book']
    r['room_agree'] = rb is not None and rb != 0 and ((rb < 0) == (r['side'] == 'more'))
    r['room_abs'] = abs(rb) if rb is not None else 0
    r['hot_less'] = r['form'] is not None and r['form'] >= 0.15 and r['side'] == 'less'
H = ['older', 'newer']
L = []
def P(s=''): L.append(s)
def pct(w, l): return 100.0 * w / (w + l) if w + l else 0
def rec(rs):
    w = sum(r['won'] for r in rs); return w, len(rs) - w
def table(title, groups, note=None, floor=60):
    P('### %s' % title)
    if note: P(note)
    P(); P('| Rule | Older half | Newer half | Both | Verdict |'); P('|---|---|---|---|---|')
    for lab, fn in groups:
        cells = []; ok = True; aw = al = 0
        for h in H:
            rs = [r for r in rows if r['half'] == h and fn(r)]
            w, l = rec(rs); aw += w; al += l
            cells.append('%d-%d (%.0f%%)' % (w, l, pct(w, l)) if rs else '-')
            if w + l < floor or pct(w, l) < 55: ok = False
        cells.append('%d-%d (%.0f%%)' % (aw, al, pct(aw, al)) if aw + al else '-')
        P('| %s | %s | %s |' % (lab, ' | '.join(cells), 'PASS' if ok else 'fail'))
    P()

P('# Apex Basketball - Phase 3b: combined rules, ranking, board sizes, honest probability')
P('Date: %s. Same %d projected props as the Phase 3 report. Older half before %s, newer half from %s.' % (TODAY, len(rows), mid, mid))
P('PASS = 55%+ in both halves with 60+ picks in each half.')
P()
P('## Combined rules')
stats = sorted(set(r['stat'] for r in rows))
table('Room 1+ in our favor, by stat', [(s, (lambda s: lambda r: r['stat'] == s and r['room_abs'] >= 1 and r['room_agree'])(s)) for s in stats])
table('Room agrees (any size), by stat', [(s, (lambda s: lambda r: r['stat'] == s and r['room_agree'])(s)) for s in stats])
table('Room + projection strength', [
    ('Room agrees, projection 50-60%', lambda r: r['room_agree'] and r['p_side'] < 0.60),
    ('Room agrees, projection 60-70%', lambda r: r['room_agree'] and 0.60 <= r['p_side'] < 0.70),
    ('Room agrees, projection 70%+', lambda r: r['room_agree'] and r['p_side'] >= 0.70),
    ('Room 1+ agrees, projection 60%+', lambda r: r['room_abs'] >= 1 and r['room_agree'] and r['p_side'] >= 0.60),
    ('Room 1+ agrees, projection 70%+', lambda r: r['room_abs'] >= 1 and r['room_agree'] and r['p_side'] >= 0.70),
    ('Room 1.5+ agrees, any projection', lambda r: r['room_abs'] >= 1.5 and r['room_agree']),
    ('Room 2+ agrees, any projection', lambda r: r['room_abs'] >= 2 and r['room_agree']),
])
table('Room agrees + side', [
    ('Room agrees, MORE', lambda r: r['room_agree'] and r['side'] == 'more'),
    ('Room agrees, LESS', lambda r: r['room_agree'] and r['side'] == 'less'),
    ('Room 1+ agrees, MORE', lambda r: r['room_agree'] and r['room_abs'] >= 1 and r['side'] == 'more'),
    ('Room 1+ agrees, LESS', lambda r: r['room_agree'] and r['room_abs'] >= 1 and r['side'] == 'less'),
])
table('Hot player + LESS (fade the hot streak)', [
    ('Hot and LESS, any room', lambda r: r['hot_less']),
    ('Hot and LESS, room agrees', lambda r: r['hot_less'] and r['room_agree']),
    ('Hot and LESS, PP same line as books', lambda r: r['hot_less'] and r['room_book'] == 0),
    ('Hot and LESS, projection 60%+', lambda r: r['hot_less'] and r['p_side'] >= 0.60),
    ('Hot (+25%) and LESS', lambda r: r['form'] is not None and r['form'] >= 0.25 and r['side'] == 'less'),
    ('Hot and LESS, not back-to-back', lambda r: r['hot_less'] and r['b2b'] == 0),
    ('Hot and LESS, minutes flat/down', lambda r: r['hot_less'] and r['min_trend'] < 2),
])
table('Room agrees + other facts', [
    ('Room agrees, not back-to-back', lambda r: r['room_agree'] and r['b2b'] == 0),
    ('Room agrees, back-to-back', lambda r: r['room_agree'] and r['b2b'] == 1),
    ('Room agrees, home', lambda r: r['room_agree'] and r['home'] == 1),
    ('Room agrees, away', lambda r: r['room_agree'] and r['home'] == 0),
    ('Room agrees, minutes up 2+', lambda r: r['room_agree'] and r['min_trend'] >= 2),
    ('Room agrees, 2+ books', lambda r: r['room_agree'] and r['n_books'] >= 2),
    ('Room agrees, 3+ books', lambda r: r['room_agree'] and r['n_books'] >= 3),
    ('Room agrees, 1 book only', lambda r: r['room_agree'] and r['n_books'] == 1),
])

# ---------- ranking choices and board sizes (whole-slip, one slip per day)
P('## Ranking choices and board sizes (one slip per day, every leg must win)')
P('Each day the candidates are ranked, the top N become the slip. A day counts only if it has at least N candidates.')
P('Flex = PrizePicks Flex still pays something at 5 of 6 and 4 of 5 (shown as "flex wins").')
P()
by_day = defaultdict(list)
for r in rows: by_day[r['date']].append(r)
RANKS = {
 'A. Projection chance only (all props)': (lambda r: True, lambda r: -r['p_side']),
 'B. Room first, projection second (room must agree)': (lambda r: r['room_agree'], lambda r: (-r['room_abs'], -r['p_side'])),
 'C. Projection first, room must agree': (lambda r: r['room_agree'], lambda r: -r['p_side']),
 'D. Room 1+ agrees, then projection': (lambda r: r['room_agree'] and r['room_abs'] >= 1, lambda r: -r['p_side']),
 'E. Room agrees, LESS only, projection order': (lambda r: r['room_agree'] and r['side'] == 'less', lambda r: -r['p_side']),
 'F. Hot+LESS or Room 1+ agrees, projection order': (lambda r: r['hot_less'] or (r['room_agree'] and r['room_abs'] >= 1), lambda r: -r['p_side']),
}
SIZES = [3, 5, 6, 10]
for name, (filt, key) in RANKS.items():
    P('### %s' % name)
    P(); P('| Board | Older half days W-L | Newer half days W-L | Both | Flex wins (both) | Legs W-L (both) |'); P('|---|---|---|---|---|---|')
    for n in SIZES:
        cells = []; tw = tl = 0; flex = 0; lw = ll = 0
        for h in H:
            w = l = 0
            for d, rs in sorted(by_day.items()):
                if rs[0]['half'] != h: continue
                c = sorted([r for r in rs if filt(r)], key=key)[:n]
                if len(c) < n: continue
                legs = sum(r['won'] for r in c)
                lw += legs; ll += n - legs
                if legs == n: w += 1
                else: l += 1
                if n == 6 and legs == 5: flex += 1
                if n == 5 and legs == 4: flex += 1
            tw += w; tl += l
            cells.append('%d-%d (%.0f%%)' % (w, l, pct(w, l)) if w + l else '-')
        cells.append('%d-%d (%.0f%%)' % (tw, tl, pct(tw, tl)) if tw + tl else '-')
        P('| Top %d | %s | %s | %d-%d (%.0f%%) |' % (n, ' | '.join(cells), flex if n in (5, 6) else '-', lw, ll, pct(lw, ll)))
    P()
P('Break-even per day, PrizePicks standard payouts: Top 3 Power (6x) needs 1 win in 6 days; Flex 5 (10x at 5/5, 2x at 4/5) and Flex 6 (25x at 6/6, 2x at 5/6, 0.4x at 4/6) need far fewer full wins. Goblin payouts are much lower; Goblin history is not on file so Goblin boards cannot be tested yet.')
P()

# ---------- honest probability: learn on older half, check on newer half
P('## Honest probability (Phase 7 check)')
P('Raw = the projection chance. Honest = the won-lost rate of the same kind of pick in the OLDER half, looked up by room size and projection bucket, then applied to the NEWER half.')
P()
def bucket(r):
    rb = r['room_abs'] if r['room_agree'] else (-r['room_abs'] if r['room_book'] not in (None, 0) else 0)
    rbk = 'against' if rb < 0 else ('same' if rb == 0 else ('room0.5' if rb < 1 else 'room1+'))
    pb = 'p<55' if r['p_side'] < .55 else 'p55-60' if r['p_side'] < .60 else 'p60-70' if r['p_side'] < .70 else 'p70+'
    return (rbk, pb, r['side'])
hon = defaultdict(lambda: [0, 0])
for r in rows:
    if r['half'] == 'older':
        b = bucket(r); hon[b][0] += r['won']; hon[b][1] += 1
newer = [r for r in rows if r['half'] == 'newer']
def honest(r):
    w, n = hon.get(bucket(r), [0, 0])
    return (w + 5 * 0.52) / (n + 5) if n else 0.52   # light shrink to 52%
raw_b = st.mean([(r['p_side'] - r['won']) ** 2 for r in newer])
hon_b = st.mean([(honest(r) - r['won']) ** 2 for r in newer])
flat_b = st.mean([(0.52 - r['won']) ** 2 for r in newer])
P('- Newer-half Brier, raw projection chance: %.4f' % raw_b)
P('- Newer-half Brier, honest (learned on older half): %.4f' % hon_b)
P('- Newer-half Brier, flat 52%% for everything: %.4f' % flat_b)
P()
P('### Honest buckets learned on the older half (won-lost), and how they did on the newer half')
P(); P('| Room | Projection | Side | Older W-L (honest %) | Newer W-L (actual %) |'); P('|---|---|---|---|---|')
newer_rec = defaultdict(lambda: [0, 0])
for r in newer:
    b = bucket(r); newer_rec[b][0] += r['won']; newer_rec[b][1] += 1
for b in sorted(hon):
    w, n = hon[b]; nw, nn = newer_rec.get(b, [0, 0])
    if n < 60: continue
    P('| %s | %s | %s | %d-%d (%.0f%%) | %d-%d (%.0f%%) |' % (b[0], b[1], b[2].upper(), w, n - w, pct(w, n - w), nw, nn - nw, pct(nw, nn - nw)))
P()
P('### Honest 55%+ only (older half says 55%+): how it did on the newer half')
sel = [r for r in newer if honest(r) >= 0.55]
w, l = rec(sel); P('- Picks with honest 55%%+: newer half %d-%d (%.0f%%)' % (w, l, pct(w, l)))
sel = [r for r in newer if honest(r) >= 0.57]
w, l = rec(sel); P('- Picks with honest 57%%+: newer half %d-%d (%.0f%%)' % (w, l, pct(w, l)))
P()
open(OUT, 'w').write('\n'.join(L) + '\n'); print('wrote', OUT)
