"""APEX-HONESTFIX-2026-11-10 (owner, "Go honest fix"): Apex only learns from lines where the player really played.
A did-not-play line is a void on PrizePicks, not a LESS win, but history stored it as a 0 result, which made LESS look better than it is
(soccer shots LESS rated 80-89 showed 80 of 100, really 67). Used by tracking/honest.py (the honest number on cards) and
backtesting/backtest.py (weekly re-fit). Reads this sport's own player_games; soccer also reads the clean match store
(~/ApexSports/_shared/clean_history/soccer_clean.sqlite: who started, who came on, minutes) when it has the match.
Rule: a line counts when the player has a box-score row for that game that shows he played. Games with no box score at all are kept
(nothing to judge by). Set ON = False to undo."""
import os, re, json, sqlite3, unicodedata, datetime as dt
import common as CM

ON = True
CLEAN = os.path.expanduser('~/ApexSports/_shared/clean_history/soccer_clean.sqlite')

def _nm(x):
    x = unicodedata.normalize('NFKD', x or '').encode('ascii', 'ignore').decode().lower()
    x = re.sub(r"[^a-z ]", ' ', x); x = re.sub(r'\b(jr|sr|ii|iii)\b', '', x); return ' '.join(x.split())

def _box(db):
    """(event_id, player_norm) -> played?, and the set of events that have any box score."""
    P = {}; EV = set()
    for ev, pn, sj in db.execute('select event_id, player_norm, stats_json from player_games'):
        try: st = json.loads(sj or '{}')
        except Exception: st = {}
        ok = bool(st.get('_played')) or bool(st.get('_box')) or any(v for k, v in st.items() if not k.startswith('_') and isinstance(v, (int, float)))
        P[(ev, pn)] = P.get((ev, pn), False) or ok; EV.add(ev)
    return P, EV

def _soccer():
    """(name, date) -> played, from the clean match store (soccer only). Empty when the store is missing."""
    if os.path.basename(CM.ROOT) != 'soccer' or not os.path.exists(CLEAN): return {}
    idx = {}
    try:
        cl = sqlite3.connect('file:' + CLEAN + '?mode=ro', uri=True, timeout=60)
        for player, day, played in cl.execute('select player, game_date, played from players'):
            n = _nm(player); d0 = dt.date.fromisoformat(day[:10])
            for k in (0, -1):
                key = (n, (d0 + dt.timedelta(days=k)).isoformat()); idx[key] = bool(idx.get(key)) or bool(played)
        cl.close()
    except Exception: return {}
    return idx

def learn_rows(db, rows):
    """rows: prop_lines dicts. Returns (rows where the player played, how many were left out)."""
    if not ON or not rows: return rows, 0
    P, EV = _box(db); S = _soccer(); keep = []
    for r in rows:
        s = S.get((_nm(r.get('player')), str(r.get('game_date'))[:10])) if S else None
        if s is not None: ok = s
        elif r['event_id'] not in EV: ok = True
        else: ok = P.get((r['event_id'], r['player_norm']), False)
        if ok: keep.append(r)
    return keep, len(rows) - len(keep)
