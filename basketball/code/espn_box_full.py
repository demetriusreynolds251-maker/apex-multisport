#!/usr/bin/env python3
"""FULL NBA box scores for the line vault (owner, 11/9/2026: "go save nba box scores").
espn_results.py keeps only points / rebounds / assists / field goals, so PrizePicks threes, steals, blocks,
turnovers and fantasy-score lines could never be graded. This saves EVERY stat column ESPN publishes for each
finished NBA game into data/processed/nba_box_full.sqlite. Own file, own database: the basketball bot, its
grading and its boards do not read it. Calls ESPN's public summary only (one call per finished game not yet
saved, 1 second apart). Never calls PrizePicks.
  python3 code/espn_box_full.py            save every finished game listed in espn_games.sqlite that is missing
"""
import json, os, sqlite3, sys, time, unicodedata, re, urllib.request
ROOT = os.environ.get('BBALL_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ESPN_DB = os.path.join(ROOT, 'data', 'processed', 'espn_games.sqlite')
FULL_DB = os.path.join(ROOT, 'data', 'processed', 'nba_box_full.sqlite')
BASE = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/'
ALIAS = {'GS': 'GSW', 'NO': 'NOP', 'NY': 'NYK', 'SA': 'SAS', 'UTAH': 'UTA', 'WSH': 'WAS'}
def _abbr(s): return ALIAS.get(str(s or '').upper(), str(s or '').upper())
def norm(s):
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r"[.'`]", '', s); s = re.sub(r'\b(jr|sr|ii|iii|iv)\b', '', s)
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z ]', ' ', s)).strip()
def connect():
    db = sqlite3.connect(FULL_DB, timeout=60)
    db.executescript("""create table if not exists player_box(event_id text, game_date text, athlete_id text, player text, player_norm text, team text, opponent text, home integer,
        played integer, minutes real, points real, rebounds real, assists real, threes real, steals real, blocks real, turnovers real,
        fgm real, fga real, ftm real, fta real, stats_json text, saved_at text, primary key(event_id, athlete_id));
      create index if not exists ix_pb on player_box(game_date, player_norm);
      create table if not exists games_saved(event_id text primary key, game_date text, players integer, saved_at text);""")
    return db
def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as r: return json.load(r)
def _num(x):
    try: return float(x)
    except (ValueError, TypeError): return None
def _pair(x):
    a = str(x or '').split('-')
    return (_num(a[0]), _num(a[1])) if len(a) == 2 else (None, None)
def _minutes(x):
    s = str(x or '').strip()
    if ':' in s:
        a, b = s.split(':')[:2]; return (_num(a) or 0) + (_num(b) or 0) / 60
    return _num(s)
def parse(j, g, now):
    rows = []
    for tb in ((j.get('boxscore') or {}).get('players') or []):
        team = _abbr((tb.get('team') or {}).get('abbreviation')); home = int(team == g['home_team']); opp = g['away_team'] if home else g['home_team']
        for sec in tb.get('statistics') or []:
            keys = [str(k) for k in sec.get('keys') or []]
            for a in sec.get('athletes') or []:
                at = a.get('athlete') or {}; s = dict(zip(keys, a.get('stats') or []))
                fgm, fga = _pair(s.get('fieldGoalsMade-fieldGoalsAttempted')); tpm, _ = _pair(s.get('threePointFieldGoalsMade-threePointFieldGoalsAttempted')); ftm, fta = _pair(s.get('freeThrowsMade-freeThrowsAttempted'))
                mins = _minutes(s.get('minutes')) or 0
                rows.append((g['event_id'], g['game_date'], str(at.get('id')), at.get('displayName'), norm(at.get('displayName')), team, opp, home, int(bool(s) and mins > 0), mins,
                             _num(s.get('points')), _num(s.get('rebounds')), _num(s.get('assists')), tpm, _num(s.get('steals')), _num(s.get('blocks')), _num(s.get('turnovers')),
                             fgm, fga, ftm, fta, json.dumps(s), now))
    return rows
def update(pause=1.0):
    import datetime as dt
    out = dict(new_games=0, players=0, failed=0, already=0)
    if not os.path.exists(ESPN_DB): return out
    src = sqlite3.connect('file:%s?mode=ro' % ESPN_DB, uri=True); src.row_factory = sqlite3.Row
    games = [dict(r) for r in src.execute('select event_id, game_date, home_team, away_team from games where final=1 order by game_date')]; src.close()
    db = connect(); have = {r[0] for r in db.execute('select event_id from games_saved')}
    for g in games:
        if g['event_id'] in have: out['already'] += 1; continue
        try:
            now = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'); rows = parse(fetch(BASE + 'summary?event=' + g['event_id']), g, now)
            if len(rows) < 10: out['failed'] += 1; continue
            db.executemany('insert or replace into player_box values(%s)' % ','.join('?' * 23), rows)
            db.execute('insert or replace into games_saved values(?,?,?,?)', (g['event_id'], g['game_date'], len(rows), now)); db.commit()
            out['new_games'] += 1; out['players'] += len(rows)
        except Exception as e:
            out['failed'] += 1; print('failed', g['event_id'], type(e).__name__, file=sys.stderr)
        time.sleep(pause)
    return out
if __name__ == '__main__': print(update())
