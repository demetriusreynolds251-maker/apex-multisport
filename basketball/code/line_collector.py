#!/usr/bin/env python3
"""Apex Basketball line collector (v2, 2026-11-04). Saves every PrizePicks NBA line, append only, with the Goblin / Demon /
Standard label. Separate from Apex Tennis: no Apex imports, no Apex writes. It only READS tennis's PrizePicks pause flag
(~/openclaw/data/logs/pp_cooldown.json) so the two products never hammer PrizePicks at the same time.

v1 (10/31) never saved a line: it used api.prizepicks.com (bot-walled) and waited whenever tennis had made 7+ calls in the
last hour, which is always. v2 uses partner-api.prizepicks.com (the same host tennis uses), pulls every PULL_EVERY minutes
from 08:00 to 23:59 CT, 60 s between calls, and stops 6 hours on a 429.
Output: data/collected/YYYY-MM-DD.jsonl (one row per new or changed line; same shape as v1 so bball_pipeline reads it).
Stop: kill the pid in logs/line_collector.pid. A Mac reboot stops it."""
import datetime as dt, json, os, time, urllib.request, urllib.error
from zoneinfo import ZoneInfo
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'collected'); LOG = os.path.join(ROOT, 'logs', 'line_collector.log'); PID = os.path.join(ROOT, 'logs', 'line_collector.pid')
STATE = os.path.join(ROOT, 'logs', 'line_collector_state.json')
TENNIS_PAUSE = os.path.expanduser('~/openclaw/data/logs/pp_cooldown.json')   # read only
SHARED_PAUSE = os.path.expanduser('~/ApexSports/_shared/pp_cooldown.json')      # his 'Go pp shared pause' 11/5: read AND written, shared with the 9 other sports
SHARED_LASTCALL = os.path.expanduser('~/ApexSports/_shared/pp_lastcall.json')   # 120 s between any Apex sport's PrizePicks call
SHARED_CALLS = os.path.expanduser('~/ApexSports/_shared/pp_calls.jsonl')      # slow-down tracker, shared with the other sports
def log_pp_call(league, code, n=0):
    try:
        with open(SHARED_CALLS, 'a') as f: f.write(json.dumps(dict(ts=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), sport='nba', league=league, code=int(code), n=int(n))) + '\n')
    except OSError: pass
CT = ZoneInfo('America/Chicago')
LEAGUES = {7: 'NBA'}                      # PrizePicks league ids; WNBA / NCAAB can be added here
PULL_EVERY, HOURS, CALL_GAP, BACKOFF_429 = 30, ('08:00', '23:59'), 60, 6 * 3600
API = 'https://partner-api.prizepicks.com/projections?league_id=%s&per_page=2000&single_stat=true'
HDR = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', 'Referer': 'https://app.prizepicks.com/', 'Origin': 'https://app.prizepicks.com', 'Accept': 'application/json'}
class RateLimited(Exception): pass
def log(m):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, 'a') as f: f.write('%s %s\n' % (dt.datetime.now(CT).strftime('%m/%d %H:%M:%S'), m))
def load():
    try: return json.load(open(STATE))
    except Exception: return {'seen': {}, 'last_pull': None, 'pause_until': 0}
def save(s):
    with open(STATE + '.tmp', 'w') as f: json.dump(s, f)
    os.replace(STATE + '.tmp', STATE)
def tennis_paused():
    for f in (TENNIS_PAUSE, SHARED_PAUSE):
        try:
            if float(json.load(open(f)).get('until') or 0) > time.time(): return True
        except Exception: pass
    return False
def _tennis_last():   # APEX-PPSPACING-2026-11-10: tennis stamps a file just before each of its PrizePicks calls
    m = 0
    for p in ('~/ApexSports/_shared/pp_lastcall_tennis.json', '~/openclaw/data/logs/pp_requests.log'):
        try: m = max(m, os.path.getmtime(os.path.expanduser(p)))
        except OSError: pass
    return m
def shared_space(min_gap=120, tennis_gap=60):
    for _ in range(40):
        try: last = float(json.load(open(SHARED_LASTCALL)).get('ts') or 0)
        except Exception: last = 0
        if time.time() - last >= min_gap and time.time() - _tennis_last() >= tennis_gap: break
        time.sleep(5)
    try:
        os.makedirs(os.path.dirname(SHARED_LASTCALL), exist_ok=True)
        with open(SHARED_LASTCALL, 'w') as f: json.dump(dict(ts=time.time(), by='nba'), f)
    except OSError: pass
