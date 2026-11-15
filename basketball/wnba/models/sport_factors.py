#!/usr/bin/env python3
"""SPORT-SPECIFIC factors: basketball (WNBA / college). Live: minutes trend (recent minutes vs usual), teammates listed Out (WNBA, ESPN feed),
back-to-back. Pending: usage %, pace, defense vs position."""
import os, statistics as ST, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as CM
def counts_as_played(g, stat):
    m = g['stats'].get('minutes'); return (m is None and bool(g['stats'])) or (m is not None and m > 0)
def adjust(E, pid, stat, date, opp, home, rest, ctx, mu):
    out = []; past = [g for g in E.games_before(pid, date) if counts_as_played(g, stat)]
    mins = [g['stats'].get('minutes') for g in past if g['stats'].get('minutes') is not None]
    if len(mins) >= 8 and stat not in ('fantasy',):
        usual = ST.mean(mins[-25:]); recent = 0.6 * ST.mean(mins[-5:]) + 0.4 * ST.mean(mins[-10:])
        if usual > 5:
            f = min(max(1 + 0.6 * (recent / usual - 1), 0.85), 1.15)
            if abs(f - 1) >= 0.02: out.append(('Minutes trend', f, '%.0f min lately vs %.0f usual' % (recent, usual)))
    inj = ctx.get('injuries') or {}; team = ctx.get('team')
    if team and inj:
        outs = [p for p, d in inj.items() if d.get('team') == team and d.get('status') in ('Out', 'Doubtful') and p != pid]
        if outs: out.append(('Teammates out', min(1 + 0.03 * len(outs), 1.10), '%d teammate%s listed out' % (len(outs), '' if len(outs) == 1 else 's')))
    if rest is not None and rest <= 1: out.append(('Rest', 0.98, 'back-to-back'))
    return out
