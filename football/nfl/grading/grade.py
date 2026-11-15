#!/usr/bin/env python3
"""Grades this sport's open picks from player_games (ESPN box scores). Win / loss / push (on the line) / void (did not play).
Updates picks.status, result_value, hit, graded_at. Then the calibration summary is rebuilt by reports/report.py.
  python3 grading/grade.py"""
import datetime as dt, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as CM
from database import db as DBM
from models.projection import stat_value

def grade(db=None):
    db = db or DBM.connect(); c = CM.cfg(); n = dict(win=0, loss=0, push=0, void=0, open=0)
    try:   # APEX-ONELINE-2026-11-12: extra copies of one line are never graded
        from tracking import dedupe as DD
        DD.clean(db)
    except Exception as e: CM.log('grading', 'one line failed: %s' % e)
    for p in db.execute("select * from picks where status='open' and game_date <= ?", (CM.ct_date(),)).fetchall():
        g = db.execute("select event_id, final, box_saved from games where game_date=? and (home=? or away=?) and source='espn'", (p['game_date'], p['team'], p['team'])).fetchone()
        if not g:
            # team abbreviations differ between PrizePicks and ESPN: find the finished game of that day the player appears in
            g = db.execute("select g.event_id, g.final, g.box_saved from games g join player_games pg on pg.event_id=g.event_id where g.game_date=? and pg.player_norm=? and pg.source='espn' and g.source='espn'", (p['game_date'], p['player_norm'])).fetchone()
        if not g or not g['final'] or not g['box_saved']:
            if g is None and any(db.execute("select 1 from games where game_date=? and source='espn' and final=1 and box_saved=1", (p['game_date'],)).fetchall()) and p['game_date'] < (CM.now_ct().date() - dt.timedelta(days=1)).isoformat():
                db.execute("update picks set status='void', graded_at=? where pick_key=?", (CM.iso(), p['pick_key'])); n['void'] += 1; continue
            n['open'] += 1; continue
        pg = db.execute("select stats_json from player_games where event_id=? and player_norm=? and source='espn'", (g['event_id'], p['player_norm'])).fetchone()
        if not pg: status, val = 'void', None
        else:
            st = json.loads(pg['stats_json'] or '{}'); val = stat_value(st, p['stat']) if p['stat'] in c['stats'] else None
            if val is None and p['stat'] == 'anytime_td' and st.get('_played') and any(st.get(k) is not None for k in ('rushing_tds', 'receiving_tds')):
                val = float(st.get('rushing_tds') or 0) + float(st.get('receiving_tds') or 0)   # APEX-GRADINGGAPS-2026-11-13: a receiver with no rush (or a back with no catch) has only one TD field; the missing one is 0, not "no stat"
            if st.get('appearances') == 0 and not any(v for k, v in st.items() if k not in ('_played', 'appearances')): status, val = 'void', None   # APEX-APPEARED-2026-11-12: never came on
            elif not st.get('_played') and not any(v for k, v in st.items() if k != '_played'): status = 'void'
            elif val is None: status = 'void'
            elif val == p['line']: status = 'push'
            else: status = 'win' if (val > p['line']) == (p['side'] == 'MORE') else 'loss'
        db.execute('update picks set status=?, result_value=?, hit=?, graded_at=? where pick_key=?', (status, val, 1 if status == 'win' else 0 if status == 'loss' else None, CM.iso(), p['pick_key'])); n[status] += 1
    db.commit(); CM.log('grading', 'graded: %s' % n); return n

if __name__ == '__main__': print(grade())
