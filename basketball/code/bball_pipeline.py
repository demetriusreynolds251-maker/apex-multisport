#!/usr/bin/env python3
"""Builds boards from scored lines, runs scoring and grading, keeps the latest scored rows in data/latest_scored.json.
Never calls PrizePicks: rescore() reads only data/collected/*.jsonl."""
import datetime as dt, json, os, threading
import score_board as SB, espn_results as ER, bball_tracker as T, prob_engine as PE, engine_scorer as ES
LATEST = os.path.join(SB.ROOT, 'data', 'latest_scored.json')
COLLECTOR_STATE = os.path.join(SB.ROOT, 'logs', 'line_collector_state.json')
FLOOR = float(PE.config().get('recommend_min', 60))   # the engine's recommend line (data/prob_engine_config.json), 11/5: 60
BOARDS = {'top3': dict(title='TOP 3', note='3-pick Power', size=3, nba_only=True), 'elite5': dict(title='ELITE 5', note='5-pick Flex', size=5, nba_only=True), 'elite6': dict(title='ELITE 6', note='6-pick Flex', size=6, nba_only=True),
          'top10': dict(title='TOP 10', note='', size=10, nba_only=False), 'bestgoblin': dict(title='BEST GOBLIN', note='MORE only', size=5, nba_only=False, kind='goblin', side='MORE'),
          'bestless': dict(title='BEST GOBLIN LESS', note='LESS only, a full step or more above the sportsbooks, 80+, Apex 75+ on LESS', size=5, nba_only=False, kind='goblin', side='LESS'),   # APEX-GOBLINLESS-NBA-2026-11-12
          'beststandard': dict(title='BEST STANDARD', note='65+', size=5, nba_only=False, kind='standard', floor=65.0), 'bestdemon': dict(title='BEST DEMON', note='MORE only, 60+', size=5, nba_only=False, kind='demon', floor=60.0)}
# Floors (his 11/5 3:11 PM CT): Top 3 / Elite 5 / Elite 6 / Best Goblin 70+. Best Standard 65+ and Best Demon 60+ = the lowest level that still won more than it
# lost in the 11/5 backtest (standard lines 65+ went 118-87 on the unseen half; 60-64 was 53%. Demon-style lines said 60-69% hit 65%).
BACKUP_MAX = 10
cancel_event = threading.Event()
class Cancelled(Exception): pass
_hist = _hist_sig = None; _engine = _engine_hist = None
def _check():
    if cancel_event.is_set(): raise Cancelled()
def history():
    """History loads once, and again only when ESPN has added games. Reload takes seconds, so callers run it off the Discord thread."""
    global _hist, _hist_sig
    sig = [os.path.getmtime(p) if os.path.exists(p) else 0 for p in (SB.HIST_DB, SB.FGM_DB, SB.ESPN_DB)]
    if _hist is None or sig != _hist_sig: _hist, _hist_sig = SB.History(), sig
    return _hist
def engine():
    """The probability engine, rebuilt only when history reloads."""
    global _engine, _engine_hist
    h = history()
    if _engine is None or _engine_hist is not h: _engine, _engine_hist = PE.Engine(hist=h), h
    return _engine
import room_goblin as RG
def rank_key(r): return (-r['win_prob'], -(r.get('edge_score') or 0), r['start'], r['player'], str(r['stat']))
def build_boards(rows, banned=(), floor=FLOOR):
    """Rank is the engine's Win Prob (ties: edge score). Floor = the engine's recommend line. Board stats only. One pick per game on a numbered board; anything else above the floor is a backup, in rank order."""
    pool = sorted([r for r in rows if r.get('win_prob') is not None and not r.get('promo') and r.get('onboard', True) and SB.norm(r['player']) not in banned], key=rank_key); out = {}
    for name, c in BOARDS.items():
        fl = c.get('floor', floor)
        cand = [r for r in pool if r['win_prob'] >= fl and (not c['nba_only'] or r['league'].upper() == 'NBA') and ('kind' not in c or r['kind'] == c['kind']) and ('side' not in c or r['side'] == c['side'])]; main, games = [], set(); best_only = RG.ON and RG.BEST_ONLY and c.get('kind') not in ('standard', 'demon')   # APEX-ROOMPLUSAPEX-2026-11-11: numbered spots only for best-group Goblins
        for r in cand:
            if len(main) < c['size'] and r['game_key'] not in games and (not best_only or (r['kind'] == 'goblin' and (r.get('groom') or {}).get('best'))) and not r.get('inj_hold'): main.append(r); games.add(r['game_key'])   # APEX-INJURYHOLD-2026-11-11: a player on the injury report waits in BACKUPS
        ids = {id(r) for r in main}; out[name] = dict(main=main, backups=[r for r in cand if id(r) not in ids][:BACKUP_MAX], qualified=len(cand))
    return out
