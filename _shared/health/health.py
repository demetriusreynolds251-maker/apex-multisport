#!/usr/bin/env python3
"""Apex health report: one block per sport (9 sports + Apex Basketball). Read only, except the report files it writes.
  python3 health.py            print the report and write ~/ApexSports/_shared/health/latest.md + latest.json
  python3 health.py --post     also drop each sport's own block into that sport's #<prefix>-system outbox (basketball: its bot posts it)
Tennis is not read or touched."""
import os, sys, json, re, glob, sqlite3, subprocess, datetime as dt, time
ROOT = os.path.expanduser('~/ApexSports'); OUT = os.path.join(ROOT, '_shared', 'health')
SPORTS = [('nfl', 'football/nfl'), ('cfb', 'football/ncaaf'), ('nhl', 'hockey/nhl'), ('cbb', 'basketball/ncaab'), ('wnba', 'basketball/wnba'),
          ('mlb', 'baseball/mlb'), ('soccer', 'soccer'), ('afl', 'afl'), ('rugby', 'rugby')]
NOW = time.time(); NOWD = dt.datetime.now().astimezone()
PS = subprocess.run(['ps', '-axww', '-o', 'pid=,args='], capture_output=True, text=True).stdout
OK, WARN, BAD = '✅', '⚠️', '❌'
def pid_alive(pidfile, needle=None):
    try: pid = int(open(pidfile).read().strip())
    except Exception: return False
    for l in PS.splitlines():
        p = l.strip().split(None, 1)
        if p and p[0] == str(pid): return (needle in p[1]) if needle and len(p) > 1 else True
    return False
def proc(needle): return any(needle in l for l in PS.splitlines())
def age_h(ts):
    if not ts: return None
    try: t = dt.datetime.fromisoformat(str(ts).replace('Z', '+00:00')).timestamp()
    except ValueError: return None
    return (NOW - t) / 3600
def ago(h): return 'never' if h is None else ('%d min ago' % (h * 60) if h < 1 else '%.1f h ago' % h)
def errors_24h(logdir):
    n = 0; last = None
    for f in glob.glob(os.path.join(logdir, '*.log')):
        if os.path.getmtime(f) < NOW - 86400: continue
        for line in open(f, errors='replace').read().splitlines()[-4000:]:
            m = re.match(r'^(\d\d)/(\d\d) (\d\d):(\d\d):(\d\d) ', line)
            if not m or not re.search(r'Traceback|[Ff]ailed|Error|FAILED|429', line): continue
            if re.search(r'failures?\b.*healthy|failed\': 0|failed: 0', line): continue
            t = dt.datetime(NOWD.year, int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))).timestamp()
            if NOW - t <= 86400: n += 1; last = line[:150]
    return n, last