def set_shared_pause(hours=2):
    try:
        with open(SHARED_PAUSE, 'w') as f: json.dump(dict(until=time.time() + hours * 3600, by='nba', at=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')), f)
    except OSError: pass
def get(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=30) as r: return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code in (403, 429): raise RateLimited(e.code)
        raise
def pull(s):
    seen_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'); added = total = 0; ids = []
    os.makedirs(OUT, exist_ok=True); fn = os.path.join(OUT, dt.datetime.now(CT).strftime('%Y-%m-%d') + '.jsonl')
    for i, (lid, lname) in enumerate(LEAGUES.items()):
        if i: time.sleep(CALL_GAP)
        shared_space()
        try: d = get(API % lid); log_pp_call(lname, 200, len(d.get('data', [])))
        except RateLimited as e: log_pp_call(lname, int(str(e)) if str(e).isdigit() else 429); raise
        inc = {(x['type'], str(x['id'])): x.get('attributes', {}) for x in d.get('included', [])}
        with open(fn, 'a') as f:
            for p in d.get('data', []):
                a = p.get('attributes', {}); total += 1; rel = p.get('relationships', {}); ids.append(str(p['id']))
                pl = inc.get(('new_player', str((rel.get('new_player', {}).get('data') or {}).get('id')))) or {}
                g = inc.get(('game', str((rel.get('game', {}).get('data') or {}).get('id')))) or {}
                teams = ((g.get('metadata') or {}).get('game_info') or {}).get('teams') or {}
                rec = dict(seen=seen_at, projection_id=p['id'], league=lname, player=pl.get('display_name') or pl.get('name'), team=pl.get('team'), position=pl.get('position'),
                           opponent=a.get('description'), home=(teams.get('home') or {}).get('abbreviation'), away=(teams.get('away') or {}).get('abbreviation'),
                           game_id=a.get('game_id'), stat=a.get('stat_display_name') or a.get('stat_type'), line=a.get('line_score'), odds_type=a.get('odds_type') or 'standard',
                           start=a.get('start_time'), status=a.get('status'), is_promo=a.get('is_promo'), flash_sale_line=a.get('flash_sale_line_score'),
                           adjusted_odds=a.get('adjusted_odds'), board_time=a.get('board_time'), updated_at=a.get('updated_at'), trending=a.get('trending_count'))
                try:   # APEX-WAGER-2026-11-12: which sides PrizePicks sells on this line, own file so nothing else reads it
                    w = a.get('allowed_wager_types') or 'none'; wk = '%s|%s|%s' % (rec['line'], rec['odds_type'], w)
                    if s.setdefault('wager', {}).get(str(p['id'])) != wk:
                        s['wager'][str(p['id'])] = wk; os.makedirs(os.path.join(ROOT, 'data', 'wager'), exist_ok=True)
                        with open(os.path.join(ROOT, 'data', 'wager', dt.datetime.now(CT).strftime('%Y-%m-%d') + '.jsonl'), 'a') as wf: wf.write(json.dumps(dict(seen=seen_at, projection_id=str(p['id']), player=rec['player'], stat=rec['stat'], line=rec['line'], odds_type=rec['odds_type'], wager=w, start=rec['start'])) + '\n')
                except Exception: pass
                k = str(p['id']); sig = '%s|%s|%s|%s' % (rec['line'], rec['odds_type'], rec['start'], rec['status'])
                if s['seen'].get(k) != sig:
                    s['seen'][k] = sig; f.write(json.dumps(rec) + '\n'); added += 1
    # forget ids older than 3 days so the state file stays small
    tmp = os.path.join(OUT, 'last_pull_ids.json.tmp')   # every id on this full pull, so scoring can drop lines PrizePicks took down
    with open(tmp, 'w') as f: json.dump(dict(at=seen_at, ids=ids), f)
    os.replace(tmp, os.path.join(OUT, 'last_pull_ids.json'))
    log('pull done: %d lines, %d new or changed' % (total, added))
    return added
def main():
    os.makedirs(os.path.dirname(PID), exist_ok=True)
    with open(PID, 'w') as f: f.write(str(os.getpid()))
    log('collector v2 started pid %d (partner API, every %d min %s-%s CT)' % (os.getpid(), PULL_EVERY, HOURS[0], HOURS[1]))
    while True:
        s = load(); now = dt.datetime.now(CT); hm = now.strftime('%H:%M')
        last = s.get('last_pull_ts') or 0
        if HOURS[0] <= hm <= HOURS[1] and time.time() - last >= PULL_EVERY * 60 and time.time() >= s.get('pause_until', 0):
            if tennis_paused(): log('PrizePicks pause flag is set (tennis or shared) -- skipping this pull')
            else:
                try:
                    pull(s); s['last_pull_ts'] = time.time(); s['last_pull'] = now.strftime('%Y-%m-%d %H:%M')
                except RateLimited as e:
                    s['pause_until'] = time.time() + BACKOFF_429; s['last_pull_ts'] = time.time(); set_shared_pause(2); log('HTTP %s: stopping for 6 hours, other sports paused 2 hours' % e)
                except Exception as e:
                    s['last_pull_ts'] = time.time(); log('pull failed %s: %s' % (type(e).__name__, e))
            save(s)
        time.sleep(60)
if __name__ == '__main__': main()
