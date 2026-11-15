#!/usr/bin/env python3
"""Board tracker for this sport (his 'Go board tracker', 11/5). Two things, both from history.db only:
1. WHOLE BOARDS: for every board (Top 3, Elite 5, Elite 6, Best Goblin/Standard/Demon, Top 10) the official slip of each slate day = the last
   posted main lineup before that slate's first game started. A day is WON when every leg hit, LOST on any miss; void legs never lose
   (a void is not a loss); a lineup with fewer legs than the board needs is SHORT and not counted; still-open legs = PENDING.
2. REAL RECORD: graded picks by line kind + stat + side + confidence band (60-64 / 65-69 / 70-74 / 75-79 / 80-89 / 90+), for the
   🧾 line on every card and the 'Is the number honest' part of the reports. Cached in cache/real_record.json for an hour.
  python3 tracking/boards.py            whole-board record + last 7 days
  python3 tracking/boards.py bands      real record table"""
import collections as C, datetime as dt, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as CM
from database import db as DBM

BANDS = ((60, 65), (65, 70), (70, 75), (75, 80), (80, 90), (90, 101))
ORDER = ('top3', 'elite5', 'elite6', 'bestgoblin', 'beststandard', 'bestdemon', 'top10')
CACHE_FILE = os.path.join(CM.CACHE, 'real_record.json')

def band_of(conf):
    for lo, hi in BANDS:
        if lo <= conf < hi: return '%d-%d' % (lo, hi - 1) if hi < 101 else '%d+' % lo
    return None

# ---------- whole boards ----------
def official_slips(db):
    """{board: {slate_day: dict(run_id, created, legs=[pick rows], size)}} using the last run before each slate's first start."""
    c = CM.cfg(); boards = c['boards']; out = {b: {} for b in boards}
    runs = {r['id']: r for r in db.execute('select id, created from runs').fetchall()}
    picks = {r['pick_key']: dict(r) for r in db.execute('select pick_key, player, team, opponent, start, stat, line, kind, side, confidence, status, result_value from picks').fetchall()}
    by_run = C.defaultdict(list)
    for r in db.execute("select run_id, board, slot, pick_key from boards where role='main' order by run_id, board, slot").fetchall(): by_run[(r['run_id'], r['board'])].append(r['pick_key'])
    for (run_id, b), keys in by_run.items():
        if b not in boards or run_id not in runs: continue
        legs = [picks[k] for k in keys if k in picks]
        if not legs: continue
        starts = [CM.parse_iso(l['start']) for l in legs if l.get('start')]
        if not starts: continue
        first = min(starts); created = CM.parse_iso(runs[run_id]['created'])
        if not created or created >= first: continue                      # posted after a leg started: not playable as a slip
        day = CM.ct_date(first)
        cur = out[b].get(day)
        if cur is None or created > cur['created']: out[b][day] = dict(run_id=run_id, created=created, legs=legs, size=boards[b]['size'])
    return out

def grade_slip(s):
    """won / lost / short / pending"""
    if len(s['legs']) < s['size']: return 'short'
    st = [l['status'] for l in s['legs']]
    if 'loss' in st: return 'lost'
    if 'open' in st: return 'pending'
    live = [x for x in st if x == 'win']
    if not live: return 'short'                                            # everything void or push: no slip to grade
    return 'won'

def record(db=None, since=None, until=None):
    db = db or DBM.connect(); slips = official_slips(db); out = {}
    for b, days in slips.items():
        R = C.Counter(); detail = []
        for day in sorted(days):
            if since and day < since: continue
            if until and day > until: continue
            g = grade_slip(days[day]); R[g] += 1; detail.append((day, g, days[day]))
        out[b] = dict(won=R['won'], lost=R['lost'], pending=R['pending'], short=R['short'], days=detail)
    return out

def leg_mark(l): return {'win': '✅', 'loss': '❌', 'push': '➖', 'void': '⚪'}.get(l['status'], '⏳')
def leg_text(l): return '%s %s %s %g %s' % (leg_mark(l), l['player'], CM.cfg()['stats'].get(l['stat'], {}).get('label', l['stat']), l['line'], l['side'])

def board_lines(rec, boards_cfg, with_days=0):
    L = []
    for b in ORDER:
        if b not in rec: continue
        r = rec[b]; t = boards_cfg[b]['title'].title()
        if not (r['won'] + r['lost'] + r['pending'] + r['short']): L.append('  %s: no full board yet' % t); continue
        s = '  %s: won %d day%s, lost %d' % (t, r['won'], '' if r['won'] == 1 else 's', r['lost'])
        if r['pending']: s += ', %d pending' % r['pending']
        if r['short']: s += ', %d short (not counted)' % r['short']
        L.append(s)
        if with_days and b in ('top3', 'elite6'):
            for day, g, sl in r['days'][-with_days:]:
                L.append('    %s %s: %s' % (dt.date.fromisoformat(day).strftime('%a %-m/%-d'), {'won': '✅ WON', 'lost': '❌ LOST', 'pending': '⏳ pending', 'short': '— short'}[g], ' · '.join(leg_text(l) for l in sl['legs'])))
    return L

