"""APEX-COLLEGE-BACKFILL-2026-11-09 (owner, "go college matchup"): college history was thin (SportsGameOdds has few
college player props), so the matchup step had too few games per opponent. Pull ESPN's free box scores for every Division I
game in a date range and add the players' real games. A game is skipped whole if it is already saved, or if any of its
players already has a stored game within a day (no double counting with SportsGameOdds rows).
Run from the sport folder: python3 history/espn_college_backfill.py START END"""
import os, sys, json, time, datetime as dt, collections as C
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import common as CM
from database import db as DBM
from grading import results as RS
GROUP = {'football/college-football': '80', 'basketball/mens-college-basketball': '50'}

def main(start, end, pause=0.25):
    db = DBM.connect(); db.execute("pragma busy_timeout=120000")
    have = set()
    for pn, d in db.execute('select player_norm, game_date from player_games'):
        day = dt.date.fromisoformat(d)
        for k in (-1, 0, 1): have.add((pn, (day + dt.timedelta(days=k)).isoformat()))
    got = C.Counter(); t0 = time.time()
    d0, d1 = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
    for path in CM.cfg()['espn']['paths']:
        g_ = GROUP.get(path)
        day = d0
        while day <= d1:
            ds = day.isoformat(); day += dt.timedelta(days=1)
            url = 'https://site.api.espn.com/apis/site/v2/sports/%s/scoreboard?dates=%s&limit=400%s' % (path, ds.replace('-', ''), ('&groups=' + g_) if g_ else '')
            try: j = RS.fetch(url)
            except Exception: got['fail'] += 1; continue
            time.sleep(pause)
            for e in j.get('events') or []:
                comp = ((e.get('competitions') or [None])[0]) or {}; tm = {t.get('homeAway'): t for t in comp.get('competitors') or [] if t}
                status = ((comp.get('status') or e.get('status') or {}).get('type') or {})
                if 'home' not in tm or 'away' not in tm or not status.get('completed'): continue
                eid = str(e['id'])
                if db.execute("select 1 from games where event_id=? and box_saved=1", (eid,)).fetchone(): got['had'] += 1; continue
                st = CM.parse_iso(e.get('date')); gd = st.astimezone(CM.CT).date().isoformat() if st else ds
                g = dict(event_id=eid, game_date=gd, home=tm['home']['team'].get('abbreviation'), away=tm['away']['team'].get('abbreviation'))
                try: rows = RS.parse_players(RS.fetch('https://site.api.espn.com/apis/site/v2/sports/%s/summary?event=%s' % (path, eid)), g); time.sleep(pause)
                except Exception: got['fail'] += 1; continue
                if not rows: got['empty'] += 1; continue
                if any((CM.norm(r['player']), gd) in have for r in rows): got['skip_game'] += 1; continue
                for r in rows:
                    db.execute('insert or replace into player_games values(?,?,?,?,?,?,?,?,?)', (eid, CM.norm(r['player']), r['player'], r['team'], r['opp'], r['home'], gd, json.dumps(r['stats']), 'espn'))
                db.execute('insert into games(event_id,game_date,start_utc,home,away,home_score,away_score,final,box_saved,source) values(?,?,?,?,?,?,?,1,1,?) on conflict(event_id) do update set box_saved=1',
                           (eid, gd, CM.iso(st) if st else None, g['home'], g['away'], RS._num(tm['home'].get('score')), RS._num(tm['away'].get('score')), 'espn'))
                got['games'] += 1; got['rows'] += len(rows)
            db.commit()
            if day.day == 1 or day > d1: print(ds, dict(got), '%.0f min' % ((time.time() - t0) / 60), flush=True)
    print('done', start, end, dict(got), flush=True)
    return dict(got)

if __name__ == '__main__': main(sys.argv[1], sys.argv[2])