def sport_block(pre, rel):
    d = os.path.join(ROOT, rel); L = []; J = dict(sport=pre); warn = 0
    cfg = json.load(open(os.path.join(d, 'config/sport.json'))); name = cfg.get('name', pre.upper()); emoji = cfg.get('emoji', '')
    if os.path.exists(os.path.join(d, 'INACTIVE')):
        why = open(os.path.join(d, 'INACTIVE')).read().strip().splitlines()[0]
        J.update(inactive=True, reason=why, warnings=0); return '%s **%s** ⏸ Inactive\n⏸ %s' % (emoji, name, why), J
    st = {}
    try: st = json.load(open(os.path.join(d, 'cache/scheduler_state.json')))
    except Exception: pass
    leagues = (cfg.get('prizepicks') or {}).get('leagues') or {}
    db = sqlite3.connect('file:%s?mode=ro' % os.path.join(d, 'database/history.db'), uri=True)
    def q1(sql, a=()):
        try: return db.execute(sql, a).fetchone()
        except Exception: return None
    sched = pid_alive(os.path.join(d, 'logs/scheduler.pid'), 'scheduler.py'); loop = pid_alive(os.path.join(d, 'logs/start.pid'))
    bot = proc('ApexSports/%s/discord/bot.py' % rel)
    def add(ok, label, detail=''):
        nonlocal warn
        mark = OK if ok is True else (WARN if ok is None else BAD)
        if ok is not True: warn += 1
        L.append('%s %s%s' % (mark, label, (' · ' + detail) if detail else '')); J[label] = dict(ok=ok, detail=detail)
    add(sched and loop, 'Scheduler', 'running' if sched else 'NOT running')
    add(bot, 'Discord', 'bot running' if bot else 'bot NOT running')
    lp, lok = st.get('last_pp'), st.get('last_pp_ok') or (q1("select v from kv where k='pp_last_pull'") or [None])[0]
    off = int((q1("select v from kv where k='pp_zero_streak'") or [0])[0] or 0) >= 3
    if not leagues: add(None, 'PrizePicks', 'unsupported: PrizePicks has no league for this sport, pulls are off')
    else:
        calls = []
        try: calls = [json.loads(l) for l in open(os.path.join(ROOT, '_shared/pp_calls.jsonl')) if '"sport": "%s"' % pre in l or "'sport': '%s'" % pre in l or '"%s"' % pre in l]
        except Exception: pass
        calls = [c for c in calls if c.get('sport') == pre]; last_code = calls[-1].get('code') if calls else None
        pause = {}
        try: pause = json.load(open(os.path.join(ROOT, '_shared/pp_cooldown.json')))
        except Exception: pass
        paused = float(pause.get('until') or 0) > NOW
        det = 'last pull %s, last good pull %s, every %d min' % (ago(age_h(lp)), ago(age_h(lok)), cfg['schedule']['pp_every_min'])
        if paused: add(None, 'PrizePicks', 'shared pause on (slow-down), ' + det)
        elif str(last_code) == '429' and (age_h(calls[-1].get('ts')) or 99) < 3: add(None, 'PrizePicks', 'slow-down (429) in the last 3 h, ' + det)
        elif off: add(True, 'PrizePicks', 'off season, checking once a day, ' + det)
        else: add(True, 'PrizePicks', det)
    eh = age_h((q1("select v from kv where k='espn_last_pull'") or [None])[0])
    w0, w1 = cfg['schedule']['window']; hm = NOWD.astimezone(dt.timezone(dt.timedelta(hours=-6))).strftime('%H:%M') if False else dt.datetime.now(dt.timezone.utc).astimezone(__import__('zoneinfo').ZoneInfo('America/Chicago')).strftime('%H:%M')
    inwin = w0 <= hm <= w1
    if not sched: add(False, 'ESPN feed', 'scheduler down')
    elif not inwin: add(True, 'ESPN feed', 'outside its %s-%s window, last pull %s' % (w0, w1, ago(eh)))
    elif (int(hm[:2]) * 60 + int(hm[3:5])) - (int(w0[:2]) * 60 + int(w0[3:5])) < 45 and (eh is None or eh >= 1.5):   # APEX-QUIETOVERNIGHT-2026-11-08: window just opened, first pull not due yet
        add(True, 'ESPN feed', 'window opened at %s, first pull of the day due, last pull %s' % (w0, ago(eh)))
    else: add(eh is not None and eh < 1.5, 'ESPN feed', 'last pull %s (every 30 min)' % ago(eh))
    gl = [l for l in open(os.path.join(d, 'logs/grading.log'), errors='replace').read().splitlines() if 'graded:' in l] if os.path.exists(os.path.join(d, 'logs/grading.log')) else []
    gfail = [l for l in open(os.path.join(d, 'logs/scheduler.log'), errors='replace').read().splitlines() if 'grade failed' in l or 'results failed' in l] if os.path.exists(os.path.join(d, 'logs/scheduler.log')) else []
    add(bool(gl) and not (gfail and gfail[-1][:14] > gl[-1][:14]), 'Grading', 'last run %s' % (gl[-1][:14] if gl else 'never'))
    pend = 0
    try:
        sys.path.insert(0, d); cwd = os.getcwd(); os.chdir(d)
        for m in [m for m in list(sys.modules) if m.split('.')[0] in ('common', 'tracking', 'database', 'models')]: del sys.modules[m]
        import importlib; TB = importlib.import_module('tracking.boards'); rec = TB.record()
        pend = sum(v['pending'] for v in rec.values()); won = sum(v['won'] for v in rec.values()); lost = sum(v['lost'] for v in rec.values())
        L.append('🧾 Boards: %d won, %d lost, %d pending (all boards, all days)' % (won, lost, pend)); J['boards_record'] = dict(won=won, lost=lost, pending=pend)
    except Exception as e: add(None, 'Board tracker', 'could not read: %s' % type(e).__name__)
    finally:
        os.chdir(cwd); sys.path.remove(d)
    if cfg.get('espn', {}).get('injuries', True):
        ih = age_h((q1('select max(fetched_at) from injuries') or [None])[0]); add(True if ih is not None and ih < 26 else None, 'Injuries', 'ESPN, last change seen %s' % ago(ih))
    else: add(None, 'Injuries', 'missing: no free injury feed for this league (cards say so)')
    nb = (q1('select count(*) from book_lines') or [0])[0]
    add(True if nb else None, 'Books', '%d book lines' % nb if nb else 'none: Odds API free plan covers NBA only')
    lm = st.get('last_mains') or {}; size = {k: v['size'] for k, v in cfg['boards'].items()}
    full = [k for k, v in lm.items() if v and v != ['SHORT'] and len(v) >= size.get(k, 99)]; short = [k for k in size if k not in full]
    if not leagues: L.append('📋 Boards: none (no PrizePicks league)')
    else: L.append('📋 Boards: %d of %d full%s' % (len(full), len(size), (' · not enough picks: ' + ', '.join(cfg['boards'][k]['title'].title() for k in short)) if short else ''))
    n, last = errors_24h(os.path.join(d, 'logs')); add(True if n == 0 else None, 'Errors last 24 h', '%d%s' % (n, (' · last: ' + last) if last else ''))
    head = '%s **%s** %s' % (emoji, name, OK if warn == 0 else WARN); J['warnings'] = warn
    return '\n'.join([head] + L), J
