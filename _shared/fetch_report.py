#!/usr/bin/env python3
"""APEX-FETCHDETAIL-2026-11-13 (owner 11/13 7:34 AM CT, "Go fetch detail"): the tennis-style fetch message for every
other sport. Same pieces as the tennis 🆕 NEW PROPS SCORED card: how many new props since the last scoring run (games,
Goblin / Standard / Demon split), the best new pick, the new props per game, every board's changes (who went in, who went
out, empty spots), Top 3 now, when the lines were saved and when the next automatic pull is due.

Used by the typed /<prefix>-fetch reply AND every automatic pull post in #<prefix>-system, for the 9 template sports
(NFL, college football, NHL, soccer, college basketball, WNBA, MLB, AFL, rugby) and NBA (~/ApexSports/basketball).

Display only. Reads what scoring just produced plus the sport's own database (read only): the previous run's boards and
when each pick was first scored. Never calls PrizePicks, never changes a pick, number, floor, board or pull time.
Never raises: on any error the caller keeps its old short line.

  report_9(s, trigger, CM, t0=None)          -> text   s = picks.pipeline.score(...) result
  quiet_9(CM, trigger, added, state=None)    -> text   a PrizePicks read that found nothing to score (or did not go through)
  report_nba(s, trigger, P, T, SB, t0=None)  -> text   s = bball_pipeline.rescore(...) result
Off switch: ON = False (callers fall back to the old line). Undo: git checkout before-fetch-detail (tag in ~/ApexSports)."""
import collections, datetime as dt, os, sqlite3, time

ON = True
KIND_DOT = {'goblin': '🟢', 'standard': '⚪', 'demon': '🔴'}
KIND_WORD = {'goblin': 'Goblin', 'standard': 'Standard', 'demon': 'Demon'}
MAX_GAMES = 12          # games listed under "New PrizePicks props"; the rest are counted
MAX_STATS = 4           # stat names per game
TRIGGER_WORDS = {'fetch': 'typed fetch', 'morning': 'automatic morning pull', 'board_open': 'automatic board-open pull',
                 'new lines': 'automatic pull, new lines', 'pre_game': 'automatic pull, 60 min before the first game',
                 'final_lock': 'automatic pull, 15 min before the first game', 'board refresh': 'board refresh, lines were old',
                 'lineups': 'lineups changed', 'ban': 'after a ban', 'unban': 'after an unban', 'auto': 'automatic re-score'}


# ------------------------------------------------------------------------------------------------ small words
def _int(x):
    try: return int(round(float(x)))
    except Exception: return None


def _n(x):
    try: return '{:,}'.format(int(x))
    except Exception: return str(x)


def _s(n, word, plural=None):
    return '%s %s' % (_n(n), word if n == 1 else (plural or word + 's'))


def _team(x):
    x = str(x or '?')
    return x.title() if x.isupper() and len(x) > 4 else x


def _line(x):
    try:
        f = float(x); return ('%d' % f) if f == int(f) else ('%g' % f)
    except Exception: return str(x)


def _clock(t, CT, now=None):
    if not t: return 'never'
    x = t.astimezone(CT); today = (now or dt.datetime.now(dt.timezone.utc)).astimezone(CT).date()
    return x.strftime('%-I:%M %p CT') if x.date() == today else x.strftime('%a %-m/%-d %-I:%M %p CT')


def _parse(s):
    if not s: return None
    try:
        t = dt.datetime.fromisoformat(str(s).replace('Z', '+00:00'))
        return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)
    except Exception: return None


def _game(p):
    """'Serbia v Germany' (away v home when known)."""
    a, b = _team(p.get('team')), _team(p.get('opponent'))
    return ('%s v %s' % (a, b)) if str(p.get('home')) in ('0', 'False') else ('%s v %s' % (b, a)) if str(p.get('home')) in ('1', 'True') else ' v '.join(sorted((a, b)))


def _game_key(p):
    return p.get('game_key') or (str(p.get('start') or '')[:16], frozenset((str(p.get('team')), str(p.get('opponent')))))