def boards_text(days=7):
    c = CM.cfg(); rec = record()
    L = ['%s **%s WHOLE-BOARD RECORD** · official slip = last board posted before the first game, every leg must hit' % (c['emoji'], c['name'].upper()), '']
    L += board_lines(rec, c['boards'], with_days=days)
    L += ['', 'A void leg never loses. A board with fewer legs than it needs is not counted. 🧪 TEST, not on the real money record.']
    return '\n'.join(L)

# ---------- real record by band ----------
def real_record(db=None, force=False):
    cached = CM.read_json(CACHE_FILE, None)
    if cached and not force and time.time() - cached.get('at', 0) < 3600: return cached['rec']
    db = db or DBM.connect(); rec = C.defaultdict(lambda: [0, 0])
    for r in db.execute("select kind, stat, side, confidence, status from picks where status in ('win','loss')").fetchall():
        b = band_of(r['confidence'] or 0)
        if not b: continue
        for key in ('%s|%s|%s|%s' % (r['kind'], r['stat'], r['side'], b), '%s|*|%s|%s' % (r['kind'], r['side'], b), '*|*|*|%s' % b):
            rec[key][0] += 1 if r['status'] == 'win' else 0; rec[key][1] += 1
    rec = dict(rec); CM.write_json(CACHE_FILE, dict(at=time.time(), rec=rec)); return rec

def real_record_line(r, rec=None):
    """🧾 line for a card. r needs kind, stat, side, confidence."""
    try:
        rec = rec or real_record(); b = band_of(r['confidence'])
        if not b: return None
        c = CM.cfg(); lab = c['stats'].get(r['stat'], {}).get('label', r['stat']); kind = r['kind'].title()
        w, n = rec.get('%s|%s|%s|%s' % (r['kind'], r['stat'], r['side'], b), [0, 0])
        if n >= 5: return '🧾 Real record: %s %s %s at %s hit %d of %d%s' % (kind, lab, r['side'], b, w, n, ' ✅' if w / n >= .75 else ' ⚠️' if w / n < .6 else '')
        w2, n2 = rec.get('%s|*|%s|%s' % (r['kind'], r['side'], b), [0, 0])
        if n2 >= 5: return '🧾 Real record: %s %s at %s hit %d of %d (all stats; %s alone %d of %d, too few to judge)' % (kind, r['side'], b, w2, n2, lab, w, n)
        w3, n3 = rec.get('*|*|*|%s' % b, [0, 0])
        if n3: return '🧾 Real record: picks at %s hit %d of %d so far (too few to judge by type)' % (b, w3, n3)
        return '🧾 Real record: nothing graded yet at %s' % b
    except Exception: return None

def bands_text(rows=None):
    """'Is the number honest' lines: rows = graded pick dicts (a report window) or None = everything."""
    db = DBM.connect(); c = CM.cfg()
    rows = rows if rows is not None else [dict(r) for r in db.execute("select kind, stat, side, confidence, status from picks where status in ('win','loss')").fetchall()]
    L = []
    for lo, hi in BANDS:
        R = [r for r in rows if lo <= (r['confidence'] or 0) < hi and r['status'] in ('win', 'loss')]
        if not R: continue
        w = sum(1 for r in R if r['status'] == 'win'); n = len(R)
        L.append('  said %s: hit %d of %d (%.0f%%)%s' % ('%d-%d%%' % (lo, hi - 1) if hi < 101 else '%d%%+' % lo, w, n, 100 * w / n, ' ✅ honest' if abs(100 * w / n - (lo + min(hi, 100)) / 2) <= 5 and n >= 20 else ' ⚠️ over-confident' if n >= 20 and 100 * w / n < lo - 5 else ''))
    for k in ('goblin', 'demon', 'standard'):
        R = [r for r in rows if r['kind'] == k and r['status'] in ('win', 'loss') and (r['confidence'] or 0) >= c['rules']['floor']]
        if R: L.append('  %s lines at %d+: hit %d of %d' % (k.title(), c['rules']['floor'], sum(1 for r in R if r['status'] == 'win'), len(R)))
    return L or ['  nothing graded yet']

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'bands': print('\n'.join(bands_text()))
    else: print(boards_text())
