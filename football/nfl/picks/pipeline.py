#!/usr/bin/env python3
"""Pick generation for this sport: current PrizePicks lines -> projection -> probability -> rules -> boards -> history.db picks.
  python3 picks/pipeline.py            score the lines not started yet and print the boards
  python3 picks/pipeline.py --post     also post changed boards to Discord (discord/post.py)"""
import datetime as dt
import collections as C, datetime as dt, json, os, statistics as ST, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as CM
from database import db as DBM
from models import projection as PJ, probability as PB
from rules import rules as RU

def current_lines(db, now=None):
    """Latest row per PrizePicks projection id that has not started, is pre-game and is on the board."""
    now = now or CM.now_utc(); out = {}
    for r in db.execute("select * from pp_lines where start > ? and status='pre_game' order by last_seen", ((now - dt.timedelta(days=1)).date().isoformat(),)):   # APEX-STARTTIME-2026-11-07: text window wide, real-time check below
        st = CM.parse_iso(r['start'])
        if not st or st <= now: continue
        out[r['projection_id']] = dict(r)
    top = {}   # fresh lines (his 11/6 go): keep only lines on each league's latest pull (15 min window), PrizePicks took the rest down
    for r in out.values(): top[r['league']] = max(top.get(r['league'], ''), r['last_seen'] or '')
    out = {k: r for k, r in out.items() if (r['last_seen'] or '') >= CM.iso(CM.parse_iso(top[r['league']]) - dt.timedelta(minutes=15))}
    rows = list(out.values()); fresh = {}
    for r in rows: fresh[r['projection_id']] = r
    try:   # APEX-ONETEAM-2026-11-12: a traded player's old-team lines are dropped (they were scored against the wrong opponent)
        from picks import one_team as OT
        return OT.one_team(list(fresh.values()), CM.log)
    except Exception as e: CM.log('pipeline', 'one team failed: %s' % e)
    return list(fresh.values())

def latest_injuries(db):
    out = {}
    for r in db.execute('select player_norm, status, team, fetched_at from injuries order by fetched_at'): out[r['player_norm']] = dict(status=r['status'], team=r['team'], at=r['fetched_at'])
    return out

def latest_books(db, hours=30):
    """(stat, player_norm) -> [(line, over, under)] latest per book."""
    since = CM.iso(CM.now_utc() - dt.timedelta(hours=hours)); last = {}
    for r in db.execute('select * from book_lines where fetched_at > ? order by fetched_at', (since,)):
        if r['stat']: last[(r['book'], r['stat'], r['player_norm'])] = (r['line'], r['over'], r['under'])
    out = C.defaultdict(list)
    for (b, s, p), v in last.items(): out[(s, p)].append(v)
    return out

def team_abbr(x): return CM.cfg().get('team_alias', {}).get(str(x or '').upper(), str(x or '').upper())
def opponent_of(r):
    """Opponent abbreviation from the PrizePicks description (e.g. 'MIA' or 'vs MIA' or '@ MIA') and home/away from the game teams."""
    team = team_abbr(r['team']); home, away = team_abbr(r['home_abbr']), team_abbr(r['away_abbr'])
    if home and away and team in (home, away): return (away if team == home else home), int(team == home)
    d = str(r['opponent'] or '').replace('@', '').replace('vs', '').strip().split()
    return (team_abbr(d[-1]) if d else None), None

def _funnel(db, now, lines, rows, reasons, mains):
    """APEX-FETCHSUMMARY-2026-11-09 (owner, "go fetch summary"): where every PrizePicks line went this run, in plain counts. Never raises."""
    try:
        import collections as _C
        now = now or CM.now_utc(); saved = DBM.kv_get(db, 'pp_last_pull') or ''
        board = {r[0]: r[1] for r in db.execute("select projection_id, start from pp_lines where last_seen=? and status='pre_game'", (saved,))}
        started = 0
        for st in board.values():
            t = CM.parse_iso(st)
            if t and t <= now: started += 1
        prev = db.execute("select max(last_seen) from pp_lines where last_seen < ?", (saved,)).fetchone()[0]
        recent = {r[0] for r in db.execute("select distinct projection_id from pp_lines where status='pre_game' and last_seen=? and start > ?", (prev, CM.iso(now)))} if prev else set()
        ids = {r['projection_id'] for r in lines}
        gone = sum(1 for p in recent if p not in ids and p not in board)
        np = _C.Counter(str(r['no_play']) for r in rows if r.get('no_play'))
        kinds = _C.Counter(str(r.get('kind')) for r in rows)
        onb = set(); per = {}
        for b, ks in (mains or {}).items(): onb.update(ks); per[b] = len(ks)
        return dict(on_board=len(board), started=started, gone=gone, not_started=len(lines), dropped=[list(x) for x in reasons.most_common()], scored=len(rows),
                    kinds=dict(kinds), no_play=[list(x) for x in np.most_common()], at_floor=sum(1 for r in rows if r['confidence'] >= CM.cfg()['rules']['floor'] and not r.get('no_play')),
                    on_boards=len(onb), per_board=per, pull_at=saved)
    except Exception as e:
        CM.log('pipeline', 'funnel failed: %s' % e); return {}