def basketball_block():
    d = os.path.join(ROOT, 'basketball'); L = []; J = dict(sport='nba'); warn = 0
    def add(ok, label, detail=''):
        nonlocal warn
        mark = OK if ok is True else (WARN if ok is None else BAD)
        if ok is not True: warn += 1
        L.append('%s %s%s' % (mark, label, (' · ' + detail) if detail else '')); J[label] = dict(ok=ok, detail=detail)
    bot = proc('ApexSports/basketball/discord/bot.py'); add(bot, 'Discord + scheduler', 'bot running' if bot else 'bot NOT running')
    wd = {}
    try: wd = json.load(open(os.path.join(d, 'logs/watchdog.json')))
    except Exception: pass
    wh = age_h(wd.get('_last_check')); add(wh is not None and wh < 0.1, 'Watchdog', 'last check %s' % ago(wh))
    for nm, short in (('line collector (PrizePicks)', 'Line collector'), ('injury collector (ESPN)', 'Injury collector'), ('book line collector (The Odds API)', 'Book line collector')):
        e = wd.get(nm) or {}; add(bool(e.get('alive')), short, 'pid %s, last activity %s, restarts %d' % (e.get('pid'), ago(age_h(e.get('last_activity'))), e.get('restarts', 0)))
    bl = open(os.path.join(d, 'logs/bball_bot.log'), errors='replace').read().splitlines()
    g = [l for l in bl if 'Graded' in l or 'Grading failed' in l]
    db = sqlite3.connect('file:%s?mode=ro' % os.path.join(d, 'data/processed/bball_tracker.sqlite'), uri=True)
    lastg = db.execute("select max(graded_at) from picks").fetchone()[0]; stuck = db.execute("select count(*) from picks where status='open' and league='NBA' and game_date < date('now','-2 day')").fetchone()[0]
    failed_last = bool(g) and 'failed' in g[-1] and (not lastg or age_h(lastg) > 28)   # APEX-NBAGRADEALERT-2026-11-13: NBA grades once a day at 4 AM CT and only logs failures, so 20 h fired every night after midnight; 28 h = a day really missed
    add(not failed_last and not stuck, 'Grading', 'last graded %s, %d picks stuck' % (ago(age_h(lastg)), stuck))
    pend = db.execute("select count(*) from slips where status='pending'").fetchone()[0]; L.append('🧾 Pending slips: %d (they settle after their last game)' % pend); J['pending_slips'] = pend
    ih = age_h(dt.datetime.fromtimestamp(os.path.getmtime(os.path.join(d, 'logs/injury_collector.log')), dt.timezone.utc).isoformat()) if os.path.exists(os.path.join(d, 'logs/injury_collector.log')) else None
    add(ih is not None and ih < 1.5 or not (8 <= NOWD.hour <= 23), 'Injuries', 'ESPN, collector log %s' % ago(ih))
    bk = os.path.exists(os.path.join(d, 'secrets/odds_api_key.txt')) and os.path.getsize(os.path.join(d, 'secrets/odds_api_key.txt')) > 0
    bh = age_h(dt.datetime.fromtimestamp(os.path.getmtime(os.path.join(d, 'logs/book_lines.log')), dt.timezone.utc).isoformat()) if os.path.exists(os.path.join(d, 'logs/book_lines.log')) else None
    add(True if bk and bh is not None and bh < 26 else None, 'Books', ('Odds API, last pull %s' % ago(bh)) if bk else 'no Odds API key')
    n, last = errors_24h(os.path.join(d, 'logs')); add(True if n == 0 else None, 'Errors last 24 h', '%d%s' % (n, (' · last: ' + last) if last else ''))
    head = '🏀 **Apex Basketball (NBA)** %s' % (OK if warn == 0 else WARN); J['warnings'] = warn
    return '\n'.join([head] + L), J
