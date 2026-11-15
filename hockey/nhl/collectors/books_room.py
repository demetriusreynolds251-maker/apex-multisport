"""APEX-ROOMFLAG-2026-11-06 (owner, "go room flag"): the books' main line for each NHL player prop, from TheOddsGap
(our own code, plain REST, no outside packages). Display only: a card shows 📚 when PrizePicks' line is above the books'
line on a LESS pick (LESS won 61% / 64% in both halves of the Aug-Nov test). It never changes a number or a board.
The key is read at run time from secrets/theoddsgap_key.txt and is never printed or logged."""
import os, io, csv, json, time, urllib.request, datetime as dt
import common as CM

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'cache', 'books_room.json')
SHOW_FLAG = True        # False = cards stop showing the 📚 line
MAP = {'sog': 'player_shots_on_goal', 'points': 'player_points', 'assists': 'player_assists', 'saves': 'player_total_saves',
       'blocked': 'player_blocks', 'goals': 'player_goals'}   # same stats as the room test
RANK = {'first_seen': 0, 't12': 1, 't6': 2, 't1': 3, 'close': 4}
_C = {'mt': 0, 'props': {}}


def run():
    """Download today's and yesterday's books lines and save the newest main line per player prop. Returns one line."""
    key = CM.secret('theoddsgap_key.txt')
    if not key:
        return '📚 Books lines skipped: no TheOddsGap key saved.'
    start = (CM.now_ct().date() - dt.timedelta(days=1)).isoformat()
    req = urllib.request.Request('https://theoddsgap.com/api/props-export.csv?start=' + start,
                                 headers={'X-OddsGap-Data-Key': key, 'User-Agent': 'ApexSports-NHL'})
    b = urllib.request.urlopen(req, timeout=300).read()
    A = {}
    for r in csv.DictReader(io.StringIO(b.decode('utf-8', 'ignore'))):
        if not (r.get('player_id') or '').startswith('nhl:') or r.get('market') not in MAP.values():
            continue
        rk = RANK.get(r.get('anchor'), -1)
        try:
            f = float(r['consensus_fair']); ln = float(r['line'])
        except (TypeError, ValueError, KeyError):
            continue
        if rk < 0:
            continue
        a = A.setdefault('%s|%s|%s' % (CM.norm(r.get('player')), r['market'], r.get('game_date')), {'r': -1, 'lines': {}, 'ts': ''})
        if rk > a['r']:
            a.update(r=rk, lines={}, ts=r.get('ts') or '')
        if rk == a['r']:
            a['lines'][ln] = f
    out = {}
    for k, a in A.items():
        if a['lines']:
            m = min(a['lines'], key=lambda x: abs(a['lines'][x] - 50))
            out[k] = dict(line=m, over=a['lines'][m], at=a['ts'])
    tmp = OUT + '.tmp'
    json.dump(dict(at=CM.iso(), props=out), open(tmp, 'w'))
    os.replace(tmp, OUT)
    return '📚 Books lines saved for %d NHL player props (TheOddsGap).' % len(out)


def _props():
    try:
        mt = os.path.getmtime(OUT)
        if mt != _C['mt']:
            _C.update(mt=mt, props=json.load(open(OUT)).get('props') or {})
    except Exception:
        pass
    return _C['props']


def lookup(r):
    """Books' main line for a scored row, or None. TheOddsGap dates games in UTC, so try the start's UTC date first."""
    mk = MAP.get(r.get('stat'))
    if not mk:
        return None
    P = _props()
    n = r.get('player_norm') or CM.norm(r.get('player'))
    days = []
    try:
        days.append(CM.parse_iso(r.get('start')).astimezone(dt.timezone.utc).date().isoformat())
    except Exception:
        pass
    days.append(str(r.get('game_date'))[:10])
    for d in days:
        x = P.get('%s|%s|%s' % (n, mk, d))
        if x:
            return x
    return None


def flag_line(r):
    """The 📚 card line, or None."""
    if not SHOW_FLAG or r.get('side') != 'LESS':
        return None
    bk = lookup(r)
    if not bk or not r.get('line') or r['line'] <= bk['line']:
        return None
    return "📚 PrizePicks' line %g is above the books' line %g. When that happened in testing, LESS won about 6 out of 10 (NHL, Aug-Nov)." % (r['line'], bk['line'])
