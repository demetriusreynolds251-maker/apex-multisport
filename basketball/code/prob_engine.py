#!/usr/bin/env python3
"""Apex Basketball - NBA prop probability engine (his 11/5 1:24 PM spec).
For every PrizePicks NBA line: projected result (mean + spread), Over %, Under %, confidence with the factor breakdown,
a real % for every ladder line (Goblin / Standard / Demon), tier A-D, EDGE SCORE and plain reasons.
Book lines are ONE factor among many (market consensus), not the gate.
Inputs on the Mac today: player game history (nba_history + ESPN box scores), The Odds API book lines, ESPN injuries,
PrizePicks lines, game total / spread from history (live: not collected yet -> neutral).
Usage: prob_engine.py today [YYYY-MM-DD] [--post] [--top N]   |   prob_engine.py backtest
Independent from Apex Tennis: reads and writes only inside ~/ApexSports/basketball.
"""
import bisect, collections as C, datetime as dt, json, math, os, statistics as ST, sqlite3, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import score_board as SB, shadow_runner as SR, room_edge as RE, room_check as RC
CT = SB.CT; PROC = os.path.join(ROOT, 'data', 'processed'); REPORTS = os.path.join(ROOT, 'reports')
CONFIG = os.path.join(ROOT, 'data', 'prob_engine_config.json'); FIT_FILE = os.path.join(PROC, 'prob_engine_fit.json')
FOOT = ''   # APEX-REMOVETEST-2026-11-10 (owner, "go remove test"): the TEST label is gone from every card

def _g(r, k): return r.get(k) if r.get(k) is not None else None
def fantasy(r): return r['points'] + 1.2 * r['rebounds'] + 1.5 * r['assists'] + 3 * r['steals'] + 3 * r['blocks'] - r['turnovers']
# engine stat: (card label, value from one game row, spread floor, on boards, usage kind)
STATS = {'points': ('Points', lambda r: r['points'], 3.0, True, 'scoring'), 'rebounds': ('Rebounds', lambda r: r['rebounds'], 1.6, True, 'rebounds'),
         'assists': ('Assists', lambda r: r['assists'], 1.3, True, 'assists'),
         'points+rebounds+assists': ('PRA', lambda r: r['points'] + r['rebounds'] + r['assists'], 4.0, True, 'scoring'),
         'points+rebounds': ('Pts+Rebs', lambda r: r['points'] + r['rebounds'], 3.5, True, 'scoring'),
         'points+assists': ('Pts+Asts', lambda r: r['points'] + r['assists'], 3.5, True, 'scoring'),
         'rebounds+assists': ('Rebs+Asts', lambda r: r['rebounds'] + r['assists'], 2.0, True, 'rebounds'),
         'threePointersMade': ('3PTM', lambda r: r['threes'], 0.9, False, 'scoring'), 'steals': ('Steals', lambda r: r['steals'], 0.7, False, 'other'),
         'blocks': ('Blocked Shots', lambda r: r['blocks'], 0.7, False, 'other'), 'turnovers': ('Turnovers', lambda r: r['turnovers'], 0.9, False, 'other'),
         'blocks+steals': ('Blks+Stls', lambda r: r['blocks'] + r['steals'], 1.0, False, 'other'), 'fantasyScore': ('Fantasy Score', fantasy, 5.0, False, 'scoring')}
NEED = {'threePointersMade': ('threes',), 'steals': ('steals',), 'blocks': ('blocks',), 'turnovers': ('turnovers',), 'blocks+steals': ('blocks', 'steals'),
        'fantasyScore': ('steals', 'blocks', 'turnovers')}
PP = {'points': 'points', 'rebounds': 'rebounds', 'assists': 'assists', 'pra': 'points+rebounds+assists', 'pts+rebs+asts': 'points+rebounds+assists',
      'pts+rebs': 'points+rebounds', 'pts+asts': 'points+assists', 'rebs+asts': 'rebounds+assists', '3ptm': 'threePointersMade', '3-pt made': 'threePointersMade',
      'steals': 'steals', 'blocked shots': 'blocks', 'blocks': 'blocks', 'turnovers': 'turnovers', 'blks+stls': 'blocks+steals', 'fantasy score': 'fantasyScore'}
MARKET = {'points': 'player_points', 'rebounds': 'player_rebounds', 'assists': 'player_assists', 'points+rebounds+assists': 'player_points_rebounds_assists',
          'points+rebounds': 'player_points_rebounds', 'points+assists': 'player_points_assists', 'rebounds+assists': 'player_rebounds_assists',
          'threePointersMade': 'player_threes', 'steals': 'player_steals', 'blocks': 'player_blocks', 'turnovers': 'player_turnovers',
          'blocks+steals': 'player_blocks_steals', 'fantasyScore': 'player_fantasy_points'}
DEFAULT = dict(min_games=8, tiers={'A': 70, 'B': 65, 'C': 60}, recommend_min=60, market_weight=0.5, opp_weight=0.5, pace_power=0.5, blowout_spread=12,
               recent_weight=0.5, usage_bump={'scoring': 0.05, 'rebounds': 0.03, 'assists': 0.04, 'other': 0.03}, sd_k={}, lg_total=228.0)

