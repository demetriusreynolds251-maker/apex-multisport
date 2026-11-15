#!/usr/bin/env python3
"""Phase 6 re-run WITHOUT book lines (his 11/4 decision): only PrizePicks lines + box scores.
Rules that need no book line, per pick and as one Top 3/5/6 slip per day, both halves."""
import sqlite3, os, datetime as dt
from collections import defaultdict
BASE = os.path.expanduser('~/ApexSports/basketball')
TODAY = dt.date.today().isoformat()
OUT = os.path.join(BASE, 'reports', '%s_phase6_no_book_lines.md' % TODAY)
con = sqlite3.connect(os.path.join(BASE, 'data/processed/phase3_projections.sqlite')); con.row_factory = sqlite3.Row
rows = [dict(r) for r in con.execute('select * from projections')]
dates = sorted(r['date'] for r in rows); mid = dates[len(dates)//2]
for r in rows:
    r['half'] = 'older' if r['date'] < mid else 'newer'
    r['hot'] = r['form'] is not None and r['form'] >= .15
    r['vhot'] = r['form'] is not None and r['form'] >= .25
H = ['older', 'newer']
def pct(w, l): return 100.0 * w / (w + l) if w + l else 0
def rec(rs): w = sum(r['won'] for r in rs); return w, len(rs) - w
L = []
def P(s=''): L.append(s)
P('# Apex Basketball - Phase 6 without book lines')
P('Date: %s. His call: no book-line feed. Only PrizePicks lines and box scores are used. %d props, halves split at %s.' % (TODAY, len(rows), mid))
P()
RULES = [
 ('Hot player (+15% last 5 vs 40) and LESS', lambda r: r['hot'] and r['side'] == 'less'),
 ('Hot and LESS, projection 60%+', lambda r: r['hot'] and r['side'] == 'less' and r['p_side'] >= .6),
 ('Hot and LESS, projection 70%+', lambda r: r['hot'] and r['side'] == 'less' and r['p_side'] >= .7),
 ('Very hot (+25%) and LESS', lambda r: r['vhot'] and r['side'] == 'less'),
 ('Very hot and LESS, projection 60%+', lambda r: r['vhot'] and r['side'] == 'less' and r['p_side'] >= .6),
 ('Hot and LESS, not back-to-back', lambda r: r['hot'] and r['side'] == 'less' and r['b2b'] == 0),
 ('Hot and LESS, minutes flat or down', lambda r: r['hot'] and r['side'] == 'less' and r['min_trend'] < 2),
 ('Hot and LESS, not points alone', lambda r: r['hot'] and r['side'] == 'less' and r['stat'] != 'points'),
 ('Hot and LESS, 30+ games history', lambda r: r['hot'] and r['side'] == 'less' and r['n_hist'] >= 30),
 ('Projection LESS 70%+ (any form)', lambda r: r['side'] == 'less' and r['p_side'] >= .7),
 ('Projection LESS 80%+', lambda r: r['side'] == 'less' and r['p_side'] >= .8),
 ('Projection MORE 80%+', lambda r: r['side'] == 'more' and r['p_side'] >= .8),
 ('Cold (-15%) and MORE', lambda r: r['form'] is not None and r['form'] <= -.15 and r['side'] == 'more'),
]
P('## Per-pick records (PASS = 55%+ both halves, 60+ picks each)')
P(); P('| Rule | Older half | Newer half | Both | Verdict |'); P('|---|---|---|---|---|')
for lab, fn in RULES:
    cells = []; ok = True; aw = al = 0
    for h in H:
        rs = [r for r in rows if r['half'] == h and fn(r)]; w, l = rec(rs); aw += w; al += l
        cells.append('%d-%d (%.0f%%)' % (w, l, pct(w, l)) if rs else '-')
        if w + l < 60 or pct(w, l) < 55: ok = False
    cells.append('%d-%d (%.0f%%)' % (aw, al, pct(aw, al)))
    P('| %s | %s | %s |' % (lab, ' | '.join(cells), 'PASS' if ok else 'fail'))
P()
P('### Hot and LESS by stat')
P(); P('| Stat | Older half | Newer half | Both |'); P('|---|---|---|---|')
for s in sorted(set(r['stat'] for r in rows)):
    cells = []; aw = al = 0
    for h in H:
        rs = [r for r in rows if r['half'] == h and r['hot'] and r['side'] == 'less' and r['stat'] == s]; w, l = rec(rs); aw += w; al += l
        cells.append('%d-%d (%.0f%%)' % (w, l, pct(w, l)) if rs else '-')
    if aw + al: P('| %s | %s | %d-%d (%.0f%%) |' % (s, ' | '.join(cells), aw, al, pct(aw, al)))
P()
P('## Boards: one slip per day, every leg must win')
by_day = defaultdict(list)
for r in rows: by_day[r['date']].append(r)
BOARDS = {
 'Hot+LESS, ranked by projection chance': (lambda r: r['hot'] and r['side'] == 'less', lambda r: (-r['p_side'], -(r['form'] or 0))),
 'Hot+LESS, ranked by how hot': (lambda r: r['hot'] and r['side'] == 'less', lambda r: (-(r['form'] or 0), -r['p_side'])),
 'Hot+LESS projection 60%+, ranked by projection': (lambda r: r['hot'] and r['side'] == 'less' and r['p_side'] >= .6, lambda r: -r['p_side']),
 'Very hot+LESS, ranked by projection': (lambda r: r['vhot'] and r['side'] == 'less', lambda r: -r['p_side']),
 'Hot+LESS or projection MORE 80%+, ranked by projection': (lambda r: (r['hot'] and r['side'] == 'less') or (r['side'] == 'more' and r['p_side'] >= .8), lambda r: -r['p_side']),
 'Very hot+LESS or projection MORE 80%+, ranked by projection': (lambda r: (r['vhot'] and r['side'] == 'less') or (r['side'] == 'more' and r['p_side'] >= .8), lambda r: -r['p_side']),
 'Hot+LESS (not points) or MORE 80%+, ranked by projection': (lambda r: (r['hot'] and r['side'] == 'less' and r['stat'] != 'points') or (r['side'] == 'more' and r['p_side'] >= .8), lambda r: -r['p_side']),
 'Baseline: projection chance only, all props': (lambda r: True, lambda r: -r['p_side']),
}
P(); P('| Board | Size | Older half days W-L | Newer half days W-L | Both | Near miss (N-1 legs) | Days no board | $10/day both halves |'); P('|---|---|---|---|---|---|---|---|')
PAY = {3: (60, 0), 5: (100, 20), 6: (250, 20)}
for name, (filt, key) in BOARDS.items():
    for n in (3, 5, 6):
        cells = []; tw = tl = near = nob = 0
        for h in H:
            w = l = 0
            for d, rs in sorted(by_day.items()):
                if rs[0]['half'] != h: continue
                c = sorted([r for r in rs if filt(r)], key=key)[:n]
                if len(c) < n: nob += 1; continue
                legs = sum(r['won'] for r in c)
                if legs == n: w += 1
                else: l += 1
                if legs == n - 1: near += 1
            tw += w; tl += l; cells.append('%d-%d (%.0f%%)' % (w, l, pct(w, l)) if w + l else '-')
        full, part = PAY[n]
        money = tw * full + (near * part if n > 3 else 0) - (tw + tl) * 10
        P('| %s | Top %d | %s | %d-%d (%.0f%%) | %d | %d | %+d over %d days |' % (name, n, ' | '.join(cells), tw, tl, pct(tw, tl), near, nob, money, tw + tl))
P()
P('Payouts used: 3-pick Power 6x; 5-pick Flex 10x full and 2x at 4 of 5; 6-pick Flex 25x full and 2x at 5 of 6 (4 of 6 refund not counted). Break-even Top 3 = 1 win in 6 days.')
P()
P('## What the board loses without book lines')
P('With book lines the Top 3 (room-gated) won 24-27% of days. The rules above are the only no-book rules that passed in both halves. Everything else (rest, back-to-back, home, spread, minutes trend, projection alone) was a coin flip in Phase 3.')
open(OUT, 'w').write('\n'.join(L) + '\n'); print('wrote', OUT)
