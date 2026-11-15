#!/usr/bin/env python3
"""Apex Basketball injury + schedule collector (2026-11-04). Free ESPN feeds, no key, no PrizePicks calls, nothing from tennis.
Every 30 minutes (08:00-23:59 CT) saves:
  data/collected/injuries/YYYY-MM-DD.jsonl  one row per listed player per pass: team, player, status (Out / Doubtful /
                                           Questionable / Day-To-Day), detail, ESPN date, seen time
  data/collected/schedule/YYYY-MM-DD.json   today's games: teams, tip time, venue city, game status (for travel, home/away,
                                           back-to-back and "who is out at tip" tests)
Only new or changed injury rows are written, so the file shows WHEN a status changed (the pre-tip timing matters).
Stop: kill the pid in logs/injury_collector.pid. A Mac reboot stops it."""
import datetime as dt, json, os, time, urllib.request
from zoneinfo import ZoneInfo
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INJ = os.path.join(ROOT, 'data', 'collected', 'injuries'); SCH = os.path.join(ROOT, 'data', 'collected', 'schedule')
LOG = os.path.join(ROOT, 'logs', 'injury_collector.log'); PID = os.path.join(ROOT, 'logs', 'injury_collector.pid'); STATE = os.path.join(ROOT, 'logs', 'injury_collector_state.json')
CT = ZoneInfo('America/Chicago'); EVERY_MIN, HOURS = 30, ('08:00', '23:59')
URL_INJ = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries'
URL_SB = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard'
HDR = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', 'Accept': 'application/json'}
def log(m):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, 'a') as f: f.write('%s %s\n' % (dt.datetime.now(CT).strftime('%m/%d %H:%M:%S'), m))
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=30) as r: return json.load(r)
def load():
    try: return json.load(open(STATE))
    except Exception: return {'seen': {}, 'last_ts': 0}
def save(s):
    with open(STATE + '.tmp', 'w') as f: json.dump(s, f)
    os.replace(STATE + '.tmp', STATE)
def pass_once(s):
    now = dt.datetime.now(CT); seen_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'); day = now.strftime('%Y-%m-%d')
    os.makedirs(INJ, exist_ok=True); os.makedirs(SCH, exist_ok=True)
    d = get(URL_INJ); n = added = 0
    with open(os.path.join(INJ, day + '.jsonl'), 'a') as f:
        for team in d.get('injuries') or []:
            tname = team.get('displayName') or team.get('name') or ''
            for i in team.get('injuries') or []:
                a = i.get('athlete') or {}; n += 1
                rec = dict(seen=seen_at, team=tname, team_abbr=(a.get('team') or {}).get('abbreviation') or team.get('abbreviation'), player=a.get('displayName'), athlete_id=a.get('id'),
                           position=(a.get('position') or {}).get('abbreviation'), status=i.get('status'), espn_date=i.get('date'), detail=(i.get('details') or {}).get('type'),
                           side=(i.get('details') or {}).get('side'), return_date=(i.get('details') or {}).get('returnDate'), short=(i.get('shortComment') or '')[:300])
                k = str(a.get('id') or rec['player']); sig = '%s|%s|%s' % (rec['status'], rec['espn_date'], rec['detail'])
                if s['seen'].get(k) != sig:
                    s['seen'][k] = sig; f.write(json.dumps(rec) + '\n'); added += 1
    sb = get(URL_SB); games = []
    for ev in sb.get('events') or []:
        c = (ev.get('competitions') or [{}])[0]; v = c.get('venue') or {}; comps = c.get('competitors') or []
        g = dict(espn_id=ev.get('id'), date=c.get('date'), status=((c.get('status') or {}).get('type') or {}).get('name'), venue=v.get('fullName'),
                 city=(v.get('address') or {}).get('city'), state=(v.get('address') or {}).get('state'), neutral=c.get('neutralSite'))
        for t in comps:
            side = t.get('homeAway'); tm = t.get('team') or {}
            g[side] = tm.get('abbreviation'); g[side + '_name'] = tm.get('displayName'); g[side + '_score'] = t.get('score')
            g[side + '_record'] = ((t.get('records') or [{}])[0]).get('summary')
        games.append(g)
    with open(os.path.join(SCH, day + '.json'), 'w') as f: json.dump({'seen': seen_at, 'games': games}, f)
    log('injuries listed %d, new or changed %d | games today %d' % (n, added, len(games)))
def main():
    os.makedirs(os.path.dirname(PID), exist_ok=True)
    with open(PID, 'w') as f: f.write(str(os.getpid()))
    log('injury collector started pid %d' % os.getpid())
    while True:
        s = load(); hm = dt.datetime.now(CT).strftime('%H:%M')
        if HOURS[0] <= hm <= HOURS[1] and time.time() - s.get('last_ts', 0) >= EVERY_MIN * 60:
            try: pass_once(s)
            except Exception as e: log('pass failed %s: %s' % (type(e).__name__, e))
            s['last_ts'] = time.time(); save(s)
        time.sleep(60)
if __name__ == '__main__': main()
