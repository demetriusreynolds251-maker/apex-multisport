#!/usr/bin/env python3
"""APEX NFL BOX SCORES (owner 11/8 "Go nfl box scores but all nfl props need to be correct").
Fills football/nfl history.db player_games from nflverse weekly player stats (official full box scores, every player every game).
- Existing row for the same player + game: box-score numbers replace the stored ones (old SGO rows only had a stat on days
  PrizePicks offered that prop, and some were wrong). Keys the box score doesn't have (longest catch / run) are kept.
- No row yet: a new row is added (source 'nflverse').
python3 nflbox.py dry   -> agreement report only;  python3 nflbox.py apply -> writes."""
import csv, glob, json, os, sqlite3, sys, collections as C, datetime as dt
NFL = os.path.expanduser('~/ApexSports/football/nfl'); sys.path.insert(0, NFL)
import common as CM
import json as _j, os as _o
_B = _o.path.dirname(_o.path.abspath(__file__))
ALIAS = dict(p.split('>') for p in open(_o.path.join(_B, 'plnames.py')).read().split('A = """')[1].split('"""')[0].split('|'))
try: ALIAS.update(_j.load(open(_o.path.join(_B, 'aliases.json'))))
except Exception: pass
RAW = os.path.expanduser('~/openclaw/_backups/_sports_staging/nfl_td/raw')
GAMES = os.path.expanduser('~/openclaw/_backups/_sports_staging/freedata/role/games.csv')
MODE = sys.argv[1] if len(sys.argv) > 1 else 'dry'


def f(x):
    try: return float(x)
    except (TypeError, ValueError): return None


def stats_of(r, tk):
    g = lambda k: f(r.get(k))
    s = {'completions': g('completions'), 'pass_attempts': g('attempts'), 'passing_yards': g('passing_yards'), 'passing_tds': g('passing_tds'),
         'interceptions_thrown': g('passing_interceptions'), 'rushing_attempts': g('carries'), 'rushing_yards': g('rushing_yards'),
         'rushing_tds': g('rushing_tds'), 'receptions': g('receptions'), 'targets': g('targets'), 'receiving_yards': g('receiving_yards'),
         'receiving_tds': g('receiving_tds'), 'sacks': g('def_sacks'), 'fg_made': g('fg_made')}
    solo, ast, wa = g('def_tackles_solo') or 0, g('def_tackle_assists') or 0, g('def_tackles_with_assist') or 0
    s['tackles'] = {'solo+assists': solo + ast, 'solo+with_assist': solo + wa}[tk]
    if g('fg_made') is not None or g('pat_made') is not None: s['kicking_points'] = 3 * (g('fg_made') or 0) + (g('pat_made') or 0)
    pos = r.get('position_group') or r.get('position')
    # only keep stat families this player actually plays (a WR's passing 0 is real, but a lineman's 0 receiving is noise either way)
    return {k: v for k, v in s.items() if v is not None}


gday = {}; espn = {}
for r in csv.DictReader(open(GAMES)):
    gday[r['game_id']] = r['gameday']; espn[r['game_id']] = r.get('espn') or ''
db = sqlite3.connect(os.path.join(NFL, 'database', 'history.db')); db.row_factory = sqlite3.Row
db.execute('pragma busy_timeout=60000')
have = C.defaultdict(list)   # (player_norm, team) -> rows
for r in db.execute('select rowid, event_id, player_norm, team, opponent, home, game_date, stats_json, source from player_games'):
    have[(r['player_norm'], r['team'])].append(dict(r))
ev_by_team_date = {}
for k, L in have.items():
    for r in L: ev_by_team_date.setdefault((r['team'], r['game_date'][:10]), r['event_id'])


def find(pn, team, d):
    for r in have.get((pn, team), []) + have.get((pn, None), []) + have.get((pn, ''), []):
        if abs((dt.date.fromisoformat(r['game_date'][:10]) - d).days) <= 1: return r
    return None


box = []
for fn in sorted(glob.glob(os.path.join(RAW, 'stats_player_week_*.csv'))):
    for r in csv.DictReader(open(fn)):
        if r['season_type'] not in ('REG', 'POST') or r['game_id'] not in gday: continue
        box.append(r)
print('box rows', len(box))
# pick the tackles definition that agrees best with what was stored
best = None
for tk in ('solo+assists', 'solo+with_assist'):
    a = n = 0
    for r in box:
        if not (f(r.get('def_tackles_solo')) or f(r.get('def_tackle_assists'))): continue
        ex = find(ALIAS.get(CM.norm(r['player_display_name']), CM.norm(r['player_display_name'])), r['team'], dt.date.fromisoformat(gday[r['game_id']]))
        if ex:
            v = json.loads(ex['stats_json']).get('tackles')
            if v is not None: n += 1; a += abs(v - stats_of(r, tk)['tackles']) < 0.01
    print('tackles as %s: agrees %d of %d' % (tk, a, n))
    if best is None or a > best[1]: best = (tk, a)
TK = best[0]
agree = C.Counter(); tot = C.Counter(); upd = new = 0; ex_d = C.defaultdict(list)
for r in box:
    d = dt.date.fromisoformat(gday[r['game_id']]); pn = CM.norm(r['player_display_name']); pn = ALIAS.get(pn, pn); st = stats_of(r, TK)
    ex = find(pn, r['team'], d)
    if ex:
        old = json.loads(ex['stats_json'])
        for k, v in st.items():
            if k in old:
                tot[k] += 1
                if abs(old[k] - v) < 0.01: agree[k] += 1
                elif len(ex_d[k]) < 3: ex_d[k].append('%s %s stored %g box %g' % (r['player_display_name'], d, old[k], v))
        merged = dict(st); merged.update(old); merged['_box'] = 'nflverse'   # stored numbers = what PrizePicks graded; box score only fills what is missing
        if merged != old:
            upd += 1
            if MODE == 'apply': db.execute('update player_games set stats_json=? where rowid=?', (json.dumps(merged), ex['rowid']))
    else:
        if not any(v for v in st.values()): continue   # player with nothing recorded (lineman, no stats)
        ev = ev_by_team_date.get((r['team'], d.isoformat())) or espn.get(r['game_id']) or ('nflv_' + r['game_id'])
        home = 1 if r['game_id'].endswith('_' + r['team']) else 0
        st['_box'] = 'nflverse'; new += 1
        if MODE == 'apply':
            db.execute('insert or ignore into player_games(event_id, player_norm, player, team, opponent, home, game_date, stats_json, source) values (?,?,?,?,?,?,?,?,?)',
                       (ev, pn, r['player_display_name'], r['team'], r['opponent_team'], home, d.isoformat(), json.dumps(st), 'nflverse'))
            have[(pn, r['team'])].append(dict(rowid=None, event_id=ev, player_norm=pn, team=r['team'], game_date=d.isoformat(), stats_json=json.dumps(st)))
print('tackles defined as', TK)
print('stored numbers that match the official box score:')
for k in sorted(tot, key=lambda k: -tot[k]):
    print('  %-22s %d of %d agree (%.1f%%)  %s' % (k, agree[k], tot[k], 100 * agree[k] / tot[k], ' | '.join(ex_d[k])))
print('rows updated %d, rows added %d, mode %s' % (upd, new, MODE))
if MODE == 'apply': db.commit()
