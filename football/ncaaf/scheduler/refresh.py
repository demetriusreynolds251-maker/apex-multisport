#!/usr/bin/env python3
"""APEX-BOARDREFRESH-2026-11-12 (owner: "Whenever I run a board I want everything refresh, I hate seeing picks that's not available").
A board command first makes sure this sport's PrizePicks lines are fresh. If the last good read is older than MAX_AGE_MIN, PrizePicks is
read again right now, every line is re-scored and changed boards are posted, THEN the board is shown. Lines PrizePicks took down or moved
drop off, the same way they do on a scheduled pull.
Safety: a refresh still waits its turn. It never calls PrizePicks within GAP_S seconds of any other Apex call (the slow-downs came from
calls about 20 seconds apart) or 60 seconds of a tennis call, and never while a slow-down pause is on. It only skips the 10 minute line
the sports keep between their scheduled pulls. Turn off: ON = False, restart the bot.
  python3 scheduler/refresh.py [window end, ISO]   -> one JSON line"""
import datetime as dt, fcntl, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as CM
ON = True
MAX_AGE_MIN = 15
GAP_S = 60
MAX_WAIT_S = 240
STATE = os.path.join(CM.CACHE, 'scheduler_state.json')
LOCK = os.path.join(CM.CACHE, 'refresh.lock')

def age_min():
    lp = (CM.read_json(STATE, {}) or {}).get('last_pp_ok'); t = CM.parse_iso(lp) if lp else None
    return (CM.now_utc() - t).total_seconds() / 60.0 if t else None

def needed():
    a = age_min(); return ON and (a is None or a >= MAX_AGE_MIN)

def _games(db, end=None):
    now = CM.now_utc(); e = CM.parse_iso(end) if end else None
    for (x,) in db.execute("select distinct start from pp_lines where start > ? and status='pre_game'", ((now - dt.timedelta(days=1)).date().isoformat(),)):
        t = CM.parse_iso(x)
        if t and t > now and (e is None or t <= e): return True
    return False

def run(end=None, why='board command'):
    """Returns dict(did, age, note). did = PrizePicks was read again and boards re-scored. note = plain reason when it could not be."""
    out = dict(did=False, age=age_min(), note=None, sport=CM.cfg().get('name'))
    if not needed(): return out
    from database import db as DBM
    from collectors import collector as CO
    db = DBM.connect()
    if not _games(db, end): out['skip'] = 'no games ahead'; return out
    if CO.pp_paused(): out['note'] = '%s: a PrizePicks slow-down pause is on, so the lines could not be read again. They were last read %s.' % (out['sport'], _ago(out['age'])); return out
    with open(LOCK, 'a+') as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)                      # two commands at once: the second waits for the first, then sees fresh lines
        if not needed(): out['did'] = True; return out
        orig = CO.pp_space
        CO.pp_space = lambda *a, **k: orig(min_gap=GAP_S, max_wait=MAX_WAIT_S, any_gap=GAP_S)
        try:
            st = CM.read_json(STATE, {}) or {}; st['last_pp'] = CM.iso(); CM.write_json(STATE, st)
            CM.log('pp_timer', 'now=%s last_pull=%s next_allowed=now decision=PULL reason=board refresh (%s), lines were %s old' % (CM.fmt_ct(CM.now_utc()), _ago(out['age']), why, _ago(out['age'])))
            CO.pull_pp(db)
        finally: CO.pp_space = orig
        if not getattr(CO, 'PP_OK', False):
            out['note'] = '%s: PrizePicks could not be read just now, so this board uses the lines from %s ago.' % (out['sport'], _ago(out['age'])); return out
        from picks import pipeline as P
        PO = CM.dmod('post'); K = CM.dmod('cards')
        s = P.score(db, trigger='board refresh')
        st = CM.read_json(STATE, {}) or {}; st['last_pp'] = st['last_pp_ok'] = st['last_scored'] = CM.iso(); st['last_mains'] = PO.post_boards(s, st.get('last_mains')); CM.write_json(STATE, st)
        try: PO.post('system', '🔄 Board refresh: lines were %s old when a board was asked for, so PrizePicks was read again.\n' % _ago(out['age']) + K.fetch_report(s, 'board refresh'), force=True)   # APEX-FETCHDETAIL-2026-11-13
        except Exception: pass
        out['did'] = True
    return out

def _ago(a):
    if a is None: return 'never'
    return '%d min' % a if a < 90 else '%.1f hours' % (a / 60.0)

if __name__ == '__main__':
    try: print(json.dumps(run(sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else None, 'cross-sport card')))
    except Exception as e:
        import traceback; CM.log('scheduler', 'refresh failed: %s' % traceback.format_exc()); print(json.dumps(dict(did=False, note='%s: refresh failed (%s), board uses the last saved lines.' % (CM.cfg().get('name'), type(e).__name__))))
