#!/usr/bin/env python3
"""Scheduler for this sport. Runs forever (python3 scheduler/scheduler.py --loop), checks every minute, no manual steps.
Pulls (times in config['schedule'], CT):
  morning        PrizePicks + ESPN schedule/injuries + books (when a key exists), then score + post boards
  board_open     same, when PrizePicks usually opens the day's board
  hourly         PrizePicks every N minutes inside the board window; score + post boards on any change
  line_movement  injuries every 30 min inside the window
  pre_game       PrizePicks + injuries + books 60 min before the first start of the day
  final_lock     PrizePicks + injuries 15 min before the first start
  results        ESPN results every hour from the first final until grading
  grading        grade picks (default 04:00), post slips / results line
  report         daily report (default 09:00); weekly Monday; monthly on the 1st; season line in the monthly
  refit          weekly backtest re-fit (Sunday, config['schedule']['refit'])
Every pull writes one line to #<prefix>-system. Silence is a bug."""
import datetime as dt, json, os, sys, time, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as CM
from database import db as DBM
from collectors import collector as CO
from picks import pipeline as P
from grading import results as R, grade as G
from reports import report as RP
from tracking import boards as TB
PO = CM.dmod("post"); K = CM.dmod("cards")

STATE = os.path.join(CM.CACHE, 'scheduler_state.json')
_S = {}
MONO = ('last_pp', 'last_pp_ok')          # pull times only ever move forward, whatever copy of the state is being saved
def load(): return CM.read_json(STATE, {}) or {}
def save(s):
    cur = load()
    for k in MONO:
        a, b = cur.get(k), s.get(k)
        if a and (not b or str(a) > str(b)): s[k] = a
    CM.write_json(STATE, s)
def _mark_pp(key='last_pp'):
    s = load(); s[key] = CM.iso(); CM.write_json(STATE, s)
def timer_log(decision, reason, last=None, nxt=None, force=False):
    """Audit line in logs/pp_timer.log: now, last pull, next allowed pull, decision, reason. WAIT lines at most every 30 min."""
    if decision == 'WAIT' and not force:
        lw = _S.get('wait_logged')
        if lw and (CM.now_utc() - lw).total_seconds() < 1800 and _S.get('wait_last') == last: return
        _S['wait_logged'] = CM.now_utc(); _S['wait_last'] = last
    CM.log('pp_timer', 'now=%s last_pull=%s next_allowed=%s decision=%s reason=%s' % (CM.fmt_ct(CM.now_utc()), CM.fmt_ct(last) if last else 'never', CM.fmt_ct(nxt) if nxt else 'now', decision, reason))
def pp_gate(gap_s, why):
    """Reads the saved last pull time from disk (never memory). True when gap_s seconds have passed since the last pull attempt."""
    lp = load().get('last_pp'); last = CM.parse_iso(lp) if lp else None
    if not last: return True, None, None
    nxt = last + dt.timedelta(seconds=gap_s)
    return CM.now_utc() >= nxt, last, nxt
def hm(t): return t.strftime('%H:%M')