def _write_latest(d):
    os.makedirs(os.path.dirname(LATEST), exist_ok=True)
    with open(LATEST + '.tmp', 'w') as f: json.dump(d, f)
    os.replace(LATEST + '.tmp', LATEST)
def read_latest():
    try:
        with open(LATEST) as f: return json.load(f)
    except (OSError, ValueError): return None
def rescore(trigger='auto', now=None):
    """Re-scores the saved lines. Returns a summary dict. No network at all."""
    cancel_event.clear(); now = now or dt.datetime.now(dt.timezone.utc)
    lines, saved, bad = SB.load_saved_lines(); _check()
    if not lines: return dict(no_lines=True, lines_saved_at=saved, bad_rows=bad)
    rows = ES.score_lines(lines, engine(), now=now); _check()
    db = T.connect()
    try:
        try: T.clean(db)
        except Exception: pass
        rows = T.rows_once(db, rows)   # APEX-ONELINE-2026-11-12: one PrizePicks line = one pick
        built = build_boards(rows, T.banned(db)); _check()
        run, changed = T.save_run(db, rows, built, saved, trigger, now=now)
    finally: db.close()
    _write_latest(dict(scored_at=now.isoformat(timespec='seconds'), lines_saved_at=saved, rows=rows))
    return dict(no_lines=False, run=run, lines_saved_at=saved, bad_rows=bad, n_lines=len(rows), n_scored=sum(r['win_prob'] is not None for r in rows), n_70=sum((r['win_prob'] or 0) >= FLOOR for r in rows), slips_changed=changed,
                last_game=history().last_game, mains={k: [T.pick_key(r) for r in v['main']] for k, v in built.items()})
def current(now=None):
    """Boards as of now from the last scoring, minus lines that have started and players banned since. Returns None before any scoring."""
    d = read_latest()
    if not d: return None
    now = (now or dt.datetime.now(dt.timezone.utc)).isoformat(timespec='seconds')
    rows = [r for r in d['rows'] if r['start'] > now]; db = T.connect()
    try: bans = T.banned(db)
    finally: db.close()
    return dict(rows=rows, boards=build_boards(rows, bans), scored_at=d['scored_at'], lines_saved_at=d['lines_saved_at'], bans=bans)
def grade(now=None, get=ER.fetch, pause=1.0):
    """Daily: ESPN for yesterday, today, tomorrow and any date with open picks (at most 7), then grade and settle."""
    now = now or dt.datetime.now(dt.timezone.utc); db = T.connect(); today = now.astimezone(SB.CT).date()
    try:
        dates = {(today + dt.timedelta(days=i)).isoformat() for i in (-1, 0, 1)}
        dates |= {r[0] for r in db.execute("select distinct game_date from picks where status='open' and league='NBA' and start_utc<=? order by game_date desc limit 7", (now.isoformat(),))}
        fetched = ER.update(sorted(dates)[-7:], get=get, pause=pause); g = T.grade_open(db, now=now)
        stuck = db.execute("select count(*) from picks where status='open' and league='NBA' and game_date<?", ((today - dt.timedelta(days=3)).isoformat(),)).fetchone()[0]
    finally: db.close()
    return dict(espn=fetched, graded=g, stuck=stuck)
def last_collector_pull():
    """When the collector last finished a pull (its state file time, read only), even if no line changed. None if it never has."""
    try: return dt.datetime.fromtimestamp(os.path.getmtime(COLLECTOR_STATE), dt.timezone.utc)
    except OSError: return None
