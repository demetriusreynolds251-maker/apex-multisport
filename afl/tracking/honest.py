"""APEX-HONEST-2026-11-07 (owner, "go honest all"): an honest number for every prop.
How often this kind of pick really hits, matched by kind (regular / Demon / Goblin), stat, MORE or LESS and how high Apex
rated it. Real tracker results are used as soon as 20+ of that kind are graded; until then past seasons (this sport's
history: real PrizePicks lines + real results, scored by today's engine; Demon and Goblin lines rebuilt 1-2 steps from the
regular line). If a stat has too few, all stats of that kind and side are used. History rebuilds itself when the engine
changes or once a week. Display only: never changes a probability, a rank or a board. This sport's own code only."""
import os, json, time, collections as C
import common as CM

OUT = os.path.join(CM.CACHE, 'honest.json')
MIN_N = 20
SHOW = True             # False = cards and boards stop showing the honest line
BANDS = [(0, 40), (40, 50), (50, 60), (60, 65), (65, 70), (70, 75), (75, 80), (80, 90), (90, 101)]
ENGINE = ('models/probability.py', 'models/projection.py', 'cache/lean.json', 'config/sport.json')
_H = {'mt': 0, 'd': {}}
_L = {'at': 0, 'd': {}}


def band(p):
    try:
        p = float(p)
    except (TypeError, ValueError):
        return None
    for lo, hi in BANDS:
        if lo <= p < hi:
            return '90+' if lo == 90 else '%d-%d' % (lo, hi - 1)
    return '90+' if p >= 100 else None


def _keys(kind, stat, side, b):
    return ('%s|%s|%s|%s' % (kind, stat, side, b), '%s|*|%s|%s' % (kind, side, b))


def _engine_stamp():
    return {f: round(os.path.getmtime(os.path.join(CM.ROOT, f))) for f in ENGINE if os.path.exists(os.path.join(CM.ROOT, f))}


def build():
    """Score every saved history line with today's engine and count real hits. Returns one line for #system."""
    from database import db as DBM
    from models import projection as PJ, probability as PB
    t0 = time.time()
    db = DBM.connect(); E = PJ.Engine(db); fits = E.fits; c = CM.cfg()
    rows = [dict(r) for r in db.execute('select * from prop_lines where pp_line is not null and result is not null and pp_before_start=1 order by game_date')]
    rows = [r for r in rows if r['stat'] in c['stats'] and c['stats'][r['stat']].get('board', True)]
    from tracking import played as PL   # APEX-HONESTFIX-2026-11-10: only lines where the player really played
    rows, left_out = PL.learn_rows(db, rows)
    if not rows:
        return None
    mid = rows[len(rows) // 2]['game_date']
    R = C.defaultdict(lambda: [0, 0, 0, 0])   # older hits, older n, newer hits, newer n
    used = 0
    for r in rows:
        try:
            pr = E.project(r['player_norm'], r['stat'], r['game_date'], r['opponent'], r['home'], dict(team=r['team'], game_date=r['game_date']))
        except Exception:
            pr = None
        if not pr:
            continue
        used += 1
        L = r['pp_line']; res = r['result']; h = 0 if r['game_date'] < mid else 2
        step = 1.0 if L < 10 else max(1.0, round(L * .05))

        def add(kind, side, p, won):
            b = band(p)
            if not b:
                return
            ks = _keys(kind, r['stat'], side, b)
            for k in (ks[:1] if r.get('source') == 'box_td' else ks):   # APEX-HONESTFIX: rebuilt touchdown lines count for touchdowns only, not for 'all stats'
                x = R[k]; x[h] += int(won); x[h + 1] += 1
        if res != L:
            o = PB.evaluate(pr, L, None, fits, L)['over']
            add('standard', 'MORE', o, res > L); add('standard', 'LESS', 100 - o, res < L)
        for k in (1, 2):
            ln = L + k * step
            if res != ln:
                add('demon', 'MORE', PB.evaluate(pr, ln, None, fits, L)['over'], res > ln)
            ln = L - k * step
            if ln > 0 and res != ln:
                add('goblin', 'MORE', PB.evaluate(pr, ln, None, fits, L)['over'], res > ln)
    out = dict(built=CM.iso(), engine=_engine_stamp(), props=used, mid=mid, first=rows[0]['game_date'], last=rows[-1]['game_date'], rates=R)
    tmp = OUT + '.tmp'; json.dump(out, open(tmp, 'w')); os.replace(tmp, OUT)
    return '🧪 Honest numbers rebuilt from %d past props (%s to %s) in %d min. %d did-not-play lines left out.' % (used, str(rows[0]['game_date'])[:10], str(rows[-1]['game_date'])[:10], (time.time() - t0) // 60, left_out)


def maybe_build():
    """Rebuild when there is none, the engine changed, or it is 7+ days old. Returns a line or None."""
    try:
        d = json.load(open(OUT))
        if d.get('engine') == _engine_stamp() and time.time() - os.path.getmtime(OUT) < 7 * 86400:
            return None
    except Exception:
        pass
    return build()


def _hist():
    try:
        mt = os.path.getmtime(OUT)
        if mt != _H['mt']:
            _H.update(mt=mt, d=json.load(open(OUT)).get('rates') or {})
    except Exception:
        pass
    return _H['d']


def _live():
    """Real tracker: every graded pick (status win/loss), same keys. Refreshed every 30 minutes."""
    if _L['at'] > time.time() - 1800:
        return _L['d']
    d = C.defaultdict(lambda: [0, 0])
    try:
        from database import db as DBM
        db = DBM.connect()
        for kind, stat, side, conf, st in db.execute("select kind, stat, side, confidence, status from picks where status in ('win','loss')"):
            b = band(conf)
            if not b:
                continue
            for k in _keys(kind, stat, side, b):
                d[k][0] += st == 'win'; d[k][1] += 1
        db.close()
    except Exception:
        pass
    _L.update(at=time.time(), d=dict(d))
    return _L['d']


def honest(r):
    """{'pct', 'n', 'src': 'real'|'history', 'all_stats': bool} or None."""
    b = band(r.get('confidence'))
    if not b or r.get('kind') not in ('standard', 'demon', 'goblin'):
        return None
    live, hist = _live(), _hist()
    for i, k in enumerate(_keys(r['kind'], r.get('stat'), r.get('side'), b)):
        w, n = live.get(k, (0, 0))
        if n >= MIN_N:
            return dict(pct=round(100.0 * w / n, 1), n=n, src='real', all_stats=i == 1)
        h = hist.get(k)
        if h and h[1] + h[3] >= MIN_N:
            return dict(pct=round(100.0 * (h[0] + h[2]) / (h[1] + h[3]), 1), n=h[1] + h[3], src='history', all_stats=i == 1)
    return None


def card_line(r):
    if not SHOW:
        return None
    x = r.get('honest') if 'honest' in r else honest(r)
    if not x:
        return '🧪 Honest: not enough graded picks of this kind yet. Tracker fills it in automatically.'
    return '🧪 Really hits about **%.0f%%** (%s, %s picks%s)' % (x['pct'], 'real tracker' if x['src'] == 'real' else 'past seasons',
                                                                 format(x['n'], ','), ', all stats' if x.get('all_stats') else '')