def _title(x):
    """'BEST GOBLIN LESS' -> 'Best Goblin LESS'"""
    return ' '.join(w if w in ('LESS', 'MORE') else w.capitalize() for w in str(x).split())


def _empty(have, size):
    if have >= size: return ''
    if have == 0: return 'all %d spots empty' % size
    return ('#%d empty' % size) if have + 1 == size else ('#%d to #%d empty' % (have + 1, size))


# ------------------------------------------------------------------------------------------------ the card
def _pick(p):
    """'🟢 Erling Haaland Shots MORE 1.5 (84)'"""
    num = _int(p.get('num'))
    return '%s %s %s %s %s%s' % (KIND_DOT.get(p.get('kind'), '▫️'), p.get('player') or '?', p.get('stat') or '?', p.get('side') or '?',
                                 _line(p.get('line')), (' (%d)' % num) if num is not None else '')


def _board_lines(boards, prev, keyinfo):
    """boards: [(key, title, size, [pick keys now])]; prev: {key: [pick keys]} or None (no earlier run)."""
    L, same = [], []
    for b, title, size, now_keys in boards:
        title = _title(title); empty = _empty(len(now_keys), size)
        etxt = (' · ' + empty) if empty else ''
        if prev is None:
            L.append('%s: first run, %d of %d filled%s' % (title, len(now_keys), size, etxt)); continue
        old = prev.get(b) or []
        if old == now_keys:
            same.append(title + (' (%s)' % empty if empty else '')); continue
        ins = [k for k in now_keys if k not in old]; outs = [k for k in old if k not in now_keys]
        if not ins and not outs:
            L.append('%s: changed · same picks, new order%s' % (title, etxt)); continue
        bits = ['%s: changed' % title]
        if ins and outs: bits.append('%s replaced' % _n(min(len(ins), len(outs))))
        if ins: bits.append('in: ' + ', '.join(_pick(keyinfo[k]) if k in keyinfo else k for k in ins[:3]) + (' +%d more' % (len(ins) - 3) if len(ins) > 3 else ''))
        if outs: bits.append('out: ' + ', '.join(('%s %s' % (keyinfo[k].get('player'), keyinfo[k].get('stat'))) if k in keyinfo else k for k in outs[:3]) + (' +%d more' % (len(outs) - 3) if len(outs) > 3 else ''))
        L.append(' · '.join(bits) + etxt)
    if same: L.append('Unchanged: ' + ', '.join(same))
    return L


