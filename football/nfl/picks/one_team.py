#!/usr/bin/env python3
"""APEX-ONETEAM-2026-11-12 (his go: "Proper fix all until it's no data poison"): one player = one team per game.
After a trade or signing PrizePicks can keep a player's OLD team label on some of his lines (Kirk Cousins LV + MIN,
Josh Downs IND + KC, Jake Moody BAL + ATL on the 11/15 slate; Audric Estime NO + CLE on 11/8). The game on the line is right,
the team label is stale, so the opponent was worked out wrong.
Rule, per player per game:
  1. a team label that is not one of the two teams in the game is corrected to the label his other lines in that game carry;
     with no other line to learn from, the line is left out (the side cannot be known);
  2. two labels that are both in the game: every line takes the label most of his lines carry.
No line is dropped when the right team can be known. Undo: ON = False."""
ON = True

def _u(x): return str(x or '').upper()

def one_team(lines, log=None):
    if not ON: return lines
    by = {}
    for r in lines:
        if '/' in str(r['team'] or ''): continue   # combo lines (two players) are not single-team lines
        by.setdefault((r['player_norm'], r.get('game_id') or r['start']), []).append(r)
    out_ids = set()
    for (pn, gid), rs in by.items():
        if len({_u(r['team']) for r in rs}) < 2 and all(not r.get('home_abbr') or _u(r['team']) in (_u(r.get('home_abbr')), _u(r.get('away_abbr'))) for r in rs): continue
        game = {_u(rs[0].get('home_abbr')), _u(rs[0].get('away_abbr'))} - {''}
        good = [r for r in rs if not game or _u(r['team']) in game]; n = {}
        for r in good: n[_u(r['team'])] = n.get(_u(r['team']), 0) + 1
        if not n:
            out_ids.update(id(r) for r in rs)
            if log: log('pipeline', 'one team: %s is labeled %s but the game is %s, side unknown, %d lines left out' % (pn, _u(rs[0]['team']), ' v '.join(sorted(game)), len(rs)))
            continue
        keep = max(n, key=lambda t: n[t]); fixed = 0
        for r in rs:
            if _u(r['team']) != keep: r['team_was'] = r['team']; r['team'] = keep; fixed += 1
        if fixed and log: log('pipeline', 'one team: %s, %d lines relabeled to %s (game %s)' % (pn, fixed, keep, ' v '.join(sorted(game))))
    return [r for r in lines if id(r) not in out_ids]
