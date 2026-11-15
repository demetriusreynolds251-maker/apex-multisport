#!/usr/bin/env python3
"""SPORT-SPECIFIC factors: baseball. Live: park factor (static table, half weight, hitters only), opponent team allowed, home/away.
Pending: opposing pitcher, bullpen, batting order, handedness splits, weather."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as CM
PARK = {'COL': 1.15, 'CIN': 1.07, 'BOS': 1.05, 'TEX': 1.03, 'PHI': 1.03, 'ATL': 1.02, 'LAD': 1.02, 'NYY': 1.02, 'SF': 0.93, 'SD': 0.95, 'SEA': 0.92, 'MIA': 0.95, 'OAK': 0.93, 'ATH': 0.95, 'STL': 0.97, 'DET': 0.96, 'CLE': 0.96, 'TB': 0.96}
HIT = ('hits', 'runs', 'rbis', 'home_runs', 'total_bases', 'hits_runs_rbis', 'singles', 'doubles')
def counts_as_played(g, stat):
    if stat in ('pitcher_ks', 'pitching_outs', 'earned_runs', 'hits_allowed', 'walks_allowed'): return g['stats'].get('pitcher_ks') is not None or g['stats'].get('pitching_outs_raw') is not None
    return bool(g['stats'])
def adjust(E, pid, stat, date, opp, home, rest, ctx, mu):
    out = []
    if stat in HIT:
        park_team = ctx.get('team') if home else opp
        f = PARK.get(str(park_team or '').upper())
        if f: f = 1 + 0.5 * (f - 1) * (2 if stat == 'home_runs' else 1); out.append(('Park', f, '%s park plays %s' % (park_team, 'up' if f > 1 else 'down')))
    return out
