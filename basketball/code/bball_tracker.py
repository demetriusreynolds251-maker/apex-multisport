#!/usr/bin/env python3
"""Basketball test tracker, data/processed/bball_tracker.sqlite: picks, boards, slips, results, bans. Never touches the tennis ledger or tennis #pnl.
Rules: a pick's numbers freeze at its start. A slip is official as the last board before its first leg, then it never changes.
Paper dollars: $[amount] on Top 3 Power only. Flex pay tables are not copied here, so Elite 5 and Elite 6 are counted by whole slip and legs, with no dollars."""
import datetime as dt, json, os, sqlite3
from zoneinfo import ZoneInfo
import score_board as SB, espn_results as ER
TRACKER_DB = os.path.join(SB.PROC, 'bball_tracker.sqlite')
CT = ZoneInfo('America/Chicago')
PAPER_STAKE = 20.0
POWER3 = {'GGG': 2.2, 'GGS': 3.25, 'GSS': 3.75, 'SSS': 6.0}   # Goblin/Standard mixes, same table tennis uses
POWER3_FALLBACK = 2.2   # any Demon in the slip: lowest pay, as tennis does, until a real payout is known
SLIP_BOARDS = {'top3': ('power', 3), 'elite5': ('flex', 5), 'elite6': ('flex', 6)}
BANDS = [(50, 60), (60, 70), (70, 75), (75, 80), (80, 101)]
def connect(path=None):
    p = path or TRACKER_DB; os.makedirs(os.path.dirname(p), exist_ok=True); db = sqlite3.connect(p); db.row_factory = sqlite3.Row
    db.executescript("""create table if not exists picks(pick_key text primary key, projection_id text, league text, player text, team text, opponent text, stat text, stat_raw text, line real, kind text, side text,
        win_prob real, projected real, start_utc text, game_date text, game_key text, promo integer, first_scored text, last_scored text, status text default 'open', result real, graded_at text);
      create table if not exists runs(id integer primary key, created text, lines_saved_at text, n_lines integer, n_scored integer, n_70 integer, trigger text);
      create table if not exists boards(run_id integer, board text, role text, slot integer, pick_key text, win_prob real);
      create table if not exists slips(id integer primary key, day text, board text, slip_kind text, legs_json text, first_start text, stake real, status text default 'pending', legs_won integer, legs_lost integer, legs_void integer,
        payout_mult real, pnl real, updated text, posted_sig text, settled_posted integer default 0, unique(day, board));
      create table if not exists results(pick_key text, status text, value real, graded_at text, source text);
      create table if not exists bans(player_norm text primary key, player text, why text, added text);
      create index if not exists ix_pick_status on picks(status);""")
    return db
def _iso(now=None): return (now or dt.datetime.now(dt.timezone.utc)).astimezone(dt.timezone.utc).isoformat(timespec='seconds')
def pick_key(r): return r.get('_pick_key') or '%s|%s|%s' % (r['projection_id'], r['line'], r['kind'])
# APEX-ONELINE-2026-11-12 (his go: "Proper fix all until it's no data poison"): one PrizePicks line = one pick. PrizePicks lists some
# lines under two projection ids (twins, or a line re-issued under a new id); both used to be saved, graded and counted.
# clean() keeps one saved pick per line and marks the copies status='dup' (never graded, never counted); rows_once() keeps one
# scored row per line before boards are built. Undo: ONE_LINE = False.
ONE_LINE = True
def clean(db):
    if not ONE_LINE: return 0
    groups = db.execute("select player, stat, line, kind, game_date from picks where status != 'dup' group by 1, 2, 3, 4, 5 having count(*) > 1").fetchall()
    if not groups: return 0
    nb = {r[0]: r[1] for r in db.execute("select pick_key, count(*) from boards where role='main' group by 1")}; n = 0; remap = {}
    for g in groups:
        ps = db.execute("select pick_key, status, last_scored from picks where player=? and stat=? and line=? and kind=? and game_date=? and status != 'dup'", tuple(g)).fetchall()
        ps = sorted(ps, key=lambda p: (nb.get(p[0], 0), 1 if p[1] in ('win', 'loss', 'push') else 0, p[2] or '', p[0]), reverse=True)
        for p in ps[1:]:
            db.execute("update picks set status='dup' where pick_key=?", (p[0],)); db.execute('update boards set pick_key=? where pick_key=?', (ps[0][0], p[0])); remap[p[0]] = ps[0][0]; n += 1
    for s in db.execute('select id, legs_json from slips').fetchall():
        keys = json.loads(s[1] or '[]'); new = [remap.get(k, k) for k in keys]
        if new != keys: db.execute('update slips set legs_json=? where id=?', (json.dumps(new), s[0]))
    db.commit(); return n
