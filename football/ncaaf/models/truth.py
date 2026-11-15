#!/usr/bin/env python3
"""APEX-COLLEGETRUTH-2026-11-13 (owner: "I don't want a cap I want the truth", then "Go college truth").
The card number of a college Goblin MORE rated by its room under the sportsbooks is the TRUE rate, no 90 cap:
how often a player went OVER a number that far under the sportsbooks, split by stat, gap (steps, as models/room.py measures them) and
steadiness (cleared tonight's number in 8-9 / 6-7 / 5 or fewer of his last 9 games this season). Under MIN cells fall back to the wider cell
(all stats, then all steadiness) and the card says the count. Beside it: the real PrizePicks Goblin record at that gap.
Table: config/truth_table.json, rebuilt by build() from data/truth_archive_rows.jsonl (2TB archive base, sportsbook lines saved before
kickoff with results, 2025 + Sep-Oct 2026) + our own saved sportsbook lines graded from ESPN boxes + our graded labeled Goblins.
Off: ON = False (room numbers go back to models/room.py), restart NCAAF. Undo: git checkout before-college-truth."""
import json, os, collections, datetime as dt, statistics as STT, re, unicodedata
ON = True
MIN = 30
# APEX-COLLEGEREALGOBLINS-2026-11-13 (owner, "Yes, go college real goblins"): the true number leans on the REAL graded PrizePicks Goblin
# MORE record at the same gap as it comes in: true = archive x (1 - w) + real x w, with w = real n / (real n + REAL_K). 0 real picks = the
# sportsbook-history number, 30 = halfway, 100+ mostly real. Real record: same stat + steadiness when it has REAL_MIN+ games, else same stat,
# else all stats at that gap. Each player-game counts once per stat (not once per rung). No shortfall is invented for gaps with no real picks.
# Off: REAL_ON = False (archive number only).
REAL_ON = True; REAL_K = 30.0; REAL_MIN = 10
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(HERE, 'config', 'truth_table.json'); BASE = os.path.join(HERE, 'data', 'truth_archive_rows.jsonl')
G = {'under 1 step': 0.5, '1-2 steps': 1.5, '2-3 steps': 2.5, '3-4 steps': 3.5, '4-6 steps': 5.0, '6+ steps': 7.0}
_T = {}


def bucket(steps):
    return 'under 1 step' if steps < 1 else '1-2 steps' if steps < 2 else '2-3 steps' if steps < 3 else '3-4 steps' if steps < 4 else '4-6 steps' if steps < 6 else '6+ steps'


def _norm(n): return ' '.join(re.sub(r'[^a-z ]', '', unicodedata.normalize('NFKD', str(n or '')).encode('ascii', 'ignore').decode().lower().replace('.', '').replace('-', ' ')).split())


def steady(E, pid, stat, line, day):
    """('8-9 of 9' | '6-7 of 9' | '5 or fewer' | None, k, n) from his games this season before the day (corrected team mapping)."""
    from models.projection import stat_value
    import common as CM
    season = CM.season_of(day)
    h = [stat_value(g['stats'], stat) for g in E.games_before(pid, day) if CM.season_of(g['date']) == season]
    h = [v for v in h if v is not None][-9:]
    if len(h) < 5: return None, 0, len(h)
    k = sum(v > line for v in h); sh = k / len(h)
    return ('8-9 of 9' if sh >= 0.85 else '6-7 of 9' if sh >= 0.62 else '5 or fewer'), k, len(h)


def _load():
    if not _T.get('t') or _T.get('m') != (os.path.getmtime(TABLE) if os.path.exists(TABLE) else 0):
        try: _T['t'] = json.load(open(TABLE)); _T['m'] = os.path.getmtime(TABLE)
        except Exception: _T['t'] = None
    return _T.get('t')


def true(stat, steps, group):
    """dict(pct, w, n, cell, real_w, real_l) or None."""
    t = _load()
    if not ON or not t: return None
    b = bucket(steps); C = t['cells']
    for key, lab in ((('%s|%s|%s' % (stat, b, group)) if group else None, 'this stat, this steady'), (('ALL|%s|%s' % (b, group)) if group else None, 'all stats, this steady'),
                     ('%s|%s|ANY' % (stat, b), 'this stat, any steadiness'), ('ALL|%s|ANY' % b, 'all stats, any steadiness')):
        if key and key in C and C[key][1] >= MIN:
            w, n = C[key]; R = t.get('real_cells') or {}; rw = rl = 0; rlab = 'all stats'
            for rk, rl_ in (((('%s|%s|%s' % (stat, b, group)) if group else None), 'this stat, this steady'), ('%s|%s|ANY' % (stat, b), 'this stat'), ('ALL|%s|ANY' % b, 'all stats')):
                if rk and rk in R and sum(R[rk]) >= REAL_MIN: rw, rl = R[rk]; rlab = rl_; break
            else:
                rw, rl = R.get('ALL|%s|ANY' % b, (0, 0))
            arch = 100.0 * w / n; rn = rw + rl
            wt = (rn / (rn + REAL_K)) if (REAL_ON and rn) else 0.0
            pct = arch * (1 - wt) + (100.0 * rw / rn if rn else 0) * wt
            return dict(pct=round(pct), arch=round(arch), w=w, n=n, cell=lab, bucket=b, real_w=rw, real_l=rl, real_cell=rlab, weight=round(wt, 2))
    return None


