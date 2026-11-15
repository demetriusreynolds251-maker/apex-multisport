"""APEX-LINEUPCHECK-2026-11-07 (owner, "Go lineup check"): soccer starting lineups from ESPN (free, no key).
In the 90 minutes before each kickoff that has PrizePicks lines, reads ESPN's match page every 15 minutes. Once a team's
lineup is posted, a player on the bench gets "benched: not in the starting lineup" and a player missing from the
matchday squad gets "not in the matchday squad". rules.no_play_reason turns that into a no-play, so he leaves the
boards and /lottery. Only the same match counts (kickoff within 15 min of the PrizePicks start), so nothing carries
over to the next game. Our own code, plain urllib, read only on ESPN. Switch: ON."""
import os, sys, json, time, urllib.request, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as CM

ON = True
WINDOW_MIN = 90          # look this long before kickoff
EVERY_MIN = 15
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, 'cache', 'lineups.json')
BASE = 'https://site.api.espn.com/apis/site/v2/sports/%s/%s'
_C = {}
# APEX-LINEUPLESS-2026-11-12 (owner, "Go lineup less"): national team games were never read (France v Italy 11/12 had no
# lineup check). These ESPN pages are read for LINEUPS ONLY, on top of the club leagues in config.
EXTRA_PATHS = ['soccer/uefa.nations', 'soccer/fifa.friendly', 'soccer/fifa.worldq.uefa', 'soccer/fifa.worldq.conmebol', 'soccer/fifa.worldq.concacaf',
               'soccer/uefa.euroq', 'soccer/fifa.world', 'soccer/uefa.euro', 'soccer/conmebol.america', 'soccer/concacaf.nations.league']
LESS_STATS = ('shots',)   # regular-line LESS on these is rated by the lineup, not pulled, when the player is on the bench


def _get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'ApexSports-lineup-check/1.0'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def _ts(s):
    try:
        return CM.parse_iso(s)
    except Exception:
        try:
            return dt.datetime.fromisoformat(str(s).replace('Z', '+00:00'))
        except Exception:
            return None


def pull(starts):
    """starts = PrizePicks kickoff datetimes (UTC aware) with lines. Reads ESPN for matches kicking off within WINDOW_MIN.
    Saves cache/lineups.json: {event_id: dict(kickoff, teams={name: dict(posted, starters=[norm], subs=[norm])})}."""
    if not ON:
        return {}
    now = CM.now_utc()
    soon = [s for s in starts if s and 0 < (s - now).total_seconds() / 60 <= WINDOW_MIN]
    if not soon:
        return {}
    old = CM.read_json(CACHE, {}) or {}
    keep = {k: v for k, v in old.items() if (_ts(v.get('kickoff')) or now) > now - dt.timedelta(hours=6)}
    days = sorted({(s - dt.timedelta(hours=5)).strftime('%Y%m%d') for s in soon})
    for path in list(CM.cfg().get('espn', {}).get('paths', [])) + [p for p in EXTRA_PATHS if p not in CM.cfg().get('espn', {}).get('paths', [])]:
        for day in days:
            try:
                sb = _get(BASE % (path, 'scoreboard?dates=' + day))
            except Exception as e:
                CM.log('lineups', 'scoreboard %s %s: %s' % (path, day, type(e).__name__)); continue
            for e in sb.get('events') or []:
                ko = _ts(e.get('date'))
                if not ko or not any(abs((ko - s).total_seconds()) <= 900 for s in soon):
                    continue
                try:
                    sm = _get(BASE % (path, 'summary?event=' + str(e['id'])))
                except Exception as ex:
                    CM.log('lineups', 'summary %s: %s' % (e.get('id'), type(ex).__name__)); continue
                teams = {}
                for t in sm.get('rosters') or []:
                    tm = t.get('team') or {}
                    ros = t.get('roster') or []
                    st = [CM.norm((p.get('athlete') or {}).get('displayName')) for p in ros if p.get('starter')]
                    sub = [CM.norm((p.get('athlete') or {}).get('displayName')) for p in ros if not p.get('starter')]
                    names = [CM.norm(x) for x in (tm.get('displayName'), tm.get('shortDisplayName'), tm.get('name'), tm.get('abbreviation')) if x]
                    teams[tm.get('displayName') or '?'] = dict(posted=len(st) >= 11, starters=st, subs=sub, names=names)
                keep[str(e['id'])] = dict(kickoff=ko.isoformat(), name=e.get('name'), teams=teams, at=CM.iso())
    CM.write_json(CACHE, keep)
    _C.pop('d', None)
    return keep