def rows_once(db, rows):
    try: return _rows_once(db, rows)
    except Exception: return rows   # never let this stop a scoring run
def _rows_once(db, rows):
    if not ONE_LINE or not rows: return rows
    lo = min(r['game_date'] for r in rows if r.get('game_date')); keep = {}
    for p in db.execute("select pick_key, player, stat, line, kind, game_date from picks where status != 'dup' and game_date >= ?", (lo,)): keep[(p[1], p[2], float(p[3]), p[4], p[5])] = p[0]
    out, seen = [], set()
    for r in rows:
        k = (r['player'], r['stat'], float(r['line']), r['kind'], r.get('game_date'))
        if k in seen: continue
        seen.add(k)
        if k in keep and keep[k] != pick_key(r): r['_pick_key'] = keep[k]
        out.append(r)
    return out
def banned(db): return {r['player_norm']: dict(r) for r in db.execute('select * from bans order by player')}
def ban(db, player, why=''):
    db.execute('insert or replace into bans values(?,?,?,?)', (SB.norm(player), player.strip(), why, _iso())); db.commit()
def unban(db, player):
    n = db.execute('delete from bans where player_norm=?', (SB.norm(player),)).rowcount; db.commit(); return n
def save_run(db, rows, built, lines_saved_at, trigger, now=None):
    """One scoring run: every numbered row into picks (open ones only), the board snapshot, and the slip update. Returns (run_id, changed slip ids)."""
    now = now or dt.datetime.now(dt.timezone.utc); ts = _iso(now); scored = [r for r in rows if r.get('win_prob') is not None]
    for r in scored:
        db.execute("""insert into picks(pick_key,projection_id,league,player,team,opponent,stat,stat_raw,line,kind,side,win_prob,projected,start_utc,game_date,game_key,promo,first_scored,last_scored)
          values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) on conflict(pick_key) do update set side=excluded.side,win_prob=excluded.win_prob,projected=excluded.projected,last_scored=excluded.last_scored,opponent=excluded.opponent,game_key=excluded.game_key
          where picks.start_utc>excluded.last_scored""", (pick_key(r), r['projection_id'], r['league'], r['player'], r['team'], r['opponent'], r['stat'], r.get('stat_raw'), float(r['line']), r['kind'], r['side'], r['win_prob'], r['projected'], r['start'], r['game_date'], r['game_key'], int(bool(r.get('promo'))), ts, ts))
    cur = db.execute('insert into runs(created,lines_saved_at,n_lines,n_scored,n_70,trigger) values(?,?,?,?,?,?)', (ts, lines_saved_at, len(rows), len(scored), sum(r['win_prob'] >= 70 for r in scored), trigger)); rid = cur.lastrowid
    for name, b in built.items():
        for role, L in (('main', b['main']), ('backup', b['backups'])):
            for i, r in enumerate(L, 1): db.execute('insert into boards values(?,?,?,?,?,?)', (rid, name, role, i, pick_key(r), r['win_prob']))
    changed = update_slips(db, built, now); db.commit(); return rid, changed
def update_slips(db, built, now=None):
    now = now or dt.datetime.now(dt.timezone.utc); nowi = _iso(now); changed = []
    for name, (sk, size) in SLIP_BOARDS.items():
        main = built.get(name, {}).get('main', [])
        if len(main) == size:
            keys = [pick_key(r) for r in main]; first = min(r['start'] for r in main); day = min(r['game_date'] for r in main)
            ex = db.execute('select * from slips where day=? and board=?', (day, name)).fetchone()
            if ex and ex['first_start'] <= nowi: continue   # first leg has started: locked
            if not ex or json.loads(ex['legs_json']) != keys:
                db.execute('insert into slips(day,board,slip_kind,legs_json,first_start,stake,updated) values(?,?,?,?,?,?,?) on conflict(day,board) do update set legs_json=excluded.legs_json,first_start=excluded.first_start,updated=excluded.updated',
                           (day, name, sk, json.dumps(keys), first, PAPER_STAKE if sk == 'power' else None, nowi)); changed.append((day, name))
        else:   # board no longer has a full slip: an unstarted slip for it comes off
            for s in db.execute("select id from slips where board=? and status='pending' and first_start>?", (name, nowi)).fetchall():
                db.execute('delete from slips where id=?', (s['id'],)); changed.append((None, name))
    return changed
