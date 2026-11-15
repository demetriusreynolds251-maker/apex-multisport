#!/usr/bin/env python3
"""Offline test of the Apex Basketball bot. Fake lines, fake history, fake ESPN, fake Discord guild, all in a temp folder. Reads the real history read only for the Step 3 parity check.
No network and no Discord login. Run: /usr/bin/python3 discord/test_offline.py"""
import asyncio, datetime as dt, json, os, random, re, shutil, sqlite3, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); REAL = os.path.dirname(HERE)
TMP = tempfile.mkdtemp(prefix='bball_test_'); os.environ['BBALL_ROOT'] = TMP
for d in ('data/collected', 'data/processed', 'logs', 'secrets'): os.makedirs(os.path.join(TMP, d))
sys.path[:0] = [os.path.join(REAL, 'code'), HERE]
import urllib.request
def _no_net(*a, **k): raise AssertionError('network call in offline test')
urllib.request.urlopen = _no_net
import score_board as SB, espn_results as ER, bball_tracker as T, bball_pipeline as P, cards as K, bot as B
PASS = FAIL = 0
def check(name, ok, info=''):
    global PASS, FAIL
    if ok: PASS += 1
    else: FAIL += 1
    print('%s %s%s' % ('PASS' if ok else 'FAIL', name, '' if ok else '  ' + str(info)))
UTC = dt.timezone.utc; NOW = dt.datetime.now(UTC).replace(microsecond=0)
# ---- real Step 3 parity
def parity():
    rh = os.path.join(REAL, 'data/processed/nba_history.sqlite'); rf = os.path.join(REAL, 'data/processed/nba_fgm.sqlite'); rp = os.path.join(REAL, 'data/processed/step3_predictions.sqlite')
    if not os.path.exists(rf): check('Step 3 parity (needs nba_fgm.sqlite)', False, 'missing'); return
    H = SB.History(rh, rf, os.path.join(TMP, 'none.sqlite')); db = sqlite3.connect('file:%s?mode=ro' % rp, uri=True); hdb = sqlite3.connect('file:%s?mode=ro' % rh, uri=True)
    rows = db.execute('select event_id,player_id,stat,game_date,pp_line,win_prob,side,projected from predictions').fetchall(); random.Random(7).shuffle(rows)
    n = bad = same = 0; worst = 0
    for e, p, s, d, l, wp, side, proj in rows[:1500]:
        m = hdb.execute('select opponent,home,back_to_back from player_games where event_id=? and player_id=?', (e, p)).fetchone()
        r, why = H.project(p, s, d, l, m[0], b2b=m[2] or 0, home=m[1])
        if not r: bad += 1; continue
        q = 100 * max(r['p_more'], 1 - r['p_more']); n += 1; worst = max(worst, abs(q - wp)); same += ('MORE' if r['p_more'] >= .5 else 'LESS') == side
    check('Step 3 parity: %d real picks, same side %d, biggest Win Prob gap %.2f points, %d not reproduced' % (n, same, worst, bad), n >= 1000 and bad == 0 and same >= n - 3 and worst < .5, (n, same, worst, bad))
    r, _ = H.project(rows[0][1], rows[0][2], rows[0][3], rows[0][4], 'Boston Celtics')
    check('b2b and home-unknown path runs on real history', r is not None)
