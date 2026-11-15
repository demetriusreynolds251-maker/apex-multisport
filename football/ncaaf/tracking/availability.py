#!/usr/bin/env python3
"""APEX-COLLEGEHOLD-2026-11-13 (owner, "Go college hold"). College football has no injury report (ESPN gives none, the injuries table is
empty), so a hurt or benched player could take a numbered board spot. This uses the box scores we already save:
  - "missed": his team played its most recent game (final ESPN box saved) and he has no box row in it
  - "barely": he played it, but his touches (pass attempts + rush attempts + receptions) were under BARELY x his usual (average of his
    earlier games this season), with a usual of at least MIN_USUAL touches
Only players with 2+ earlier box games for that team this season are judged (otherwise unknown = no hold). Used by rules.build_boards:
a held MORE pick never takes a numbered spot; it waits in BACKUPS with the reason on its card. LESS picks are not touched.
Off: ON = False, restart NCAAF. Undo: git checkout before-college-hold."""
import collections, json
ON = True
BARELY = 0.25
MIN_USUAL = 4.0
SEASON_START = '2026-08-01'
_cache = {}


def _touches(stats_json):
    try: s = json.loads(stats_json or '{}')
    except Exception: return 0.0
    return float(s.get('pass_attempts') or 0) + float(s.get('rushing_attempts') or 0) + float(s.get('receptions') or 0)


def _load(db, day):
    key = (id(db), day)
    if key in _cache: return _cache[key]
    games = collections.defaultdict(list)   # team -> [(date, event)] finished with a box, before day
    for ev, d, h, a in db.execute("select event_id, game_date, home, away from games where source='espn' and final=1 and box_saved=1 and game_date >= ? and game_date < ?", (SEASON_START, day)):
        games[h].append((d, ev)); games[a].append((d, ev))
    for t in games: games[t].sort()
    rows = collections.defaultdict(list)    # player_norm -> [(date, event, team, touches)]
    for pn, d, ev, tm, sj in db.execute("select player_norm, game_date, event_id, team, stats_json from player_games where source='espn' and game_date >= ? and game_date < ?", (SEASON_START, day)):
        rows[pn].append((d, ev, tm, _touches(sj)))
    for pn in rows: rows[pn].sort()
    _cache.clear(); _cache[key] = (games, rows)
    return games, rows


def hold(db, player_norm, game_date):
    """None, or (code, plain reason) for this player before a game on game_date."""
    if not ON: return None
    games, rows = _load(db, game_date)
    mine = rows.get(player_norm) or []
    if len(mine) < 2: return None
    team = mine[-1][2]; tg = games.get(team) or []
    if not tg: return None
    last_d, last_ev = tg[-1]
    import datetime as _dt
    if (_dt.date.fromisoformat(game_date[:10]) - _dt.date.fromisoformat(last_d[:10])).days > 10: return None   # his team's last saved game is too old to judge (box coverage gap)
    played = [x for x in mine if x[1] == last_ev]
    earlier = [x[3] for x in mine if x[0] < last_d and x[2] == team]
    if len(earlier) < 2: return None
    usual = sum(earlier) / len(earlier)
    if usual < MIN_USUAL: return None   # only regular offensive players are judged (defenders and kickers have no touches)
    if not played:
        return ('missed', 'Missed his last game (%s, %s): not in the box score. No injury report exists for college, so he waits in BACKUPS.' % (team, last_d))
    last = played[0][3]
    if last < BARELY * usual:
        return ('barely', 'Barely played last game (%s): %d touches vs his usual %.0f. No injury report exists for college, so he waits in BACKUPS.' % (last_d, last, usual))
    return None