def _load():
    if _C.get('at', 0) < time.time() - 60:
        _C['d'] = CM.read_json(CACHE, {}) or {}; _C['at'] = time.time()
    return _C.get('d') or {}


def _same(a, b):
    """Same player: full name, or same last name + same first initial."""
    if a == b:
        return True
    x, y = a.split(), b.split()
    if len(x) > 1 and len(y) > 1 and x[-1] == y[-1] and x[0][0] == y[0][0]:
        return True
    # APEX-LINEUPNAMES-2026-11-12 (owner, "Fix line up names"): ESPN drops a first name ("Pio Esposito" for "Francesco Pio
    # Esposito"). Same last name and every word of the shorter name inside the longer one (2+ words) = same player. A brother
    # ("Sebastiano Esposito") does not match.
    sx, sy = set(x), set(y); short, long_ = (sx, sy) if len(sx) <= len(sy) else (sy, sx)
    return len(short) >= 2 and x[-1] == y[-1] and short <= long_


def status(row):
    """APEX-LINEUPLESS-2026-11-12: 'start' / 'bench' / 'out' from the posted ESPN lineup of this row's own match, or None (not posted)."""
    if not ON:
        return None
    try:
        st = _ts(row.get('start')); pn = row.get('player_norm') or CM.norm(row.get('player')); team = CM.norm(row.get('team'))
        if not st or not pn:
            return None
        for ev in _load().values():
            ko = _ts(ev.get('kickoff'))
            if not ko or abs((ko - st).total_seconds()) > 900:
                continue
            for tname, t in (ev.get('teams') or {}).items():
                if not t.get('posted'):
                    continue
                if any(_same(pn, n) for n in t['starters']):
                    return 'start'
                if any(_same(pn, n) for n in t['subs']):
                    return 'bench'
            mine = [t for t in (ev.get('teams') or {}).values() if team and any(team == n or team in n.split() or (len(team) > 3 and team in n) for n in t.get('names', []))]
            if len(mine) == 1 and mine[0].get('posted'):
                return 'out'
        return None
    except Exception:
        return None


def less_row(row):
    return row.get('kind') == 'standard' and row.get('side') == 'LESS' and row.get('stat') in LESS_STATS


def reason(row):
    """Plain no-play reason for a scored row, or None."""
    if not ON:
        return None
    if less_row(row) and status(row) == 'bench':   # APEX-LINEUPLESS: a bench player is the BEST case for Shots LESS, so it stays playable
        return None
    try:
        st = _ts(row.get('start')); pn = row.get('player_norm') or CM.norm(row.get('player')); team = CM.norm(row.get('team'))
        if not st or not pn:
            return None
        for ev in _load().values():
            ko = _ts(ev.get('kickoff'))
            if not ko or abs((ko - st).total_seconds()) > 900:
                continue
            for tname, t in (ev.get('teams') or {}).items():
                if not t.get('posted'):
                    continue
                if any(_same(pn, n) for n in t['starters']):
                    return None
                if any(_same(pn, n) for n in t['subs']):
                    return 'benched: not in the starting lineup (ESPN lineup, %s)' % ev.get('name')
            mine = [t for t in (ev.get('teams') or {}).values() if team and any(team == n or team in n.split() or (len(team) > 3 and team in n) for n in t.get('names', []))]
            if len(mine) == 1 and mine[0].get('posted'):
                return 'not in the matchday squad (ESPN lineup, %s)' % ev.get('name')
        return None
    except Exception:
        return None


if __name__ == '__main__':
    from database import db as DBM
    db = DBM.connect()
    starts = [_ts(r[0]) for r in db.execute("select distinct start from pp_lines where start > ? and status='pre_game'", ((CM.now_utc() - dt.timedelta(days=1)).date().isoformat(),))]
    if len(sys.argv) > 1 and sys.argv[1] == 'all':
        WINDOW_MIN = 24 * 60
    d = pull([s for s in starts if s])
    print('matches read:', len(d))
    for ev in d.values():
        print(ev['name'], ev['kickoff'], {k: (v['posted'], len(v['starters']), len(v['subs'])) for k, v in ev['teams'].items()})
