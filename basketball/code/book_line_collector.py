#!/usr/bin/env python3
"""Apex Basketball - live NBA book lines from The Odds API (his go "Go odds api", 2026-11-05).
Key: secrets/odds_api_key.txt only (read at call time, never logged). Waits for the key when missing.
Output: data/collected/books/YYYY-MM-DD.jsonl, one row per book line per pull (seen, event_id, start, home, away, book, market, player, line, over, under).
Credits: 1 per market per region per event. 9 markets x 1 region = 9 a game, ~110 a full slate. Pull times below; stops when credits left < MIN_LEFT.
Usage: --loop | --once [--dry]
"""
import datetime as dt, json, os, sys, time, urllib.request, urllib.error, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY_FILE = os.path.join(ROOT, 'secrets', 'odds_api_key.txt'); OUT = os.path.join(ROOT, 'data', 'collected', 'books')
LOG = os.path.join(ROOT, 'logs', 'book_lines.log'); STATE = os.path.join(ROOT, 'data', 'book_lines_state.json')
TOKEN_FILE = os.path.join(ROOT, 'secrets', 'discord_bot_token.txt'); CHANNEL_FILE = os.path.join(ROOT, 'data', 'discord_channels.json')
try:
    from zoneinfo import ZoneInfo; CT = ZoneInfo('America/Chicago')
except Exception: CT = dt.timezone(dt.timedelta(hours=-6))
SPORT = 'basketball_nba'; REGIONS = 'us'
MARKETS = ['player_points', 'player_rebounds', 'player_assists', 'player_points_rebounds_assists', 'player_points_rebounds', 'player_points_assists', 'player_rebounds_assists', 'player_field_goals', 'player_fantasy_points']
PULL_TIMES = ('09:15', '12:45', '16:05', '18:35')   # CT: morning (APEX-EARLYDEMON-2026-11-13: sportsbook lines for the Early Demon board), after the PrizePicks noon drop, before the 4 PM board, late-game refresh
MIN_LEFT = 30
# APEX-SGOBOOKS-2026-11-11 (owner, "Go sgo book"): book lines come from SportsGameOdds, not The Odds API (out of credits since 11/8).
# Same output rows, same pull times. Key stays inside openclaw/data/sgo_archive/tools/sgo_raw.py (never read or logged here). SOURCE = 'oddsapi' puts the old feed back.
SOURCE = 'sgo'
SGO_TOOLS = '/path/to/home/openclaw/data/sgo_archive/tools'
SGO_STAT = {'points': 'player_points', 'rebounds': 'player_rebounds', 'assists': 'player_assists', 'points+rebounds+assists': 'player_points_rebounds_assists', 'points+rebounds': 'player_points_rebounds',
            'points+assists': 'player_points_assists', 'rebounds+assists': 'player_rebounds_assists', 'fieldGoalsMade': 'player_field_goals', 'fantasyScore': 'player_fantasy_points'}
# Real sportsbooks only. Left out on purpose: PrizePicks / Underdog / Sleeper / Fliff (pick'em apps, PrizePicks would be comparing to itself), exchanges and prediction markets, SugarHouse (same lines as BetRivers).
SGO_BOOKS = {'fanduel', 'draftkings', 'betmgm', 'caesars', 'bet365', 'espnbet', 'betrivers', 'bovada', 'betonline', 'pinnacle', 'hardrockbet', 'fanatics', 'ballybet', 'betparx', 'circa', 'bookmakereu'}
SGO_ODDS_RANGE = (-200, 160)   # a book whose price is outside this is showing a lopsided side line, not its main number
def _amer(v):
    try: return int(str(v).replace('+', ''))
    except (TypeError, ValueError): return None