def phi(z): return 0.5 * math.erfc(-z / math.sqrt(2))
def phi_inv(p):
    p = min(max(p, 1e-6), 1 - 1e-6); lo, hi = -8.0, 8.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if phi(mid) < p: lo = mid
        else: hi = mid
    return (lo + hi) / 2
def amer_prob(o):
    """American odds text -> implied probability (with the vig still in)."""
    try: o = float(str(o).replace('+', ''))
    except (TypeError, ValueError): return None
    return 100 / (o + 100) if o > 0 else -o / (-o + 100)
def devig(po, pu):
    if po is None and pu is None: return 0.5
    if po is None: return 1 - pu
    if pu is None: return po
    return po / (po + pu)
def season(d): return SB.season(d)
def config():
    c = dict(DEFAULT)
    try: c.update(json.load(open(CONFIG)))
    except (OSError, ValueError): pass
    try: f = json.load(open(FIT_FILE)); c['sd_k'] = f.get('sd_k', c['sd_k']); c['market_weight'] = f.get('market_weight', c['market_weight']); c['anchor'] = f.get('anchor', {})
    except (OSError, ValueError): c['anchor'] = {}
    return c

class Engine:
    """Everything the model needs from history, loaded once."""
    def __init__(self, cfg=None, hist=None):
        self.cfg = cfg or config(); self.hist = hist or SB.History(); self.H = self.hist.H
        db = sqlite3.connect('file:%s?mode=ro' % SB.HIST_DB, uri=True); db.row_factory = sqlite3.Row
        self.games = {g['event_id']: dict(g) for g in db.execute('select * from games where final=1')}; db.close()
        self.game_by_team = {}
        for g in self.games.values():
            for t in (g['home'], g['away']): self.game_by_team[(g['game_date'], t)] = g
        self.totals = sorted((g['game_date'], g['close_total'] if g['open_total'] is None else g['open_total']) for g in self.games.values() if g['close_total'] or g['open_total'])
        # allowed per game by opponent, per stat; team rosters per game (for 'who is out' in history)
        Allow = C.defaultdict(lambda: C.defaultdict(float)); Rost = C.defaultdict(dict); gd = {}
        for pid, rows in self.H.items():
            for r in rows:
                gd[r['event_id']] = r['game_date']; Rost[(r['event_id'], r['team'])][pid] = r['minutes']
                for s, (lab, fn, fl, ob, kind) in STATS.items():
                    if any(r.get(k) is None for k in NEED.get(s, ())): continue
                    try: Allow[(r['event_id'], r['opponent'])][s] += fn(r)
                    except TypeError: pass
        self.TeamG = C.defaultdict(list)
        for (eid, team), v in Allow.items(): self.TeamG[team].append((gd[eid], dict(v)))
        for v in self.TeamG.values(): v.sort(key=lambda x: x[0])
        self.Lg = C.defaultdict(list)
        for v in self.TeamG.values():
            for d, a in v:
                for s, x in a.items(): self.Lg[s].append((d, x))
        for v in self.Lg.values(): v.sort()
        self.Rost = C.defaultdict(list)   # team id -> [(date, {pid: minutes})]
        for (eid, team), v in Rost.items(): self.Rost[team].append((gd[eid], v))
        for v in self.Rost.values(): v.sort(key=lambda x: x[0])
        self.name_of = {pid: rows[-1]['player'] for pid, rows in self.H.items()}
        self._of, self._reg, self._lg = {}, {}, {}
    def lg_mean(self, s, d):
        k = (s, d)
        if k not in self._lg:
            v = self.Lg[s]; i = bisect.bisect_left(v, (d,)); w = v[max(0, i - 400):i]
            self._lg[k] = ST.mean(x for _, x in w) if len(w) >= 50 else None
        return self._lg[k]
    def opp_factor(self, s, team_long, d):
        k = (s, team_long, d)
        if k not in self._of:
            a = [x[1].get(s) for x in self.TeamG.get(team_long, []) if x[0] < d][-15:]; a = [x for x in a if x is not None]; m = self.lg_mean(s, d)
            self._of[k] = ST.mean(a) / m if len(a) >= 5 and m else 1.0
        return self._of[k]
    def lg_total(self, d):
        i = bisect.bisect_left(self.totals, (d,)); w = [x for _, x in self.totals[max(0, i - 300):i]]
        return ST.mean(w) if len(w) >= 30 else self.cfg['lg_total']
    def regulars(self, team_id, d):
        """Players who have been playing real minutes for this team lately: pid -> average minutes (last 10 team games before d)."""
        k = (team_id, d)
        if k not in self._reg:
            v = self.Rost.get(team_id, []); i = bisect.bisect_left([x[0] for x in v], d); last = v[max(0, i - 10):i]; out = {}
            if len(last) >= 4:
                mins = C.defaultdict(list)
                for _, ro in last:
                    for pid, m in ro.items(): mins[pid].append(m or 0)
                for pid, L in mins.items():
                    if len(L) >= max(3, len(last) * 0.6) and ST.mean(L) >= 22: out[pid] = ST.mean(L)
            self._reg[k] = out
        return self._reg[k]
    def played(self, team_id, d):
        v = self.Rost.get(team_id, []); i = bisect.bisect_left([x[0] for x in v], d)
        return v[i][1] if i < len(v) and v[i][0] == d else None

    def project(self, pid, stat, date, opp_long, home=None, total=None, spread=None, out_mins=0.0, rest=None, out_names=()):
        """Projection for one player and stat. Returns dict(mean, sd, steps=[(factor, mean after it, note)], ...) or None."""
        cfg = self.cfg; lab, fn, floor, onboard, kind = STATS[stat]; rows = self.H.get(pid, [])
        i = bisect.bisect_left([h['game_date'] for h in rows], date); past = [h for h in rows[:i] if h['minutes'] and h['minutes'] > 0]
        need = NEED.get(stat, ()); past = [h for h in past if all(h.get(k) is not None for k in need)]
        n = len(past)
        if n < cfg['min_games']: return None
        l5, l10, l20 = past[-5:], past[-10:], past[-20:]; sea = [h for h in past if h['season'] == season(date)]; base = sea if len(sea) >= 10 else past[-40:]
        rate = lambda L: sum(fn(h) for h in L) / max(1.0, sum(h['minutes'] for h in L))
        mins5, mins10, mins20, minsb = (ST.mean(h['minutes'] for h in L) for L in (l5, l10, l20, base))
        r_base, r_rec = rate(base), .45 * rate(l5) + .55 * rate(l10); wf = cfg['recent_weight']; r = (1 - wf) * r_base + wf * r_rec
        steps = []; m = r_base * minsb; steps.append(('Base projection', m, '%s per game over %d games' % (fmt(m), len(base))))
        m = r * minsb; steps.append(('Recent form', m, 'last 10 games %s per game vs %s before' % (fmt(ST.mean(fn(h) for h in l10)), fmt(r_base * minsb))))
        mins = .6 * mins5 + .4 * mins10; m = r * mins; steps.append(('Minutes trend', m, 'playing %.0f min lately vs %.0f min usual' % (mins, minsb)))
        of = self.opp_factor(stat, opp_long, date); of = max(.85, min(1.15, of)); m *= 1 + cfg['opp_weight'] * (of - 1)
        steps.append(('Matchup', m, '%s allows %+.0f%% %s vs league' % (opp_long.split()[-1], 100 * (of - 1), lab.lower())))
        note = 'no game total saved'; pf = 1.0
        if total:
            lt = self.lg_total(date); pf = (total / lt) ** cfg['pace_power']; note = 'game total %.0f vs %.0f average' % (total, lt)
        if spread is not None and abs(spread) >= cfg['blowout_spread'] and mins >= 28: pf *= .96; note += ', blowout risk (spread %g) trims minutes' % spread
        m *= pf; steps.append(('Pace / blowout', m, note))
        rf = 1.0; note = []
        if rest == 1: rf *= .98; note.append('back-to-back')
        elif rest is not None and rest >= 3: rf *= 1.01; note.append('%d days rest' % rest)
        if home is not None and len(base) >= 10:
            hb = [h for h in base if h['home'] == home]
            if len(hb) >= 4:
                hs = rate(hb) / max(r_base, 1e-6); hs = max(.95, min(1.05, hs)); rf *= 1 + .5 * (hs - 1); note.append('%s split %+.0f%%' % ('home' if home else 'away', 100 * (hs - 1)))
        m *= rf; steps.append(('Rest / home', m, ', '.join(note) or 'normal rest'))
        bump = min(.15, cfg['usage_bump'][kind] * out_mins / 30.0) if out_mins else 0.0; m *= 1 + bump
        steps.append(('Teammates out', m, ('%s out (%d min to redistribute)' % (', '.join(out_names[:3]), round(out_mins))) if out_mins else 'no regular out'))
        resid = [fn(h) - r * h['minutes'] for h in l20]; sd = ST.pstdev(resid) if len(resid) >= 5 else floor
        msd = ST.pstdev([h['minutes'] for h in l10]) if len(l10) >= 3 else 4.0; sd = math.sqrt(sd ** 2 + (r * msd) ** 2) * (1 + 4.0 / n)
        sd = max(sd, floor) * cfg['sd_k'].get(stat, 1.0)
        return dict(stat=stat, mean=m, sd=sd, sd_raw=sd / cfg['sd_k'].get(stat, 1.0), steps=steps, mins=mins, mins_usual=minsb, games=n, l5=ST.mean(fn(h) for h in l5), l10=ST.mean(fn(h) for h in l10),
                    base=r_base * minsb, form=(ST.mean(fn(h) for h in l5) / max(r_base * minsb, 1e-6)) - 1, last=past[-1]['game_date'])