parity()
# ---- fake history: 16 games each for a few players, Boston and Lakers etc.
def make_history():
    db = sqlite3.connect(SB.HIST_DB)
    db.executescript("""create table games(event_id text primary key, season text, game_date text, start_utc text, home text, away text, home_pts real, away_pts real, close_spread_home real, open_spread_home real, close_total real, open_total real, final integer);
      create table player_games(event_id text, player_id text, player text, team text, opponent text, home integer, game_date text, season text, minutes real, points real, rebounds real, assists real, threes real, steals real, blocks real, turnovers real, rest_days integer, back_to_back integer, primary key(event_id, player_id));""")
    day = NOW.astimezone(SB.CT).date(); teams = [('Star A', 'LAL', 'BOS', 30), ('Star B', 'MIA', 'NYK', 20), ('Star C', 'DEN', 'PHX', 25), ('Star D', 'GSW', 'SAC', 18), ('Star E', 'DAL', 'HOU', 22), ('Star F', 'CHI', 'DET', 15), ('Star G', 'ORL', 'ATL', 16), ('Second A', 'LAL', 'BOS', 12)]
    for pi, (name, t, o, pts) in enumerate(teams):
        for i in range(16):
            d = (day - dt.timedelta(days=3 + i * 2)).isoformat(); e = 'ev%d_%d' % (pi, i)
            db.execute('insert into games(event_id,season,game_date,final) values(?,?,?,1)', (e, SB.season(d), d))
            db.execute('insert into player_games(event_id,player_id,player,team,opponent,home,game_date,season,minutes,points,rebounds,assists) values(?,?,?,?,?,?,?,?,?,?,?,?)', (e, 'p%d' % pi, name, SB.TEAMS[t][1], SB.TEAMS[o][0], 1, d, SB.season(d), 30, pts + (i % 3), 8, 4))
    db.commit(); db.close()
make_history()
START = (NOW + dt.timedelta(hours=3)).isoformat()
def line(pid, player, team, opp, stat, val, kind='standard', league='NBA', start=START, **kw):
    r = dict(seen=NOW.isoformat(), projection_id=pid, league=league, player=player, team=team, position='G', opponent=opp, stat=stat, line=val, odds_type=kind, start=start, status='pre_game', is_promo=False, flash_sale_line=None, adjusted_odds=None); r.update(kw); return r
def write_lines(rows):
    with open(os.path.join(SB.COLLECTED, 'x.jsonl'), 'w') as f:
        for r in rows: f.write(json.dumps(r) + '\n')
        f.write('not json\n')
BASE = [line('1', 'Star A', 'LAL', 'BOS', 'Points', 8.5), line('1b', 'Second A', 'LAL', 'BOS', 'Points', 1.5), line('2', 'Star B', 'MIA', 'NYK', 'Points', 2.5), line('3', 'Star C', 'DEN', 'PHX', 'Points', 3.5), line('4', 'Star D', 'GSW', 'SAC', 'Points', 2.5),
        line('5', 'Star E', 'DAL', 'HOU', 'Points', 3.5), line('6', 'Star F', 'CHI', 'DET', 'Points', 1.5), line('7', 'Star A', 'LAL', 'BOS', 'Points', 2.5, 'goblin'), line('8', 'Star B', 'MIA', 'NYK', 'Points', 200.5, 'demon'), line('9', 'Star A', 'LAL', 'BOS', 'Points', 200.5),
        line('10', 'Nobody Here', 'LAL', 'BOS', 'Points', 10.5), line('11', 'Star A', 'LAL', 'BOS', 'Assists', 5.5), line('12', 'Foreign Guy', 'ABC', 'XYZ', 'Points', 3.5, league='WNBA'), line('13', 'Star C', 'DEN', 'PHX', 'Points', 1.5, is_promo=True), line('14', 'Star A', 'LAL', 'BOS', 'Points', 1.5, start=(NOW - dt.timedelta(hours=1)).isoformat())]
