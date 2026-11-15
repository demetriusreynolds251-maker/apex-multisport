"""APEX-GOBLINREAL-2026-11-10 (owner, "Fix all" after "check goblins", then "go touches tune"): NFL Goblin ratings moved to
what they really win, where the replay of past seasons at real Goblin depth showed a steady gap in BOTH halves (did-not-play left out).
Touches = rush attempts + catches, average of the player's last 5 games; busy = 12 or more.
  Rush Attempts, busy backs   rated 60-69: won 81 of 140 / 87 of 134 (about 61)   70-79: 64 of 111 / 85 of 122 (about 64)
                              80+: 51 of 63 / 45 of 62 (about 77).   Medium-use backs matched their number (49 of 66 in the 70s): no change.
  Rush Yards, busy backs      rated 60-69: won 73 of 95 / 59 of 79 (about 76); real picks 11/8-11/9: 57 won 16 lost. Raised to 76 at most.
  Tackles+Ast (any player)    rated 80-89: won 28 of 36 / 40 of 56 (about 74)
Every other NFL Goblin type matched its number and touches made no difference there. The picks still compete for board spots like
any other. Tests: ~/openclaw/_backups/goblins_1110/syn.py and ~/openclaw/_backups/touches_all_1110/t.py.
Turn off: ON = False, restart NFL."""
ON = True
BUSY = 12.0
KNOTS = {'rush_att': ((58, 58), (65, 61), (75, 64), (84, 77), (96, 87)),       # busy backs only
         'tackles_ast': ((62, 62), (75, 73), (83, 74), (96, 81))}                # any player
WORDS = {'rush_att': 'Rush Attempts', 'tackles_ast': 'Tackles', 'rush_yds': 'Rush Yards'}
RUSH_YDS_FROM, RUSH_YDS_TOP, RUSH_YDS_ADD = 60, 76, 11                           # busy backs only


def _line(K, conf):
    if conf <= K[0][0]: return conf
    for (x0, y0), (x1, y1) in zip(K, K[1:]):
        if conf <= x1: return y0 + (y1 - y0) * (conf - x0) / float(x1 - x0)
    return K[-1][1]


def real(stat, kind, side, conf, touches=None):
    """None, or dict(was, to, what, busy) when this Goblin's rating moves to its real number."""
    if not ON or kind != 'goblin' or side != 'MORE': return None
    busy = touches is not None and touches >= BUSY
    if stat == 'tackles_ast': to = _line(KNOTS[stat], conf)
    elif stat == 'rush_att' and busy: to = _line(KNOTS[stat], conf)
    elif stat == 'rush_yds' and busy and RUSH_YDS_FROM <= conf < RUSH_YDS_TOP: to = min(RUSH_YDS_TOP, conf + RUSH_YDS_ADD)
    else: return None
    to = round(to)
    return dict(was=round(conf), to=to, what=WORDS[stat], busy=busy and stat != 'tackles_ast', t=round(touches) if touches is not None else None) if to != round(conf) else None


def card_line(row):
    c = row.get('goblin_real')
    if not c: return None
    who = ' on busy backs (about %d touches a game)' % c['t'] if c.get('busy') and c.get('t') else ''
    if c['to'] > c['was']: return '📈 %s Goblins%s rated like this really win about %d of 100, so Apex raised %d → %d.' % (c['what'], who, c['to'], c['was'], c['to'])
    return '📉 %s Goblins%s rated this high really win about %d of 100, so Apex lowered %d → %d.' % (c['what'], who, c['to'], c['was'], c['to'])
