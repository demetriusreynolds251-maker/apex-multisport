#!/usr/bin/env python3
"""SPORT-SPECIFIC factors: generic start (AFL / Rugby League). Live: recent form, season base, opponent allowed, home/away.
Pending: everything in config factors.pending; the engine starts once the collector has saved games and results for this sport."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as CM
def counts_as_played(g, stat): return bool(g['stats'])
def adjust(E, pid, stat, date, opp, home, rest, ctx, mu):
    out = []
    if rest is not None and rest <= 4: out.append(('Rest', 0.98, 'short turnaround, %d days' % rest))
    return out
