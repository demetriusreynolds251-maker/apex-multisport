"""Step 3 of NFL box scores: (a) same player stored under two spellings (De'Von / Devon Achane, Kenny / Kenneth Gainwell):
join them under the name PrizePicks uses; (b) stored rows the official box score never saw: preseason rows, and all-zero rows
for players with NO snaps that game (did not play) are moved to player_games_removed (kept for audit, not used).
All-zero rows where the player did take snaps (played, got nothing) stay: those are real games."""
import sqlite3, json, sys, csv, glob, os, re, unicodedata, collections as C
H = os.path.expanduser('~')
c = sqlite3.connect(H + '/ApexSports/football/nfl/database/history.db'); c.row_factory = sqlite3.Row
c.execute('pragma busy_timeout=60000')
MODE = sys.argv[1] if len(sys.argv) > 1 else 'dry'
def norm(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    s = re.sub(r"[^a-z ]", '', s.replace('-', ' ')); s = re.sub(r'\b(jr|sr|ii|iii|iv)\b', '', s); return ' '.join(s.split())
pp = {r[0] for r in c.execute('select distinct player_norm from pp_lines')}
rows = [dict(r) for r in c.execute('select rowid, * from player_games')]
isbox = lambda r: r['source'] == 'nflverse' or '"_box"' in (r['stats_json'] or '')
cmp = lambda n: n.replace(' ', '')
NICK = {frozenset(x) for x in (('michael', 'mike'), ('julius', 'juju'), ('deaundre', 'dee'), ('kevin', 'kc'), ('folorunso', 'foley'))}
def first_ok(fa, fb):   # Cam / Cameron, Kenny / Kenneth, Josh / Joshua yes;  Brian / Bijan, Chris / Cam, Jaycee / Jimmy no
    if fa.startswith(fb) or fb.startswith(fa) or frozenset((fa, fb)) in NICK: return True
    n = 0
    while n < min(len(fa), len(fb)) and fa[n] == fb[n]: n += 1
    return n >= 3
def last_ok(la, lb):    # same last name, or one letter off on a long name (Okonokwo / Okonkwo typo)
    if la == lb: return True
    if min(len(la), len(lb)) < 6 or abs(len(la) - len(lb)) > 1: return False
    if len(la) == len(lb): return sum(x != y for x, y in zip(la, lb)) == 1
    s, l = sorted((la, lb), key=len)
    return any(l[:i] + l[i + 1:] == s for i in range(len(l)))
def same(a, b):
    if cmp(a) == cmp(b): return True
    ta, tb = a.split(), b.split()
    return len(ta) > 1 and len(tb) > 1 and last_ok(cmp(' '.join(ta[1:])), cmp(' '.join(tb[1:]))) and first_ok(ta[0], tb[0])
grp = C.defaultdict(list)
for r in rows: grp[(r['team'], r['game_date'][:10])].append(r)
pairs = C.Counter()
for k, L in grp.items():
    lone = [r for r in L if not isbox(r) and r['source'] == 'sgo']; bx = [r for r in L if isbox(r)]
    for a in lone:
        m = [b for b in bx if b['player_norm'] != a['player_norm'] and same(a['player_norm'], b['player_norm'])]
        if len(m) == 1: pairs[(a['player_norm'], m[0]['player_norm'])] += 1
alias = {}
for (a, b), n in pairs.items():
    canon = a if (a in pp and b not in pp) else b
    alias[b if canon == a else a] = canon
print('name pairs', len(alias))
for o, n in sorted(alias.items()): print('   %s -> %s' % (o, n))
renamed = merged = 0
if MODE == 'apply':
    for old, new in alias.items():
        for r in [dict(x) for x in c.execute('select rowid, * from player_games where player_norm=?', (old,)).fetchall()]:
            tgt = c.execute('select rowid, stats_json from player_games where player_norm=? and team is ? and substr(game_date,1,10)=?', (new, r['team'], r['game_date'][:10])).fetchone()
            if tgt:
                st = json.loads(tgt['stats_json'] or '{}')
                for k, v in json.loads(r['stats_json'] or '{}').items():
                    if not k.startswith('_'): st[k] = v      # stored PrizePicks-graded number wins (same rule as the box load)
                c.execute('update player_games set stats_json=? where rowid=?', (json.dumps(st), tgt['rowid']))
                c.execute('delete from player_games where rowid=?', (r['rowid'],)); merged += 1
            else:
                c.execute('update or ignore player_games set player_norm=? where rowid=?', (new, r['rowid'])); renamed += 1
    c.commit()
print('rows merged', merged, 'rows renamed', renamed)
if MODE == 'apply':
    _p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'aliases.json')
    try: _a = json.load(open(_p))
    except Exception: _a = {}
    _a.update(alias); json.dump(_a, open(_p, 'w'), indent=0)
# (b) who took snaps in which game (nflverse snap counts)
ST = H + '/openclaw/_backups/_sports_staging/freedata/role'
gday = {r['game_id']: r['gameday'] for r in csv.DictReader(open(ST + '/games.csv'))}
snap = set(); snap_teams = set()
for fn in glob.glob(ST + '/snap_counts_*.csv'):
    for r in csv.DictReader(open(fn)):
        d = gday.get(r['game_id'])
        if d: snap.add((norm(r['player']), d)); snap_teams.add(d)
inv = C.defaultdict(set)
for o, n in alias.items(): inv[n].add(o)
rows = [dict(r) for r in c.execute('select rowid, * from player_games')]
cand = [r for r in rows if r['source'] == 'sgo' and not isbox(r) and r['game_date'][:10] >= '2024-08-01']
pre, dnp, played0, nums = [], [], [], []
for r in cand:
    d = r['game_date'][:10]; st = json.loads(r['stats_json'] or '{}')
    zero = not any(v for k, v in st.items() if not k.startswith('_'))
    if d[5:7] == '08': pre.append(r); continue
    if not zero: nums.append(r); continue
    names = {r['player_norm']} | inv.get(r['player_norm'], set())
    if d not in snap_teams: played0.append(r); continue            # no snap data for that day: keep (can't prove)
    if any((nm, d) in snap for nm in names): played0.append(r)
    else: dnp.append(r)
print('stored rows the box score never saw since Aug 2024: %d' % len(cand))
print('   preseason (August) %d  -> remove' % len(pre))
print('   all zeros, player took NO snaps that game (did not play) %d  -> remove' % len(dnp))
print('   all zeros but he did play (or no snap data) %d  -> keep' % len(played0))
print('   with real numbers %d  -> keep' % len(nums))
print('   examples kept with numbers:', [(r['player_norm'], r['game_date'][:10], r['team']) for r in nums[:10]])
print('   examples did-not-play:', [(r['player_norm'], r['game_date'][:10], r['team']) for r in dnp[:8]])
if MODE == 'apply' and len(sys.argv) > 2 and sys.argv[2] == 'remove':
    c.execute('create table if not exists player_games_removed as select * from player_games where 0')
    for r in pre + dnp:
        c.execute('insert into player_games_removed select * from player_games where rowid=?', (r['rowid'],)); c.execute('delete from player_games where rowid=?', (r['rowid'],))
    c.commit(); print('moved to player_games_removed:', len(pre) + len(dnp))