write_lines(BASE)
before = SB.collector_signature()
# ---- scoring
s = P.rescore('test', now=NOW)
check('rescore works from files with no network (urlopen blocked)', not s['no_lines'] and s['n_lines'] == 14, s)
check('bad row in a saved file is counted, not fatal', s['bad_rows'] == 1)
cur = P.current(NOW); R = {r['projection_id']: r for r in cur['rows']}
check('started line left out', '14' not in R)
check('LESS is possible on a Standard', R['9']['side'] == 'LESS' and R['9']['win_prob'] > 50, R['9'])
check('Demon stays MORE even when a low number', R['8']['side'] == 'MORE' and R['8']['win_prob'] < 50, R['8'])
check('Goblin is MORE', R['7']['side'] == 'MORE')
check('other league: no number and the exact tag', R['12']['win_prob'] is None and R['12']['reason'] == '🧪 no tested history yet for WNBA')
check('untested stat has no number', R['11']['win_prob'] is None and 'not tested' in R['11']['reason'])
check('unknown player has no number', R['10']['win_prob'] is None)
fg = [r for r in SB.score_lines([line('f', 'Star A', 'LAL', 'BOS', 'FG Made', 5.5)], P.history(), now=NOW)][0]
check('FG Made refused when its file is missing, not guessed', fg['win_prob'] is None and 'field goals' in fg['reason'])
hist2 = SB.History(); hist2.names['two guys'] = {'p0', 'p1'}
check('two people, one name, no matching team: refused', hist2.resolve('Two Guys', 'BOS') == (None, 'two players share this name'))
check('two people, one name, team separates them', hist2.resolve('Two Guys', 'LAL') == ('p0', None))
check('name match ignores accents and Jr', SB.norm('Nikola Jokić Jr.') == 'nikola jokic')
check('@ means away, vs means home', SB.parse_opponent('@ LAL') == ('LAL', 0) and SB.parse_opponent('vs. GS') == ('GSW', 1) and SB.parse_opponent('BOS') == ('BOS', None))
future = SB.History(); pre = future.project('p0', 'points', (NOW.astimezone(SB.CT).date() - dt.timedelta(days=20)).isoformat(), 20.5, 'Boston Celtics')
check('only earlier games used: not enough before that date', pre[0] is None and pre[1] == 'under 10 earlier games', pre)
# ---- boards
bo = cur['boards']
hi = [r for r in cur['rows'] if (r['win_prob'] or 0) >= 70]
check('fake board has picks at 70+', len(hi) >= 6, [(r['projection_id'], r['win_prob']) for r in cur['rows']])
for n, b in bo.items():
    check('%s: floor 70, one per game, ranked by Win Prob only' % n, all(r['win_prob'] >= 70 for r in b['main'] + b['backups']) and len({r['game_key'] for r in b['main']}) == len(b['main']) and [r['win_prob'] for r in b['main']] == sorted([r['win_prob'] for r in b['main']], reverse=True))
check('promo line off boards', not any(r['projection_id'] == '13' for b in bo.values() for r in b['main'] + b['backups']))
check('Best Goblin only Goblin, Best Standard only Standard', all(r['kind'] == 'goblin' for r in bo['bestgoblin']['main']) and all(r['kind'] == 'standard' for r in bo['beststandard']['main']))
fake_w = dict(R['1'], projection_id='w1', league='WNBA', win_prob=101.0, game_key='WNBA|x', kind='standard'); b2 = P.build_boards(cur['rows'] + [fake_w])
check('another league with a high number stays off Top 3 and Elite', not any(r['league'] == 'WNBA' for n in ('top3', 'elite5', 'elite6') for r in b2[n]['main'] + b2[n]['backups']))
check('and can sit on Top 10 with its tag', b2['top10']['main'][0]['league'] == 'WNBA' and '[WNBA]' in K.pick_line(b2['top10']['main'][0]))
same = [r for r in bo['top3']['backups'] if r['game_key'] in {x['game_key'] for x in bo['top3']['main']}]
check('second pick in a game goes to backups', len(same) >= 1)
empty = P.build_boards([dict(R['1'], win_prob=69.9)])
check('69.9 is under the floor', not empty['top3']['main'] and not empty['top10']['backups'])
# ---- cards and footers
TXT = {'fetch': K.fetch_result_text(s), 'board': K.board_diag_text(), 'allprops': K.allprops_text(), 'slips': K.slips_text(), 'pnl': K.pnl_text(), 'counters': K.counters_text(), 'besttime': K.besttime_text(), 'soon': K.soon_text(), 'soon3': K.soon_card('top3'), 'soon6': K.soon_card('elite6'),
       'banned': K.banned_text(), 'h2h': K.h2h_text('Star A'), 'h2h2': K.h2h_text('Star A vs Star B'), 'learning': K.learning_text(), 'status': K.status_line()}