def fmt(x): return '%.1f' % x

def market_mean(books, sd):
    """books: list of (line, over_odds, under_odds). Returns (market mean, median line, n books, implied over prob at that line) or None."""
    books = [b for b in books if b and b[0] is not None]
    if not books: return None
    med = ST.median(b[0] for b in books); ps = [devig(amer_prob(b[1]), amer_prob(b[2])) for b in books if abs(b[0] - med) < 1e-9]
    p = ST.mean(ps) if ps else 0.5; p = min(max(p, .2), .8)
    return med + sd * phi_inv(p), med, len(books), p

def evaluate(proj, line, books=None, cfg=None, anchor=None):
    """Over / under % for one line with the factor breakdown. books -> market consensus is blended in as one factor.
    anchor = the PrizePicks standard line for this player and stat: history says it is a sharp number, so the projection is pulled toward it by the fitted share."""
    cfg = cfg or DEFAULT; sd = proj['sd']; p_over = lambda mu: 1 - phi((line - mu) / sd); steps = list(proj['steps'])
    a = cfg.get('anchor', {}).get(proj.get('stat'), 0.0) if anchor is not None else 0.0
    if a: m0 = steps[-1][1]; m1 = m0 + a * (anchor - m0); steps.append(('PrizePicks standard line', m1, 'standard line %g pulls the projection %+.1f (books and PrizePicks are sharp)' % (anchor, m1 - m0)))
    contrib = []; prev = 0.5
    for name, mu, note in steps:
        p = p_over(mu); contrib.append((name, 100 * (p - prev), note)); prev = p
    p_model = prev; mk = market_mean(books or [], sd); p = p_model; mnote = 'no book line'
    if mk:
        mm, med, nb, pb = mk; w = cfg['market_weight'] * min(1.0, nb / 3.0); p_mkt = p_over(mm); p = (1 - w) * p_model + w * p_mkt
        mnote = 'books at %g (%d book%s, over %.0f%%), PrizePicks %g' % (med, nb, 's' if nb != 1 else '', 100 * pb, line)
    contrib.append(('Market consensus', 100 * (p - p_model), mnote))
    p = min(max(p, .02), .98); side = 'over' if p >= .5 else 'under'; conf = 100 * max(p, 1 - p)
    return dict(line=line, over=100 * p, under=100 * (1 - p), side=side, conf=conf, contrib=contrib, p_model=100 * p_model, market=mk, mean_used=steps[-1][1])