def pull_sgo(dry=False):
    if SGO_TOOLS not in sys.path: sys.path.insert(0, SGO_TOOLS)
    import sgo_raw as R, importlib as _il; R = _il.reload(R)   # APEX-KEYRELOAD-2026-11-15: re-read the saved key every pull so a new /setkey works without a restart
    now = dt.datetime.now(CT); seen = now.isoformat(timespec='seconds'); utc = dt.datetime.now(dt.timezone.utc)
    end = (now.replace(hour=0, minute=0, second=0, microsecond=0) + dt.timedelta(days=1, hours=3)).astimezone(dt.timezone.utc)
    status, d, _ = R.get('/v2/events/', {'leagueID': 'NBA', 'oddsAvailable': 'true', 'startsAfter': utc.strftime('%Y-%m-%dT%H:%M:%SZ'), 'startsBefore': end.strftime('%Y-%m-%dT%H:%M:%SZ'), 'limit': 30}, 'nba_books')
    if status != 200: raise RuntimeError('SportsGameOdds answered %s' % status)
    rows = []; books = set(); games = 0; nev = 0
    for e in d.get('data') or []:
        st = e.get('status') or {}
        try: start = dt.datetime.fromisoformat(st['startsAt'].replace('Z', '+00:00'))
        except (KeyError, ValueError, AttributeError): continue
        if start.astimezone(CT).date() != now.date() or start <= utc or st.get('started') or st.get('cancelled'): continue
        nev += 1; tm = e.get('teams') or {}; players = e.get('players') or {}; od = e.get('odds') or {}; got = False
        home = ((tm.get('home') or {}).get('names') or {}).get('long'); away = ((tm.get('away') or {}).get('names') or {}).get('long')
        for o in od.values():
            if o.get('sideID') != 'over' or o.get('betTypeID') != 'ou' or o.get('periodID') != 'game' or o.get('statID') not in SGO_STAT: continue
            pid = o.get('playerID') or o.get('statEntityID'); name = (players.get(pid) or {}).get('name')
            if not name: continue
            under = (od.get(o.get('opposingOddID')) or {}).get('byBookmaker') or {}
            for bk, v in (o.get('byBookmaker') or {}).items():
                u = under.get(bk) or {}
                if bk not in SGO_BOOKS or not v.get('available') or not u.get('available') or v.get('overUnder') != u.get('overUnder'): continue
                try: line = float(v['overUnder'])
                except (KeyError, TypeError, ValueError): continue
                ov, un = _amer(v.get('odds')), _amer(u.get('odds'))
                if ov is None or un is None or not (SGO_ODDS_RANGE[0] <= ov <= SGO_ODDS_RANGE[1]) or not (SGO_ODDS_RANGE[0] <= un <= SGO_ODDS_RANGE[1]): continue
                books.add(bk); got = True
                rows.append(dict(seen=seen, event_id=e.get('eventID'), start=st['startsAt'], home=home, away=away, book=bk, book_updated=v.get('lastUpdatedAt'),
                                 market=SGO_STAT[o['statID']], player=name, line=line, over=ov, under=un, source='sgo'))
        games += got
    if not dry and rows:
        os.makedirs(OUT, exist_ok=True)
        with open(os.path.join(OUT, now.strftime('%Y-%m-%d') + '.jsonl'), 'a') as f:
            for r in rows: f.write(json.dumps(r) + '\n')
    players_n = len({(r['player'], r['market']) for r in rows})
    if rows: msg = '📚 Book lines saved from SportsGameOdds: %d games, %d player lines (%d player-stats), %d books: %s.' % (games, len(rows), players_n, len(books), ', '.join(sorted(books)))
    else: msg = '📚 Book lines: SportsGameOdds had no player lines for the %d game%s still to start today.' % (nev, '' if nev == 1 else 's')
    log(msg)
    if not dry: post('bball-system', msg)
    s = load_state(); s['last_pull'] = seen; s['source'] = 'sgo'; s.setdefault('pulls', []).append(dict(at=seen, games=games, rows=len(rows), left='sgo')); s['pulls'] = s['pulls'][-200:]
    if not dry: save_state(s)
    return len(rows), 'sgo'
def log(m):
    os.makedirs(os.path.dirname(LOG), exist_ok=True); line = '%s %s' % (dt.datetime.now(CT).strftime('%m/%d %H:%M:%S'), m)
    print(line, flush=True); open(LOG, 'a').write(line + '\n')
def key():
    try: return open(KEY_FILE).read().strip() or None
    except OSError: return None
def load_state():
    try: return json.load(open(STATE))
    except (OSError, ValueError): return {}