for n in P.BOARDS: TXT[n] = K.board_text(n); TXT[n + ' backups'] = K.backups_text(n)
check('every card ends in the TEST footer', all(K.FOOT in t for t in TXT.values()), [k for k, t in TXT.items() if K.FOOT not in t])
check('every board says the honest 9-9', all(K.HONEST in TXT[n] for n in P.BOARDS))
check('fetch says no PrizePicks call and when lines were saved', 'No call was made to PrizePicks' in TXT['fetch'] and 'last saved' in TXT['fetch'])
check('all props shows the 🧪 tag', 'no tested history yet for WNBA' in TXT['allprops'])
check('all messages fit Discord', all(len(p) <= 2000 for t in TXT.values() for p in K.chunks(t)) and all(len(p) <= 2000 for p in K.chunks('x' * 5000 + '\nb')))
check('h2h finds past meetings', 'last 10 meetings' in TXT['h2h'] or 'meetings' in TXT['h2h'], TXT['h2h'])
check('no real-looking record before anything graded', 'Nothing graded yet' in TXT['learning'] and 'No answer yet' in TXT['besttime'])
# ---- ban
K.ban_text('Star A', 'test'); c2 = P.current(NOW)
check('ban takes the player off every board', not any(r['player'] == 'Star A' for b in c2['boards'].values() for r in b['main'] + b['backups']))
K.unban_text('star a'); check('unban brings them back', any(r['player'] == 'Star A' for r in P.current(NOW)['boards']['top3']['main']))
# ---- cancel
P.cancel_event.clear(); P._check(); P.cancel_event.set()
try: P._check(); check('cancel raises', False)
except P.Cancelled: check('cancel stops at the next step', True)
P.cancel_event.clear()
# ---- slips and locking
db = T.connect(); sl = {x['board']: x for x in db.execute('select * from slips')}
check('Top 3 slip saved as Power with $20 paper; Elite 5 as Flex no dollars', sl['top3']['slip_kind'] == 'power' and sl['top3']['stake'] == 20 and (('elite5' not in sl) or sl['elite5']['stake'] is None))
legs0 = sl['top3']['legs_json']
built = P.build_boards(cur['rows']); built['top3']['main'] = built['top3']['main'][::-1]
T.update_slips(db, built, now=NOW); check('slip follows the board before the first leg', db.execute("select legs_json from slips where board='top3'").fetchone()[0] != legs0); legs1 = db.execute("select legs_json from slips where board='top3'").fetchone()[0]
built['top3']['main'] = built['top3']['main'][::-1]; T.update_slips(db, built, now=NOW + dt.timedelta(hours=4)); check('slip is locked once the first leg started', db.execute("select legs_json from slips where board='top3'").fetchone()[0] == legs1)
# ---- ESPN parse and grading with fake responses
def sb_for(events): return dict(events=events)
top = [db.execute('select * from picks where pick_key=?', (k,)).fetchone() for k in json.loads(legs1)]
def event(i, p):
    ht, at = p['team'], p['opponent']
    return dict(id=str(i), date=p['start_utc'], competitions=[dict(status=dict(type=dict(completed=True)), competitors=[dict(homeAway='home', score='100', team=dict(abbreviation={'GSW': 'GS', 'NYK': 'NY'}.get(ht, ht))), dict(homeAway='away', score='90', team=dict(abbreviation=at))])])
KEYS = ['minutes', 'fieldGoalsMade-fieldGoalsAttempted', 'rebounds', 'assists', 'points']
def summary(p, won):
    pts = (p['line'] + 3) if won == (p['side'] == 'MORE') else (p['line'] - 1)
    return dict(boxscore=dict(players=[dict(team=dict(abbreviation={'GSW': 'GS', 'NYK': 'NY'}.get(p['team'], p['team'])), statistics=[dict(keys=KEYS, athletes=[dict(athlete=dict(id='9%s' % p['projection_id'], displayName=p['player']), stats=['31', '7-14', '5', '2', str(pts)]), dict(athlete=dict(id='8', displayName='Bench Guy'), stats=[])])])]))
calls = []
def fake_get(url):
    calls.append(url)
    assert 'prizepicks' not in url.lower() and 'espn.com' in url
    if 'scoreboard' in url: return sb_for([event(i, p) for i, p in enumerate(top, 100)])
    return summary(top[int(url.split('=')[1]) - 100], True)