def card_line(c):
    """The 🧪 line for a room-rated Goblin carrying c['truth']."""
    t = c.get('truth')
    if not t: return None
    who = {'8-9 of 9': 'players who cleared the number in nearly every recent game', '6-7 of 9': 'players who cleared it in most recent games (about 2 of 3)', '5 or fewer': 'players who cleared it in about half their recent games or fewer'}.get(c.get('steady'), 'players')
    s = '🧪 %s %d: %s, %s under the sportsbooks, went over %s of %s' % ('Sportsbook history' if t.get('weight') else 'True number', t.get('arch', t['pct']) if t.get('weight') else t['pct'], who if t['cell'].endswith('this steady') else 'players', t['bucket'], '{:,}'.format(t['w']), '{:,}'.format(t['n']))
    if c.get('steady'): s += ' · he cleared %g in %d of his last %d' % (c['line'], c['k'], c['h'])
    elif c.get('h') is not None: s += ' · not enough games this season (%d) to judge how steady he is' % c['h']
    s += ' · real PrizePicks Goblins at this gap (%s, one per player-game): won %d, lost %d' % (t.get('real_cell', 'all stats'), t['real_w'], t['real_l'])
    if t.get('arch') is not None and t.get('weight'): s += ' · sportsbook history says %d · true number now %d' % (t['arch'], t['pct'])
    return s


def build(db, E):
    """Rebuilds config/truth_table.json. Returns a one-line summary."""
    import common as CM
    from models import room as RM
    from models.projection import stat_value
    rows = []
    if os.path.exists(BASE):
        for l in open(BASE):
            r = json.loads(l)
            if r['stat'] in RM.UNIT: rows.append((r['stat'], r['book'], r['score'], _norm(r['player']), r['date']))
    pg = {}
    for x in db.execute("select player_norm, game_date, stats_json from player_games where source='espn' and game_date >= '2026-11-01'"):
        pg[(x[0], x[1])] = json.loads(x[2] or '{}')
    snaps = collections.defaultdict(dict)
    for pn, stat, line, start, fa in db.execute("select player_norm, stat, line, start, fetched_at from book_lines where stat is not null and start is not null"):
        try: st = dt.datetime.fromisoformat(start.replace('Z', '+00:00'))
        except Exception: continue
        if fa >= st.isoformat(): continue
        d = st.astimezone(CM.CT).date().isoformat(); snaps[(pn, stat, d)].setdefault(fa[:16], []).append(line)
    ours = 0
    for (pn, stat, d), s in snaps.items():
        if stat not in RM.UNIT or (pn, d) not in pg: continue
        lines = s[max(s)]
        if len(lines) < 2: continue
        a = stat_value(pg[(pn, d)], stat)
        if a is None: continue
        rows.append((stat, STT.median(lines), a, pn, d)); ours += 1
    cells = collections.defaultdict(lambda: [0, 0])
    for stat, book, act, pn, d in rows:
        u = RM.UNIT[stat]
        for b, g in G.items():
            X = book - g * u; won = act > X
            grp = steady(E, pn, stat, X, d)[0]
            for key in ('%s|%s|ANY' % (stat, b), 'ALL|%s|ANY' % b) + ((('%s|%s|%s' % (stat, b, grp)), ('ALL|%s|%s' % (b, grp))) if grp else ()):
                cells[key][0] += won; cells[key][1] += 1
    real = collections.defaultdict(lambda: [0, 0]); one = {}
    for pn, d, stat, line, status, mj in db.execute("select player_norm, game_date, stat, line, status, market_json from picks where kind='goblin' and side='MORE' and status in ('win','loss') and pick_key not like '%gless' order by line"):
        try: m = json.loads(mj or 'null')
        except Exception: m = None
        if not m or not m.get('line') or stat not in RM.UNIT or (m.get('n') or 0) < 2: continue
        steps = (m['line'] - line) / RM.UNIT[stat]
        if steps < 0: continue
        one.setdefault((pn, d, stat, bucket(steps)), []).append((line, status))   # every rung of one player-game in one gap bucket
    real_cells = collections.defaultdict(lambda: [0, 0])
    for (pn, d, stat, b), rs in one.items():
        line, status = rs[len(rs) // 2]   # one result per player-game: the middle rung
        real[b][status == 'loss'] += 1
        grp = steady(E, pn, stat, line, d)[0]
        for key in ('%s|%s|ANY' % (stat, b), 'ALL|%s|ANY' % b) + (('%s|%s|%s' % (stat, b, grp),) if grp else ()):
            real_cells[key][status == 'loss'] += 1
    t = dict(built=CM.iso(), lines=len(rows), ours=ours, cells={k: v for k, v in cells.items()}, real={k: v for k, v in real.items()}, real_cells={k: v for k, v in real_cells.items()})
    with open(TABLE + '.tmp', 'w') as f: json.dump(t, f)
    os.replace(TABLE + '.tmp', TABLE); _T.clear()
    c = cells.get('ALL|3-4 steps|8-9 of 9', [0, 0])
    return '🧪 College true numbers rebuilt: %s lines with a sportsbook number before kickoff (%d of ours since 11/11). Example: steady players 3-4 steps under the books went over %s of %s.' % ('{:,}'.format(len(rows)), ours, '{:,}'.format(c[0]), '{:,}'.format(c[1]))
