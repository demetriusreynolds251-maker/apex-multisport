"""Step 6 of NFL box scores: is every graded NFL prop's result the official number?
(a) each stored result vs the official nflverse box score -> agreement per stat; 'apply' fixes wrong results to the official number.
(b) Rush+Rec TDs: PrizePicks posts it at 0.5 for nearly every skill player, but no graded history was saved.
    'apply td' adds one graded 0.5 line (source 'box_td') for every RB/WR/TE/QB game where PrizePicks had ANY line on that player that day."""
import csv, glob, json, os, sys, sqlite3, collections as C, datetime as dt
H = os.path.expanduser('~'); NFL = H + '/ApexSports/football/nfl'; sys.path.insert(0, NFL)
import common as CM
RAW = H + '/openclaw/_backups/_sports_staging/nfl_td/raw'
GAMES = H + '/openclaw/_backups/_sports_staging/freedata/role/games.csv'
import json as _j, os as _o
_B = _o.path.dirname(_o.path.abspath(__file__))
A = dict(p.split('>') for p in open(_o.path.join(_B, 'plnames.py')).read().split('A = """')[1].split('"""')[0].split('|'))
try: A.update(_j.load(open(_o.path.join(_B, 'aliases.json'))))
except Exception: pass
gday = {r['game_id']: r['gameday'] for r in csv.DictReader(open(GAMES))}
def f(x):
    try: return float(x)
    except (TypeError, ValueError): return 0.0
OFF = {'pass_yds': lambda r: f(r['passing_yards']), 'pass_tds': lambda r: f(r['passing_tds']), 'completions': lambda r: f(r['completions']),
       'pass_att': lambda r: f(r['attempts']), 'ints': lambda r: f(r['passing_interceptions']), 'rush_yds': lambda r: f(r['rushing_yards']),
       'rush_att': lambda r: f(r['carries']), 'rec_yds': lambda r: f(r['receiving_yards']), 'receptions': lambda r: f(r['receptions']),
       'targets': lambda r: f(r['targets']), 'rush_rec_yds': lambda r: f(r['rushing_yards']) + f(r['receiving_yards']),
       'pass_rush_yds': lambda r: f(r['passing_yards']) + f(r['rushing_yards']), 'anytime_td': lambda r: f(r['rushing_tds']) + f(r['receiving_tds']),
       'rec_tds': lambda r: f(r['receiving_tds']), 'rush_tds': lambda r: f(r['rushing_tds']), 'sacks': lambda r: f(r['def_sacks']),
       'fg_made': lambda r: f(r.get('fg_made')), 'kicking_pts': lambda r: 3 * f(r.get('fg_made')) + f(r.get('pat_made')),
       'tackles_ast': lambda r: f(r['def_tackles_solo']) + f(r['def_tackle_assists'])}
box = C.defaultdict(list)   # name -> [(date, team, row)]
for fn in sorted(glob.glob(RAW + '/stats_player_week_*.csv')):
    for r in csv.DictReader(open(fn)):
        if r['season_type'] in ('REG', 'POST') and r['game_id'] in gday:
            n = CM.norm(r['player_display_name']); n = A.get(n, n)
            box[n].append((dt.date.fromisoformat(gday[r['game_id']]), r['team'], r))
last_box = max(d for L in box.values() for d, _, _ in L)
def find(pn, d, team):
    d = dt.date.fromisoformat(d[:10]); m = [x for x in box.get(pn, []) if abs((x[0] - d).days) <= 1]
    if len(m) > 1 and team: m = [x for x in m if x[1] == team] or m
    return m[0] if len(m) == 1 else None
