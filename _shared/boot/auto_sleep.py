#!/usr/bin/env python3
"""Auto sleep (his 'go auto sleep', 11/6/2026). Run by apex_boot.sh every 5 minutes.
A running sport whose PrizePicks board has been empty 7 days in a row (and that has at least 7 days of pulls, so a new sport is never
put to sleep) posts a goodnight line, gets an INACTIVE file with its wake date, and its scheduler + bot are stopped. apex_boot.sh wakes
it on that date. Tennis is never read or touched.   python3 auto_sleep.py [--dry]"""
import os, sys, json, sqlite3, signal, subprocess, time, datetime as dt
ROOT = os.path.expanduser('~/ApexSports'); LOG = os.path.join(ROOT, '_shared/boot/boot.log'); DAYS = 7
WAKE = {'football/nfl': (8, 1), 'football/ncaaf': (8, 20), 'hockey/nhl': (9, 25), 'basketball/ncaab': (10, 25), 'soccer': (7, 15),
        'basketball/wnba': (5, 1), 'baseball/mlb': (3, 15), 'afl': (3, 1), 'basketball': (10, 1)}
DRY = '--dry' in sys.argv
def log(m):
    with open(LOG, 'a') as f: f.write('%s %s\n' % (dt.datetime.now().strftime('%m/%d %H:%M:%S'), m))
def ts(s):
    try: return dt.datetime.fromisoformat(str(s).replace('Z', '+00:00')).timestamp()
    except Exception: return None
def next_wake(md):
    t = dt.date.today(); w = dt.date(t.year, *md)
    return w if w > t else dt.date(t.year + 1, *md)
def pp_window(rel):
    """(first pull, last pull with lines) as epoch seconds, from this sport's own records."""
    if rel == 'basketball':
        rows = []
        try: rows = [json.loads(l) for l in open(os.path.join(ROOT, '_shared/pp_calls.jsonl')) if '"nba"' in l]
        except OSError: pass
        rows = [r for r in rows if r.get('sport') == 'nba']
        first = min((ts(r['ts']) for r in rows), default=None); last = max((ts(r['ts']) for r in rows if (r.get('n') or 0) > 0), default=None)
        empties = sum(1 for r in rows if (r.get('n') or 0) == 0 and str(r.get('code')) == '200' and (ts(r['ts']) or 0) > time.time() - DAYS * 86400)
        return first, last, empties
    db = sqlite3.connect('file:%s?mode=ro' % os.path.join(ROOT, rel, 'database/history.db'), uri=True)
    a, b = db.execute("select min(fetched_at), max(case when n>0 then fetched_at end) from snapshots where kind='pp'").fetchone()
    since = dt.datetime.fromtimestamp(time.time() - DAYS * 86400, dt.timezone.utc).isoformat(timespec='seconds')
    e = db.execute("select count(distinct substr(fetched_at,1,10)) from snapshots where kind='pp' and n=0 and fetched_at>=?", (since,)).fetchone()[0]; db.close()
    return ts(a), ts(b), e
def stop(rel):
    if rel == 'basketball':
        pids = ['logs/bball_bot.pid', 'logs/line_collector.pid', 'logs/injury_collector.pid', 'logs/book_line_collector.pid']   # bot loop first, so its watchdog stops
    else: pids = ['logs/start.pid']                     # start.sh stops its scheduler and bot on TERM
    for p in pids:
        try: os.kill(int(open(os.path.join(ROOT, rel, p)).read().strip()), signal.SIGTERM)
        except Exception: pass
        time.sleep(1)
def announce(rel, text):
    if rel == 'basketball':
        open(os.path.join(ROOT, 'basketball/logs/announce.txt'), 'w').write(text)          # the bot posts it to #bball-system on its next tick
        for _ in range(45):
            if not os.path.exists(os.path.join(ROOT, 'basketball/logs/announce.txt')): return True
            time.sleep(2)
        return False
    subprocess.run(['/usr/bin/python3', '-c', "import sys; sys.path.insert(0,'.'); import common as CM; CM.dmod('post').post('system', sys.argv[1], force=True)", text], cwd=os.path.join(ROOT, rel), timeout=60)
    ob = os.path.join(ROOT, rel, 'cache/outbox')
    for _ in range(45):
        if not [f for f in os.listdir(ob) if f.endswith('.json')]: return True
        time.sleep(2)
    return False
now = time.time()
for rel, md in WAKE.items():
    if os.path.exists(os.path.join(ROOT, rel, 'INACTIVE')): continue
    try: first, last, empties = pp_window(rel)
    except Exception as e: log('auto sleep: could not read %s: %s' % (rel, e)); continue
    if not first or now - first < DAYS * 86400: continue                        # under 7 days of pulls: never sleep a new sport
    if last and now - last < DAYS * 86400: continue                             # lines seen in the last 7 days: in season
    if empties < DAYS: continue                                                 # needs real empty checks on 7 days (a Mac that was off does not count)
    w = next_wake(md); name = rel.split('/')[-1].upper()
    msg = '😴 Season is over: no PrizePicks lines for %d days in a row, so this sport is going to sleep until %s. No pulls, no bot, nothing runs until then. It turns itself back on that day.' % (DAYS, w.strftime('%b %-d, %Y'))
    if DRY: print('WOULD SLEEP', rel, 'wake', w); continue
    open(os.path.join(ROOT, rel, 'INACTIVE'), 'w').write('Off season (auto): no PrizePicks lines for %d days, asleep since %s. WAKE: %s\nTurned off by auto sleep. The autostart turns it back on that day.\n' % (DAYS, dt.date.today(), w))
    ok = announce(rel, msg); stop(rel); log('auto sleep: %s asleep until %s (goodnight line %s)' % (rel, w, 'posted' if ok else 'NOT confirmed'))
