#!/usr/bin/env python3
"""Edge report: can we predict PrizePicks NBA lines better than random and better than the books? All 20,837 clean props."""
import sqlite3, os, json, statistics as st, datetime as dt
from collections import defaultdict
BASE = os.path.expanduser('~/ApexSports/basketball'); TODAY = dt.date.today().isoformat()
OUT = os.path.join(BASE, 'reports', '%s_edge_report.md' % TODAY)
con = sqlite3.connect(os.path.join(BASE, 'data/processed/nba_history.sqlite')); con.row_factory = sqlite3.Row
raw = [dict(r) for r in con.execute("select stat, game_date, pp_line, book_lines_json, pinnacle_before_start, result, more_won, less_won from prop_lines p where pp_before_start=1 and result is not null and books_before_start>0 and exists (select 1 from player_games g where g.event_id=p.event_id and g.player_id=p.player_id and g.minutes>0)")]
dnp = con.execute("select count(*) from prop_lines p where pp_before_start=1 and result is not null and books_before_start>0 and not exists (select 1 from player_games g where g.event_id=p.event_id and g.player_id=p.player_id and g.minutes>0)").fetchone()[0]
for r in raw:
    try: bl = [v[0] for v in json.loads(r['book_lines_json'] or '{}').values() if v and v[0] is not None]
    except Exception: bl = []
    r['nb'] = len(bl); r['bm'] = st.median(bl) if bl else None; r['room'] = (r['pp_line'] - r['bm']) if bl else None
