#!/usr/bin/env python3
"""Adds finished NBA box scores from ESPN's public scoreboard to data/processed/espn_games.sqlite (separate from nba_history.sqlite) and grades tracker picks.
NBA only. One scoreboard call per date, one summary call per finished game not yet saved, 1 second apart. Nothing else is called.
Run by hand: python3 code/espn_results.py 2026-10-30"""
import datetime as dt, json, os, sqlite3, time, urllib.request
from zoneinfo import ZoneInfo
ROOT = os.environ.get('BBALL_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ESPN_DB = os.path.join(ROOT, 'data', 'processed', 'espn_games.sqlite')
BASE = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/'
CT = ZoneInfo('America/Chicago')
ALIAS = {'GS': 'GSW', 'NO': 'NOP', 'NY': 'NYK', 'SA': 'SAS', 'UTAH': 'UTA', 'WSH': 'WAS'}
def _abbr(s): return ALIAS.get(str(s or '').upper(), str(s or '').upper())
def connect(path=None):
    p = path or ESPN_DB; os.makedirs(os.path.dirname(p), exist_ok=True); db = sqlite3.connect(p)
    db.executescript("""create table if not exists games(event_id text primary key, game_date text, start_utc text, home_team text, away_team text, home_pts real, away_pts real, final integer, box_saved integer default 0);
      create table if not exists player_games(event_id text, athlete_id text, player text, team text, opponent text, home integer, minutes real, points real, rebounds real, assists real, fgm real, primary key(event_id, athlete_id));
      create index if not exists ix_eg on games(game_date);""")
    return db
def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as r: return json.load(r)
def parse_scoreboard(j):
    out = []
    for e in j.get('events') or []:
        c = (e.get('competitions') or [{}])[0]; teams = {t.get('homeAway'): t for t in c.get('competitors') or []}
        if 'home' not in teams or 'away' not in teams: continue
        st = dt.datetime.fromisoformat(e['date'].replace('Z', '+00:00')); status = ((c.get('status') or e.get('status') or {}).get('type') or {})
        fl = lambda t: float(t['score']) if t.get('score') not in (None, '') else None
        out.append(dict(event_id=str(e['id']), game_date=st.astimezone(CT).date().isoformat(), start_utc=st.astimezone(dt.timezone.utc).isoformat(), home_team=_abbr(teams['home']['team']['abbreviation']),
                        away_team=_abbr(teams['away']['team']['abbreviation']), home_pts=fl(teams['home']), away_pts=fl(teams['away']), final=int(bool(status.get('completed')))))
    return out
def _num(x):
    try: return float(str(x).split('-')[0])
    except (ValueError, TypeError): return None
def _minutes(x):
    s = str(x or '').strip()
    if ':' in s:
        a, b = s.split(':')[:2]; return (_num(a) or 0) + (_num(b) or 0) / 60
    return _num(s)
def parse_summary(j, game):
    """One row per player from an ESPN summary. A player with no stats did not play: minutes 0."""
    rows = []
    for tb in ((j.get('boxscore') or {}).get('players') or []):
        team = _abbr((tb.get('team') or {}).get('abbreviation')); home = int(team == game['home_team']); opp = game['away_team'] if home else game['home_team']
        for sec in tb.get('statistics') or []:
            keys = [str(k) for k in sec.get('keys') or []]
            for a in sec.get('athletes') or []:
                at = a.get('athlete') or {}; s = dict(zip(keys, a.get('stats') or []))
                fg = next((s.get(k) for k in keys if k.startswith('fieldGoalsMade')), None)
                rows.append((game['event_id'], str(at.get('id')), at.get('displayName'), team, opp, home, _minutes(s.get('minutes')) or 0, _num(s.get('points')), _num(s.get('rebounds')), _num(s.get('assists')), _num(fg)))
    return rows
def update(dates, db_path=None, get=fetch, pause=1.0):
    """Saves schedule rows and box scores for the dates (YYYY-MM-DD). Returns counts."""
    db = connect(db_path); got = dict(dates=0, scheduled=0, new_box=0, unfinished=0, failed=0)
    for d in dates:
        ev = parse_scoreboard(get(BASE + 'scoreboard?dates=' + d.replace('-', ''))); got['dates'] += 1; time.sleep(pause)
        for g in ev:
            db.execute('insert into games(event_id,game_date,start_utc,home_team,away_team,home_pts,away_pts,final) values(?,?,?,?,?,?,?,?) on conflict(event_id) do update set game_date=excluded.game_date,start_utc=excluded.start_utc,home_pts=excluded.home_pts,away_pts=excluded.away_pts,final=excluded.final',
                       (g['event_id'], g['game_date'], g['start_utc'], g['home_team'], g['away_team'], g['home_pts'], g['away_pts'], g['final'])); got['scheduled'] += 1
            if not g['final']: got['unfinished'] += 1; continue
            if db.execute('select box_saved from games where event_id=?', (g['event_id'],)).fetchone()[0]: continue
            try:
                rows = parse_summary(get(BASE + 'summary?event=' + g['event_id']), g); time.sleep(pause)
            except Exception: got['failed'] += 1; continue
            if rows:
                db.executemany('insert or replace into player_games values(?,?,?,?,?,?,?,?,?,?,?)', rows); db.execute('update games set box_saved=1 where event_id=?', (g['event_id'],)); got['new_box'] += 1
            else: got['failed'] += 1
        db.commit()
    db.close(); return got
VALUE = {'points': lambda r: r[0], 'rebounds': lambda r: r[1], 'rebounds+assists': lambda r: (r[1] or 0) + (r[2] or 0), 'points+rebounds+assists': lambda r: (r[0] or 0) + (r[1] or 0) + (r[2] or 0),
         'points+rebounds': lambda r: (r[0] or 0) + (r[1] or 0), 'points+assists': lambda r: (r[0] or 0) + (r[2] or 0), 'assists': lambda r: r[2],
          'fieldGoalsMade': lambda r: r[3]}
def grade_pick(espn, norm, player, team, game_date, stat, line, side):
    """(status, value). Open until the game is final. Did not play = void. Same as the line = push."""
    g = espn.execute('select event_id from games where game_date=? and final=1 and box_saved=1 and (home_team=? or away_team=?)', (game_date, team, team)).fetchone()
    if not g: return 'open', None
    rows = [r for r in espn.execute('select points,rebounds,assists,fgm,minutes,player from player_games where event_id=? and team=?', (g[0], team)) if norm(r[5]) == norm(player)]
    if not rows or not rows[0][4]: return 'void', None
    if stat not in VALUE: return 'nostat', None   # 3PM / steals / blocks / turnovers / fantasy: ESPN box here has no column, never a board stat
    v = VALUE[stat](rows[0])
    if v is None: return 'open', None
    if v == line: return 'push', v
    return ('win' if (v > line) == (side == 'MORE') else 'loss'), v
if __name__ == '__main__':
    import sys; print(update(sys.argv[1:] or [(dt.datetime.now(CT).date() - dt.timedelta(days=1)).isoformat()]))
