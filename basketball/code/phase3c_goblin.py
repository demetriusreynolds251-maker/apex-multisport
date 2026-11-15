#!/usr/bin/env python3
"""Phase 3c: Goblin / Demon estimate from history.
Step 1: measure tonight's real PrizePicks Goblin and Demon gaps vs the standard line (data/collected/*.jsonl).
Step 2: apply the typical gap per stat to every clean historical prop and see how often MORE would have hit."""
import sqlite3, os, json, glob, statistics as st, datetime as dt
from collections import defaultdict
BASE = os.path.expanduser('~/ApexSports/basketball')
TODAY = dt.date.today().isoformat()
OUT = os.path.join(BASE, 'reports', '%s_phase3c_goblin_demon.md' % TODAY)
# step 1
lines = defaultdict(dict)   # (player, stat, start) -> odds_type -> line
for f in sorted(glob.glob(os.path.join(BASE, 'data/collected/*.jsonl'))):
    for ln in open(f):
        try: r = json.loads(ln)
        except Exception: continue
        if r.get('league') != 'NBA' or r.get('is_promo'): continue
        k = (r['player'], r['stat'], r.get('start'))
        lines[k][r['odds_type']] = r['line']
NAME = {'Points':'points','Rebounds':'rebounds','Assists':'assists','3PTM':'threePointersMade','3-PT Made':'threePointersMade',
 'Steals':'steals','Blocked Shots':'blocks','Turnovers':'turnovers','FG Made':'fieldGoalsMade','Pts+Rebs':'points+rebounds',
 'Pts+Asts':'points+assists','Rebs+Asts':'rebounds+assists','PRA':'points+rebounds+assists','Pts+Rebs+Asts':'points+rebounds+assists','Blks+Stls':'blocks+steals'}
gaps = defaultdict(lambda: defaultdict(list))
for k, d in lines.items():
    if 'standard' not in d: continue
    for ot in ('goblin', 'demon'):
        if ot in d:
            gaps[NAME.get(k[1], k[1])][ot].append(d[ot] - d['standard'])
L = []
def P(s=''): L.append(s)
P('# Apex Basketball - Phase 3c: Goblin and Demon, estimated from history')
P('Date: %s.' % TODAY)
P()
P('## Step 1: real PrizePicks gaps tonight (Goblin/Demon line minus the standard line, same player and stat)')
P(); P('| Stat | Goblin gap (median, n) | Demon gap (median, n) |'); P('|---|---|---|')
gmed = {}
for s in sorted(gaps):
    g = gaps[s]['goblin']; d = gaps[s]['demon']
    gmed[s] = (st.median(g) if g else None, st.median(d) if d else None)
    P('| %s | %s | %s |' % (s, ('%.1f (%d)' % (st.median(g), len(g))) if g else '-', ('%.1f (%d)' % (st.median(d), len(d))) if d else '-'))