def _render(d):
    """d: emoji, name, trigger, new [pick dicts], keyinfo, boards, prev, scored_line, saved, CT, now, next_txt, warn."""
    CT, now = d['CT'], d['now']; new = d['new']; warn = d.get('warn') or []
    games = collections.OrderedDict()
    for p in sorted(new, key=lambda p: (str(p.get('start') or ''), _game(p))):
        games.setdefault(_game_key(p), []).append(p)
    kinds = collections.Counter(p.get('kind') for p in new)
    playable = [p for p in new if not p.get('held')]
    best = max(playable, key=lambda p: float(p.get('num') or 0)) if playable else None
    blines = _board_lines(d['boards'], d['prev'], d['keyinfo'])
    changed = any(not x.startswith('Unchanged:') for x in blines) and d['prev'] is not None
    when = TRIGGER_WORDS.get(d['trigger'], d['trigger'])
    if not new and not changed:   # nothing new: one line, never silence
        return ('🔁 %s **%s** · %s · %s · no new props since the last run · boards unchanged · lines saved %s · next pull about %s'
                % (d['emoji'], d['name'], now.astimezone(CT).strftime('%-I:%M %p CT'), when, _clock(d['saved'], CT, now), d['next_txt'])
                + ''.join('\n⚠️ ' + w for w in warn))
    L = ['🆕 **NEW PROPS SCORED · %s %s** · %s' % (d['emoji'], d['name'], when)]
    L.append('%s scored (%s)' % (_s(len(new), 'new prop'), _s(len(games), 'game')) if new else 'No new props since the last run')
    if best: L.append('Best new pick: %s' % _pick(best))
    elif new: L.append('Best new pick: none playable (all held or flash-sale lines)')
    L.append('Lines saved %s · boards updated %s' % (_clock(d['saved'], CT, now), now.astimezone(CT).strftime('%-I:%M %p CT')))
    if new:
        L.append('Board watch: %s across %s (%s)' % (_s(len(new), 'new prop'), _s(len(games), 'game'),
                                                      ', '.join('%d %s' % (kinds[k], k) for k in ('demon', 'goblin', 'standard') if kinds.get(k))))
        L += ['', '🆕 **New PrizePicks props**']
        for i, (g, ps) in enumerate(games.items()):
            if i >= MAX_GAMES:
                rest = list(games.values())[MAX_GAMES:]
                L.append('· %s more (%s)' % (_s(len(rest), 'game'), _s(sum(len(x) for x in rest), 'prop'))); break
            stats = [s for s, _ in collections.Counter(p.get('stat') for p in ps).most_common()]
            lab = next((p for p in ps if len(str(p.get('team') or '')) > 3 and len(str(p.get('opponent') or '')) > 3), ps[0])
            L.append('· %s: %d (%s%s)' % (_game(lab), len(ps), ', '.join(str(s) for s in stats[:MAX_STATS]), ' +%d more' % (len(stats) - MAX_STATS) if len(stats) > MAX_STATS else ''))
    L += ['', '📋 **Board changes**'] + blines
    top = [x for x in d['boards'] if x[0] == 'top3']
    if top:
        ks = top[0][3]
        L.append('Top 3 now: ' + ('  '.join('%d. %s' % (i, _pick(d['keyinfo'][k]) if k in d['keyinfo'] else k) for i, k in enumerate(ks, 1)) or 'empty'))
    L += ['', d['scored_line']]
    L += ['⚠️ ' + w for w in warn]
    L.append('⏭️ Next automatic pull about %s' % d['next_txt'])
    return '\n'.join(L)


# ------------------------------------------------------------------------------------------------ 9 template sports
def _next_9(CM, trigger, now):
    sc = CM.cfg().get('schedule') or {}; every = float(sc.get('pp_every_min', 180)); win = sc.get('window') or ['05:30', '23:30']
    st = CM.read_json(os.path.join(CM.CACHE, 'scheduler_state.json'), {}) or {}
    lp = _parse(st.get('last_pp'))
    base = now if (trigger == 'fetch' or not lp or lp > now) else lp
    nct = max(base + dt.timedelta(minutes=every), now).astimezone(CM.CT); hm = nct.strftime('%H:%M')
    if hm > win[1]:
        h, m = map(int, sc.get('morning', win[0]).split(':')); nct = (nct + dt.timedelta(days=1)).replace(hour=h, minute=m, second=0)
    elif hm < win[0]:
        h, m = map(int, win[0].split(':')); nct = nct.replace(hour=h, minute=m, second=0)
    when = nct.strftime('%-I:%M %p CT') if nct.date() == now.astimezone(CM.CT).date() else nct.strftime('%a %-I:%M %p CT')
    return '%s (every %d min, %s to %s CT, plus 60 and 15 min before the first game)' % (when, every, win[0], win[1])


def _info_9(r, held=False):
    return dict(player=r.get('player'), stat=r.get('label') or r.get('stat_raw') or r.get('stat'), side=r.get('side'), line=r.get('line'),
                kind=r.get('kind'), num=r.get('confidence'), team=r.get('team'), opponent=r.get('opponent'), home=r.get('home'),
                start=r.get('start'), game_key=r.get('game_key'), held=held or bool(r.get('no_play')) or bool(r.get('promo')))


