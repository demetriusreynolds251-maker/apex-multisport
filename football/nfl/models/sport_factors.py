#!/usr/bin/env python3
"""SPORT-SPECIFIC factors: football (NFL / college). Live: game script from the ESPN spread and total saved in games (favorites run more,
underdogs throw more; high totals lift everything). Pending (no data on this Mac yet): snap share, target share, routes, red zone usage, weather."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as CM

PASS = ('pass_yds', 'pass_tds', 'completions', 'pass_att', 'rec_yds', 'receptions', 'targets', 'long_rec', 'rec_tds', 'pass_rush_yds'); RUSH = ('rush_yds', 'rush_att', 'long_rush', 'rush_tds')
def counts_as_played(g, stat): return bool(g['stats'])
def game_row(ctx):
    db = ctx.get('db')
    if not db or not ctx.get('team'): return None
    return db.execute("select total, spread_home, home, away from games where game_date=? and (home=? or away=?) and source='espn' order by rowid desc limit 1", (ctx.get('game_date'), ctx['team'], ctx['team'])).fetchone()
def adjust(E, pid, stat, date, opp, home, rest, ctx, mu):
    out = []; g = game_row(ctx)
    if g:
        total, sp = g['total'], g['spread_home']
        if sp is not None and g['home'] and g['away']:
            my_sp = sp if ctx['team'] == g['home'] else -sp      # negative = favorite
            if stat in PASS and abs(my_sp) >= 6: f = 1 + 0.04 * (1 if my_sp > 0 else -1); out.append(('Game script', f, '%s by %g: %s' % ('underdog' if my_sp > 0 else 'favorite', abs(my_sp), 'more passing expected' if my_sp > 0 else 'less passing expected')))
            if stat in RUSH and abs(my_sp) >= 6: f = 1 + 0.05 * (1 if my_sp < 0 else -1); out.append(('Game script', f, '%s by %g: %s' % ('favorite' if my_sp < 0 else 'underdog', abs(my_sp), 'more running expected' if my_sp < 0 else 'less running expected')))
        if total is not None:
            lg = 45.0 if CM.cfg()['sport'] == 'nfl' else 55.0; f = min(max((total / lg) ** 0.5, 0.92), 1.08)
            if abs(f - 1) >= 0.02: out.append(('Game total', f, 'total %g vs usual %g' % (total, lg)))
    return out
