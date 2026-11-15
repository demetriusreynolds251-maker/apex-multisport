# APEX-SOCCERHISTORY-2026-11-12 (owner, "Fix soccer history"): stored SGO shot counts before Dec 2025 left out blocked shots (about 1 row in 5 too low).
# Replace a stored shot count with the ESPN box score count (clean store) when the same player + day is found, he played, and the stored count is LOWER.
# Every change is written to table shots_fix_log (old + new) so it can be undone. Only 'shots' is touched; other stats matched ESPN already.
import os, sqlite3, re, unicodedata, datetime as dt, json
CLEAN = os.path.expanduser('~/ApexSports/_shared/clean_history/soccer_clean.sqlite')
def nm(x):
    x = unicodedata.normalize('NFKD', x or '').encode('ascii', 'ignore').decode().lower(); x = re.sub(r"[^a-z ]", ' ', x); x = re.sub(r'\b(jr|sr|ii|iii)\b', '', x); return ' '.join(x.split())
def index():
    cl = sqlite3.connect('file:' + CLEAN + '?mode=ro', uri=True); idx = {}
    for p, d, played, shots in cl.execute('select player, game_date, played, shots from players'):
        d0 = dt.date.fromisoformat(d[:10])
        for k in (0, -1, 1): idx.setdefault((nm(p), (d0 + dt.timedelta(days=k)).isoformat()), (played, shots or 0))
    return idx
def apply(path):
    idx = index(); db = sqlite3.connect(path, timeout=60)
    db.execute('create table if not exists shots_fix_log(tbl text, event_id text, player_norm text, pp_line real, old real, new real, fixed text)')
    now = dt.datetime.utcnow().isoformat(timespec='seconds'); n1 = n2 = 0
    for ev, pn, p, d, sj in db.execute("select event_id, player_norm, player, game_date, stats_json from player_games where source='sgo'").fetchall():
        st = json.loads(sj or '{}'); v = st.get('shots'); c = idx.get((nm(p), d[:10]))
        if v is None or not c or not c[0] or c[1] <= v: continue
        st['shots'] = float(c[1]); db.execute("update player_games set stats_json=? where event_id=? and player_norm=? and source='sgo'", (json.dumps(st), ev, pn))
        db.execute('insert into shots_fix_log values(?,?,?,?,?,?,?)', ('player_games', ev, pn, None, v, c[1], now)); n1 += 1
    for ev, pn, p, d, L, res in db.execute("select event_id, player_norm, player, game_date, pp_line, result from prop_lines where stat='shots' and result is not null").fetchall():
        c = idx.get((nm(p), d[:10]))
        if not c or not c[0] or c[1] <= res: continue
        db.execute("update prop_lines set result=? where event_id=? and player_norm=? and stat='shots' and pp_line=?", (float(c[1]), ev, pn, L))
        db.execute('insert into shots_fix_log values(?,?,?,?,?,?,?)', ('prop_lines', ev, pn, L, res, c[1], now)); n2 += 1
    db.commit(); db.close(); return n1, n2