def tier(conf, cfg):
    t = cfg['tiers']
    return 'A' if conf >= t['A'] else 'B' if conf >= t['B'] else 'C' if conf >= t['C'] else 'D'

def edge_score(ev, room_edge=0):
    """Points above a coin flip, plus 5 when model and books agree on the side, plus 3 per Room Edge level."""
    s = ev['conf'] - 50
    if ev['market']:
        mside = 'over' if ev['market'][0] > ev['line'] else 'under'
        if mside == ev['side']: s += 5
    return round(s + 3 * room_edge)

# ----------------------------------------------------------------------------------------------------------------- backtest
def _books_hist(r):
    """Book lines known for a history prop: saved book lines when any were there before the start, else the opening line, else none."""
    try: bl = json.loads(r['book_lines_json'] or '{}')
    except ValueError: bl = {}
    if bl and (r['books_before_start'] or 0) > 0: return [(v[0], v[1] if len(v) > 1 else None, None) for v in bl.values() if isinstance(v, list) and v], 'books'
    if r['open_line'] is not None: return [(r['open_line'], None, None)], 'open'
    return [], 'none'

def backtest(out_md=None, mode='pre'):
    """mode 'pre' = PrizePicks lines saved BEFORE the start only (the lines he could have played). 'open' = every graded prop, using the
    books' opening line as the line (bigger sample, pre-game line). 'all' = every PrizePicks line incl. ones saved after tip (in-game lines, not fair)."""
    cfg = config(); cfg['sd_k'] = {}; cfg['market_weight'] = DEFAULT['market_weight']; E = Engine(cfg)
    db = sqlite3.connect('file:%s?mode=ro' % SB.HIST_DB, uri=True); db.row_factory = sqlite3.Row
    rows = [dict(r) for r in db.execute("select p.*, g.home, g.away, g.open_total, g.close_total, g.open_spread_home, g.close_spread_home from prop_lines p join games g using(event_id) where g.final=1 and p.pp_line is not null and p.stat in (%s)" % ','.join('?' * len(STATS)), list(STATS))]
    db.close(); byev = {}
    for pid, L in E.H.items():
        for r in L: byev[(r['event_id'], pid)] = r
    P = []; skipped = C.Counter(); t0 = dt.datetime.now()
    for r in rows:
        if mode == 'pre' and not r['pp_before_start']: skipped['PrizePicks line saved after tip'] += 1; continue
        if mode == 'open':
            if r['open_line'] is None: skipped['no opening book line'] += 1; continue
            r = dict(r, pp_line=r['open_line'], pp_before_start=1)
        pg = byev.get((r['event_id'], r['player_id']))
        if not pg or not pg['minutes']: skipped['did not play (void)'] += 1; continue
        if any(pg.get(k) is None for k in NEED.get(r['stat'], ())): skipped['stat not in box score'] += 1; continue
        res = STATS[r['stat']][1](pg) if r['stat'] == 'fantasyScore' or r['result'] is None else r['result']
        if res is None: skipped['no result'] += 1; continue
        team = pg['team']; opp_long = r['away'] if pg['home'] else r['home']; d = r['game_date']
        total = r['open_total'] if r['open_total'] is not None else r['close_total']; sp = r['open_spread_home'] if r['open_spread_home'] is not None else r['close_spread_home']
        if sp is not None and not pg['home']: sp = -sp
        reg = E.regulars(team, d); pl = E.played(team, d) or {}; outs = [p for p in reg if p not in pl and p != r['player_id']]
        out_mins = sum(reg[p] for p in outs)
        pr = E.project(r['player_id'], r['stat'], d, opp_long, pg['home'], total, sp, out_mins, pg.get('rest_days'))
        if not pr: skipped['under %d games' % cfg['min_games']] += 1; continue
        books, bsrc = _books_hist(r)
        P.append(dict(stat=r['stat'], date=d, line=r['pp_line'], res=res, m=pr['mean'], sd_raw=pr['sd_raw'], steps=[mu for _, mu, _ in pr['steps']], books=books, bsrc=bsrc,
                      pre=int(r['pp_before_start'] or 0), pid=r['player_id'], board=STATS[r['stat']][3], ev=r['event_id']))
    P.sort(key=lambda x: x['date']); mid = P[len(P) // 2]['date']; first = [x for x in P if x['date'] < mid]; second = [x for x in P if x['date'] >= mid]
    L = ['# NBA probability engine backtest (%s) - %s' % ({'pre': 'PrizePicks lines saved before the start', 'open': 'opening book line as the line', 'all': 'every PrizePicks line incl. after tip'}[mode], dt.datetime.now(CT).strftime('%Y-%m-%d %-I:%M %p CT')), '',
         'Every graded PrizePicks NBA line in the history download with a result and %d+ earlier games for the player: **%d props**, %s to %s.' % (cfg['min_games'], len(P), P[0]['date'], P[-1]['date']),
         'Skipped: ' + ', '.join('%s %d' % (k, v) for k, v in skipped.most_common()) + '.',
         'First half = before %s (%d props), second half = %s onward (%d props). The spread scale per stat and the book weight are FIT ON THE FIRST HALF ONLY and then checked on the second half.' % (mid, len(first), mid, len(second)),
         'Book lines in history: saved pre-start book lines when there were any, else the opening line, else none (%s).' % ', '.join('%s %d' % kv for kv in C.Counter(x['bsrc'] for x in P).most_common()), '']
    # --- fit spread scale per stat (model only) on first half
    OFFS = (-3, -2, -1, 1, 2, 3)
    def p_over(x, k, w, a=0.0, ln=None):
        ln = x['line'] if ln is None else ln; m = x['m'] + a * (x['line'] - x['m']); sd = x['sd_raw'] * k; pm = 1 - phi((ln - m) / sd); mk = market_mean(x['books'], sd)
        if mk and w: ww = w * min(1.0, mk[2] / 3.0); pm = (1 - ww) * pm + ww * (1 - phi((ln - mk[0]) / sd))
        return min(max(pm, .02), .98)
    def logloss(S, k, w, a):
        t = 0.0; n = 0
        for x in S:
            for off in (0,) + OFFS:
                ln = x['line'] + off
                if ln < 0.5: continue
                p = p_over(x, k, w, a, ln); t -= math.log(p if x['res'] > ln else 1 - p); n += 1
        return t / max(1, n)
    import random; rnd = random.Random(7); sd_k = {}; anchor = {}
    for s in STATS:
        S = [x for x in first if x['stat'] == s]
        if len(S) < 200: sd_k[s] = 1.0; anchor[s] = 0.0; continue
        if len(S) > 2500: S = rnd.sample(S, 2500)
        a_, k_ = min(((a / 10.0, k / 10.0) for a in range(0, 10) for k in range(6, 31, 2)), key=lambda ak: logloss(S, ak[1], 0, ak[0]))
        sd_k[s] = k_; anchor[s] = a_
    for x in P: x['k'] = sd_k[x['stat']]; x['a'] = anchor[x['stat']]
    def pov(x, w): return p_over(x, x['k'], w, x['a'])
    wbest = min((w / 10.0 for w in range(0, 11)), key=lambda w: -sum(math.log(pov(x, w) if x['res'] > x['line'] else 1 - pov(x, w)) for x in first if x['books']))
    cfg['sd_k'] = sd_k; cfg['market_weight'] = wbest; cfg['anchor'] = anchor
    if mode == 'pre': json.dump(dict(sd_k=sd_k, anchor=anchor, market_weight=wbest, fit_on='before %s' % mid, fitted=dt.datetime.now(CT).isoformat(), props=len(first), mode=mode), open(FIT_FILE, 'w'), indent=1)
    L += ['## Fit (first half only)', '', 'Fitted on the PrizePicks line and the same line moved -3..+3, so the engine is honest at the line AND on the Goblin/Demon ladder.',
          'Spread scale per stat: ' + ', '.join('%s %.1f' % (STATS[s][0], k) for s, k in sd_k.items()) + '.',
          'Pull toward the PrizePicks standard line per stat (0 = trust our projection only, 0.9 = almost the line itself): ' + ', '.join('%s %.1f' % (STATS[s][0], a) for s, a in anchor.items()) + '.',
          'Book weight %.1f (0 = ignore books, 1 = books only).' % wbest, '']
    for x in P:
        p = pov(x, wbest); x['p'] = p; x['side'] = 'over' if p >= .5 else 'under'; x['conf'] = 100 * max(p, 1 - p); x['tier'] = tier(x['conf'], cfg)
        x['won'] = int((x['res'] > x['line']) == (x['side'] == 'over')) if x['res'] != x['line'] else None
        x['pm_only'] = p_over(x, x['k'], 0, x['a'])
    def pov_at(x, ln): return p_over(x, x['k'], wbest, x['a'], ln)
    def rec(S): S = [x for x in S if x['won'] is not None]; w = sum(x['won'] for x in S); return w, len(S) - w
    def pct(w, l): return '%.0f%%' % (100 * w / (w + l)) if w + l else '-'
    def calib(S, title):
        out = ['### ' + title, '', '| stated confidence | props | actual hit rate |', '|---|---|---|']
        for lo, hi in ((50, 55), (55, 60), (60, 65), (65, 70), (70, 75), (75, 80), (80, 101)):
            B = [x for x in S if lo <= x['conf'] < hi]; w, l = rec(B)
            out.append('| %d-%d%% | %d | %s |' % (lo, min(hi - 1, 99), len(B), pct(w, l)))
        out.append('')
        return out
    for name, S in (('First half (fit half)', first), ('Second half (unseen)', second)):
        L += ['## ' + name, '']; L += calib(S, 'All lines, stated confidence vs what happened')
        L += ['### By tier', '', '| tier | props | won-lost | hit rate |', '|---|---|---|---|']
        for t in 'ABCD':
            B = [x for x in S if x['tier'] == t]; w, l = rec(B); L.append('| %s | %d | %d-%d | %s |' % (t, len(B), w, l, pct(w, l)))
        L += ['', '### Tier A and B by stat', '', '| stat | A+B props | won-lost | hit rate |', '|---|---|---|---|']
        for s in STATS:
            B = [x for x in S if x['stat'] == s and x['tier'] in 'AB']; w, l = rec(B)
            if B: L.append('| %s | %d | %d-%d | %s |' % (STATS[s][0], len(B), w, l, pct(w, l)))
        Bk = [x for x in S if x['books']]
        w1, l1 = rec([dict(x, won=int((x['res'] > x['line']) == (ST.median(b[0] for b in x['books']) > x['line'])) if ST.median(b[0] for b in x['books']) != x['line'] and x['res'] != x['line'] else None) for x in Bk])
        w2, l2 = rec([dict(x, won=int((x['res'] > x['line']) == (x['pm_only'] >= .5)) if x['res'] != x['line'] else None) for x in Bk])
        w3, l3 = rec([x for x in Bk if x['tier'] in 'AB'])
        L += ['', '### Baselines on the %d lines that had a book line' % len(Bk), '', '- Books only (take the side the book line points to): %d-%d (%s)' % (w1, l1, pct(w1, l1)),
              '- Projection only, no books, any confidence: %d-%d (%s)' % (w2, l2, pct(w2, l2)), '- Engine tier A+B (projection + books): %d-%d (%s)' % (w3, l3, pct(w3, l3)), '']
        # ladder check: other lines around the PrizePicks line
        L += ['### Ladder check (Goblin / Demon style lines around the PrizePicks line)', '', 'Same props, lines moved by -6 to +6. Stated over % vs how often the over hit.', '',
              '| stated over % | lines | over hit |', '|---|---|---|']
        LD = C.defaultdict(lambda: [0, 0]); LT = C.defaultdict(lambda: [0, 0])
        for x in S:
            for off in (-6, -4, -3, -2, -1, 1, 2, 3, 4, 6):
                ln = x['line'] + off
                if ln < 0.5 or x['res'] == ln: continue
                p = pov_at(x, ln); b = min(int(p * 10) * 10, 90); LD[b][0] += 1; LD[b][1] += int(x['res'] > ln)
                t = tier(100 * max(p, 1 - p), cfg); won = int((x['res'] > ln) == (p >= .5)); LT[(t, 'Goblin-style (line below ours)' if off < 0 else 'Demon-style (line above ours)')][0] += won; LT[(t, 'Goblin-style (line below ours)' if off < 0 else 'Demon-style (line above ours)')][1] += 1 - won
        for b in sorted(LD): L.append('| %d-%d%% | %d | %.0f%% |' % (b, b + 9, LD[b][0], 100 * LD[b][1] / LD[b][0]))
        L += ['', '### Ladder lines by tier (the engine side, over or under)', '', '| tier | line kind | won-lost | hit rate |', '|---|---|---|---|']
        for (t, kd) in sorted(LT): w_, l_ = LT[(t, kd)]; L.append('| %s | %s | %d-%d | %s |' % (t, kd, w_, l_, pct(w_, l_)))
        L.append('')
        # board test: pre-start lines only, board stats, top 3 by confidence (tier A, then B)
        days = C.defaultdict(list)
        for x in S:
            if x['pre'] and x['board'] and x['won'] is not None and x['tier'] in 'AB': days[x['date']].append(x)
        res = C.Counter(); legs = [0, 0]
        for d, xs in sorted(days.items()):
            xs.sort(key=lambda x: -x['conf']); top = xs[:3]
            if len(top) < 3: res['no board (under 3 picks)'] += 1; continue
            w = sum(x['won'] for x in top); legs[0] += w; legs[1] += 3 - w; res['won' if w == 3 else 'lost'] += 1
        nd = len({x['date'] for x in S if x['pre']})
        L += ['### Top 3 board test (lines saved before the start only, board stats, tier A then B, best 3 by confidence)', '',
              '- Days with PrizePicks lines before the start: %d. Boards built: %d. No board: %d.' % (nd, res['won'] + res['lost'], res['no board (under 3 picks)']),
              '- Whole board won-lost: **%d-%d** (%s). Legs %d-%d (%s).' % (res['won'], res['lost'], pct(res['won'], res['lost']), legs[0], legs[1], pct(*legs)), '']
    L += ['## Honest notes', '', '- A result exactly on the line is a push and is not counted.', '- "Who is out" in history is read from who did not play that night, which includes late scratches nobody knew about before tip. Live, it comes from the ESPN injury feed only.',
          '- History book lines are the saved pre-start lines or the opening line. Live, the engine sees 6 books from The Odds API, which is better than most of history had.',
          '- Game totals and spreads exist for history (%d games) but are not collected live yet, so live cards use a neutral pace factor until that feed is added.' % len(E.totals),
          '- The ESPN box scores that fill the last days have points, rebounds, assists and FG only, so 3PTM / steals / blocks / turnovers / fantasy use history up to the last full download.',
          '', 'Ran in %.0f seconds.' % (dt.datetime.now() - t0).total_seconds()]
    txt = '\n'.join(L); out_md = out_md or os.path.join(REPORTS, '%s_prob_engine_backtest_%s.md' % (dt.datetime.now(CT).strftime('%Y-%m-%d'), mode))
    os.makedirs(REPORTS, exist_ok=True); open(out_md, 'w').write(txt); print(txt); return txt

# ----------------------------------------------------------------------------------------------------------------- today
def book_lines(day):
    """Latest saved line per book: (market, player) -> [(line, over odds, under odds)]."""
    f = os.path.join(ROOT, 'data', 'collected', 'books', day + '.jsonl'); last = {}
    if not os.path.exists(f): return {}
    for l in open(f):
        try: r = json.loads(l)
        except ValueError: continue
        last[(r['book'], r['market'], RC.norm(r['player']))] = (r.get('line'), r.get('over'), r.get('under'))
    out = {}
    for (b, m, p), v in last.items(): out.setdefault((m, p), []).append(v)
    return out
def injuries(day):
    f = os.path.join(ROOT, 'data', 'collected', 'injuries', day + '.jsonl'); last = {}
    if not os.path.exists(f): return {}
    for l in open(f):
        try: r = json.loads(l)
        except ValueError: continue
        last[(r.get('team_abbr'), r.get('player'))] = r.get('status')
    out = C.defaultdict(dict)
    for (t, p), s in last.items(): out[t][p] = s
    return out

def today(day, E=None, now=None):
    E = E or Engine(); now = now or dt.datetime.now(dt.timezone.utc); cfg = E.cfg; lines, saved, bad = SB.load_saved_lines(); books = book_lines(day); inj = injuries(day)
    groups = C.defaultdict(list); meta = {}
    for r in lines:
        try: st = dt.datetime.fromisoformat(str(r.get('start')).replace('Z', '+00:00')).astimezone(dt.timezone.utc)
        except (ValueError, TypeError): continue
        if st.astimezone(CT).date().isoformat() != day or str(r.get('league') or '') != 'NBA' or st <= now or r.get('is_promo') or r.get('flash_sale_line') is not None: continue
        stat = PP.get(str(r.get('stat') or '').strip().lower())
        if not stat: continue
        try: line = float(r.get('line'))
        except (ValueError, TypeError): continue
        name = str(r.get('player') or '?'); team = SB.abbr(r.get('team')); opp, home = SB.parse_opponent(r.get('opponent')); sch = SB._schedule_lookup(team, day)
        if sch: opp = opp or sch[0]
        if not team or not opp or opp not in SB.TEAMS or team not in SB.TEAMS: continue
        pid, why = E.hist.resolve(name, team)
        if not pid: continue
        kind = SB._kind(r); groups[(pid, stat)].append((kind, line)); meta[(pid, stat)] = dict(player=name, team=team, opp=opp, home=home, start=st)
    cards = []
    for (pid, stat), ls in groups.items():
        m = meta[(pid, stat)]; team_id = SB.TEAMS[m['team']][1]; opp_long = SB.TEAMS[m['opp']][0]; lab, fn, floor, onboard, kind = STATS[stat]
        reg = E.regulars(team_id, day); outs, quest = [], []
        for p, s in inj.get(m['team'], {}).items():
            if RC.norm(p) == RC.norm(m['player']): continue
            ids = [i for i in reg if RC.norm(E.name_of.get(i, '')) == RC.norm(p)]
            if s in ('Out', 'Doubtful') and ids: outs.append((p, reg[ids[0]]))
            elif s in ('Questionable', 'Day-To-Day', 'Game Time Decision') and ids: quest.append(p)
        rows = E.H.get(pid, []); last = [h for h in rows if h['game_date'] < day]; rest = (dt.date.fromisoformat(day) - dt.date.fromisoformat(last[-1]['game_date'])).days if last else None
        pr = E.project(pid, stat, day, opp_long, m['home'], None, None, sum(x[1] for x in outs), rest, [x[0] for x in outs])
        if not pr: continue
        bl = books.get((MARKET[stat], RC.norm(m['player'])), [])
        evs = []; stdl = [l for k, l in ls if k == 'standard']; anchor = ST.median(stdl) if stdl else None
        for k, line in sorted(set(ls), key=lambda x: x[1]):
            ev = evaluate(pr, line, bl, cfg, anchor); ev['kind'] = k; e = RE.room_edge(line, [b[0] for b in bl]) if bl else dict(edge=0, side=None, text='')
            ev['room'] = e['edge'] if (e['side'] or '').lower()[:1] == ('m' if ev['side'] == 'over' else 'l') or not e['side'] else 0
            ev['tier'] = tier(ev['conf'], cfg); ev['edge_score'] = edge_score(ev, ev['room']); evs.append(ev)
        # the pick: PrizePicks allows only the over on Goblin and Demon lines
        ok = [e for e in evs if e['kind'] == 'standard' or e['side'] == 'over']
        best = max(ok, key=lambda e: (e['conf'], e['edge_score'])) if ok else None
        cards.append(dict(m, pid=pid, stat=stat, label=lab, onboard=onboard, proj=pr, evs=evs, best=best, quest=quest, outs=outs, nbooks=len(bl), rest=rest))
    cards.sort(key=lambda c: (-(c['best']['conf'] if c['best'] else 0), c['player']))
    return cards, saved

def card_text(c, i, cfg):
    b = c['best']; pr = c['proj']; L = ['%d. **%s** %s v %s · %s · %s' % (i, c['player'], c['team'], c['opp'], c['label'], c['start'].astimezone(CT).strftime('%-I:%M %p CT')) + ('' if c['onboard'] else ' · not a board stat')]
    L.append('   PrizePicks: ' + ' · '.join('%s %g' % (e['kind'].title(), e['line']) for e in c['evs']))
    L.append('   Projection: **%.1f** (spread ±%.1f) · %.0f min · last 5 %.1f · last 10 %.1f · %d games' % (pr['mean'], pr['sd'], pr['mins'], pr['l5'], pr['l10'], pr['games']))
    for e in c['evs']:
        L.append('   %s %g: Over %.0f%% / Under %.0f%%%s' % (e['kind'].title(), e['line'], e['over'], e['under'], ' · tier %s' % e['tier'] if e['kind'] == 'standard' or e['side'] == 'over' else ' · over only on this line'))
    if b and b['conf'] >= cfg['recommend_min']:
        L.append('   🎯 **%s %s %g** · Classification %s · Confidence **%.0f%%** · Tier %s · EDGE SCORE %d' % (b['side'].upper(), c['label'], b['line'], b['kind'].title(), b['conf'], b['tier'], b['edge_score']))
    else: L.append('   🎯 No recommendation (best line %.0f%%, needs %d%%)' % (b['conf'] if b else 0, cfg['recommend_min']))
    if b:
        sgn = 1 if b['side'] == 'over' else -1; why = []
        for name, d, note in b['contrib']:
            d = d * sgn
            if abs(d) >= 1 or name == 'Matchup' or name in ('Market consensus', 'Teammates out') and note not in ('no book line', 'no regular out'): why.append('• %s %+.0f%%: %s' % (name, d, note))
        if c['quest']: why.append('• ⚠ questionable teammates: ' + ', '.join(c['quest'][:3]))
        if c['rest'] == 1: why.append('• 📅 back-to-back')
        if why: L.append('   Why: ' + '  '.join(why))
    return '\n'.join(L)

def text(day, cards, saved, cfg, top=10):
    d = dt.date.fromisoformat(day).strftime('%a %-m/%-d'); rec = [c for c in cards if c['best'] and c['best']['conf'] >= cfg['recommend_min']]
    tiers = C.Counter(c['best']['tier'] for c in rec)
    L = ['🏀 **NBA PROBABILITY ENGINE %s** · %d player-stats not started · recommendations %d (tier A %d, B %d, C %d) · books on %d · ordered by confidence. Report, not a board.'
         % (d, len(cards), len(rec), tiers['A'], tiers['B'], tiers['C'], sum(1 for c in cards if c['nbooks']))]
    L.append('Confidence = the engine\'s own chance the side hits (history, minutes, matchup, rest, teammates out, books as one factor). Tier A 70%+, B 65-69, C 60-64. Goblin/Demon lines: over only.')
    for i, c in enumerate(cards[:top], 1): L.append(card_text(c, i, cfg))
    if len(cards) > top: L.append('… %d more. Full list: python3 code/prob_engine.py today %s --top 999' % (len(cards) - top, day))
    L.append('📥 Lines saved %s. %s' % (dt.datetime.fromisoformat(saved.replace('Z', '+00:00')).astimezone(CT).strftime('%-I:%M %p CT') if saved else 'never', FOOT))
    return '\n'.join(L)

if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == 'backtest': backtest(mode=a[1] if len(a) > 1 else 'pre'); sys.exit()
    days = [x for x in a if x.count('-') == 2 and len(x) == 10]; day = days[0] if days else dt.datetime.now(CT).strftime('%Y-%m-%d')
    top = int(a[a.index('--top') + 1]) if '--top' in a else 10
    E = Engine(); cards, saved = today(day, E); t = text(day, cards, saved, E.cfg, top); print(t)
    if '--post' in a: SR.post('bball-picks', t)