later = NOW + dt.timedelta(hours=8); db.commit()
g = P.grade(now=later, get=fake_get, pause=0)
check('grader: slip legs all won from fake ESPN', all(db.execute('select status from picks where pick_key=?', (p['pick_key'],)).fetchone()[0] == 'win' for p in top), g)
sx = db.execute("select * from slips where board='top3'").fetchone()
kinds = ''.join(sorted('G' if p['kind'] == 'goblin' else 'S' for p in top)) ; want = T.POWER3.get(kinds)
check('Power slip won at the right pay', sx['status'] == 'won' and sx['payout_mult'] == want and abs(sx['pnl'] - 20 * (want - 1)) < .01, dict(sx))
check('no box score call twice', sum('summary' in u for u in calls) == len(top)); n0 = len(calls); P.grade(now=later, get=fake_get, pause=0); check('second grade uses saved box scores', not [u for u in calls[n0:] if 'summary' in u])
espn = ER.connect()
check('did not play is void', ER.grade_pick(espn, SB.norm, 'Bench Guy', top[0]['team'], top[0]['game_date'], 'points', 5.5, 'MORE')[0] == 'void')
check('player missing from a final box score is void', ER.grade_pick(espn, SB.norm, 'Gone Guy', top[0]['team'], top[0]['game_date'], 'points', 5.5, 'MORE')[0] == 'void')
check('game not final stays open', ER.grade_pick(espn, SB.norm, 'Star Z', 'TOR', '2020-01-01', 'points', 5.5, 'MORE')[0] == 'open')
espn.execute("insert into games(event_id,game_date,home_team,away_team,final,box_saved) values('c1','2020-01-01','TOR','BOS',1,1)"); espn.execute("insert into player_games values('c1','1','Toe','TOR','BOS',1,30,10,2,1,4)"); espn.commit()
g1 = lambda st, l, side: ER.grade_pick(espn, SB.norm, 'Toe', 'TOR', '2020-01-01', st, l, side)
check('win, loss, push, combo, FG', g1('points', 9.5, 'MORE')[0] == 'win' and g1('points', 9.5, 'LESS')[0] == 'loss' and g1('points', 10, 'MORE')[0] == 'push' and g1('points+rebounds+assists', 13, 'MORE')[1] == 13 and g1('fieldGoalsMade', 3.5, 'MORE')[1] == 4)
check('ESPN games feed the history after the download', SB.History().espn_rows > 0)
n_before = SB.History().espn_rows; old_day = (NOW.astimezone(SB.CT).date() - dt.timedelta(days=3)).isoformat()
espn.execute("insert into games(event_id,game_date,home_team,away_team,final,box_saved) values('c2',?,'LAL','BOS',1,1)", (old_day,)); espn.execute("insert into player_games values('c2','2','Star A','LAL','BOS',1,30,50,2,1,4)"); espn.commit()
check('ESPN game the download already has is not counted twice', SB.History().espn_rows == n_before)
def tslip(kind, legs, sk='power'):
    keys = []
    for i, st in enumerate(legs):
        k = 'z%s%d%d' % (kind, i, random.randint(0, 10**8)); db.execute("insert into picks(pick_key,league,player,kind,status,start_utc,game_date,win_prob,side,line,stat,opponent) values(?,?,?,?,?,?,?,?,?,?,?,?)", (k, 'NBA', 'x', kind, st, '2020-01-01T00:00:00+00:00', '2020-01-01', 72.0, 'MORE', 1.5, 'points', 'BOS')); keys.append(k)
    db.execute('insert into slips(day,board,slip_kind,legs_json,first_start,stake) values(?,?,?,?,?,?)', (str(random.random()), 'top3' if sk == 'power' else 'elite5', sk, json.dumps(keys), '2020', 20 if sk == 'power' else None)); db.commit()
    return db.execute('select id from slips order by id desc limit 1').fetchone()[0]
