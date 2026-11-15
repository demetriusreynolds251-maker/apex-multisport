#!/usr/bin/env python3
"""NIGHTLY NBA RECHECK (owner, 11/9/2026: "Go nightly recheck").
ESPN corrects box scores the day after a game (a rebound, an assist, a point). The bot saved each box score once at
4 AM and never looked again, so 327 results sat off by one (found 11/9). Every night this re-reads the last DAYS days
of finished NBA games from ESPN's public summary, fixes any changed number in both box-score stores, regrades the
tracker picks those numbers touch, and re-settles any slip whose leg changed. ESPN only. Never calls PrizePicks.
Writes data/processed/nba_recheck_last.json (read by the line vault's morning #system line).
  python3 code/nba_recheck.py [days]      Undo: remove its line from ~/openclaw_jobs/line_vault.sh
"""
import datetime as dt, json, os, sqlite3, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import espn_results as ER, espn_box_full as FB, score_board as SB, bball_tracker as BT
from zoneinfo import ZoneInfo
ROOT = FB.ROOT; CT = ZoneInfo('America/Chicago'); DAYS = 3
STATE = os.path.join(ROOT, 'data', 'processed', 'nba_recheck_last.json')
TRACKER = os.path.join(ROOT, 'data', 'processed', 'bball_tracker.sqlite')

def recheck(days=DAYS, pause=1.0):
    now = dt.datetime.now(dt.timezone.utc); ts = now.isoformat(timespec='seconds')
    since = (now.astimezone(CT).date() - dt.timedelta(days=days)).isoformat()
    out = dict(run_at=ts, since=since, games=0, failed=0, box_fixed=0, picks_fixed=0, flipped=0, slips_changed=0, examples=[])
    e = sqlite3.connect(ER.ESPN_DB, timeout=60); e.row_factory = sqlite3.Row; full = FB.connect()
    games = [dict(r) for r in e.execute('select event_id, game_date, home_team, away_team from games where final=1 and box_saved=1 and game_date>=? order by game_date', (since,))]
    touched = set()
    for g in games:
        try: rows = FB.parse(FB.fetch(FB.BASE + 'summary?event=' + g['event_id']), g, ts)
        except Exception: out['failed'] += 1; time.sleep(pause); continue
        time.sleep(pause)
        if len(rows) < 10: out['failed'] += 1; continue
        out['games'] += 1
        full.executemany('insert or replace into player_box values(%s)' % ','.join('?' * 23), rows)
        full.execute('insert or replace into games_saved values(?,?,?,?)', (g['event_id'], g['game_date'], len(rows), ts))
        for r in rows:
            ev, aid, player, team, mins, pts, reb, ast, fgm = r[0], r[2], r[3], r[5], r[9], r[10], r[11], r[12], r[17]
            o = e.execute('select minutes, points, rebounds, assists, fgm from player_games where event_id=? and athlete_id=?', (ev, aid)).fetchone()
            if o is None or pts is None: continue
            new = (pts, reb, ast, fgm); old = (o['points'], o['rebounds'], o['assists'], o['fgm'])
            if any(a is not None and b is not None and abs(a - b) > 1e-9 for a, b in zip(new, old)) or any((a is None) != (b is None) for a, b in zip(new, old)):
                e.execute('update player_games set minutes=?, points=?, rebounds=?, assists=?, fgm=? where event_id=? and athlete_id=?', (mins, pts, reb, ast, fgm, ev, aid))
                out['box_fixed'] += 1; touched.add(g['game_date'])
                if len(out['examples']) < 5: out['examples'].append('%s %s: %s -> %s (pts, reb, ast, fgm)' % (player, g['game_date'], old, new))
    full.commit(); e.commit()
    if touched:
        t = sqlite3.connect(TRACKER, timeout=60); t.row_factory = sqlite3.Row; changed = set()
        for p in t.execute("select * from picks where status in ('win','loss','push') and upper(league)='NBA' and game_date in (%s)" % ','.join('?' * len(touched)), sorted(touched)).fetchall():
            st, v = ER.grade_pick(e, SB.norm, p['player'], p['team'], p['game_date'], p['stat'], p['line'], p['side'])
            if st in ('open', 'nostat') or (v == p['result'] and st == p['status']): continue
            out['picks_fixed'] += 1
            if st != p['status']: out['flipped'] += 1; changed.add(p['pick_key'])
            t.execute('update picks set status=?, result=? where pick_key=?', (st, v, p['pick_key']))
            t.execute("update results set status=?, value=?, source='espn corrected box', graded_at=? where pick_key=?", (st, v, ts, p['pick_key']))
        if changed:   # a settled slip with a changed leg is settled again by the tracker's own rule (not re-posted: settled_posted stays)
            for s in t.execute("select id, legs_json, status from slips where status!='pending'").fetchall():
                if changed & set(json.loads(s['legs_json'])):
                    t.execute("update slips set status='pending' where id=?", (s['id'],)); out['slips_changed'] += 1
            BT.settle_slips(t, ts)
        t.commit(); t.close()
    e.close(); full.close()
    json.dump(out, open(STATE + '.tmp', 'w'), indent=1); os.replace(STATE + '.tmp', STATE)
    return out

if __name__ == '__main__':
    print(json.dumps(recheck(int(sys.argv[1]) if len(sys.argv) > 1 else DAYS), indent=1))
