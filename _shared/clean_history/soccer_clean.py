"""APEX CLEAN HISTORY (soccer), 2026-11-10. Side store only: nothing live reads this yet.
For every finished match in the leagues Apex covers, save from ESPN's free box score: who started, who came on and when,
minutes played, and the real per-player numbers, plus the pre-game spread/total. Purpose: tell a real 0 from did-not-play.
Run: /usr/bin/python3 soccer_clean.py [START] [END]"""
import os, sys, json, time, sqlite3, urllib.request, datetime as dt, re
HERE = os.path.dirname(os.path.abspath(__file__))
LEAGUES = ['mex.1', 'uefa.europa', 'ita.1', 'ger.1', 'bra.1', 'esp.1', 'fra.1', 'usa.1', 'eng.1', 'uefa.champions', 'ned.1']
def get(u):
    for i in range(3):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=25))
        except Exception: time.sleep(2 + 2 * i)
    return {}
def minute(txt):
    m = re.match(r"(\d+)'(?:\+(\d+)')?", txt or '')
    return min(90, int(m.group(1))) if m else None
def main(start, end):
    db = sqlite3.connect(os.path.join(HERE, 'soccer_clean.sqlite'), timeout=300)
    db.executescript("""create table if not exists games(event_id text primary key, league text, game_date text, start_utc text, home text, away text, home_score real, away_score real,
        spread_home real, total real, odds_details text, saved_at text);
      create table if not exists players(event_id text, athlete_id text, player text, team text, opponent text, home integer, game_date text, league text,
        starter integer, sub_in integer, sub_out integer, in_minute integer, out_minute integer, minutes integer, played integer, position text,
        shots real, sot real, goals real, assists real, saves real, fouls real, stats_json text, primary key(event_id, athlete_id));
      create index if not exists ix_pl on players(game_date, player);
      create table if not exists done(day_league text primary key);""")
    have = set(r[0] for r in db.execute('select event_id from games'))
    n = 0; t0 = time.time()
    src = sqlite3.connect('file:' + os.path.expanduser('~/ApexSports/soccer/database/history.db') + '?mode=ro', uri=True)
    days = set()
    for (g,) in src.execute('select distinct game_date from games where game_date between ? and ?', (start, end)):
        d = dt.date.fromisoformat(g)
        for k in (0, 1): days.add((d + dt.timedelta(days=k)).isoformat())
    done = set(r[0] for r in db.execute('select day_league from done')) 
    for i, day in enumerate(sorted(days)):
        for lg in LEAGUES:
            if day + lg in done: continue
            sb = get('https://site.api.espn.com/apis/site/v2/sports/soccer/%s/scoreboard?dates=%s&limit=300' % (lg, day.replace('-', '')))
            if dt.date.fromisoformat(day) < dt.date.today() - dt.timedelta(days=3) and 'events' in sb: db.execute('insert or ignore into done values(?)', (day + lg,))
            for e in sb.get('events') or []:
                eid = str(e['id'])
                comp = (e.get('competitions') or [{}])[0]
                if eid in have or not ((comp.get('status') or e.get('status') or {}).get('type') or {}).get('completed'): continue
                tm = {t.get('homeAway'): t for t in comp.get('competitors') or []}
                if 'home' not in tm or 'away' not in tm: continue
                s = get('https://site.api.espn.com/apis/site/v2/sports/soccer/%s/summary?event=%s' % (lg, eid)); time.sleep(0.25)
                ros = s.get('rosters') or []
                if not ros: continue
                pc = (s.get('pickcenter') or [{}])[0]
                gd = e.get('date', '')[:10]
                ab = {k: (v.get('team') or {}).get('abbreviation') for k, v in tm.items()}
                for side in ros:
                    ha = side.get('homeAway'); team = ab.get(ha); opp = ab.get('away' if ha == 'home' else 'home')
                    for p in side.get('roster') or []:
                        st = {x.get('name'): x.get('value') for x in p.get('stats') or []}
                        subs = [minute(((pl.get('clock') or {}).get('displayValue'))) for pl in p.get('plays') or [] if pl.get('substitution')]
                        subs = [x for x in subs if x is not None]
                        starter = int(bool(p.get('starter'))); si = int(bool(p.get('subbedIn'))); so = int(bool(p.get('subbedOut')))
                        inm = 0 if starter else (min(subs) if si and subs else None)
                        outm = (max(subs) if so and subs else 90) if (starter or si) else None
                        played = int(bool(starter or si))
                        mins = (outm - inm) if played and inm is not None and outm is not None else (None if played else 0)
                        a = p.get('athlete') or {}
                        db.execute('insert or replace into players values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (eid, str(a.get('id')), a.get('displayName'), team, opp, int(ha == 'home'), gd, lg,
                                   starter, si, so, inm, outm, mins, played, ((p.get('position') or {}).get('abbreviation')), st.get('totalShots'), st.get('shotsOnTarget'), st.get('totalGoals'),
                                   st.get('goalAssists'), st.get('saves'), st.get('foulsCommitted'), json.dumps(st)))
                def num(x):
                    try: return float(x)
                    except Exception: return None
                db.execute('insert or replace into games values(?,?,?,?,?,?,?,?,?,?,?,?)', (eid, lg, gd, e.get('date'), ab.get('home'), ab.get('away'), num(tm['home'].get('score')), num(tm['away'].get('score')),
                           pc.get('spread'), pc.get('overUnder'), pc.get('details'), dt.datetime.utcnow().isoformat()))
                have.add(eid); n += 1
                if n % 25 == 0: db.commit()
        db.commit()
        if i % 10 == 0: print(day, i, len(days), 'games saved', n, '%.0f min' % ((time.time() - t0) / 60), flush=True)
    db.commit(); print('DONE', n, flush=True)
if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '2024-08-01', sys.argv[2] if len(sys.argv) > 2 else dt.date.today().isoformat())
