"""APEX-SOCCERREAL-2026-11-12 (owner, "Go fix soccer numbers"): a regular-line Shots LESS pick is rated at what picks rated
like it really hit, not the engine's raw number. Test 11/12 (~/openclaw/_backups/soccer_numbers_1112/): 5,301 regular Shots LESS
lines where the player really played, scored by today's engine, older days / newer days (split 11/1/2025), real hits per 100:
  rated 70-74: 71 / 62     75-79: 76 / 68     80-84: 78 / 70     85-89: 80 / 71     90-94: 82 / 76     95+: 76 / 75
The order is right, the level ran 10-16 too high. The newer days are used (2,678 lines, the lower and more current number), and the
rating is only ever lowered. Shots on Target and Goalie Saves LESS matched their numbers (they rarely rate above 70): no change.
Turn off: ON = False, restart soccer."""
# APEX-SOCCERHISTORY-2026-11-12 (owner, "Fix soccer history"): the stored shot counts before Dec 2025 left out blocked shots, which made
# the older days look better than they were and taught the engine ratings that ran high. History was re-graded with the real box scores
# (history/shots_fix.py) and the engine learned again. Every line re-scored and graded by the box score, 2025 / 2026 / all, real hits per 100:
#   rated 60-64: 57 / 59 / 58   65-69: 62 / 62 / 62   70-74: 65 / 69 / 67   75-79: 69 / 68 / 68   80-84: 71 / 78 / 74   85+: 72 / 68 / 70
# The two years agree now, so all days are used (4,171 lines). Old numbers before this: git tag before-soccer-history.
ON = True
KNOTS = {'shots': ((58, 57), (62.5, 58), (67.5, 62), (72.5, 67), (77.5, 68), (82.5, 73), (100, 73))}
N = {'shots': 4171}
WORDS = {'shots': 'Shots'}


def _line(K, conf):
    if conf <= K[0][0]: return conf
    for (x0, y0), (x1, y1) in zip(K, K[1:]):
        if conf <= x1: return y0 + (y1 - y0) * (conf - x0) / float(x1 - x0)
    return K[-1][1]


# APEX-LINEUPLESS-2026-11-12 (owner, "Go lineup less"): once ESPN posts the lineup, the lineup sets the number.
# Same 5,017 clean Shots LESS lines, by what the player did THAT match (older / newer days):
#   STARTED:   any rating 1515-610 / 945-735 (56)   rated 80+ 75 / 59   85+ 75 / 61   90+ 76 / 64
#   BENCH:     rated 70+ 396-24 / 559-64 (90)       80+ 93 / 89         90+ 91 / 89   under 70: 44-1 / 97-27 (78)
# Newer days used. A bench player who never comes on is a void on PrizePicks, not a loss.
LINEUP_ON = True
# APEX-SOCCERHISTORY-2026-11-12: after the history fix (box score grading, both years):
#   STARTED: rated under 60: 52   60-64: 54   65-69: 55   70-79: 58   80+: 60     (2025 1302-1029, 2026 781-634)
#   BENCH:   rated 70+: 687-81 (89)   under 70: 2026 186-41 (82)                  (2025 496-65, 2026 581-80)
START_KNOTS = ((0, 52), (57, 52), (62.5, 54), (67.5, 55), (72.5, 58), (77.5, 58), (82.5, 60), (100, 60))
START_N, BENCH_N = 3746, 1222
BENCH_HI, BENCH_LO = 88, 82      # raw Apex rating 70+ / under 70


def real(stat, kind, side, conf, lineup=None):
    """None, or dict(was, to, what, n[, lineup]) when this regular LESS pick's rating moves to its real number."""
    if not ON or kind != 'standard' or side != 'LESS' or stat not in KNOTS: return None
    if LINEUP_ON and lineup == 'start':
        to = round(min(conf, _line(START_KNOTS, conf)), 1)
        return dict(was=round(conf), to=to, what=WORDS[stat], n=START_N, lineup='start')
    if LINEUP_ON and lineup == 'bench':
        return dict(was=round(conf), to=float(BENCH_HI if conf >= 70 else BENCH_LO), what=WORDS[stat], n=BENCH_N, lineup='bench')
    to = round(min(conf, _line(KNOTS[stat], conf)), 1)
    return dict(was=round(conf), to=to, what=WORDS[stat], n=N[stat]) if round(to) < round(conf) else None


def card_line(row):
    c = row.get('less_real')
    if not c: return None
    if c.get('lineup') == 'start': return '📉 Lineup is out and he STARTS. Regular %s LESS on a starter really hits about %d of 100, so the rating is %d, not %d.' % (c['what'], round(c['to']), round(c['to']), c['was'])
    if c.get('lineup') == 'bench': return '🪑 Lineup is out and he is on the BENCH. Regular %s LESS on a bench player really hits about %d of 100 (a void if he never comes on). Rating %d.' % (c['what'], round(c['to']), round(c['to']))
    return '📉 Regular %s LESS picks Apex rated %d really hit about %d of 100 (clean history, players who played), so the rating is %d, not %d.' % (c['what'], c['was'], round(c['to']), round(c['to']), c['was'])