def score(db=None, now=None, trigger='manual'):
    db = db or DBM.connect(); E = PJ.Engine(db); fits = E.fits; lines = current_lines(db, now); inj = latest_injuries(db); books = latest_books(db)
    banned = {r[0] for r in db.execute('select player_norm from bans')}; rows = []; reasons = C.Counter()
    anchors = C.defaultdict(list)
    for r in lines:
        if r['kind'] == 'standard' and r['stat']: anchors[(r['player_norm'], r['stat'], r['start'][:10])].append(r['line'])
    try:   # APEX-GOBLINLESS-2026-11-12: Demon lines where PrizePicks also sells LESS (as a Goblin)
        from models import goblin_less as GL
        gl_sold = GL.sold(db)
    except Exception as e: gl_sold = set(); CM.log('pipeline', 'goblin less (sold) failed: %s' % e)
    cache = {}
    for r in lines:
        stat = r['stat']
        if not stat: reasons['stat the engine does not score'] += 1; continue
        opp, home = opponent_of(r); day = CM.parse_iso(r['start']).astimezone(CM.CT).date().isoformat()
        key = (r['player_norm'], stat, day)
        if key not in cache:
            ctx = dict(team=team_abbr(r['team']), injuries=inj, db=db, game_date=day)
            cache[key] = E.project(r['player_norm'], stat, day, opp, home, ctx)
        pr = cache[key]
        if not pr: reasons['under %d games of history' % CM.cfg().get('min_games', 6)] += 1; continue
        anc = anchors.get(key); anc = ST.median(anc) if anc else None
        ev = PB.evaluate(pr, r['line'], books.get((stat, r['player_norm'])), fits, anc)
        side = 'MORE' if ev['side'] == 'over' else 'LESS'
        if r['kind'] in ('goblin', 'demon') and side != 'MORE':
            # the only allowed play on these lines is the over: report its own number
            ev = dict(ev, side='over', conf=ev['over']); ev['tier'] = PB.tier(ev['conf']); side = 'MORE'; ev['edge_score'] = PB.edge_score(ev); ev['reasons'] = PB.reasons(ev)
        tdc = None
        try:   # APEX-TDTOUCHES-2026-11-10: "no touchdown" picks rated by how busy the player is
            from models import td_touches as TT
            tdc = TT.cap(db, r['player_norm'], stat, r['kind'], side, day, ev['conf'])
            if tdc:
                ev = dict(ev, conf=float(tdc['to']), under=float(tdc['to']), over=100.0 - tdc['to'])
                ev['tier'] = PB.tier(ev['conf']); ev['edge_score'] = PB.edge_score(ev)
                ev['reasons'] = list(ev['reasons']) + [('Touches', tdc['to'] - tdc['was'], '%.0f a game' % tdc['t'])]
        except Exception as e: CM.log('pipeline', 'td touches failed: %s' % e)
        gbr = None
        try:   # APEX-GOBLINREAL-2026-11-10: Rush Attempts / Tackles Goblins rated at what they really win
            from models import goblin_real as GR
            from models import td_touches as _TT
            gbr = GR.real(stat, r['kind'], side, ev['conf'], _TT.touches(db, r['player_norm'], day) if stat in ('rush_att', 'rush_yds') else None)
            if gbr:
                ev = dict(ev, conf=float(gbr['to']), over=float(gbr['to']), under=100.0 - gbr['to'])
                ev['tier'] = PB.tier(ev['conf']); ev['edge_score'] = PB.edge_score(ev)
                ev['reasons'] = list(ev['reasons']) + [('Real record', gbr['to'] - gbr['was'], gbr['what'])]
        except Exception as e: CM.log('pipeline', 'goblin real failed: %s' % e)
        rmc = None
        try:   # APEX-ROOM-2026-11-11: Goblins rated by their room under the sportsbooks (real lines, this season)
            from models import room as RM
            rmc = RM.room(stat, r['kind'], side, r['line'], books.get((stat, r['player_norm'])), ev['conf'])
            if rmc:
                _rk = rmc['to'] + rmc['was'] / 1000.0   # same room number: the pick Apex itself rated higher goes first
                ev = dict(ev, conf=_rk, over=_rk, under=100.0 - _rk)
                ev['tier'] = PB.tier(ev['conf']); ev['edge_score'] = PB.edge_score(ev)
                ev['reasons'] = list(ev['reasons']) + [('Room', rmc['to'] - rmc['was'], '%g under the books' % rmc['room'])]
        except Exception as e: CM.log('pipeline', 'room failed: %s' % e)
        rows.append(dict(pick_key='%s|%g|%s' % (r['projection_id'], r['line'], r['kind']), projection_id=r['projection_id'], league=r['league'], player=r['player'], player_norm=r['player_norm'], team=team_abbr(r['team']), opponent=opp, home=home,
                         game_date=day, start=r['start'], last_seen=r.get('last_seen'), stat=stat, stat_raw=r['stat_raw'], label=CM.cfg()['stats'][stat]['label'], line=r['line'], kind=r['kind'], side=side, projection=pr['mean'], used=ev.get('mean_used', pr['mean']), sd=pr['sd'],
                         over_p=ev['over'], under_p=ev['under'], confidence=ev['conf'], tier=ev['tier'], edge_score=ev['edge_score'], reasons=ev['reasons'], market=ev['market'], games=pr['games'], l5=pr['l5'], l10=pr['l10'], base=pr['base'],
                         rest=pr['rest'], injury=inj.get(r['player_norm']), promo=r['promo'], no_play_hint=pr.get('no_play'), game_key=(frozenset([team_abbr(r['team']), opp or '?']), day), td_touches=tdc, goblin_real=gbr, room=rmc))
        try:   # APEX-GOBLINLESS-2026-11-12: the LESS side of this Demon line is its own Goblin pick, rated by its gap above the sportsbooks
            if r['kind'] == 'demon' and (str(r['projection_id']), float(r['line'])) in gl_sold:
                from models import room as _RM
                up = float(rows[-1]['under_p']); glc = GL.rate(stat, r['line'], books.get((stat, r['player_norm'])), up, _RM.UNIT)
                cf = (glc['to'] + glc['was'] / 1000.0) if glc else up
                ev2 = dict(ev, side='under', conf=cf, over=100.0 - cf, under=cf); ev2['tier'] = PB.tier(cf); ev2['edge_score'] = PB.edge_score(ev2)
                rs = [x for x in PB.reasons(ev2)] + ([('Gap', glc['to'] - glc['was'], '%g above the books' % glc['room'])] if glc else [])
                rows.append(dict(rows[-1], pick_key='%s|%g|gless' % (r['projection_id'], r['line']), kind='goblin', side='LESS', over_p=100.0 - up, under_p=up, confidence=cf, tier=ev2['tier'], edge_score=ev2['edge_score'], reasons=rs,
                                 td_touches=None, goblin_real=None, room=glc, less_ok=True))
        except Exception as e: CM.log('pipeline', 'goblin less failed: %s' % e)
    try:   # APEX-HONESTBOARDS-2026-11-07: honest numbers before the boards are built (boards need them)
        from tracking import honest as HN
        for r in rows: r['honest'] = HN.honest(r)
        for r in rows:   # APEX-ROOM-2026-11-11: a room-rated Goblin's honest number is the room record itself
            if r.get('room'): r['honest'] = dict(pct=float(r['room']['to']), n=r['room']['n'], src='room', all_stats=True)
    except Exception as e: CM.log('pipeline', 'honest (before boards) failed: %s' % e)
    try:   # APEX-ONELINE-2026-11-12: one PrizePicks line = one pick (same line under two ids is saved, graded and ranked once)
        from tracking import dedupe as DD
        DD.clean(db); rows = DD.rows_once(db, rows)
    except Exception as e: CM.log('pipeline', 'one line failed: %s' % e)
    boards = RU.build_boards(rows, inj, banned); saved_at = DBM.kv_get(db, 'pp_last_pull'); floor = CM.cfg()['rules']['floor']
    cur = db.execute('insert into runs(created,lines_saved_at,n_lines,n_scored,n_floor,trigger) values(?,?,?,?,?,?)', (CM.iso(), saved_at, len(lines), len(rows), sum(1 for r in rows if r['confidence'] >= floor and not r.get('no_play')), trigger)); run_id = cur.lastrowid
    on_board = {}
    for b, d in boards.items():
        for i, r in enumerate(d['main'], 1): db.execute('insert into boards values(?,?,?,?,?,?)', (run_id, b, 'main', i, r['pick_key'], r['confidence'])); on_board.setdefault(r['pick_key'], []).append(b)
        for i, r in enumerate(d['backups'], 1): db.execute('insert into boards values(?,?,?,?,?,?)', (run_id, b, 'backup', i, r['pick_key'], r['confidence']))
    for r in rows:
        db.execute('''insert into picks(pick_key,run_id,created,league,player,player_norm,team,opponent,game_date,start,stat,stat_raw,line,kind,side,projection,sd,over_p,under_p,confidence,tier,edge_score,reasons_json,market_json,injury_json,on_board)
                      values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) on conflict(pick_key) do update set run_id=excluded.run_id, team=excluded.team, opponent=excluded.opponent, side=excluded.side, projection=excluded.projection, sd=excluded.sd, over_p=excluded.over_p, under_p=excluded.under_p,
                      confidence=excluded.confidence, tier=excluded.tier, edge_score=excluded.edge_score, reasons_json=excluded.reasons_json, market_json=excluded.market_json, injury_json=excluded.injury_json, on_board=excluded.on_board where picks.status='open' ''',
                   (r['pick_key'], run_id, CM.iso(), r['league'], r['player'], r['player_norm'], r['team'], r['opponent'], r['game_date'], r['start'], r['stat'], r['stat_raw'], r['line'], r['kind'], r['side'], r['projection'], r['sd'], r['over_p'], r['under_p'],
                    r['confidence'], r['tier'], r['edge_score'], json.dumps(r['reasons']), json.dumps(r['market']), json.dumps(r['injury']), ','.join(on_board.get(r['pick_key'], []))))
    db.commit()
    try:   # APEX-HONEST-2026-11-07: honest number on every row (display only)
        from tracking import honest as HN
        for r in rows: r['honest'] = HN.honest(r)
        for r in rows:   # APEX-ROOM-2026-11-11: a room-rated Goblin's honest number is the room record itself
            if r.get('room'): r['honest'] = dict(pct=float(r['room']['to']), n=r['room']['n'], src='room', all_stats=True)
    except Exception as e: CM.log('pipeline', 'honest failed: %s' % e)
    s = dict(run_id=run_id, n_lines=len(lines), n_scored=len(rows), n_floor=sum(1 for r in rows if r['confidence'] >= floor and not r.get('no_play')), reasons=reasons.most_common(), lines_saved_at=saved_at, boards=boards, rows=rows,
             mains={b: [r['pick_key'] for r in d['main']] for b, d in boards.items()})
    s['funnel'] = _funnel(db, now, lines, rows, reasons, s['mains'])   # APEX-FETCHSUMMARY-2026-11-09
    CM.write_json(os.path.join(CM.CACHE, 'latest_scored.json'), dict(created=CM.iso(), run_id=run_id, lines_saved_at=saved_at, n_lines=len(lines), n_scored=len(rows), n_floor=s['n_floor'], mains=s['mains'], funnel=s['funnel'],
                                                                     rows=[{k: v for k, v in r.items() if k != 'game_key'} for r in rows]))
    return s

if __name__ == '__main__':
    s = score(trigger='manual'); print('lines', s['n_lines'], 'scored', s['n_scored'], 'at floor', s['n_floor'], 'skipped', s['reasons'])
    K = CM.dmod("cards")
    for b, d in s['boards'].items(): print(K.board_text(b, d, s)); print()
    if '--post' in sys.argv:
        PO = CM.dmod("post"); PO.post_boards(s)
