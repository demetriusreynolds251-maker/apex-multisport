"""Step 5: after the name join, a few old rows (blank or wrong team) sit next to the box-score row for the same player and day.
Fold the old row's PrizePicks-graded numbers into the box-score row (stored number wins) and drop the old row.
Two box-score rows for one name on one day = two real players with the same name: left alone."""
import sqlite3, json, os, sys, collections as C
c = sqlite3.connect(os.path.expanduser('~/ApexSports/football/nfl/database/history.db')); c.row_factory = sqlite3.Row; c.execute('pragma busy_timeout=60000')
isbox = lambda r: r['source'] == 'nflverse' or '"_box"' in (r['stats_json'] or '')
g = C.defaultdict(list)
for r in c.execute('select rowid, * from player_games'): g[(r['player_norm'], r['game_date'][:10])].append(dict(r))
fold = same = 0; ex = []
for k, L in g.items():
    if len(L) < 2: continue
    bx = [r for r in L if isbox(r)]; old = [r for r in L if not isbox(r)]
    if len(bx) != 1 or not old:
        same += 1; continue
    t = bx[0]; st = json.loads(t['stats_json'])
    for o in old:
        for kk, v in json.loads(o['stats_json'] or '{}').items():
            if not kk.startswith('_'): st[kk] = v
        if len(ex) < 6: ex.append('%s %s old team %r -> %s' % (k[0], k[1], o['team'], t['team']))
        if sys.argv[1:] == ['apply']: c.execute('delete from player_games where rowid=?', (o['rowid'],))
        fold += 1
    if sys.argv[1:] == ['apply']: c.execute('update player_games set stats_json=? where rowid=?', (json.dumps(st), t['rowid']))
c.commit()
print('old rows folded into the box-score row: %d   same-name different players left alone: %d' % (fold, same)); print(ex)