def report_9(s, trigger, CM, t0=None):
    c = CM.cfg(); now = CM.now_utc(); rows = s.get('rows') or []; warn = []
    byk = {r.get('pick_key'): r for r in rows}
    keyinfo = {k: _info_9(r) for k, r in byk.items()}
    new_keys, prev = set(), None
    db = sqlite3.connect('file:%s?mode=ro' % CM.DB_FILE, uri=True, timeout=10)
    try:
        run = db.execute('select id, created from runs where id < ? order by id desc limit 1', (s.get('run_id') or 10 ** 12,)).fetchone()
        if run:
            prev = collections.defaultdict(list)
            for b, k in db.execute("select board, pick_key from boards where run_id=? and role='main' order by board, slot", (run[0],)):
                prev[b].append(k)
            prev = dict(prev)
            new_keys = {k for (k,) in db.execute('select pick_key from picks where created > ?', (run[1],))} & set(byk)
            outs = {k for v in prev.values() for k in v if k not in keyinfo}
            if outs:
                q = 'select pick_key, player, stat_raw, side, line, kind, confidence, team, opponent, start from picks where pick_key in (%s)' % ','.join('?' * len(outs))
                for k, pl, st, sd, ln, kd, cf, tm, op, stt in db.execute(q, list(outs)):
                    keyinfo[k] = dict(player=pl, stat=st, side=sd, line=ln, kind=kd, num=cf, team=tm, opponent=op, start=stt)
        else:
            new_keys = set(byk)
    finally: db.close()
    boards = []
    for b, bc in (c.get('boards') or {}).items():
        d = (s.get('boards') or {}).get(b) or {}
        keys = (s.get('mains') or {}).get(b)
        if keys is None: keys = [r.get('pick_key') for r in (d.get('main') or [])]
        boards.append((b, bc.get('title') or d.get('title') or b.upper(), int(d.get('size') or bc.get('size') or 0), list(keys)))
    new = [keyinfo[k] for k in new_keys]
    floor = c['rules']['floor']
    scored_line = '🧪 %s lines not started · %s with a number · %s at %d+' % (_n(s.get('n_lines', 0)), _n(s.get('n_scored', 0)), _n(s.get('n_floor', 0)), floor)
    if t0: scored_line += ' · took %d s' % max(0, time.time() - t0)
    try:
        import importlib
        CO = importlib.import_module('collectors.collector')
        if CO.pp_paused(): warn.append('PrizePicks reads are paused right now (slow-down), so lines may be older than usual')
        if trigger == 'fetch' and not getattr(CO, 'PP_OK', True): warn.append('PrizePicks could not be read on this fetch, scoring used the last saved lines')
    except Exception: pass
    if s.get('n_lines') and not s.get('n_scored'): warn.append('lines were found but none got a number')
    return _render(dict(emoji=c.get('emoji', ''), name=c.get('name', ''), trigger=trigger, new=new, keyinfo=keyinfo, boards=boards, prev=prev,
                        scored_line=scored_line, saved=_parse(s.get('lines_saved_at')), CT=CM.CT, now=now, next_txt=_next_9(CM, trigger, now), warn=warn))


def quiet_9(CM, trigger, added, state=None):
    """One line for an automatic PrizePicks read that gave scoring nothing to do (no new or moved line, paused, off season,
    or the read did not go through). state: the scheduler state dict, used to post the off-season line once a day only."""
    c = CM.cfg(); now = CM.now_utc(); n = None
    try:
        db = sqlite3.connect('file:%s?mode=ro' % CM.DB_FILE, uri=True, timeout=10)
        try:
            x = db.execute("select fetched_at, n from snapshots where kind='pp' order by fetched_at desc limit 1").fetchone()
            n = x[1] if x else None
        finally: db.close()
    except Exception: pass
    why = None
    try:
        import importlib
        CO = importlib.import_module('collectors.collector')
        if CO.pp_paused(): why = 'PrizePicks reads are paused (slow-down), boards unchanged'
    except Exception: pass
    if why is None and added is None: why = 'the PrizePicks read did not go through (too soon after the last one, or it failed; failures post to #%s-alerts), boards unchanged' % c.get('prefix', '')
    if why is None and n == 0:
        if state is not None:
            day = now.astimezone(CM.CT).date().isoformat()
            if state.get('fd_quiet_offseason') == day: return None
            state['fd_quiet_offseason'] = day
        why = 'PrizePicks has no lines for this sport (off season or no games), checked again later'
    if why is None: why = 'nothing new or moved%s, boards unchanged' % ((' (%s lines checked)' % _n(n)) if n else '')
    return '🔁 %s **%s** · %s · %s · %s · next pull about %s' % (c.get('emoji', ''), c.get('name', ''), now.astimezone(CM.CT).strftime('%-I:%M %p CT'),
                                                               TRIGGER_WORDS.get(trigger, trigger), why, _next_9(CM, trigger, now))