dates = sorted(r['game_date'] for r in raw); mid = dates[len(dates)//2]
for r in raw: r['half'] = 'older' if r['game_date'] < mid else 'newer'
H = ['older', 'newer']
def pct(w, l): return 100.0 * w / (w + l) if w + l else 0
L = []
def P(s=''): L.append(s)
P('# Apex Basketball - Edge report: better than random? better than the books?')
P('Date: %s. %d clean props where the player actually played (PrizePicks line before tip, 1+ book line before tip, graded). %d more clean props belong to players with no minutes that night (did not play): on PrizePicks those are voids, not losses, so they are left out of every number here. Older half before %s, newer half from %s.' % (TODAY, len(raw), dnp, mid, mid))
P()
P('## Q5. How often do the books disagree with PrizePicks?')
P(); P('| Stat | Props | Same line | PP lower by 0.5 | PP lower by 1+ | PP higher by 0.5 | PP higher by 1+ | Any disagreement |'); P('|---|---|---|---|---|---|---|---|')
def dis_row(lab, rs):
    n = len(rs); same = sum(1 for r in rs if r['room'] == 0); lo5 = sum(1 for r in rs if r['room'] is not None and -1 < r['room'] < 0); lo1 = sum(1 for r in rs if r['room'] is not None and r['room'] <= -1)
    hi5 = sum(1 for r in rs if r['room'] is not None and 0 < r['room'] < 1); hi1 = sum(1 for r in rs if r['room'] is not None and r['room'] >= 1)
    P('| %s | %d | %d (%.0f%%) | %d | %d | %d | %d | %.0f%% |' % (lab, n, same, pct(same, n - same), lo5, lo1, hi5, hi1, pct(n - same, same)))
for s in sorted(set(r['stat'] for r in raw), key=lambda s: -sum(1 for r in raw if r['stat'] == s)): dis_row(s, [r for r in raw if r['stat'] == s])
dis_row('ALL', raw)
P()
P('## Q6. When they disagree, who is right? (take the side PrizePicks made easier: PP lower -> MORE, PP higher -> LESS)')
def side_rec(rs, sidew):
    w = sum(1 for r in rs if (r['more_won'] if sidew == 'more' else r['less_won']) == 1 and r['result'] != r['pp_line']); l = sum(1 for r in rs if (r['more_won'] if sidew == 'more' else r['less_won']) == 0 and r['result'] != r['pp_line']); return w, l
LEVELS = [('PP lower by 0.5', lambda r: -1 < r['room'] < 0, 'more'), ('PP lower by 1', lambda r: -2 < r['room'] <= -1, 'more'), ('PP lower by 2+', lambda r: r['room'] <= -2, 'more'),
          ('PP higher by 0.5', lambda r: 0 < r['room'] < 1, 'less'), ('PP higher by 1', lambda r: 1 <= r['room'] < 2, 'less'), ('PP higher by 2+', lambda r: r['room'] >= 2, 'less'),
          ('Same line, blind MORE', lambda r: r['room'] == 0, 'more'), ('Same line, blind LESS', lambda r: r['room'] == 0, 'less')]
P(); P('| Disagreement | Older half | Newer half | Both | Verdict |'); P('|---|---|---|---|---|')
for lab, fn, sidew in LEVELS:
    cells = []; aw = al = 0; ok = True
    for h in H:
        rs = [r for r in raw if r['half'] == h and r['room'] is not None and fn(r)]; w, l = side_rec(rs, sidew); aw += w; al += l
        cells.append('%d-%d (%.0f%%)' % (w, l, pct(w, l)) if w + l else '-')
        if w + l < 60 or pct(w, l) < 55: ok = False
    P('| %s | %s | %d-%d (%.0f%%) | %s |' % (lab, ' | '.join(cells), aw, al, pct(aw, al), 'PASS' if ok else 'fail'))
P()
P('### Q6 by stat: PP line 1+ off the books, book side taken')
P(); P('| Stat | Older half | Newer half | Both |'); P('|---|---|---|---|')
for s in sorted(set(r['stat'] for r in raw)):
    cells = []; aw = al = 0
    for h in H:
        rs = [r for r in raw if r['half'] == h and r['stat'] == s and r['room'] is not None and abs(r['room']) >= 1]
        w1, l1 = side_rec([r for r in rs if r['room'] < 0], 'more'); w2, l2 = side_rec([r for r in rs if r['room'] > 0], 'less'); w, l = w1 + w2, l1 + l2; aw += w; al += l
        cells.append('%d-%d (%.0f%%)' % (w, l, pct(w, l)) if w + l else '-')
    if aw + al: P('| %s | %s | %d-%d (%.0f%%) |' % (s, ' | '.join(cells), aw, al, pct(aw, al)))
P()
P('### Pinnacle only (sharpest book), PP 0.5+ off Pinnacle, Pinnacle side taken')
rs = [r for r in raw if r['pinnacle_before_start'] is not None and r['pinnacle_before_start'] != r['pp_line']]
w1, l1 = side_rec([r for r in rs if r['pp_line'] < r['pinnacle_before_start']], 'more'); w2, l2 = side_rec([r for r in rs if r['pp_line'] > r['pinnacle_before_start']], 'less')
P('- %d props had a Pinnacle line that differed: Pinnacle side %d-%d (%.0f%%). Too few to lean on.' % (len(rs), w1 + w2, l1 + l2, pct(w1 + w2, l1 + l2)))
P()
# ---- factors per stat from the projection table
pc = sqlite3.connect(os.path.join(BASE, 'data/processed/phase3_projections.sqlite')); pc.row_factory = sqlite3.Row
pr = [dict(r) for r in pc.execute('select * from projections')]
for r in pr:
    r['half'] = 'older' if r['date'] < mid else 'newer'; rb = r['room_book']
    r['room_agree'] = rb is not None and rb != 0 and ((rb < 0) == (r['side'] == 'more'))
    r['hot'] = r['form'] is not None and r['form'] >= .15; r['cold'] = r['form'] is not None and r['form'] <= -.15
def rec(rs): w = sum(r['won'] for r in rs); return w, len(rs) - w
FACT = [('Our projection side (box scores only)', lambda r: True),
        ('Our projection 70%+ sure', lambda r: r['p_side'] >= .7),
        ('Book side (PP line off the books, any size)', lambda r: r['room_agree']),
        ('Book side AND our projection agree', lambda r: r['room_agree']),
        ('Our projection AGAINST the book side', lambda r: r['room_book'] not in (None, 0) and not r['room_agree']),
        ('Hot player + our LESS', lambda r: r['hot'] and r['side'] == 'less'),
        ('Hot player + our MORE', lambda r: r['hot'] and r['side'] == 'more'),
        ('Cold player + our MORE', lambda r: r['cold'] and r['side'] == 'more'),
        ('Minutes up 2+ + our MORE', lambda r: r['min_trend'] >= 2 and r['side'] == 'more'),
        ('Minutes down 2+ + our LESS', lambda r: r['min_trend'] <= -2 and r['side'] == 'less'),
        ('Back-to-back + our LESS', lambda r: r['b2b'] == 1 and r['side'] == 'less'),
        ('Blowout spread 10+ + our LESS', lambda r: r['team_spread'] is not None and abs(r['team_spread']) >= 10 and r['side'] == 'less'),
        ('Home + our MORE', lambda r: r['home'] == 1 and r['side'] == 'more')]
P('## Q1-Q4. Which factors predict the side, per prop type (projection side taken; both halves; PASS = 55%+ in both with 60+ picks)')
P('Our projection = minutes x per-minute rate x opponent factor from the box scores only. "Book side" = the side the PrizePicks line makes easier compared with the middle book line.')
stats = ['points', 'rebounds', 'assists', 'points+rebounds+assists', 'threePointersMade', 'blocks', 'steals', 'turnovers', 'fieldGoalsMade', 'points+rebounds', 'points+assists', 'rebounds+assists', 'blocks+steals']
for s in stats:
    rs_s = [r for r in pr if r['stat'] == s]
    if not rs_s: continue
    P(); P('### %s (%d props projected)' % (s, len(rs_s))); P(); P('| Factor | Older half | Newer half | Both | Verdict |'); P('|---|---|---|---|---|')
    for lab, fn in FACT:
        cells = []; aw = al = 0; ok = True
        for h in H:
            rs = [r for r in rs_s if r['half'] == h and fn(r)]; w, l = rec(rs); aw += w; al += l
            cells.append('%d-%d (%.0f%%)' % (w, l, pct(w, l)) if rs else '-')
            if w + l < 60 or pct(w, l) < 55: ok = False
        if aw + al: P('| %s | %s | %d-%d (%.0f%%) | %s |' % (lab, ' | '.join(cells), aw, al, pct(aw, al), 'PASS' if ok else ('small' if aw + al < 120 else 'fail')))
P()
P('## Fantasy Score')
P('No Fantasy Score lines exist in the two seasons of history (the archive carried the box-score stats, not PrizePicks Fantasy lines). It cannot be tested until the saver has a few weeks of real lines (saving since 2026-11-04).')
open(OUT, 'w').write('\n'.join(L) + '\n'); print('wrote', OUT)