P()
# step 2
con = sqlite3.connect(os.path.join(BASE, 'data/processed/phase3_projections.sqlite')); con.row_factory = sqlite3.Row
rows = [dict(r) for r in con.execute('select * from projections')]
dates = sorted(r['date'] for r in rows); mid = dates[len(dates)//2]
for r in rows:
    r['half'] = 'older' if r['date'] < mid else 'newer'
    rb = r['room_book']; r['room_more'] = rb is not None and rb < 0
    r['room_less'] = rb is not None and rb > 0
H = ['older', 'newer']
def pct(w, l): return 100.0 * w / (w + l) if w + l else 0
def tab(title, fn_line, side, groups, need):
    """fn_line(r)-> estimated line or None; side more/less; groups (label, filter)"""
    P('### %s' % title)
    P('Needed to break even: about %s per leg.' % need)
    P(); P('| Picks | Older half | Newer half | Both |'); P('|---|---|---|---|')
    for lab, filt in groups:
        cells = []; aw = al = 0
        for h in H:
            w = l = 0
            for r in rows:
                if r['half'] != h or not filt(r): continue
                ln = fn_line(r)
                if ln is None or r['result'] == ln: continue
                hit = (r['result'] > ln) if side == 'more' else (r['result'] < ln)
                if hit: w += 1
                else: l += 1
            aw += w; al += l
            cells.append('%d-%d (%.0f%%)' % (w, l, pct(w, l)) if w + l else '-')
        cells.append('%d-%d (%.0f%%)' % (aw, al, pct(aw, al)) if aw + al else '-')
        P('| %s | %s |' % (lab, ' | '.join(cells)))
    P()
def gob(r):
    g = gmed.get(r['stat'], (None, None))[0]
    return None if g is None else r['line'] + g
def dem(r):
    d = gmed.get(r['stat'], (None, None))[1]
    return None if d is None else r['line'] + d
P('## Step 2: history replay with those gaps (standard PP line moved by the typical gap)')
P('This is an estimate: real Goblin/Demon lines were not saved before 2026-11-04. Goblin MORE = lower line, Demon MORE = higher line.')
P()
tab('Goblin MORE (line lowered by the typical Goblin gap)', gob, 'more', [
    ('Every prop', lambda r: True),
    ('Projection says MORE', lambda r: r['side'] == 'more'),
    ('Projection says MORE, 60%+', lambda r: r['side'] == 'more' and r['p_side'] >= .6),
    ('Room favors MORE (PP standard line below books)', lambda r: r['room_more']),
    ('Room favors MORE and projection MORE', lambda r: r['room_more'] and r['side'] == 'more'),
    ('Hot player (form +15%)', lambda r: r['form'] is not None and r['form'] >= .15),
    ('Minutes up 2+', lambda r: r['min_trend'] >= 2),
    ('Not back-to-back', lambda r: r['b2b'] == 0),
], '79% on a 3-pick Goblin Power at 2x; 76% on a 2-pick Goblin at 1.7x')
tab('Demon MORE (line raised by the typical Demon gap)', dem, 'more', [
    ('Every prop', lambda r: True),
    ('Projection says MORE', lambda r: r['side'] == 'more'),
    ('Projection says MORE, 70%+', lambda r: r['side'] == 'more' and r['p_side'] >= .7),
    ('Room favors MORE', lambda r: r['room_more']),
    ('Hot player (form +15%)', lambda r: r['form'] is not None and r['form'] >= .15),
    ('Minutes up 2+', lambda r: r['min_trend'] >= 2),
], '47% on a 3-pick all-Demon Power at about 9.5x (PrizePicks Demon payouts vary by slip)')
tab('Goblin-size cushion, LESS side (standard line raised by the Goblin gap; not a PP product, shows the cushion effect)', dem, 'less', [
    ('Every prop', lambda r: True),
    ('Projection says LESS', lambda r: r['side'] == 'less'),
    ('Hot player and LESS', lambda r: r['form'] is not None and r['form'] >= .15 and r['side'] == 'less'),
], 'no payout: PrizePicks does not sell LESS at Goblin lines on NBA either way; shown for the simulation design only')
P('## Per-stat Goblin MORE hit rate (every prop, both halves)')
P(); P('| Stat | Goblin gap used | Older half | Newer half | Both |'); P('|---|---|---|---|---|')
for s in sorted(set(r['stat'] for r in rows)):
    g = gmed.get(s, (None, None))[0]
    if g is None: continue
    cells = []; aw = al = 0
    for h in H:
        w = l = 0
        for r in rows:
            if r['half'] != h or r['stat'] != s: continue
            ln = r['line'] + g
            if r['result'] == ln: continue
            if r['result'] > ln: w += 1
            else: l += 1
        aw += w; al += l; cells.append('%d-%d (%.0f%%)' % (w, l, pct(w, l)) if w + l else '-')
    P('| %s | %.1f | %s | %d-%d (%.0f%%) |' % (s, g, ' | '.join(cells), aw, al, pct(aw, al)))
P()
P('Fantasy Score: PrizePicks NBA Fantasy = points + 1.2 rebounds + 1.5 assists + 3 steals + 3 blocks - turnovers. No Fantasy lines exist in the history, so it cannot be graded yet; the line saver is collecting them from 2026-11-04.')
open(OUT, 'w').write('\n'.join(L) + '\n'); print('wrote', OUT)
