#!/usr/bin/env python3
"""Performance reports for this sport from its picks table: daily, weekly, monthly, season. Overall, by tier, by stat, by line kind (market),
board picks vs all picks, and calibration (stated confidence vs hit rate). Writes reports/<date>_<period>.md and returns the text.
  python3 reports/report.py daily|weekly|monthly|season"""
import collections as C, datetime as dt, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as CM
from database import db as DBM
from tracking import boards as TB

def rec(rows): w = sum(1 for r in rows if r['status'] == 'win'); l = sum(1 for r in rows if r['status'] == 'loss'); return w, l
def pct(w, l): return '%.0f%%' % (100 * w / (w + l)) if w + l else '-'
def line(title, rows):
    w, l = rec(rows); return '%s: %d-%d (%s)' % (title, w, l, pct(w, l)) if w + l else '%s: nothing graded' % title

def build(period='daily', day=None):
    c = CM.cfg(); db = DBM.connect(); today = dt.date.fromisoformat(day) if day else CM.now_ct().date() - dt.timedelta(days=1)
    if period == 'daily': lo = today
    elif period == 'weekly': lo = today - dt.timedelta(days=6)
    elif period == 'monthly': lo = today.replace(day=1)
    else: lo = dt.date(2000, 1, 1)
    rows = [dict(r) for r in db.execute("select * from picks where status in ('win','loss','push','void') and game_date between ? and ?", (lo.isoformat(), today.isoformat()))]
    board = [r for r in rows if r['on_board']]
    L = ['%s **%s %s RESULTS** %s' % (c['emoji'], c['name'].upper(), period.upper(), today.strftime('%a %-m/%-d') if period == 'daily' else '%s to %s' % (lo.strftime('%-m/%-d'), today.strftime('%-m/%-d'))), '']
    if not rows:
        L.append('Nothing graded in this window.')
        try: L += ['', '**Whole boards**'] + TB.board_lines(TB.record(db, lo.isoformat(), today.isoformat()), c['boards'])
        except Exception: pass
        return _out('\n'.join(L), period)
    L.append(line('Board picks (Top 3 / Elite / Best boards)', board)); L.append(line('Every scored line at %d+' % c['rules']['floor'], [r for r in rows if r['confidence'] >= c['rules']['floor']])); L.append(line('Every scored line', rows))
    L += ['', '**By tier**']
    for t in 'ABCD':
        R = [r for r in rows if r['tier'] == t]
        if R: L.append('  Tier %s: %d-%d (%s)' % (t, *rec(R), pct(*rec(R))))
    L += ['', '**By stat**']
    bys = C.defaultdict(list)
    for r in rows: bys[r['stat']].append(r)
    for s, R in sorted(bys.items(), key=lambda kv: -len(kv[1]))[:12]: L.append('  %s: %d-%d (%s)' % (c['stats'].get(s, {}).get('label', s), *rec(R), pct(*rec(R))))
    L += ['', '**By line kind**']
    for k in ('standard', 'goblin', 'demon'):
        R = [r for r in rows if r['kind'] == k]
        if R: L.append('  %s: %d-%d (%s)' % (k.title(), *rec(R), pct(*rec(R))))
    L += ['', '**Whole boards** (official slip = last board before the first game; every leg must hit)']
    try: L += TB.board_lines(TB.record(db, lo.isoformat(), today.isoformat()), c['boards'])
    except Exception as e: L.append('  board record not available: %s' % type(e).__name__)
    L += ['', '**Is the number honest** (what the card said vs what hit, this window)']
    L += TB.bands_text(rows)
    try: TB.real_record(db, force=True)
    except Exception: pass
    pushes = sum(1 for r in rows if r['status'] == 'push'); voids = sum(1 for r in rows if r['status'] == 'void')
    L += ['', 'Pushes %d, voids (did not play) %d. Whole numbers are the pick count, not money.' % (pushes, voids)]
    return _out('\n'.join(L), period)
def _out(txt, period):
    os.makedirs(CM.REPORTS, exist_ok=True); open(os.path.join(CM.REPORTS, '%s_%s.md' % (CM.now_ct().strftime('%Y-%m-%d'), period)), 'w').write(txt); return txt

if __name__ == '__main__': print(build(sys.argv[1] if len(sys.argv) > 1 else 'daily'))
