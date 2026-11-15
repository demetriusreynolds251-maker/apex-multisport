#!/usr/bin/env python3
"""SPORT-SPECIFIC factors for this sport (edited per sport; the generic engine calls adjust() and counts_as_played()).
Each factor returns (name, multiplier, plain note). Only factors with data on this Mac are live; the rest are listed in README as pending."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as CM

def counts_as_played(g, stat):
    """A game counts in the history when the player actually took part. Default: any recorded stat."""
    return bool(g['stats'])

def adjust(E, pid, stat, date, opp, home, rest, ctx, mu):
    out = []
    if rest is not None and rest <= 1 and CM.cfg().get('b2b_factor'): out.append(('Rest', CM.cfg()['b2b_factor'], 'played yesterday'))
    return out
