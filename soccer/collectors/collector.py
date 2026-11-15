#!/usr/bin/env python3
"""Collector for this sport: PrizePicks board, ESPN schedule + injuries, The Odds API book lines (when a key and credits exist).
Every fetch is timestamped and appended under database/snapshots/<kind>/YYYY-MM-DD.jsonl, and summarised into database/history.db.
Line, odds, injury and board changes are kept as new rows, never overwrites, so movement can be read back later.

  python3 collectors/collector.py pp          PrizePicks board (all leagues in config)
  python3 collectors/collector.py espn        schedule + injuries from ESPN (free, no key)
  python3 collectors/collector.py books       The Odds API player props (needs secrets/odds_api_key.txt and credits)
  python3 collectors/collector.py results     finished games + box scores from ESPN (grading/results.py)
  python3 collectors/collector.py all
PrizePicks safety: 60 s between calls, read the tennis pause flag and the Apex Sports shared flag, stop for 6 hours on a 429 and set the shared flag."""
import datetime as dt, json, os, sys, time, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as CM
from database import db as DBM

HDR = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', 'Referer': 'https://app.prizepicks.com/', 'Origin': 'https://app.prizepicks.com', 'Accept': 'application/json'}
PP_API = 'https://partner-api.prizepicks.com/projections?league_id=%s&per_page=2000&single_stat=true'
ESPN = 'https://site.api.espn.com/apis/site/v2/sports/%s/'
ODDS = 'https://api.the-odds-api.com/v4/sports/%s/'
class RateLimited(Exception): pass

def get(url, hdr=None, timeout=30):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=hdr or HDR), timeout=timeout) as r: return json.load(r), dict(r.headers)
    except urllib.error.HTTPError as e:
        if e.code in (403, 429): raise RateLimited(e.code)
        raise

QUIET = os.path.join(CM.CACHE, 'log_quiet.json')
def log_changed(key, msg, every_h=24, shape=None):
    """Writes msg to collector.log only when it differs from the last one under this key, or every_h hours passed."""
    st = CM.read_json(QUIET, {}) or {}; e = st.get(key) or {}; now = time.time(); sh = shape if shape is not None else msg
    if e.get('shape') == sh and now - e.get('t', 0) < every_h * 3600: return
    st[key] = dict(shape=sh, t=now); CM.write_json(QUIET, st); CM.log('collector', msg)

def espn_get(url, tries=3, waits=(2, 5)):
    """ESPN with retries. Raises only after the last try fails; the caller then skips that league/day and keeps going."""
    for i in range(tries):
        try: return get(url, {'User-Agent': 'Mozilla/5.0'})
        except Exception as e:
            if i == tries - 1: raise
            CM.log('collector', 'ESPN try %d failed (%s), retrying: %s' % (i + 1, type(e).__name__, url.split('/sports/')[-1][:80])); time.sleep(waits[min(i, len(waits) - 1)])

SHARED_LASTCALL = os.path.expanduser('~/ApexSports/_shared/pp_lastcall.json')
SPORTS_LASTCALL = os.path.expanduser('~/ApexSports/_shared/pp_lastcall_sports.json')
PP_OK = False                                  # True only after this pull got at least one PrizePicks answer
TENNIS_STAMP = os.path.expanduser('~/ApexSports/_shared/pp_lastcall_tennis.json')   # APEX-PPSPACING-2026-11-10: tennis stamps this just before each of its calls
def _tennis_last():
    m = 0
    for f in (TENNIS_STAMP, os.path.expanduser('~/openclaw/data/logs/pp_requests.log')):
        try: m = max(m, os.path.getmtime(f))
        except OSError: pass
    return m