def save_state(s): json.dump(s, open(STATE, 'w'), indent=1)
def post(channel, text):
    try: ch = json.load(open(CHANNEL_FILE)).get(channel); tok = open(TOKEN_FILE).read().strip()
    except (OSError, ValueError): log('NOT POSTED: no channel file or token'); return False
    if not ch: log('NOT POSTED: no channel #%s' % channel); return False
    req = urllib.request.Request('https://discord.com/api/v10/channels/%s/messages' % ch, data=json.dumps({'content': text[:1900]}).encode(),
                                 headers={'Authorization': 'Bot ' + tok, 'Content-Type': 'application/json', 'User-Agent': 'ApexBasketballBooks/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r: r.read(); return True
    except Exception as e: log('NOT POSTED #%s: %s' % (channel, type(e).__name__)); return False
def get(path, params):
    k = key()
    if not k: raise RuntimeError('no key')
    q = dict(params); q['apiKey'] = k
    req = urllib.request.Request('https://api.the-odds-api.com/v4' + path + '?' + urllib.parse.urlencode(q), headers={'User-Agent': 'ApexBasketball/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            h = r.headers; return json.loads(r.read().decode()), h.get('x-requests-remaining'), h.get('x-requests-used')
    except urllib.error.HTTPError as e:
        body = ''
        try: body = e.read().decode()[:200].replace(k, '<key>')
        except Exception: pass
        raise RuntimeError('HTTP %s %s' % (e.code, body))
def pull(dry=False):
    if SOURCE == 'sgo': return pull_sgo(dry)
    now = dt.datetime.now(CT); seen = now.isoformat(timespec='seconds')
    events, left, used = get('/sports/%s/events' % SPORT, {})
    todays = [e for e in events if dt.datetime.fromisoformat(e['commence_time'].replace('Z', '+00:00')).astimezone(CT).date() == now.date()]
    pending = [e for e in todays if dt.datetime.fromisoformat(e['commence_time'].replace('Z', '+00:00')) > dt.datetime.now(dt.timezone.utc)]
    log('events today %d, not started %d, credits left %s' % (len(todays), len(pending), left))
    if left is not None and int(left) < MIN_LEFT + 9 * len(pending):
        log('STOP: only %s credits left, need ~%d for this pull' % (left, 9 * len(pending))); post('bball-system', '📚 Book lines: NOT pulled, only %s credits left on The Odds API. %d games waiting.' % (left, len(pending))); return 0, left
    rows = []; books = set(); games = 0
    for e in pending:
        try: data, left, used = get('/sports/%s/events/%s/odds' % (SPORT, e['id']), {'regions': REGIONS, 'markets': ','.join(MARKETS), 'oddsFormat': 'american'})
        except RuntimeError as ex: log('event %s failed: %s' % (e['id'], ex)); continue
        games += 1
        for bk in data.get('bookmakers', []):
            books.add(bk['key'])
            for m in bk.get('markets', []):
                by = {}
                for o in m.get('outcomes', []):
                    k2 = (o.get('description'), o.get('point')); d = by.setdefault(k2, {})
                    d[o['name'].lower()] = o.get('price')
                for (player, point), pr in by.items():
                    rows.append(dict(seen=seen, event_id=e['id'], start=e['commence_time'], home=e['home_team'], away=e['away_team'], book=bk['key'], book_updated=m.get('last_update'),
                                     market=m['key'], player=player, line=point, over=pr.get('over'), under=pr.get('under')))
        time.sleep(0.3)
    if not dry and rows:
        os.makedirs(OUT, exist_ok=True)
        with open(os.path.join(OUT, now.strftime('%Y-%m-%d') + '.jsonl'), 'a') as f:
            for r in rows: f.write(json.dumps(r) + '\n')
    players = len({(r['player'], r['market']) for r in rows})
    msg = '📚 Book lines saved: %d games, %d player lines (%d player-stats), books: %s. Odds API credits left %s.' % (games, len(rows), players, ', '.join(sorted(books)) or 'none', left)
    log(msg)
    if not dry: post('bball-system', msg)
    s = load_state(); s['last_pull'] = seen; s['credits_left'] = left; s['credits_used'] = used; s.setdefault('pulls', []).append(dict(at=seen, games=games, rows=len(rows), left=left)); s['pulls'] = s['pulls'][-200:]; save_state(s)
    return len(rows), left
def loop():
    log('loop start, source %s, pull times CT %s, markets %d' % (SOURCE, PULL_TIMES, len(MARKETS))); said_nokey = False; s = load_state()
    while True:
        now = dt.datetime.now(CT); hm = now.strftime('%H:%M'); day = now.strftime('%Y-%m-%d')
        if SOURCE != 'sgo' and not key():
            if not said_nokey: log('waiting for secrets/odds_api_key.txt'); said_nokey = True
            time.sleep(60); continue
        if SOURCE != 'sgo' and (said_nokey or not s.get('key_seen')):
            said_nokey = False
            try:
                sports, left, used = get('/sports', {}); s['key_seen'] = now.isoformat(timespec='seconds'); save_state(s)
                log('key works, credits left %s' % left); post('bball-system', '🔑 The Odds API key is in and works. Credits left: %s. First book-line pull at the next pull time (%s CT).' % (left, ', '.join(PULL_TIMES)))
            except Exception as e: log('key test failed: %s' % e); post('bball-alerts', '⚠️ The Odds API key did not work: %s' % str(e)[:150]); time.sleep(600); continue
        done = s.get('done', {}).get(day, [])
        due = [t for t in PULL_TIMES if t not in done and hm >= t and (dt.datetime.strptime(hm, '%H:%M') - dt.datetime.strptime(t, '%H:%M')).seconds < 3600]
        if due:
            try: pull()
            except Exception as e: log('pull failed: %s' % e); post('bball-alerts', '⚠️ Book-line pull failed: %s' % str(e)[:150])
            s.setdefault('done', {})[day] = done + due; s['done'] = {k: v for k, v in s['done'].items() if k >= day}; save_state(s)
        time.sleep(60)
if __name__ == '__main__':
    if '--once' in sys.argv: print(pull(dry='--dry' in sys.argv))
    elif '--loop' in sys.argv:
        open(os.path.join(ROOT, 'logs', 'book_line_collector.pid'), 'w').write(str(os.getpid())); loop()
    else: print(__doc__)
