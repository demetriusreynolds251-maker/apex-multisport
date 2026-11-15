#!/usr/bin/env python3
"""SPORT-SPECIFIC factors: hockey. Live: back-to-back, goalie starter check (saves only for a goalie who started most of the team's last 10),
opponent allowed, home/away. Pending: ice time trend, power play usage, goalie matchup (opponent save %)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as CM
def counts_as_played(g, stat):
    if stat in ('saves', 'goals_against'): return g['stats'].get('saves') is not None
    return bool(g['stats'])
def adjust(E, pid, stat, date, opp, home, rest, ctx, mu):
    out = []
    if rest is not None and rest <= 1: out.append(('Rest', 0.97, 'back-to-back'))
    if stat in ('saves', 'goals_against'):
        past = E.games_before(pid, date)[-10:]; team = past[-1]['team'] if past else None
        if team:
            tg = [x for x in E.TG.get(team, []) if x[0] < date][-10:]; started = sum(1 for g in past if g['stats'].get('saves') is not None and g['date'] >= (tg[0][0] if tg else '0'))
            if tg and started < 5: out.append(('!starter', 1.0, 'goalie started only %d of the team\'s last %d, starter not confirmed' % (started, len(tg))))
            else: out.append(('Starter check', 1.0, 'started %d of the last %d team games' % (started, len(tg) or 10)))
    return out