a = tslip('standard', ['win', 'loss', 'open']); b = tslip('standard', ['win', 'win', 'void']); c = tslip('goblin', ['win', 'win', 'win']); d = tslip('standard', ['win', 'win', 'loss', 'win', 'win'], 'flex'); e = tslip('demon', ['win', 'win', 'win'])
T.settle_slips(db); gs = lambda i: db.execute('select status,pnl,payout_mult from slips where id=?', (i,)).fetchone()
check('Power: one losing leg loses at once', gs(a)['status'] == 'lost' and gs(a)['pnl'] == -20)
check('void leg asks for the app amount, no made up dollars', gs(b)['status'] == 'check_app' and gs(b)['pnl'] is None)
check('all Goblin Power pays 2.2x', gs(c)['payout_mult'] == 2.2 and gs(e)['payout_mult'] == 2.2)
check('Flex counted with no dollars', gs(d)['status'] == 'partial' and gs(d)['pnl'] is None)
check('counters and P&L add up', T.counters(db)['top3']['lost'] >= 1 and T.pnl(db)['lost'] >= 1)
check('slip result card renders', K.FOOT in K.slip_card(db, db.execute('select * from slips where id=?', (a,)).fetchone()))
db.close()
# ---- parser on an ESPN shape with mm:ss minutes
pg = ER.parse_summary(summary(dict(team='GSW', side='MORE', line=5.5, projection_id='1', player='A'), True), dict(event_id='1', home_team='GSW', away_team='BOS'))
check('ESPN GS becomes GSW; FG split; no stats means 0 minutes', pg[0][3] == 'GSW' and pg[0][10] == 7 and pg[1][6] == 0 and ER._minutes('31:30') == 31.5)
# ---- no PrizePicks anywhere, nothing from Apex, token handling
srcs = {f: open(os.path.join(REAL, f)).read() for f in ('code/score_board.py', 'code/espn_results.py', 'code/bball_tracker.py', 'code/bball_pipeline.py', 'discord/bot.py', 'discord/cards.py')}
check('no PrizePicks URL in bot code', not any('api.prizepicks' in s for s in srcs.values()))
check('no Apex imports or paths', not any(re.search(r'(from|import)\s+openclaw|/openclaw/|^\s*(from|import)\s+apex|sportsgameodds\.com|oddspapi', s, re.M | re.I) for s in srcs.values()))
sb = os.path.join(TMP, 'sb'); os.makedirs(os.path.join(sb, 'discord')); shutil.copy(os.path.join(HERE, 'start_bot.sh'), os.path.join(sb, 'discord'))
import signal, time as _t
pr = subprocess.Popen(['bash', os.path.join(sb, 'discord/start_bot.sh')]); _t.sleep(2); pidf = os.path.join(sb, 'logs/bball_bot.pid'); waited = 'waiting for secrets' in open(os.path.join(sb, 'logs/bball_bot.log')).read(); pid_ok = open(pidf).read().strip() == str(pr.pid)
pr.send_signal(signal.SIGTERM); pr.wait(timeout=10)
check('start script with no token waits, writes its pid, and stops cleanly', waited and pid_ok and not os.path.exists(pidf))
check('collector files untouched by scoring', SB.collector_signature() == before)
check('token missing: load_token gives None', B.load_token(os.path.join(TMP, 'nope')) is None)
r = subprocess.run(['/usr/bin/python3', os.path.join(HERE, 'bot.py')], env=dict(os.environ, BBALL_ROOT=TMP), capture_output=True, text=True, timeout=120)
check('no token: clean exit code 3 and a message, no traceback', r.returncode == 3 and 'No Discord token' in r.stdout and 'Traceback' not in r.stderr, (r.returncode, r.stdout, r.stderr[-300:]))
tok = 'FAKE-TOKEN-VALUE-123'
tp = os.path.join(TMP, 'tok.txt'); open(tp, 'w').write(tok + '\n'); check('token read and stripped', B.load_token(tp) == tok)
check('token value in no source', not any('FAKE-TOKEN' in s for s in srcs.values()))
check('start script is valid bash', subprocess.run(['bash', '-n', os.path.join(HERE, 'start_bot.sh')]).returncode == 0)
# ---- channels, fake guild
class Ch:
    def __init__(s, name, id): s.name, s.id = name, id