db = sqlite3.connect(NFL + '/database/history.db'); db.row_factory = sqlite3.Row; db.execute('pragma busy_timeout=60000')
MODE = sys.argv[1:]
tot = C.Counter(); ok = C.Counter(); flip = C.Counter(); nobox = C.Counter(); ex = C.defaultdict(list); fixes = []; kind = C.Counter(); bad = []; ex2 = []
for r in db.execute('select rowid, * from prop_lines where result is not null'):
    s = r['stat']
    if s not in OFF: continue
    if r['game_date'][:10] > str(last_box): continue
    b = find(r['player_norm'], r['game_date'], r['team'])
    if not b: nobox[s] += 1; continue
    v = OFF[s](b[2]); tot[s] += 1
    if abs(v - r['result']) < 0.01: ok[s] += 1; continue
    L = r['pp_line']; fl = L is not None and (r['result'] > L) != (v > L)
    if r['result'] == 0 and v > 0 and s not in ('tackles_ast', 'sacks'):
        kind['fake zero stored, real game had numbers -> FIX'] += 1; flip[s] += fl; fixes.append((v, r['rowid']))
        if len(ex[s]) < 3: ex[s].append('%s %s line %s stored 0 official %g' % (r['player'], r['game_date'][:10], L, v))
    elif v == 0 and r['result'] > 0: kind['official 0 but stored number (line belongs to a different player with a similar name) -> move out of history'] += 1; bad.append(r['rowid'])
    elif abs(v - r['result']) <= 2 or s in ('tackles_ast', 'sacks'): kind['small official-vs-play-by-play difference or tackle/sack counting -> keep PrizePicks grade'] += 1
    else: kind['other big difference -> keep, flagged'] += 1; ex2.append('%s %s %s stored %g official %g' % (r['player'], r['game_date'][:10], s, r['result'], v))
print('graded NFL props vs the official box score (through %s):' % last_box)
for s in sorted(tot, key=lambda s: -tot[s]):
    print('  %-14s %5d of %5d match (%.1f%%)  fixes that flip won/lost: %d   not in box: %d   %s' % (s, ok[s], tot[s], 100 * ok[s] / tot[s], flip[s], nobox[s], ' | '.join(ex[s])))
print('mismatch types:'); [print('   %5d  %s' % (n, k)) for k, n in kind.most_common()]
print('fixes flip won/lost on %d lines' % sum(flip.values())); print('other big:', ex2[:8])
if 'apply' in MODE and 'grades' in MODE:
    for v, rid in fixes: db.execute('update prop_lines set result=? where rowid=?', (v, rid))
    db.commit(); print('results corrected:', len(fixes))
# (b) Rush+Rec TDs history
have = {(r[0], r[1][:10]) for r in db.execute("select player_norm, game_date from prop_lines where stat='anytime_td'")}
days = C.defaultdict(set)
for r in db.execute('select player_norm, game_date, team, opponent, home, event_id from prop_lines where pp_before_start=1'):
    days[(r['player_norm'], r['game_date'][:10])].add((r['team'], r['opponent'], r['home'], r['event_id'], r['game_date']))
new = []; hits = 0
for (pn, d), S in days.items():
    if (pn, d) in have or d > str(last_box): continue
    b = find(pn, d, next(iter(S))[0])
    if not b or b[2]['position'] not in ('RB', 'WR', 'TE', 'QB', 'FB'): continue
    t, o, h, e, gd = sorted(S, key=lambda x: (x[0] is None, str(x)))[0]
    v = OFF['anytime_td'](b[2]); hits += v > 0.5
    new.append((e, gd, b[2]['player_display_name'], pn, t or b[1], o or b[2]['opponent_team'], h, 'anytime_td', 0.5, 1, None, None, v, 'box_td'))
print('Rush+Rec TDs history lines that can be added: %d (scored a TD in %d = %.1f%%)' % (len(new), hits, 100 * hits / max(1, len(new))))
if 'apply' in MODE and 'td' in MODE:
    db.executemany('insert or ignore into prop_lines(event_id, game_date, player, player_norm, team, opponent, home, stat, pp_line, pp_before_start, book_lines_json, open_line, result, source) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)', new)
    db.commit(); print('added', len(new))
if 'apply' in MODE and 'flagged' in MODE:
    db.execute('create table if not exists prop_lines_removed as select * from prop_lines where 0')
    for rid in bad:
        db.execute('insert into prop_lines_removed select * from prop_lines where rowid=?', (rid,)); db.execute('delete from prop_lines where rowid=?', (rid,))
    db.commit(); print('wrong-player lines moved to prop_lines_removed:', len(bad))
