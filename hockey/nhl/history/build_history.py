#!/usr/bin/env python3
"""Builds this sport's history from the SportsGameOdds download on the 2TB drive (read only):
  prop_lines   every graded player over/under line (PrizePicks line when PrizePicks had one, book lines as JSON, result)
  player_games one row per player per game with every stat the graded odds revealed (the `score` field = what the player did)
  games        scores, start times, totals and spreads
Only this sport's leagues (config['sgo']['leagues']). Nothing is shared with any other sport.
  python3 history/build_history.py [--since 2024-01-01]"""
import csv, glob, gzip, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as CM
from database import db as DBM

SGO = '/Volumes/2TB Drive/SportsData/sportsgameodds'

def sgo_stat(stat_id):
    return CM.cfg()['sgo']['stat_map'].get(stat_id)

def build(since='2023-01-01'):
    c = CM.cfg(); db = DBM.connect(); n_ev = n_pl = n_pg = 0; key2stat = {}
    for sid, sc in c['stats'].items():
        f = sc['formula']
        if len(f) == 1 and not isinstance(f[0], list): key2stat.setdefault(f[0], sid)
        if sc.get('alt'): key2stat.setdefault(sc['alt'], sid)
    for lg in c['sgo']['leagues']:
        idx = os.path.join(SGO, 'index', '%s_events.csv' % lg)
        if not os.path.exists(idx): CM.log('history', 'no index for %s' % lg); continue
        for r in csv.DictReader(open(idx)):
            if r.get('ended') != 'True' or r['start'] < since or not int(r.get('markets') or 0): continue
            f = os.path.join(SGO, r['file'])
            try: d = json.load(gzip.open(f))
            except Exception: continue
            teams = d.get('teams') or {}; home = ((teams.get('home') or {}).get('names') or {}).get('short') or (teams.get('home') or {}).get('teamID'); away = ((teams.get('away') or {}).get('names') or {}).get('short') or (teams.get('away') or {}).get('teamID')
            home_id = (teams.get('home') or {}).get('teamID'); away_id = (teams.get('away') or {}).get('teamID')
            st = CM.parse_iso(((d.get('status') or {}).get('startsAt')) or r['start']); day = st.astimezone(CM.CT).date().isoformat() if st else r['start'][:10]
            res = d.get('results') or {}; hs = _num(((res.get('game') or {}).get('home') or {}).get('points')); as_ = _num(((res.get('game') or {}).get('away') or {}).get('points'))
            odds = d.get('odds') or {}; total = spread = None
            for k, o in odds.items():
                p = k.split('-')
                if len(p) >= 5 and p[0] == 'points' and p[1] == 'all' and p[2] == 'game' and p[3] == 'ou' and p[4] == 'over': total = _num(o.get('closeBookOverUnder') or o.get('openBookOverUnder') or o.get('bookOverUnder'))
                if len(p) >= 5 and p[0] == 'points' and p[1] == 'home' and p[2] == 'game' and p[3] == 'sp' and p[4] == 'home': spread = _num(o.get('closeBookSpread') or o.get('openBookSpread') or o.get('bookSpread'))
            db.execute('insert into games(event_id,game_date,start_utc,home,away,home_score,away_score,final,box_saved,source,total,spread_home) values(?,?,?,?,?,?,?,?,1,?,?,?) on conflict(event_id) do nothing',
                       (r['eventID'], day, CM.iso(st) if st else None, home, away, hs, as_, 1, 'sgo', total, spread)); n_ev += 1
            players = d.get('players') or {}; pg = {}
            for k, o in odds.items():
                p = k.split('-')
                if len(p) < 5 or p[1] in ('all', 'home', 'away') or p[3] != 'ou' or p[4] != 'over' or p[2] != 'game': continue
                sid, ent = p[0], p[1]; pl = players.get(ent) or {}; name = pl.get('name') or ent.replace('_', ' ').title(); tid = pl.get('teamID')
                team = home if tid == home_id else away if tid == away_id else None; opp = away if team == home else home if team == away else None
                score = _num(o.get('score')); mapped = sgo_stat(sid)
                if score is not None and mapped:
                    g = pg.setdefault(ent, dict(player=name, team=team, opp=opp, home=int(team == home) if team else None, stats={})); g['stats'][mapped] = score
                by = o.get('byBookmaker') or {}; pp = by.get('prizepicks'); pre = None
                if pp and pp.get('overUnder') is not None:
                    pre = (CM.parse_iso(pp.get('lastUpdatedAt')) or st) <= st if st else None
                    books = {b: [_num(v.get('overUnder')), _num(v.get('odds')), None] for b, v in by.items() if b != 'prizepicks' and v.get('overUnder') is not None}
                    sid_ = key2stat.get(mapped)
                    if sid_ and score is not None:
                        db.execute('insert or ignore into prop_lines values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (r['eventID'], day, name, CM.norm(name), team, opp, int(team == home) if team else None, sid_, _num(pp.get('overUnder')), int(bool(pre)),
                                   json.dumps(books), _num(o.get('openBookOverUnder')), score, 'sgo')); n_pl += 1
            for ent, g in pg.items():
                db.execute('insert or replace into player_games values(?,?,?,?,?,?,?,?,?)', (r['eventID'], CM.norm(g['player']), g['player'], g['team'], g['opp'], g['home'], day, json.dumps(g['stats']), 'sgo')); n_pg += 1
        db.commit(); CM.log('history', '%s done: events %d, prop lines %d, player games %d' % (lg, n_ev, n_pl, n_pg))
    DBM.kv_set(db, 'history_built', CM.iso()); return dict(events=n_ev, prop_lines=n_pl, player_games=n_pg)
def _num(x):
    try: return float(x)
    except (TypeError, ValueError): return None

if __name__ == '__main__':
    since = sys.argv[sys.argv.index('--since') + 1] if '--since' in sys.argv else '2023-01-01'; print(build(since))
