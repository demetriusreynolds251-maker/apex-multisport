#!/usr/bin/env python3
"""Probability engine for this sport: Over % / Under % for a line from a projection, with the factor breakdown, tiers, edge score and plain reasons.
Normal tail for volume stats (yards, points, shots), Poisson / negative-binomial for count stats (goals, touchdowns, home runs, tries).
The PrizePicks standard line is a sharp number, so the projection is pulled toward it by a fitted share (database.fits.anchor, fit by backtesting/backtest.py).
Book lines (when collected) are one more factor, blended by the fitted market weight."""
import math, os, statistics as ST, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as CM

def phi(z): return 0.5 * math.erfc(-z / math.sqrt(2))
def phi_inv(p):
    p = min(max(p, 1e-6), 1 - 1e-6); lo, hi = -8.0, 8.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if phi(mid) < p: lo = mid
        else: hi = mid
    return (lo + hi) / 2
def amer_prob(o):
    try: o = float(o)
    except (TypeError, ValueError): return None
    return 100 / (o + 100) if o > 0 else -o / (-o + 100)
def devig(po, pu):
    if po is None or pu is None: return 0.5
    return po / (po + pu)

def p_over(mu, sd, line, dist='normal'):
    """P(X > line). A line like 24.5 means X >= 25 for count stats."""
    if dist == 'poisson':
        mu = max(mu, 1e-6); var = max(sd * sd, mu + 1e-9); k = int(math.floor(line))
        if var <= mu * 1.02:  # plain Poisson
            cdf = sum(math.exp(-mu) * mu ** i / math.factorial(i) for i in range(0, min(k, 170) + 1))
        else:                  # negative binomial with the same mean and variance
            r = mu * mu / (var - mu); p = r / (r + mu); cdf = 0.0; pm = p ** r
            for i in range(0, min(k, 300) + 1):
                cdf += pm; pm *= (r + i) / (i + 1) * (1 - p)
        return min(max(1 - cdf, 0.0), 1.0)
    return 1 - phi((line - mu) / max(sd, 1e-6))

def market_mean(books, sd, dist='normal'):
    """books: [(line, over odds, under odds)] -> (market mean, median line, n books, implied over prob) or None."""
    books = [b for b in books if b and b[0] is not None]
    if not books: return None
    med = ST.median(b[0] for b in books); ps = [devig(amer_prob(b[1]), amer_prob(b[2])) for b in books if abs(b[0] - med) < 1e-9 and b[1] is not None and b[2] is not None]
    p = ST.mean(ps) if ps else 0.5; p = min(max(p, .2), .8)
    return med + sd * phi_inv(p), med, len(books), p

def evaluate(proj, line, books=None, fits=None, anchor=None):
    c = CM.cfg(); fit = (fits or {}).get(proj['stat']) or {}; sd = proj['sd']; dist = proj.get('dist', 'normal'); steps = list(proj['steps'])
    a = fit.get('anchor') or 0.0
    if a and anchor is not None:
        m0 = steps[-1][1]; m1 = m0 + a * (anchor - m0); steps.append(('PrizePicks line', m1, 'standard line %g pulls the projection %+.1f (sharp number)' % (anchor, m1 - m0)))
    contrib = []; prev = 0.5
    for name, mu, note in steps:
        p = p_over(mu, sd, line, dist); contrib.append((name, 100 * (p - prev), note)); prev = p
    p_model = prev; mk = market_mean(books or [], sd, dist); p = p_model; mnote = 'no book line'
    if mk:
        mm, med, nb, pb = mk; w = (fit.get('market_weight') if fit.get('market_weight') is not None else c.get('market_weight', 0.5)) * min(1.0, nb / 3.0)
        if c.get('books_display_only'): w = 0.0   # APEX-SGOBOOKS-2026-11-11: book line shows on the card, the rating does not move (book weight never proven on clean history)
        p = (1 - w) * p_model + w * p_over(mm, sd, line, dist); mnote = 'books at %g (%d book%s, over %.0f%%)' % (med, nb, '' if nb == 1 else 's', 100 * pb)
    contrib.append(('Market', 100 * (p - p_model), mnote))
    p = min(max(p, .02), .98); side = 'over' if p >= .5 else 'under'; conf = 100 * max(p, 1 - p)
    ev = dict(line=line, mean_used=steps[-1][1], over=100 * p, under=100 * (1 - p), side=side, conf=conf, contrib=contrib, p_model=100 * p_model, market=mk and dict(mean=mk[0], line=mk[1], n=mk[2], p=mk[3]))
    ev['tier'] = tier(conf); ev['edge_score'] = edge_score(ev); ev['reasons'] = reasons(ev); return ev

def tier(conf):
    t = CM.cfg()['tiers']; return 'A' if conf >= t['A'] else 'B' if conf >= t['B'] else 'C' if conf >= t['C'] else 'D'
def edge_score(ev):
    """Points above a coin flip, plus 5 when the books point the same way."""
    s = ev['conf'] - 50
    if ev['market'] and not CM.cfg().get('books_display_only'): s += 5 if (('over' if ev['market']['line'] < ev['line'] else 'under') == ev['side'] if ev['market']['line'] != ev['line'] else False) else 0
    return round(s)
def reasons(ev):
    sgn = 1 if ev['side'] == 'over' else -1; out = []
    for name, d, note in ev['contrib']:
        d *= sgn
        # APEX-COLLEGEREASONS-2026-11-13 (owner, "Go fix college reasons"): the Matchup step is always kept (even under 1 point) so the card
        # always says what the opponent did to the pick. Display only. Undo: git checkout before-college-reasons.
        if abs(d) >= 1 or name in ('Market',) and note != 'no book line' or name == 'Matchup': out.append((name, round(d), note))
    return out