def grade_open(db, espn_path=None, now=None):
    """Grades open NBA picks that have a finished ESPN box score. Other leagues stay open: there is no grader for them yet."""
    clean(db)   # APEX-ONELINE-2026-11-12: copies of one line are never graded
    now = now or dt.datetime.now(dt.timezone.utc); ts = _iso(now); espn = ER.connect(espn_path); got = dict(win=0, loss=0, push=0, void=0, open=0, other_league=0, nostat=0)
    for p in db.execute("select * from picks where status='open' and start_utc<=?", (ts,)).fetchall():
        if p['league'].upper() != 'NBA': got['other_league'] += 1; continue
        st, v = ER.grade_pick(espn, SB.norm, p['player'], p['team'], p['game_date'], p['stat'], p['line'], p['side']); got[st] += 1
        if st != 'open':
            db.execute('update picks set status=?, result=?, graded_at=? where pick_key=?', (st, v, ts, p['pick_key'])); db.execute('insert into results values(?,?,?,?,?)', (p['pick_key'], st, v, ts, 'espn'))
    espn.close(); settled = settle_slips(db, ts); db.commit(); got['settled'] = settled; return got
def _power_mult(kinds):
    if 'demon' in kinds: return POWER3_FALLBACK
    code = ''.join(sorted('G' if k == 'goblin' else 'S' for k in kinds))
    return POWER3.get(code, POWER3_FALLBACK)
def settle_slips(db, ts=None):
    """lost: Power with a losing leg. check_app: a void or push leg, because PrizePicks then changes the pay. all_hit/partial: Flex, no dollars."""
    out = []
    for s in db.execute("select * from slips where status='pending'").fetchall():
        keys = json.loads(s['legs_json']); legs = [db.execute('select * from picks where pick_key=?', (k,)).fetchone() for k in keys]
        if any(l is None for l in legs): continue
        st = [l['status'] for l in legs]; w, lo, v = st.count('win'), st.count('loss'), st.count('void') + st.count('push') + st.count('nostat'); status = mult = pnl = None
        if s['slip_kind'] == 'power' and lo:
            status, mult = 'lost', 0.0; pnl = -s['stake']
        elif 'open' not in st:
            if v: status = 'check_app'
            elif s['slip_kind'] == 'power':
                status, mult = 'won', _power_mult([l['kind'] for l in legs]); pnl = round(s['stake'] * (mult - 1), 2)
            else: status = 'all_hit' if not lo else 'partial'
        if status:
            db.execute('update slips set status=?, legs_won=?, legs_lost=?, legs_void=?, payout_mult=?, pnl=?, updated=? where id=?', (status, w, lo, v, mult, pnl, ts or _iso(), s['id'])); out.append(s['id'])
    return out
def counters(db):
    out = {}
    for b in SLIP_BOARDS:
        rows = db.execute('select * from slips where board=?', (b,)).fetchall()
        out[b] = dict(won=sum(r['status'] in ('won', 'all_hit') for r in rows), lost=sum(r['status'] in ('lost', 'partial') for r in rows), check=sum(r['status'] == 'check_app' for r in rows), pending=sum(r['status'] == 'pending' for r in rows),
                      legs_won=sum(r['legs_won'] or 0 for r in rows), legs_lost=sum(r['legs_lost'] or 0 for r in rows))
    return out
def pnl(db, since=None, until=None):
    q = "select * from slips where pnl is not null"; a = []
    if since: q += ' and day>=?'; a.append(since)
    if until: q += ' and day<=?'; a.append(until)
    rows = db.execute(q, a).fetchall(); return dict(net=round(sum(r['pnl'] for r in rows), 2), staked=sum(r['stake'] for r in rows), won=sum(r['pnl'] > 0 for r in rows), lost=sum(r['pnl'] < 0 for r in rows))
def calibration(db):
    """Graded picks by Win Probability band: is 70 hitting 7 out of 10?"""
    out = []
    for a, b in BANDS:
        r = db.execute("select sum(status='win') w, sum(status='loss') l from picks where league='NBA' and win_prob>=? and win_prob<?", (a, b)).fetchone()
        out.append((a, b, r['w'] or 0, r['l'] or 0))
    return out
def besttime(db):
    """By hour the lines were saved: did the Top 3 / Elite 5 / Elite 6 on the board then hit in full? Only boards where every leg is graded count."""
    out = {}
    for run in db.execute('select * from runs').fetchall():
        if not run['lines_saved_at']: continue
        hour = dt.datetime.fromisoformat(run['lines_saved_at']).astimezone(CT).strftime('%-I %p')
        for b, (_, size) in SLIP_BOARDS.items():
            st = [r['status'] for r in db.execute("select p.status from boards x join picks p using(pick_key) where x.run_id=? and x.board=? and x.role='main'", (run['id'], b))]
            if len(st) != size or any(s in ('open', 'void', 'push') for s in st): continue
            c = out.setdefault((b, hour), [0, 0]); c[0 if all(s == 'win' for s in st) else 1] += 1
    return out
