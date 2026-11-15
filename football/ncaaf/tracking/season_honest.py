"""APEX-SEASONHONEST-2026-11-10 (owner, "go honest college ... it needs to automatically update"): honest numbers from THIS
season's real PrizePicks lines. Every saved line for this sport (the line vault: real regular / Goblin / Demon lines, graded from
box scores) is scored the way the bot scores it live, using only games before that day, and counted won or lost. Rebuilt every
morning after the vault's 4:40 AM run, so it grows by itself as the season goes on. Used by tracking/honest.py after the bot's
own graded picks and before past seasons. Reads only our own files; no PrizePicks call. Turn off: ON = False, restart."""
import os, json, sqlite3, time, collections as C
import common as CM

ON = True
OUT = os.path.join(CM.CACHE, 'honest_season.json')
VAULT = os.path.expanduser('~/ApexSports/_shared/line_vault/line_vault.sqlite')
POOL_FROM = 70          # ratings of 70+ are also counted together, for when one band has too few lines
_S = {'mt': 0, 'd': {}}


def build():
    """Returns one line for #system."""
    from database import db as DBM
    from models import projection as PJ, probability as PB
    from tracking import honest as HN
    c = CM.cfg(); sport = c['sport']
    v = sqlite3.connect('file:%s?mode=ro' % VAULT, uri=True); v.row_factory = sqlite3.Row
    rows = v.execute("select * from lines where sport=? and result in ('more','less') and more_won is not null and actual is not null and status_last='pre_game' and copy_of is null and stat_code is not null and stat_code != '' and line_last is not null order by game_date", (sport,)).fetchall()
    v.close()
    rows = [r for r in rows if r['stat_code'] in c['stats'] and c['stats'][r['stat_code']].get('board', True) and r['kind'] in ('standard', 'goblin', 'demon')]
    if not rows:
        return None
    anchor = {(r['player'], r['game_date'], r['stat_code']): r['line_last'] for r in rows if r['kind'] == 'standard'}
    db = DBM.connect(); E = PJ.Engine(db); fits = E.fits
    R = C.defaultdict(lambda: [0, 0]); cache = {}; used = 0

    def add(kind, stat, side, p, won):
        b = HN.band(p)
        if not b:
            return
        ks = list(HN._keys(kind, stat, side, b))
        if p >= POOL_FROM:
            ks.append('%s|*|%s|%d+' % (kind, side, POOL_FROM))
        for k in ks:
            R[k][0] += int(won); R[k][1] += 1
    for r in rows:
        L = r['line_last']; a = r['actual']
        if a == L:
            continue
        pn = CM.norm(r['player']); k = (pn, r['stat_code'], r['game_date'])
        if k not in cache:
            try:
                cache[k] = E.project(pn, r['stat_code'], r['game_date'], r['opponent'], 1 if (r['home_team'] or '') == (r['team'] or '') else 0, dict(team=r['team'], game_date=r['game_date']))
            except Exception:
                cache[k] = None
        pr = cache[k]
        if not pr:
            continue
        try:
            o = PB.evaluate(pr, L, None, fits, anchor.get((r['player'], r['game_date'], r['stat_code'])))['over']
        except Exception:
            continue
        used += 1
        if r['kind'] == 'standard':
            add('standard', r['stat_code'], 'MORE', o, a > L)
            if r['less_offered']:
                add('standard', r['stat_code'], 'LESS', 100 - o, a < L)
        else:
            add(r['kind'], r['stat_code'], 'MORE', o, a > L)
    out = dict(built=CM.iso(), lines=used, first=rows[0]['game_date'], last=rows[-1]['game_date'], rates=R)
    tmp = OUT + '.tmp'; json.dump(out, open(tmp, 'w')); os.replace(tmp, OUT)
    return "🧪 This season's real lines: honest numbers updated from %s graded PrizePicks lines (%s to %s)." % (format(used, ','), rows[0]['game_date'], rows[-1]['game_date'])


def rates():
    if not ON:
        return {}
    try:
        mt = os.path.getmtime(OUT)
        if mt != _S['mt']:
            _S.update(mt=mt, d=json.load(open(OUT)).get('rates') or {})
    except Exception:
        pass
    return _S['d']


def lookup(kind, stat, side, conf, key, min_n):
    """(won, n, pooled) for this exact key, else the 70+ pool of that kind and side when the rating is 70+, else None."""
    d = rates(); x = d.get(key)
    if x and x[1] >= min_n:
        return x[0], x[1], False
    try:
        if float(conf) >= POOL_FROM and key.split('|')[1] == '*':
            x = d.get('%s|*|%s|%d+' % (kind, side, POOL_FROM))
            if x and x[1] >= min_n:
                return x[0], x[1], True
    except (TypeError, ValueError):
        pass
    return None