def pp_space(min_gap=600, max_wait=2400, any_gap=120, tennis_gap=60):
    """Every Apex sport waits until no other sport has called PrizePicks in the last min_gap seconds, then claims the slot."""
    import fcntl
    t0 = time.time(); said = False
    while True:
        with open(SHARED_LASTCALL + '.lock', 'a+') as lf:
            fcntl.flock(lf, fcntl.LOCK_EX)                     # one sport at a time checks and claims the slot
            last_sport = float((CM.read_json(SPORTS_LASTCALL, {}) or {}).get('ts') or 0)   # the 9 sports only
            last_any = float((CM.read_json(SHARED_LASTCALL, {}) or {}).get('ts') or 0)     # anyone, basketball included
            if time.time() - last_sport >= min_gap and time.time() - last_any >= any_gap and time.time() - _tennis_last() >= tennis_gap:   # APEX-PPSPACING-2026-11-10: never right behind a tennis call
                now = time.time(); me = CM.cfg()['sport']
                CM.write_json(SPORTS_LASTCALL, dict(ts=now, by=me)); CM.write_json(SHARED_LASTCALL, dict(ts=now, by=me)); return True
        if not said: CM.log('collector', 'PrizePicks: another Apex product called just now, waiting for the slot'); said = True
        if time.time() - t0 > max_wait:
            CM.log('collector', 'PrizePicks: no free slot after %d min, skipping this pull (next one tries again)' % (max_wait // 60)); return False
        time.sleep(5)
def pp_paused():
    for f in (CM.TENNIS_COOLDOWN, CM.SHARED_COOLDOWN):
        try:
            if float(CM.read_json(f, {}).get('until') or 0) > time.time(): return True
        except (TypeError, ValueError): pass
    return False
def set_shared_pause(hours):
    try: CM.write_json(CM.SHARED_COOLDOWN, dict(until=time.time() + hours * 3600, by=CM.cfg()['sport'], at=CM.iso()))
    except OSError: pass

# ---------------------------------------------------------------------------------- PrizePicks slow-down tracker (11/5, his ask)
SHARED_CALLS = os.path.expanduser('~/ApexSports/_shared/pp_calls.jsonl')          # every PrizePicks call from every Apex sport + basketball
TENNIS_REQ_LOG = os.path.expanduser('~/openclaw/data/logs/pp_requests.log')        # tennis, read only: "YYYY-MM-DD HH:MM:SS<tab>job<tab>code"
def _tennis_calls(minutes=None, day=None):
    """Tennis PrizePicks calls as (ct_datetime, job, code); last `minutes` or a whole CT day."""
    out = []
    try:
        with open(TENNIS_REQ_LOG, 'rb') as f:
            f.seek(0, 2); size = f.tell(); f.seek(max(0, size - 400000)); lines = f.read().decode('utf-8', 'ignore').split('\n')[1:]
        now = CM.now_ct()
        for ln in lines:
            p = ln.strip().split('\t')
            if len(p) < 3: continue
            try: t = dt.datetime.strptime(p[0], '%Y-%m-%d %H:%M:%S').replace(tzinfo=CM.CT)
            except ValueError: continue
            if minutes is not None and (now - t).total_seconds() > minutes * 60: continue
            if day is not None and t.date().isoformat() != day: continue
            out.append((t, p[1], p[2]))
    except OSError: pass
    return out
def tennis_space(min_gap=60):
    """Never call PrizePicks within min_gap seconds of a tennis call (tennis is read-only to us)."""
    for _ in range(12):
        last = _tennis_calls(minutes=5)
        if not last or (CM.now_ct() - last[-1][0]).total_seconds() >= min_gap: return
        time.sleep(5)
def log_pp_call(league, code, n=0):
    try: CM.jsonl_append(SHARED_CALLS, [dict(ts=CM.iso(), sport=CM.cfg()['sport'], league=league, code=int(code), n=int(n))])
    except Exception: pass
def pp_health(day=None):
    """Counts for one CT day (default yesterday): tennis calls, basketball calls, new-sport calls, slow-downs with who called in the 10 minutes before."""
    day = day or (CM.now_ct().date() - dt.timedelta(days=1)).isoformat()
    ours = [r for r in CM.jsonl_read(SHARED_CALLS) if CM.ct_date(CM.parse_iso(r['ts'])) == day] if os.path.exists(SHARED_CALLS) else []
    ten = _tennis_calls(day=day)
    slow = [r for r in ours if r['code'] in (429, 403)]
    return dict(day=day, tennis=len(ten), tennis_slow=sum(1 for t in ten if t[2] in ('429', '403')), basketball=sum(1 for r in ours if r['sport'] == 'nba'),
                sports=sum(1 for r in ours if r['sport'] != 'nba'), slow=slow, ours=ours)
def pp_health_line(day=None):
    h = pp_health(day)
    s = '📡 PrizePicks %s: tennis %d calls (%d slow-downs), basketball %d, the 9 sports %d, slow-downs on the 9 sports %d.' % (dt.date.fromisoformat(h['day']).strftime('%a %-m/%-d'), h['tennis'], h['tennis_slow'], h['basketball'], h['sports'], len(h['slow']))
    if h['slow']: s += ' ' + ' · '.join('%s %s' % (CM.fmt_ct(r['ts'], '%-I:%M %p'), r['sport'].upper()) for r in h['slow'][:6])
    return s
def slowdown_context(minutes=10):
    """Who called PrizePicks in the last N minutes, for the alert."""
    now = CM.now_utc(); ours = [r for r in CM.jsonl_read(SHARED_CALLS) if (now - CM.parse_iso(r['ts'])).total_seconds() <= minutes * 60] if os.path.exists(SHARED_CALLS) else []
    ten = _tennis_calls(minutes=minutes)
    return 'In the %d minutes before: tennis %d call%s, basketball %d, the 9 sports %d (%s).' % (minutes, len(ten), '' if len(ten) == 1 else 's', sum(1 for r in ours if r['sport'] == 'nba'), sum(1 for r in ours if r['sport'] != 'nba'), ', '.join(sorted(set(r['sport'] for r in ours if r['sport'] != 'nba'))) or 'none')

def stat_id(raw):
    return CM.cfg()['stats_by_pp_name'].get(str(raw or '').strip().lower())

# ------------------------------------------------------------------------------------------------------------- PrizePicks
def pull_pp(db):
    global PP_OK; PP_OK = False
    if pp_paused(): CM.log('collector', 'PrizePicks paused by another product, skipping'); return 0
    c = CM.cfg(); seen_at = CM.iso(); day = CM.ct_date(); added = total = 0; rows = []
    # APEX-WAGER-2026-11-12: save which sides PrizePicks sells on each line ('over' or 'under_or_over'); his 'go goblin less'
    try: db.execute('create table if not exists pp_wager(projection_id text, line real, kind text, wager text, first_seen text, last_seen text, primary key(projection_id, line, kind, wager))')
    except Exception: pass
    # off season: after 3 empty boards in a row, look only once a day until lines come back
    zero = int(DBM.kv_get(db, 'pp_zero_streak', 0) or 0); lastp = CM.parse_iso(DBM.kv_get(db, 'pp_last_pull') or '')
    if zero >= 3 and lastp and (CM.now_utc() - lastp).total_seconds() < 24 * 3600: log_changed('pp_offseason', 'PrizePicks: board empty %d pulls in a row (off season), checking once a day' % zero, shape='offseason'); return 0
    if not c['prizepicks']['leagues']: log_changed('pp_noleague', 'PrizePicks: no league id for this sport, PrizePicks is not pulled'); return 0
    for i, (lid, lname) in enumerate(c['prizepicks']['leagues'].items()):
        if not pp_space(): break
        tennis_space()
        try: d, _ = get(PP_API % lid); log_pp_call(lname, 200, len(d.get('data', []))); PP_OK = True
        except RateLimited as e:
            set_shared_pause(2); log_pp_call(lname, int(str(e)) if str(e).isdigit() else 429); CM.log('collector', 'PrizePicks HTTP %s on league %s: every Apex sport pauses 2 h' % (e, lname))
            try: CM.dmod('post').post('alerts', '🐢 PrizePicks slow-down (HTTP %s) on %s at %s. Every Apex sport pauses 2 hours; basketball too. %s' % (e, lname, CM.now_ct().strftime('%-I:%M %p CT'), slowdown_context()))
            except Exception: pass
            break
        inc = {(x['type'], str(x['id'])): x.get('attributes', {}) for x in d.get('included', [])}
        for p in d.get('data', []):
            a = p.get('attributes', {}); rel = p.get('relationships', {}); total += 1
            pl = inc.get(('new_player', str((rel.get('new_player', {}).get('data') or {}).get('id')))) or {}
            g = inc.get(('game', str((rel.get('game', {}).get('data') or {}).get('id')))) or {}
            teams = ((g.get('metadata') or {}).get('game_info') or {}).get('teams') or {}
            raw = a.get('stat_display_name') or a.get('stat_type')
            rec = dict(seen=seen_at, projection_id=str(p['id']), league=lname, player=pl.get('display_name') or pl.get('name'), team=pl.get('team'), position=pl.get('position'),
                       opponent=a.get('description'), home=(teams.get('home') or {}).get('abbreviation'), away=(teams.get('away') or {}).get('abbreviation'), game_id=a.get('game_id'),
                       stat=raw, stat_id=stat_id(raw), line=a.get('line_score'), odds_type=a.get('odds_type') or 'standard', start=a.get('start_time'), status=a.get('status'),
                       wager=a.get('allowed_wager_types'), is_promo=bool(a.get('is_promo')), flash_sale_line=a.get('flash_sale_line_score'), adjusted_odds=a.get('adjusted_odds'), board_time=a.get('board_time'), updated_at=a.get('updated_at'))
            try: line = float(rec['line'])
            except (TypeError, ValueError): continue
            try: db.execute('insert into pp_wager values(?,?,?,?,?,?) on conflict(projection_id, line, kind, wager) do update set last_seen=excluded.last_seen', (rec['projection_id'], line, rec['odds_type'], rec['wager'] or 'none', seen_at, seen_at))
            except Exception: pass
            cur = db.execute('select rowid, seen_count from pp_lines where projection_id=? and line=? and kind=? and status=?', (rec['projection_id'], line, rec['odds_type'], rec['status'])).fetchone()
            if cur: db.execute('update pp_lines set last_seen=?, seen_count=? where rowid=?', (seen_at, cur[1] + 1, cur[0]))
            else:
                db.execute('insert into pp_lines values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)', (rec['projection_id'], lname, rec['player'], CM.norm(rec['player']), rec['team'], rec['opponent'], rec['home'], rec['away'], str(rec['game_id']),
                           raw, rec['stat_id'], line, rec['odds_type'], rec['start'], rec['status'], int(rec['is_promo'] or rec['flash_sale_line'] is not None), seen_at, seen_at))
                rows.append(rec); added += 1
    if rows: CM.jsonl_append(os.path.join(CM.SNAP, 'pp', day + '.jsonl'), rows)
    db.execute('insert into snapshots(fetched_at,kind,league,n,file) values(?,?,?,?,?)', (seen_at, 'pp', ','.join(c['prizepicks']['leagues'].values()), total, 'pp/%s.jsonl' % day)); db.commit()
    DBM.kv_set(db, 'pp_last_pull', seen_at); DBM.kv_set(db, 'pp_zero_streak', 0 if total else zero + 1); CM.log('collector', 'PrizePicks: %d lines on the board, %d new or moved' % (total, added)); return added

# ------------------------------------------------------------------------------------------------------------- ESPN schedule + injuries
def espn_paths(): return CM.cfg()['espn']['paths']
def pull_espn(db, days=2):
    seen_at = CM.iso(); day = CM.ct_date(); n_g = n_i = 0; rows_i = []
    for path in espn_paths():
        for off in range(days):
            d = (CM.now_ct().date() + dt.timedelta(days=off)).strftime('%Y%m%d')
            try: j, _ = espn_get(ESPN % path + 'scoreboard?dates=' + d + '&limit=300')
            except Exception as e: CM.log('collector', 'ESPN scoreboard %s %s failed after 3 tries: %s (skipped, next pull tries again)' % (path, d, type(e).__name__)); continue
            if not isinstance(j, dict): CM.log('collector', 'ESPN scoreboard %s %s: not a JSON object, skipped' % (path, d)); continue
            for e in j.get('events') or []:
              try:
                comp = ((e.get('competitions') or [None])[0]) or {}; tm = {t.get('homeAway'): t for t in comp.get('competitors') or [] if t}
                if 'home' not in tm or 'away' not in tm or not tm['home'].get('team') or not tm['away'].get('team'): continue
                st = CM.parse_iso(e.get('date')); status = ((comp.get('status') or e.get('status') or {}).get('type') or {})
                odds = ((comp.get('odds') or [None])[0]) or {}
                db.execute('insert into games(event_id,game_date,start_utc,home,away,home_score,away_score,final,source,total,spread_home) values(?,?,?,?,?,?,?,?,?,?,?) on conflict(event_id) do update set start_utc=excluded.start_utc,home_score=excluded.home_score,away_score=excluded.away_score,final=excluded.final,total=coalesce(excluded.total,games.total),spread_home=coalesce(excluded.spread_home,games.spread_home)',
                           (str(e['id']), st.astimezone(CM.CT).date().isoformat() if st else day, CM.iso(st) if st else None, tm['home']['team'].get('abbreviation'), tm['away']['team'].get('abbreviation'),
                            _f(tm['home'].get('score')), _f(tm['away'].get('score')), int(bool(status.get('completed'))), 'espn', _f(odds.get('overUnder')), _spread(odds, tm))); n_g += 1
              except Exception as ex: CM.log('collector', 'ESPN event skipped: %s' % type(ex).__name__)
            time.sleep(1)
        if CM.cfg()['espn'].get('injuries', True):
            try:
                j, _ = espn_get(ESPN % path + 'injuries')
                for team in j.get('injuries') or []:
                    for i in team.get('injuries') or []:
                        a = i.get('athlete') or {}; rec = dict(seen=seen_at, team=(a.get('team') or {}).get('abbreviation') or team.get('abbreviation') or team.get('displayName'), player=a.get('displayName'), status=i.get('status'), detail=(i.get('details') or {}).get('type'), espn_date=i.get('date'))
                        rec['impact'] = {'out': 100, 'injured reserve': 100, 'ir': 100, 'suspended': 100, 'doubtful': 75, 'questionable': 50, 'game time decision': 50, 'day-to-day': 25, 'probable': 10}.get(str(rec['status'] or '').lower(), 0)
                        last = db.execute('select status from injuries where team=? and player_norm=? order by fetched_at desc limit 1', (rec['team'], CM.norm(rec['player']))).fetchone()
                        if not last or last[0] != rec['status']:
                            db.execute('insert or ignore into injuries values(?,?,?,?,?,?)', (seen_at, rec['team'], rec['player'], CM.norm(rec['player']), rec['status'], rec['detail'])); rows_i.append(rec); n_i += 1
            except Exception as e: CM.log('collector', 'ESPN injuries %s: %s (this league may have no injury feed)' % (path, type(e).__name__))
    if rows_i: CM.jsonl_append(os.path.join(CM.SNAP, 'injuries', day + '.jsonl'), rows_i)
    db.execute('insert into snapshots(fetched_at,kind,league,n,file) values(?,?,?,?,?)', (seen_at, 'espn', ','.join(espn_paths()), n_g, 'injuries/%s.jsonl' % day)); db.commit()
    DBM.kv_set(db, 'espn_last_pull', seen_at); log_changed('espn_line', 'ESPN: %d games on the schedule, %d injury changes' % (n_g, n_i), every_h=6, shape='%d|%d' % (n_g, min(n_i, 1)) if n_i == 0 else str(time.time())); return n_g
def _f(x):
    try: return float(x)
    except (TypeError, ValueError): return None
def _spread(odds, tm):
    try:
        d = odds.get('details') or ''; fav, num = d.rsplit(' ', 1); num = float(num)
        return num if fav.strip() == tm['home']['team'].get('abbreviation') else -num
    except Exception: return None

# ------------------------------------------------------------------------------------------------------------- The Odds API
# APEX-SGOBOOKS-2026-11-11 (owner, "Go sgo other sports"): book lines from SportsGameOdds when config odds_api.source is "sgo".
# Key stays inside openclaw/data/sgo_archive/tools/sgo_raw.py (never read or logged here). Same book_lines table and snapshot file as before.
SGO_TOOLS = '/path/to/home/openclaw/data/sgo_archive/tools'
# Real sportsbooks only: no pick'em apps (PrizePicks, Underdog, Sleeper, Fliff), no exchanges or prediction markets, no SugarHouse (same lines as BetRivers).
SGO_BOOKS = {'fanduel', 'draftkings', 'betmgm', 'caesars', 'bet365', 'espnbet', 'betrivers', 'bovada', 'betonline', 'pinnacle', 'hardrockbet', 'fanatics', 'ballybet', 'betparx', 'circa', 'bookmakereu'}
def _amer(v):
    try: return int(str(v).replace('+', ''))
    except (TypeError, ValueError): return None
def pull_books_sgo(db, c):
    if SGO_TOOLS not in sys.path: sys.path.insert(0, SGO_TOOLS)
    import sgo_raw as R, importlib as _il; R = _il.reload(R)   # APEX-KEYRELOAD-2026-11-15: re-read the saved key every pull so a new /setkey works without a restart
    seen_at = CM.iso(); day = CM.ct_date(); rows = []; n = 0; games = 0; books = set(); now = CM.now_utc(); end = now + dt.timedelta(hours=c.get('hours_ahead', 30)); lo, hi = c.get('sgo_odds_range', [-200, 160])
    for lg in c.get('sgo_leagues') or []:
        status, d, _ = R.get('/v2/events/', {'leagueID': lg, 'oddsAvailable': 'true', 'startsAfter': now.strftime('%Y-%m-%dT%H:%M:%SZ'), 'startsBefore': end.strftime('%Y-%m-%dT%H:%M:%SZ'), 'limit': 50}, 'books_' + lg)
        if status != 200: CM.log('collector', 'books: SportsGameOdds %s answered %s' % (lg, status)); continue
        for e in d.get('data') or []:
            st = e.get('status') or {}; start = CM.parse_iso(st.get('startsAt'))
            if not start or start < now or start > end or st.get('started') or st.get('cancelled'): continue
            players = e.get('players') or {}; od = e.get('odds') or {}; got = False
            for o in od.values():
                stat = c['sgo_stat'].get(o.get('statID'))
                if not stat or o.get('sideID') != 'over' or o.get('betTypeID') != 'ou' or o.get('periodID') != 'game': continue
                pl = (players.get(o.get('playerID') or o.get('statEntityID')) or {}).get('name')
                if not pl: continue
                under = (od.get(o.get('opposingOddID')) or {}).get('byBookmaker') or {}
                for bk, v in (o.get('byBookmaker') or {}).items():
                    u = under.get(bk) or {}
                    if bk not in SGO_BOOKS or not v.get('available') or not u.get('available') or v.get('overUnder') != u.get('overUnder'): continue
                    try: pt = float(v['overUnder'])
                    except (KeyError, TypeError, ValueError): continue
                    ov, un = _amer(v.get('odds')), _amer(u.get('odds'))
                    if ov is None or un is None or not (lo <= ov <= hi) or not (lo <= un <= hi): continue
                    rows.append(dict(seen=seen_at, book=bk, market='sgo:' + o['statID'], stat=stat, player=pl, line=pt, over=ov, under=un, event_id=e.get('eventID'), start=st.get('startsAt'), source='sgo')); n += 1; got = True; books.add(bk)
                    db.execute('insert into book_lines values(?,?,?,?,?,?,?,?,?,?,?)', (seen_at, bk, 'sgo:' + o['statID'], stat, pl, CM.norm(pl), pt, ov, un, e.get('eventID'), st.get('startsAt')))
            games += got
    if rows: CM.jsonl_append(os.path.join(CM.SNAP, 'books', day + '.jsonl'), rows)
    db.execute('insert into snapshots(fetched_at,kind,league,n,file) values(?,?,?,?,?)', (seen_at, 'books', ','.join(c.get('sgo_leagues') or []), n, 'books/%s.jsonl' % day)); db.commit()
    CM.log('collector', 'books: %d book lines saved from SportsGameOdds (%d games, %d books)' % (n, games, len(books))); return n

def pull_books(db):
    c = CM.cfg()['odds_api']; key = CM.secret('odds_api_key.txt')
    if c.get('source') == 'sgo': return pull_books_sgo(db, c)
    if not key: CM.log('collector', 'books: no Odds API key in secrets/, skipped'); return 0
    seen_at = CM.iso(); day = CM.ct_date(); rows = []; n = 0
    for sk in c['sport_keys']:
        try: ev, h = get(ODDS % sk + 'events?apiKey=' + key, {'User-Agent': 'Mozilla/5.0'})
        except Exception as e: CM.log('collector', 'books events %s failed: %s' % (sk, type(e).__name__)); continue
        left = _f(h.get('x-requests-remaining') or h.get('X-Requests-Remaining'))
        for e in ev:
            st = CM.parse_iso(e.get('commence_time'))
            if not st or st < CM.now_utc() or st > CM.now_utc() + dt.timedelta(hours=c.get('hours_ahead', 30)): continue
            if left is not None and left < c.get('min_left', 30): CM.log('collector', 'books: only %d credits left, stopping' % left); break
            try: j, h = get(ODDS % sk + 'events/%s/odds?apiKey=%s&regions=%s&markets=%s&oddsFormat=american' % (e['id'], key, c.get('regions', 'us'), ','.join(c['markets'])), {'User-Agent': 'Mozilla/5.0'})
            except Exception as ex: CM.log('collector', 'books event %s failed: %s' % (e['id'], type(ex).__name__)); continue
            left = _f(h.get('x-requests-remaining') or h.get('X-Requests-Remaining'))
            for bk in j.get('bookmakers') or []:
                for m in bk.get('markets') or []:
                    by = {}
                    for o in m.get('outcomes') or []:
                        k = (o.get('description'), o.get('point')); by.setdefault(k, {})[o.get('name')] = o.get('price')
                    for (pl, pt), pr in by.items():
                        rec = dict(seen=seen_at, book=bk['key'], market=m['key'], stat=c['stat_by_market'].get(m['key']), player=pl, line=pt, over=pr.get('Over'), under=pr.get('Under'), event_id=e['id'], start=e.get('commence_time'))
                        rows.append(rec); n += 1
                        db.execute('insert into book_lines values(?,?,?,?,?,?,?,?,?,?,?)', (seen_at, rec['book'], rec['market'], rec['stat'], pl, CM.norm(pl), pt, pr.get('Over'), pr.get('Under'), e['id'], e.get('commence_time')))
            time.sleep(0.5)
        DBM.kv_set(db, 'odds_api_credits_left', left)
    if rows: CM.jsonl_append(os.path.join(CM.SNAP, 'books', day + '.jsonl'), rows)
    db.execute('insert into snapshots(fetched_at,kind,league,n,file) values(?,?,?,?,?)', (seen_at, 'books', ','.join(c['sport_keys']), n, 'books/%s.jsonl' % day)); db.commit()
    CM.log('collector', 'books: %d book lines saved' % n); return n

if __name__ == '__main__':
    what = sys.argv[1] if len(sys.argv) > 1 else 'all'; db = DBM.connect()
    if what in ('pp', 'all'): pull_pp(db)
    if what in ('espn', 'all'): pull_espn(db)
    if what in ('books', 'all'): pull_books(db)
    if what in ('results',):
        from grading import results as R; print(R.update(db))