def main():
    os.makedirs(OUT, exist_ok=True); blocks = []; js = []
    for fn, args in [(basketball_block, ())] + [(sport_block, s) for s in SPORTS]:
        try: t, j = fn(*args)
        except Exception as e: t, j = '%s %s: health check failed: %s: %s' % (BAD, args[0] if args else 'nba', type(e).__name__, e), dict(error=str(e))
        blocks.append(t); js.append(j)
    stamp = NOWD.strftime('%a %-m/%-d %-I:%M %p CT')
    txt = '🩺 **APEX HEALTH** · %s\n\n' % stamp + '\n\n'.join(blocks)
    open(os.path.join(OUT, 'latest.md'), 'w').write(txt); json.dump(dict(at=NOWD.isoformat(), sports=js), open(os.path.join(OUT, 'latest.json'), 'w'), indent=1)
    open(os.path.join(OUT, 'history_%s.md' % NOWD.strftime('%Y-%m-%d_%H%M')), 'w').write(txt)
    print(txt)
    if '--post' in sys.argv:
        why = sys.argv[sys.argv.index('--post') + 1] if len(sys.argv) > sys.argv.index('--post') + 1 else 'daily'
        for (pre, rel), b in zip(SPORTS, blocks[1:]):
            if os.path.exists(os.path.join(ROOT, rel, 'INACTIVE')): continue
            ob = os.path.join(ROOT, rel, 'cache/outbox'); os.makedirs(ob, exist_ok=True)
            name = '%d_health_%s.json' % (int(time.time() * 1000), pre)
            json.dump(dict(channel='system', text='🩺 Health (%s) · %s\n%s' % (why, stamp, b), created=NOWD.isoformat()), open(os.path.join(ob, name), 'w'))
        open(os.path.join(ROOT, 'basketball/logs/health_post.txt'), 'w').write('🩺 Health (%s) · %s\n%s' % (why, stamp, blocks[0]))
if __name__ == '__main__': main()