# ------------------------------------------------------------------------------------------------ NBA (~/ApexSports/basketball)
def report_nba(s, trigger, P, T, SB, t0=None):
    now = dt.datetime.now(dt.timezone.utc); CT = SB.CT; warn = []
    rows = (P.read_latest() or {}).get('rows') or []
    scored = [r for r in rows if r.get('win_prob') is not None]
    keyinfo = {}
    for r in scored:
        keyinfo[T.pick_key(r)] = dict(player=r.get('player'), stat=r.get('stat_raw') or r.get('stat'), side=r.get('side'), line=r.get('line'),
                                      kind=r.get('kind'), num=r.get('win_prob'), team=r.get('team'), opponent=r.get('opponent'), home=r.get('home'),
                                      start=r.get('start'), game_key=r.get('game_key'), held=bool(r.get('promo')) or not r.get('onboard', True))
    new_keys, prev = set(), None
    db = T.connect()
    try:
        run = db.execute('select id, created from runs where id < ? order by id desc limit 1', (s.get('run') or 10 ** 12,)).fetchone()
        if run:
            prev = collections.defaultdict(list)
            for x in db.execute("select board, pick_key from boards where run_id=? and role='main' order by board, slot", (run[0],)):
                prev[x[0]].append(x[1])
            prev = dict(prev)
            new_keys = {x[0] for x in db.execute('select pick_key from picks where first_scored > ?', (run[1],))} & set(keyinfo)
            outs = [k for v in prev.values() for k in v if k not in keyinfo]
            if outs:
                q = 'select pick_key, player, stat_raw, side, line, kind, win_prob, team, opponent, start_utc from picks where pick_key in (%s)' % ','.join('?' * len(outs))
                for x in db.execute(q, outs):
                    keyinfo[x[0]] = dict(player=x[1], stat=x[2], side=x[3], line=x[4], kind=x[5], num=x[6], team=x[7], opponent=x[8], start=x[9])
        else:
            new_keys = set(keyinfo)
    finally: db.close()
    boards = [(b, bc['title'], bc['size'], list((s.get('mains') or {}).get(b) or [])) for b, bc in P.BOARDS.items()]
    scored_line = '🧪 %s lines not started · %s with a number · %s at %d+' % (_n(s.get('n_lines', 0)), _n(s.get('n_scored', 0)), _n(s.get('n_70', 0)), int(P.FLOOR))
    if t0: scored_line += ' · took %d s' % max(0, time.time() - t0)
    if s.get('bad_rows'): warn.append('%d saved line rows could not be read' % s['bad_rows'])
    try:
        import line_collector as LC; every, hours = LC.PULL_EVERY, LC.HOURS
    except Exception: every, hours = 30, ('08:00', '23:59')
    try: last = P.last_collector_pull()
    except Exception: last = None
    nxt = max((last + dt.timedelta(minutes=every)) if last else now, now).astimezone(CT)
    if nxt.strftime('%H:%M') < hours[0]:
        h, m = map(int, hours[0].split(':')); nxt = nxt.replace(hour=h, minute=m, second=0)
    elif nxt.strftime('%H:%M') > hours[1]:
        h, m = map(int, hours[0].split(':')); nxt = (nxt + dt.timedelta(days=1)).replace(hour=h, minute=m, second=0)
    next_txt = '%s (the line collector reads PrizePicks every %d min, %s to %s CT; boards re-score a few minutes after each read; /bball-fetch re-scores saved lines only)' % (
        nxt.strftime('%-I:%M %p CT') if nxt.date() == now.astimezone(CT).date() else nxt.strftime('%a %-I:%M %p CT'), every, hours[0], hours[1])
    return _render(dict(emoji='🏀', name='NBA', trigger=trigger, new=[keyinfo[k] for k in new_keys], keyinfo=keyinfo, boards=boards, prev=prev,
                        scored_line=scored_line, saved=_parse(s.get('lines_saved_at')), CT=CT, now=now, next_txt=next_txt, warn=warn))
