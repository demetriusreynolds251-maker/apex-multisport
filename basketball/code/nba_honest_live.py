"""APEX-HONEST-NBA-2026-11-07 (owner, "Go both"): honest number for every NBA prop.
Real tracker (graded NBA picks since the engine went live) once 20+ are graded at the same kind|stat|side|band,
else past seasons (every pre-tip PrizePicks line 1/2025-10/2026 scored with today's engine, data/processed/honest.json),
else the same with all stats together, else None. Same rules as the other sports' tracking/honest.py."""
import os, json, time, sqlite3
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(ROOT, 'data', 'processed', 'honest.json')
TRACK = os.path.join(ROOT, 'data', 'processed', 'bball_tracker.sqlite')
ENGINE_SINCE = '2026-11-05T20:30:00'
MIN_N = 20
SHOW = True
BANDS = [(0, 40), (40, 50), (50, 60), (60, 65), (65, 70), (70, 75), (75, 80), (80, 90), (90, 101)]
_C = {}


def band(p):
    try: p = float(p)
    except (TypeError, ValueError): return None
    for lo, hi in BANDS:
        if lo <= p < hi:
            return '90+' if lo == 90 else '%d-%d' % (lo, hi - 1)
    return '90+'


def _keys(kind, stat, side, b):
    return ('%s|%s|%s|%s' % (kind, stat, side, b), '%s|*|%s|%s' % (kind, side, b))


def _hist():
    if 'h' not in _C:
        try: _C['h'] = json.load(open(HIST))['rates']
        except Exception: _C['h'] = {}
    return _C['h']


def _live():
    if _C.get('at', 0) > time.time() - 1800: return _C['l']
    d = {}
    try:
        db = sqlite3.connect('file:%s?mode=ro' % TRACK, uri=True)
        for kind, stat, side, p, st in db.execute("select kind, stat, side, win_prob, status from picks where league='NBA' and first_scored>=? and status in ('win','loss')", (ENGINE_SINCE,)):
            b = band(p)
            if not b: continue
            for k in _keys(kind, stat, side, b):
                x = d.setdefault(k, [0, 0]); x[0] += st == 'win'; x[1] += 1
        db.close()
    except Exception:
        pass
    _C.update(at=time.time(), l=d); return d


def honest(r):
    """{'pct', 'n', 'src': 'real'|'history', 'all_stats': bool} or None."""
    b = band(r.get('win_prob'))
    if not b or r.get('kind') not in ('standard', 'demon', 'goblin') or r.get('side') not in ('MORE', 'LESS'):
        return None
    live, hist = _live(), _hist()
    for i, k in enumerate(_keys(r['kind'], r.get('stat'), r['side'], b)):
        w, n = live.get(k, (0, 0))
        if n >= MIN_N:
            return dict(pct=round(100.0 * w / n, 1), n=n, src='real', all_stats=i == 1)
        h = hist.get(k)
        if h and h[1] + h[3] >= MIN_N:
            return dict(pct=round(100.0 * (h[0] + h[2]) / (h[1] + h[3]), 1), n=h[1] + h[3], src='history', all_stats=i == 1)
    return None


def card_line(r):
    if not SHOW: return None
    x = r.get('honest') if 'honest' in r else honest(r)
    if not x:
        return '🧪 Honest: not enough graded picks of this kind yet. Tracker fills it in automatically.'
    return '🧪 Really hits about **%.0f%%** (%s, %s picks%s)' % (x['pct'], 'real tracker' if x['src'] == 'real' else 'real Goblin lines with this much room' if x['src'] == 'room' else 'real lines with this gap, LESS side' if x['src'] == 'gap' else 'past seasons',
                                                                 format(x['n'], ','), ', all stats' if x.get('all_stats') else '')
