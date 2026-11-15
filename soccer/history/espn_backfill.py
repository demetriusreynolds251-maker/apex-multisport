"""APEX-ESPN-BACKFILL-2026-11-07 (owner: "fix it, don't push it away"). Root cause: our soccer history came only from
SportsGameOdds graded odds, and SGO has no per-player total shots for Liga MX (and some Europa / Serie A / Bundesliga /
Brazil games), so it graded those players 0. ESPN's free box scores have real per-player shots. For every date that has an
incomplete SGO game, pull ESPN's box scores for that league and add the players' real games, skipping any player who
already has a complete game within a day: that whole match is skipped (no double counting). Run: python3 history/espn_backfill.py"""
import os, sys, csv, glob, json, time, datetime as dt, collections as C
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import common as CM
from database import db as DBM
from grading import results as RS
from models import projection as PJ
IDX = '/Volumes/2TB Drive/SportsData/sportsgameodds/index'
PATH = {'LIGA_MX': 'soccer/mex.1', 'UEFA_EUROPA_LEAGUE': 'soccer/uefa.europa', 'IT_SERIE_A': 'soccer/ita.1', 'BUNDESLIGA': 'soccer/ger.1',
        'BR_SERIE_A': 'soccer/bra.1', 'LA_LIGA': 'soccer/esp.1', 'FR_LIGUE_1': 'soccer/fra.1', 'MLS': 'soccer/usa.1', 'EPL': 'soccer/eng.1',
        'UEFA_CHAMPIONS_LEAGUE': 'soccer/uefa.champions', 'EREDIVISIE': 'soccer/ned.1'}
def main(pause=0.4):
    db = DBM.connect(); db.execute("pragma busy_timeout=120000"); E = PJ.Engine(db)
    lg = {}
    for f in glob.glob(os.path.join(IDX, '*_events.csv')):
        L = os.path.basename(f)[:-11]
        for r in csv.DictReader(open(f, encoding='utf-8', errors='ignore')): lg[r['eventID']] = L
    want = C.defaultdict(set)
    for e, d in db.execute('select event_id, game_date from games'):
        if e in E.incomplete and lg.get(e) in PATH:
            day = dt.date.fromisoformat(d)
            for k in (0, 1): want[PATH[lg[e]]].add((day + dt.timedelta(days=k)).isoformat())
    complete = set()
    for e, pn, d in db.execute('select event_id, player_norm, game_date from player_games'):
        if e not in E.incomplete:
            day = dt.date.fromisoformat(d)
            for k in (-1, 0, 1): complete.add((pn, (day + dt.timedelta(days=k)).isoformat()))
    got = C.Counter(); t0 = time.time()
    print('dates to pull:', {p: len(v) for p, v in want.items()}, flush=True)
    for path, days in want.items():
        for d in sorted(days):
            try: j = RS.fetch('https://site.api.espn.com/apis/site/v2/sports/%s/scoreboard?dates=%s&limit=300' % (path, d.replace('-', '')))
            except Exception: got['fail'] += 1; continue
            time.sleep(pause)
            for e in j.get('events') or []:
                comp = ((e.get('competitions') or [None])[0]) or {}; tm = {t.get('homeAway'): t for t in comp.get('competitors') or [] if t}
                status = ((comp.get('status') or e.get('status') or {}).get('type') or {})
                if 'home' not in tm or 'away' not in tm or not status.get('completed'): continue
                eid = str(e['id'])
                if db.execute("select 1 from games where event_id=? and box_saved=1", (eid,)).fetchone(): got['had'] += 1; continue
                st = CM.parse_iso(e.get('date')); gd = st.astimezone(CM.CT).date().isoformat() if st else d
                g = dict(event_id=eid, home=tm['home']['team'].get('abbreviation'), away=tm['away']['team'].get('abbreviation'))
                try: rows = RS.parse_players(RS.fetch('https://site.api.espn.com/apis/site/v2/sports/%s/summary?event=%s' % (path, eid)), g); time.sleep(pause)
                except Exception: got['fail'] += 1; continue
                n = 0
                if any((CM.norm(r['player']), gd) in complete for r in rows):   # this match is already stored complete: skip it whole
                    got['skip_game'] += 1; continue
                if any((CM.norm(r['player']), gd) in complete for r in rows):   # this match is already stored complete: skip it whole
                    got['skip_game'] += 1; continue
                for r in rows:
                    pn = CM.norm(r['player'])
                    if (pn, gd) in complete: got['skip_dupe'] += 1; continue
                    db.execute('insert or replace into player_games values(?,?,?,?,?,?,?,?,?)', (eid, pn, r['player'], r['team'], r['opp'], r['home'], gd, json.dumps(r['stats']), 'espn')); n += 1
                db.execute('insert into games(event_id,game_date,start_utc,home,away,home_score,away_score,final,box_saved,source) values(?,?,?,?,?,?,?,1,1,?) on conflict(event_id) do update set box_saved=1',
                           (eid, gd, CM.iso(st) if st else None, g['home'], g['away'], RS._num(tm['home'].get('score')), RS._num(tm['away'].get('score')), 'espn'))
                got['games'] += 1; got['rows'] += n; db.commit()
            db.commit()
        print(path, dict(got), '%.0f min' % ((time.time() - t0) / 60), flush=True)
    print('done', dict(got), flush=True)
if __name__ == '__main__': main()