def guard(name, fn, *a):
    if name == 'pp':
        gap = float(CM.cfg()['schedule'].get('pp_min_gap_min', 30)) * 60
        ok, last, nxt = pp_gate(gap, 'min gap')
        if not ok:
            timer_log('BLOCK', 'scheduled pull asked within %d min of the last pull' % (gap // 60), last, nxt); return None
        timer_log('PULL', _S.pop('why', 'scheduled pull'), last, nxt); _mark_pp()
    try:
        r = fn(*a)
        if name == 'pp' and getattr(CO, 'PP_OK', True): _mark_pp('last_pp_ok')   # skipped / paused / off season is not a good pull
        return r
    except Exception as e:
        CM.log('scheduler', '%s failed: %s\n%s' % (name, e, traceback.format_exc())); PO.post('alerts', '⚠️ %s failed: %s: %s' % (name, type(e).__name__, str(e)[:200])); return None

def _quiet(s, trigger, added):
    """APEX-FETCHDETAIL-2026-11-13: one #system line for an interval read with nothing to score (never silent)."""
    try:
        t = K.quiet_report(trigger, added, s)
        if t: PO.post('system', t, force=True); save(s)
    except Exception as e: CM.log('scheduler', 'quiet line failed: %s' % e)

def rescore(db, s, trigger):
    res = guard('score', P.score, db, None, trigger)
    if not res: return
    PO.post('system', K.fetch_report(res, trigger), force=True); s['last_mains'] = PO.post_boards(res, s.get('last_mains')); s['last_scored'] = CM.iso(); save(s)
    if trigger in ('morning', 'board_open', 'pre_game') and res['n_scored']: PO.post('picks', K.tier_report(res))


def _free():
    """APEX-FREEDATA-2026-11-06: our own free-data collector (collectors/free_data.py). Data only, no pick change.
    Runs in the background so a slow download never holds up a PrizePicks pull. Posts one line to system."""
    import threading
    def go():
        try:
            from collectors import free_data as FD
            PO.post('system', FD.run())
        except Exception as e:
            CM.log('scheduler', 'free data failed: %s' % e); PO.post('system', '⚠️ free data failed: %s' % type(e).__name__)
    threading.Thread(target=go, daemon=True).start()

def _nflbox():
    """APEX-NFLWEEKLY-2026-11-08 (owner, "Do #5"): Tuesdays, re-pull the official NFL box scores (collectors/nfl_box_weekly.py)
    in the background and post one line to system."""
    import threading
    def go():
        try:
            from collectors import nfl_box_weekly as NB
            PO.post('system', NB.run())
        except Exception as e:
            CM.log('scheduler', 'nfl box weekly failed: %s' % e); PO.post('system', '⚠️ weekly NFL box scores failed: %s' % type(e).__name__)
    threading.Thread(target=go, daemon=True).start()

def _honest_season():
    """APEX-SEASONHONEST-2026-11-10: every morning, honest numbers from this season's real saved PrizePicks lines (the line vault). Posts one line."""
    import threading
    def go():
        try:
            from tracking import season_honest as SH
            msg = SH.build(); PO.post('system', msg or "🧪 This season's real lines: nothing graded yet.")
        except Exception as e:
            CM.log('scheduler', 'season honest failed: %s' % e); PO.post('system', '⚠️ season honest numbers failed: %s' % type(e).__name__)
    threading.Thread(target=go, daemon=True).start()

def _honest():
    """APEX-HONEST-2026-11-07: rebuild the honest numbers in the background when the engine changed or weekly."""
    import threading
    def go():
        try:
            from tracking import honest as HN
            msg = HN.maybe_build()
            if msg: PO.post('system', msg)
        except Exception as e:
            CM.log('scheduler', 'honest build failed: %s' % e); PO.post('system', '⚠️ honest numbers failed: %s' % type(e).__name__)
    threading.Thread(target=go, daemon=True).start()

def first_start_today(db):
    now = CM.now_utc()   # APEX-STARTTIME-2026-11-07: compare real times, not Eastern text vs UTC text
    xs = [CM.parse_iso(x[0]) for x in db.execute("select distinct start from pp_lines where start > ? and status='pre_game'", ((now - dt.timedelta(days=1)).date().isoformat(),))]
    xs = [x for x in xs if x and x > now]
    return min(xs) if xs else None

def tick(db, s):
    c = CM.cfg(); sc = c['schedule']; now = CM.now_ct(); today = now.date().isoformat(); t = hm(now); fired = s.setdefault('fired', {})
    def once(key, cond, fn):
        if cond and fired.get(key) != today: fired[key] = today; save(s); fn()
    once('morning', t >= sc['morning'], lambda: (guard('pp', CO.pull_pp, db), guard('espn', CO.pull_espn, db), guard('books', CO.pull_books, db), rescore(db, s, 'morning')))
    once('honest_season', t >= sc['morning'], _honest_season)   # APEX-SEASONHONEST-2026-11-10
    once('honest_build', t >= sc['morning'], _honest)   # APEX-HONEST-2026-11-07
    once('free_morning', t >= sc['morning'], _free)   # APEX-FREEDATA-2026-11-06
    if now.weekday() == 1: once('nflbox_weekly', t >= sc['morning'], _nflbox)   # APEX-NFLWEEKLY-2026-11-08 (Tuesdays)
    once('board_open', t >= sc['board_open'], lambda: (guard('pp', CO.pull_pp, db), guard('espn', CO.pull_espn, db), rescore(db, s, 'board_open')))
    if sc['window'][0] <= t <= sc['window'][1]:
        due, last, nxt = pp_gate(sc['pp_every_min'] * 60, 'interval')
        if due:
            _S['why'] = 'every %d min interval reached' % sc['pp_every_min']
            added = guard('pp', CO.pull_pp, db)
            if added: rescore(db, s, 'new lines')
            else: _quiet(s, 'new lines', added)   # APEX-FETCHDETAIL-2026-11-13: a pull that finds nothing still posts one line
        else: timer_log('WAIT', 'every %d min interval not reached' % sc['pp_every_min'], last, nxt)
        lasti = CM.parse_iso(s.get('last_inj')) if s.get('last_inj') else None
        if not lasti or (CM.now_utc() - lasti).total_seconds() >= 30 * 60:
            s['last_inj'] = CM.iso(); save(s); guard('espn', CO.pull_espn, db)
    fs = first_start_today(db)
    if fs:
        mins = (fs - CM.now_utc()).total_seconds() / 60
        once('free_pre', 0 < mins <= 90, _free)   # APEX-FREEDATA-2026-11-06
        once('pre_game', 0 < mins <= 60, lambda: (guard('pp', CO.pull_pp, db), guard('espn', CO.pull_espn, db), guard('books', CO.pull_books, db), rescore(db, s, 'pre_game')))
        once('final_lock', 0 < mins <= 15, lambda: (guard('pp', CO.pull_pp, db), guard('espn', CO.pull_espn, db), rescore(db, s, 'final_lock')))
        for extra in sc.get('book_pulls', []): once('books_' + extra, t >= extra, lambda: guard('books', CO.pull_books, db))
    lastr = CM.parse_iso(s.get('last_results')) if s.get('last_results') else None
    if (t >= sc['results_from'] or t < sc['grading']) and (not lastr or (CM.now_utc() - lastr).total_seconds() >= 3600):
        s['last_results'] = CM.iso(); save(s); got = guard('results', R.update, db)
        if got and got.get('new_box'): n = guard('grade', G.grade, db); PO.post('system', '🧾 %d new box scores, graded: %s' % (got['new_box'], n))
    once('grading', t >= sc['grading'], lambda: (guard('results', R.update, db, [(now.date() - dt.timedelta(days=1)).isoformat(), today]), PO.post('pnl', '📒 ' + str(guard('grade', G.grade, db))), PO.post('pnl', guard('report', RP.build, 'daily')), PO.post('pnl', guard('boards', TB.boards_text, 3))))
    once('report', t >= sc['report'], lambda: (PO.post('general', status_line(db)), now.weekday() == 0 and PO.post('pnl', guard('report', RP.build, 'weekly')), now.day == 1 and PO.post('pnl', guard('report', RP.build, 'monthly')), now.day == 1 and PO.post('pnl', guard('report', RP.build, 'season'))))
    if now.weekday() == 6: once('refit', t >= sc.get('refit', '05:00'), lambda: refit())
    save(s)

def refit():
    from backtesting import backtest as BT
    txt = guard('refit', BT.run, False)
    if txt: PO.post('learning', '🧪 Weekly re-fit done. ' + txt.split('\n')[2][:300] + ' Full report in reports/.')

def status_line(db):
    c = CM.cfg(); y = (CM.now_ct().date() - dt.timedelta(days=1)).isoformat()
    rows = db.execute("select status from picks where game_date=? and on_board!='' and status in ('win','loss')", (y,)).fetchall(); w = sum(1 for r in rows if r[0] == 'win')
    n = db.execute("select count(*) from pp_lines where start > ?", (CM.iso(),)).fetchone()[0]
    return '%s %s: yesterday board picks %d-%d. %d PrizePicks lines on the board for today. Collectors last ran %s.\n%s\n%s' % (c['emoji'], c['name'], w, len(rows) - w, n, CM.fmt_ct(DBM.kv_get(db, 'pp_last_pull')) if DBM.kv_get(db, 'pp_last_pull') else 'never', CO.pp_health_line(), K.foot())

def main():
    os.makedirs(CM.LOGS, exist_ok=True); open(os.path.join(CM.LOGS, 'scheduler.pid'), 'w').write(str(os.getpid()))
    CM.log('scheduler', 'started pid %d' % os.getpid()); PO.post('system', '🟢 %s scheduler started.' % CM.cfg()['name']); db = DBM.connect(); s = load()
    while True:
        try: tick(db, load())                    # fresh state from disk every cycle
        except Exception: CM.log('scheduler', traceback.format_exc())
        time.sleep(60)

if __name__ == '__main__':
    if '--loop' in sys.argv: main()
    else: db = DBM.connect(); s = load(); tick(db, s); print('one tick done')