class G:
    def __init__(s, fail=False): s.text_channels = [Ch('general', 1), Ch('picks', 2)]; s.categories = []; s.made = 0; s.fail = fail
    async def create_category(s, n): c = Ch(n, 900); s.categories.append(c); return c
    async def create_text_channel(s, n, category=None, topic=None, reason=None):
        if s.fail: raise PermissionError('no')
        s.made += 1; c = Ch(n, 1000 + s.made); s.text_channels.append(c); return c
g = G(); cp = os.path.join(TMP, 'data/discord_channels.json')
m, f = asyncio.run(B.ensure_channels(g, cp))
check('all 8 bball- channels made and saved; tennis channels left alone', g.made == 8 and not f and json.load(open(cp)) == m and {c.name for c in g.text_channels} >= {'general', 'picks'} and all(n.startswith('bball-') for n in m))
m2, _ = asyncio.run(B.ensure_channels(g, cp)); check('second run creates nothing', g.made == 8 and m2 == m)
bad = G(fail=True); m3, f3 = asyncio.run(B.ensure_channels(bad, os.path.join(TMP, 'c2.json'))); check('no permission: reported, not a crash', len(f3) == 8 and not m3)
# ---- commands register without logging in, job loop against a fake poster
os.environ.pop('X', None)
async def build():
    bb = B.Bot(); names = {c.name for c in bb.tree.get_commands(guild=bb.guild_obj)}; want = {'bball-fetch', 'bball-board', 'bball-top3', 'bball-elite5', 'bball-elite6', 'bball-top10', 'bball-allprops', 'bball-bestgoblin', 'bball-beststandard', 'bball-bestdemon', 'bball-top3backups', 'bball-elite5backups', 'bball-elite6backups', 'bball-top10backups', 'bball-goblinbackups', 'bball-demonbackups', 'bball-standardbackups', 'bball-slips', 'bball-pnl', 'bball-counters', 'bball-besttime', 'bball-soon', 'bball-soon3', 'bball-soon6', 'bball-h2h', 'bball-ban', 'bball-unban', 'bball-banned', 'bball-cancel'}
    check('all commands register, only on this guild (%d)' % len(names), names == want and not bb.tree.get_commands(), names ^ want)
    posts = []
    async def fake(ch, t): posts.append((ch, t)); return True
    bb.post = fake; await bb.run_rescore('test')
    check('new scoring posts boards to bball-picks and a line to bball-system', any(c == 'bball-picks' for c, _ in posts) and any(c == 'bball-system' for c, _ in posts))
    n = len([1 for c, _ in posts if c == 'bball-picks']); await bb.run_rescore('test'); check('same board: no repeat post, system line still goes', len([1 for c, _ in posts if c == 'bball-picks']) == n and sum(c == 'bball-system' for c, _ in posts) == 2)
    posts.clear(); write_lines(BASE + [line('77', 'Star G', 'ORL', 'ATL', 'Points', 2.5)]); await bb.tick(); first = bb.pending_sig
    check('new file waits until it stops growing', first is not None and not any('Scored' in t for _, t in posts))
    bb.pending_since -= dt.timedelta(minutes=6); await bb.tick(); check('then scores on its own', any('Scored' in t for _, t in posts) or bb.state.get('last_sig') == SB.collector_signature(), posts[:2])
    bb.state.pop('status', None); posts.clear(); bb.state['graded'] = dt.datetime.now(SB.CT).date().isoformat(); await bb.tick()
    if dt.datetime.now(SB.CT).hour >= 9: check('9 AM line posts once, even with nothing to say', sum(c == 'bball-general' for c, _ in posts) == 1); posts.clear(); await bb.tick(); check('and not twice', not any(c == 'bball-general' for c, _ in posts))
    bb.state['silence_alerted'] = False; posts.clear(); await bb.tick(); check('collector never pulled: alert fires, once', sum('collector' in t.lower() for c, t in posts if c == 'bball-alerts') == 1, posts); posts.clear(); await bb.tick(); check('and does not repeat', not any(c == 'bball-alerts' for c, _ in posts))
    await bb.client.close()
asyncio.run(build())
shutil.rmtree(TMP, ignore_errors=True)
print('\n%d passed, %d failed' % (PASS, FAIL)); sys.exit(1 if FAIL else 0)
