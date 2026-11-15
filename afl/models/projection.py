#!/usr/bin/env python3
"""Projection engine for this sport. Reads this sport's history.db only.
For a player + stat on a date it returns a projected mean, a spread, and the step-by-step factor list:
base (season to date) -> recent form (last 5 / last 10) -> opponent allowed -> home/away split -> rest -> sport-specific factors (models/sport_factors.py).
Stat values come from config['stats'][stat]['formula'] over the box-score keys stored in player_games.stats_json."""
import bisect, collections as C, datetime as dt, json, math, os, statistics as ST, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as CM
from database import db as DBM
from models import sport_factors as SF

def stat_value(stats, stat):
    """Value of a configured stat from one game's box-score dict. None when any part is missing."""
    sc = CM.cfg()['stats'][stat]; tot = 0.0
    for k in sc['formula']:
        w = 1.0
        if isinstance(k, list): k, w = k
        v = stats.get(k)
        if v is None:
            a = sc.get('alt'); return float(stats[a]) if a and stats.get(a) is not None else None
        tot += w * float(v)
    return tot

class Engine:
    def __init__(self, db=None, upto=None):
        self.cfg = CM.cfg(); self.db = db or DBM.connect(); self.fits = {r['stat']: dict(r) for r in self.db.execute('select * from fits')}
        rows = self.db.execute('select event_id, player_norm, player, team, opponent, home, game_date, stats_json, source from player_games' + (' where game_date<?' if upto else '') + ' order by game_date, source', (upto,) if upto else ())
        merged = {}
        for r in rows:
            k = (r['event_id'], r['player_norm']); d = merged.get(k)
            st = json.loads(r['stats_json'] or '{}')
            if d: d['stats'].update(st)                       # later source (espn after sgo) fills / overrides
            else: merged[k] = dict(event_id=r['event_id'], pid=r['player_norm'], player=r['player'], team=r['team'], opp=r['opponent'], home=r['home'], date=r['game_date'], stats=st)
        self.H = C.defaultdict(list)             # player -> games sorted by date
        self.TG = C.defaultdict(list)            # (team) -> [(date, event, allowed stats dict)] what the team's opponents did against it
        self.names = {}
        tmp = C.defaultdict(lambda: C.defaultdict(float)); tmpn = C.defaultdict(set)
        for d in merged.values():
            self.H[d['pid']].append(d); self.names[d['pid']] = d['player']
            if d['opp']:
                for k, v in d['stats'].items():
                    if isinstance(v, (int, float)): tmp[(d['opp'], d['event_id'], d['date'])][k] += v
                tmpn[(d['opp'], d['event_id'], d['date'])].add(d['team'])
        for L in self.H.values(): L.sort(key=lambda x: x['date'])
        for (team, ev, date), st in tmp.items(): self.TG[team].append((date, ev, dict(st)))
        for L in self.TG.values(): L.sort(key=lambda x: x[0])
        self.lg_cache = {}

    # ----------------------------------------------------------------------------------------------- team / league context
    def team_allowed(self, team, stat, date, n=None):
        """Average of this stat that opponents produced against `team` in its last n games before date."""
        n = n or self.cfg.get('opp_games', 12); L = self.TG.get(team) or []
        i = bisect.bisect_left([x[0] for x in L], date); vals = []
        for d, ev, st in L[max(0, i - n):i]:
            v = stat_value(st, stat)
            if v is not None: vals.append(v)
        return (ST.mean(vals), len(vals)) if vals else (None, 0)
    def league_allowed(self, stat, date):
        key = (stat, date[:7])
        if key not in self.lg_cache:
            vals = []
            for team, L in self.TG.items():
                i = bisect.bisect_left([x[0] for x in L], date)
                for d, ev, st in L[max(0, i - 12):i]:
                    v = stat_value(st, stat)
                    if v is not None: vals.append(v)
            self.lg_cache[key] = ST.mean(vals) if len(vals) >= 20 else None
        return self.lg_cache[key]

    # ----------------------------------------------------------------------------------------------- projection
    def games_before(self, pid, date):
        L = self.H.get(pid) or []; i = bisect.bisect_left([x['date'] for x in L], date); return L[:i]
    def project(self, pid, stat, date, opp=None, home=None, ctx=None):
        c = self.cfg; sc = c['stats'][stat]; ctx = ctx or {}
        past = [g for g in self.games_before(pid, date) if SF.counts_as_played(g, stat)]
        # APEX-SAMENAME-ALL-2026-11-08 (owner "Fix all problems"; same as soccer 11/7): two players with one name show up
        # as games for two teams in the same months. Then keep only the games for the team he plays for today. A trade
        # (one team ends, the next starts) is not touched.
        tc = (ctx or {}).get('team_code') or (ctx or {}).get('team')
        if tc and past:
            span = {}
            for g in past: lo, hi = span.get(g['team'], (g['date'], g['date'])); span[g['team']] = (min(lo, g['date']), max(hi, g['date']))
            mine = [g for g in past if g['team'] == tc]
            if tc in span and len(span) > 1 and len(mine) >= self.cfg.get('min_games', 6) and any(t != tc and hi > span[tc][0] and lo < span[tc][1] for t, (lo, hi) in span.items()):
                past = mine
        vals = [(g['date'], stat_value(g['stats'], stat), g) for g in past]; vals = [v for v in vals if v[1] is not None]
        if len(vals) < c.get('min_games', 6): return None
        xs = [v[1] for v in vals]; season = CM.season_of(date); sx = [v[1] for v in vals if CM.season_of(v[0]) == season]
        base = ST.mean(sx) if len(sx) >= c.get('min_games', 6) else (0.6 * ST.mean(sx) + 0.4 * ST.mean(xs[-25:]) if sx else ST.mean(xs[-25:]))
        l5 = ST.mean(xs[-5:]); l10 = ST.mean(xs[-10:]); rw = c.get('recent_weight', 0.5)
        steps = [('Base projection', base, '%s average %.1f over %d games' % ('season' if len(sx) >= c.get('min_games', 6) else 'recent', base, len(sx) or len(xs[-25:])))]
        mu = (1 - rw) * base + rw * (0.45 * l5 + 0.55 * l10); steps.append(('Recent form', mu, 'last 5 %.1f, last 10 %.1f' % (l5, l10)))
        if opp:
            ta, n = self.team_allowed(opp, stat, date); lg = self.league_allowed(stat, date)
            if ta is not None and lg and n >= 5:
                f = ta / lg; f = 1 + c.get('opp_weight', 0.5) * (f - 1); f = min(max(f, 0.8), 1.2); mu *= f
                steps.append(('Matchup', mu, '%s allows %+.0f%% %s vs league (last %d)' % (opp, 100 * (ta / lg - 1), sc['label'].lower(), n)))
        if home is not None and len(vals) >= 10:
            hv = [v[1] for v in vals if v[2]['home'] == int(home)]; av = [v[1] for v in vals if v[2]['home'] != int(home)]
            if len(hv) >= 4 and len(av) >= 4 and ST.mean(xs) > 0:
                f = 1 + 0.5 * (ST.mean(hv) / ST.mean(xs) - 1); f = min(max(f, 0.9), 1.1); mu *= f
                steps.append(('Home / away', mu, '%s average %.1f vs %.1f overall' % ('home' if home else 'away', ST.mean(hv), ST.mean(xs))))
        rest = None
        try: rest = (dt.date.fromisoformat(date) - dt.date.fromisoformat(vals[-1][0])).days
        except ValueError: pass
        no_play = None
        for name, mult, note in SF.adjust(self, pid, stat, date, opp, home, rest, ctx, mu):
            if name.startswith('!'): no_play = note; continue
            mu *= mult; steps.append((name, mu, note))
        mu = max(mu, 0.0)
        # spread: residual around a rolling mean of the last 20, inflated for small samples, with a floor per stat
        tail = xs[-20:]; resid = [tail[i] - ST.mean(tail[max(0, i - 10):i] or [tail[i]]) for i in range(1, len(tail))]
        sd = ST.pstdev(resid) if len(resid) >= 3 else ST.pstdev(tail) if len(tail) >= 2 else max(mu * 0.5, sc.get('sd_floor', 1))
        sd = max(sd, sc.get('sd_floor', 0.5)) * (1 + 4.0 / len(xs))
        if sc.get('dist') == 'poisson': sd = max(sd, math.sqrt(max(mu, 0.05)))
        k = (self.fits.get(stat) or {}).get('sd_k') or 1.0
        return dict(stat=stat, pid=pid, mean=mu, sd=sd * k, sd_raw=sd, steps=steps, games=len(xs), l5=l5, l10=l10, base=base, season_games=len(sx), last_date=vals[-1][0], rest=rest, dist=sc.get('dist', 'normal'), no_play=no_play)

if __name__ == '__main__':
    E = Engine(); print('players with history', len(E.H), 'teams', len(E.TG))
