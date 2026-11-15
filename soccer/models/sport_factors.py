#!/usr/bin/env python3
"""SPORT-SPECIFIC factors: soccer. Live: starter check (played most of the team's last 10), home/away, opponent allowed.
Pending: xG / xA, possession, league strength, confirmed line-ups."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as CM
def counts_as_played(g, stat):
    if stat == 'saves': return g['stats'].get('saves') is not None
    if g['stats'].get('appearances') == 0 and not any(v for k, v in g['stats'].items() if k not in ('_played', 'appearances')): return False   # APEX-APPEARED-2026-11-12: never came on
    return bool(g['stats'])
def adjust(E, pid, stat, date, opp, home, rest, ctx, mu):
    out = []; past = E.games_before(pid, date); team = past[-1]['team'] if past else None
    if team:
        tg = [x for x in E.TG.get(team, []) if x[0] < date][-10:]
        if tg:
            played = sum(1 for g in past if g['date'] >= tg[0][0] and counts_as_played(g, stat))   # APEX-APPEARED-2026-11-12: bench games are not games played
            if played < 6: out.append(('!starter', 1.0, 'played %d of the team\'s last %d, not a regular starter' % (played, len(tg))))
            else: out.append(('Starter check', 1.0, 'played %d of the last %d team games' % (played, len(tg))))
    if rest is not None and rest <= 3: out.append(('Rest', 0.98, 'second game in %d days' % rest))
    return out
