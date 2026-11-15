#!/usr/bin/env python3
"""APEX-SOCCERSTARTS-2026-11-10 (owner, "Go soccer starts", then "do what you know is best" = starts only).
A player who did not start his last match takes fewer shots: Shots LESS on those players won 34-17 / 50-35 as 3-pick slips
(older / newer half of history) against 43-40 / 68-69 for every player. So a regular-line Shots LESS pick only takes a numbered
board spot when the player did NOT start his last match; the others stay visible in BACKUPS with the reason.
Start records come from the clean match store (~/ApexSports/_shared/clean_history/soccer_clean.sqlite: ESPN box scores, who started,
who came on), refreshed every night by refresh(). Soccer only. Set ON = False to undo."""
import os, re, sys, sqlite3, subprocess, unicodedata, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as CM

ON = True
STORE = os.path.expanduser('~/ApexSports/_shared/clean_history/soccer_clean.sqlite')
JOB = os.path.expanduser('~/ApexSports/_shared/clean_history/soccer_clean.py')
MIN_MATCHES = 4      # same as the test: needs 4+ earlier matches in the store
MAX_AGE_DAYS = 60    # last match older than this = no usable record
_C = {'mt': 0, 'h': {}}

def _nm(x):
    x = unicodedata.normalize('NFKD', x or '').encode('ascii', 'ignore').decode().lower()
    x = re.sub(r"[^a-z ]", ' ', x); x = re.sub(r'\b(jr|sr|ii|iii)\b', '', x); return ' '.join(x.split())

def _load():
    try: mt = os.path.getmtime(STORE)
    except OSError: return {}
    if mt != _C['mt']:
        h = {}
        try:
            db = sqlite3.connect('file:' + STORE + '?mode=ro', uri=True, timeout=60)
            for aid, player, day, starter in db.execute('select athlete_id, player, game_date, starter from players order by game_date'):
                h.setdefault(_nm(player), {}).setdefault(aid, []).append((day[:10], int(starter or 0)))
            db.close()
        except Exception as e:
            CM.log('starts', 'store read failed: %s' % e); return _C['h']
        _C.update(mt=mt, h=h)
    return _C['h']

def record(player, date):
    """Start record before `date`: dict(last_started, starts, n, last_date) or None when the store does not know him well enough."""
    date = str(date)[:10]; best = None
    for rows in (_load().get(_nm(player)) or {}).values():
        prev = [g for g in rows if g[0] < date][-5:]
        if prev and (best is None or prev[-1][0] > best[-1][0]): best = prev
    if not best or len(best) < MIN_MATCHES: return None
    try:
        if (dt.date.fromisoformat(date) - dt.date.fromisoformat(best[-1][0])).days > MAX_AGE_DAYS: return None
    except ValueError: return None
    return dict(last_started=bool(best[-1][1]), starts=sum(g[1] for g in best), n=len(best), last_date=best[-1][0])

def applies(row): return ON and row.get('stat') == 'shots' and row.get('kind') == 'standard' and row.get('side') == 'LESS'

def hold(row):
    """Plain reason a Shots LESS pick may not take a numbered spot, or None. Also leaves the record on the row for the card."""
    if not applies(row): return None
    rec = record(row.get('player'), row.get('game_date')); row['starts'] = rec
    if not rec: return 'no start record for him yet, so Shots LESS stays in BACKUPS'
    if rec['last_started']: return 'he started his last match (%s). Shots LESS only takes a spot when the player did not start his last match' % _d(rec['last_date'])
    return None

def _d(s):
    try: d = dt.date.fromisoformat(s); return '%d/%d' % (d.month, d.day)
    except ValueError: return s

def card_line(row):
    if not applies(row): return None
    rec = row.get('starts') if 'starts' in row else record(row.get('player'), row.get('game_date'))
    if row.get('starts_hold') and str(row['starts_hold']).startswith(('Starts, so off', 'Waiting for lineup')): return '🪑 %s' % row['starts_hold']   # APEX-BENCHONLY-2026-11-14
    if row.get('starts_hold'): return '🪑 BACKUP only: %s.' % row['starts_hold']
    if rec: return '🪑 Did not start his last match (%s). Started %d of his last %d. Shots LESS on these players really wins about 7 of 10.' % (_d(rec['last_date']), rec['starts'], rec['n'])
    return None

def refresh(days=6):
    """Nightly: add the last few days of finished matches to the clean store (ESPN only). Returns one line for #system."""
    end = dt.date.today(); start = end - dt.timedelta(days=days)
    try:
        p = subprocess.run(['/usr/bin/python3', JOB, start.isoformat(), end.isoformat()], capture_output=True, text=True, timeout=1500)
        last = (p.stdout.strip().splitlines() or ['?'])[-1]
        db = sqlite3.connect('file:' + STORE + '?mode=ro', uri=True, timeout=60); n, mx = db.execute('select count(*), max(game_date) from games').fetchone(); db.close()
        if p.returncode != 0 or not last.startswith('DONE'): return '⚠️ Soccer start records: nightly update failed (%s). Shots LESS picks use records through %s.' % ((p.stderr or last)[-150:], mx)
        return '🪑 Soccer start records updated: %s new matches, %s in the store, through %s.' % (last.split()[-1], format(n, ','), mx)
    except Exception as e:
        return '⚠️ Soccer start records: nightly update failed (%s: %s).' % (type(e).__name__, str(e)[:150])
