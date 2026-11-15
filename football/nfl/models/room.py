"""APEX-ROOM-2026-11-11 (owner, "Go room NFL"): NFL Goblins rated by their ROOM under the sportsbooks, the tennis way.
Room = sportsbooks' number (middle of the books saved from SportsGameOdds) minus the PrizePicks Goblin line, counted in steps
(1 catch, 10 yards, 2 rush attempts, 25 pass yards ...). The number is how often real PrizePicks lines with that much room won
this season: 136 NFL games 9/10-11/10/2026 from SportsGameOdds history (lines posted before kickoff, books' number at kickoff,
did-not-play left out). All stats together, older half (to 10/15) then newer half:
  under 1 step of room  1830-1343 / 1375-1099  (57 of 100)      1 to 2 steps  318-140 / 551-270  (68 of 100)
  2 to 3 steps          36-9 / 385-84          (82 of 100)      3+ steps      5-0 / 142-12       (92 of 100, shown as 90 at most)
Each stat uses its own record blended with the all-stats record (weight 30 lines). Only Goblin MORE picks with 2+ sportsbooks.
Data + test: ~/openclaw/_backups/sgo_book_1111/alt/NFL.jsonl, alt_pull.py. Turn off: ON = False, restart NFL."""
import statistics as ST
ON = True
MIN_BOOKS = 2; TOP = 90; BLEND = 30.0
UNIT = {'receptions': 1, 'rec_yds': 10, 'rush_yds': 10, 'rush_att': 2, 'pass_yds': 25, 'pass_att': 3, 'completions': 2, 'tackles_ast': 1, 'long_rec': 3, 'long_rush': 2, 'rush_rec_yds': 10, 'pass_rush_yds': 25}
WORD = {1: 'catch', 10: 'yards', 2: 'attempts', 25: 'yards', 3: ''}
# (wins, lines) by steps of room: 0 = under 1 step, 1 = 1 to 2, 2 = 2 to 3, 3 = 3 or more
POOL = {0: (3205, 5647), 1: (869, 1279), 2: (421, 514), 3: (147, 159)}
REC = {'completions': {0: (56, 93), 1: (26, 40), 2: (23, 28), 3: (5, 5)}, 'long_rec': {0: (774, 1397), 1: (200, 328), 2: (48, 63), 3: (22, 22)}, 'long_rush': {0: (199, 375), 1: (111, 175), 2: (21, 26), 3: (4, 4)},
       'pass_att': {0: (114, 176), 1: (38, 53), 2: (31, 37), 3: (1, 1)}, 'pass_rush_yds': {0: (651, 1197), 1: (20, 34), 2: (60, 74), 3: (4, 4)}, 'pass_yds': {0: (391, 641), 1: (25, 38), 2: (63, 72), 3: (6, 7)},
       'rec_yds': {0: (1106, 1952), 1: (166, 225), 2: (68, 86), 3: (54, 62)}, 'receptions': {0: (24, 39), 1: (108, 146), 2: (52, 59), 3: (6, 6)}, 'rush_att': {0: (120, 206), 1: (76, 96), 2: (33, 39), 3: (16, 16)},
       'rush_rec_yds': {0: (396, 770), 1: (60, 78), 2: (17, 25), 3: (22, 26)}, 'rush_yds': {0: (420, 762), 1: (80, 126), 2: (61, 80), 3: (20, 22)}, 'tackles_ast': {0: (1, 6), 1: (39, 52), 2: (21, 24), 3: (13, 14)}}
# APEX-ROOMPLUSAPEX-2026-11-11 (owner, "Go room plus apex", best of the best only): the number now comes from BOTH the room and
# Apex's own rating. CELL[(room steps, Apex band)] = (wins, picks) of this bot's own graded Goblin picks with that room and that Apex
# rating (band 0 = under 70, 1 = 70-79, 2 = 80-89, 3 = 90+), blended (weight 30) with the room record above.
# BEST group = 2 or more steps of room and Apex 70+ (won 197-38 on 11/8, 16-2 on 11/9). BEST_ONLY: only that group takes a numbered board spot
# (Top 3, Elite 5, Elite 6, Top 10, Best Goblin); everything else waits in BACKUPS and boards may be short or empty.
# Test: device ~/room_x_apex.py. Turn off: BEST_ONLY = False (boards refill), CELL_ON = False (room-only number), restart.
CELL_ON = True; BEST_ONLY = True
BEST_WORD = '2+ steps of room and Apex 70+'
CELL = {(0, 0): (610, 1101), (0, 1): (1, 2), (0, 2): (1, 2), (1, 0): (593, 845), (1, 1): (59, 80), (1, 2): (5, 9), (1, 3): (1, 1), (2, 0): (287, 369), (2, 1): (108, 135), (2, 2): (38, 44), (2, 3): (3, 5), (3, 0): (49, 57), (3, 1): (39, 41), (3, 2): (19, 22), (3, 3): (6, 6)}
def _band(conf): return 0 if conf < 70 else 1 if conf < 80 else 2 if conf < 90 else 3
def is_best(b, band): return b >= 2 and band >= 1
ABOVE = 45   # a Goblin line above the sportsbooks' number: lines above the books won 268 of 984


def room(stat, kind, side, line, books, conf):
    """None, or dict(was, to, room, steps, book, n_books, w, n) when this Goblin has a sportsbook number to measure room against."""
    if not ON or kind != 'goblin' or side != 'MORE' or stat not in UNIT: return None
    bl = [b[0] for b in (books or []) if b and b[0] is not None]
    if len(bl) < MIN_BOOKS: return None
    book = ST.median(bl); rm = book - line; steps = rm / float(UNIT[stat])
    if rm < 0: return dict(was=round(conf), to=ABOVE, room=rm, steps=steps, book=book, n_books=len(bl), w=268, n=984, bucket=-1, band=_band(conf), best=False)
    b = min(3, int(steps + 1e-9)); pw, pn = POOL[b]; w, n = REC.get(stat, {}).get(b, (0, 0))
    base = (w + BLEND * pw / pn) / (n + BLEND); band = _band(conf); room_only = min(TOP, round(100.0 * base))
    if CELL_ON:
        cw, cn = CELL.get((b, band), (0, 0)); to = min(TOP, round(100.0 * (cw + BLEND * base) / (cn + BLEND)))
    else: to = room_only
    return dict(was=round(conf), to=to, room=rm, steps=steps, book=book, n_books=len(bl), w=pw, n=pn, bucket=b, band=band, best=bool(CELL_ON and is_best(b, band)), room_only=room_only)


def card_line(row):
    c = row.get('room')
    if not c: return None
    if c.get('less'):   # APEX-GOBLINLESS-2026-11-12
        from models import goblin_less as GL
        return GL.card_line(c)
    if c['bucket'] < 0: return '📏 Room: none. This line is %g ABOVE the sportsbooks (%g at %d books). Lines above the books won about %d of 100 this season, so Apex set %d → %d.' % (-c['room'], c['book'], c['n_books'], c['to'], c['was'], c['to'])
    if 'band' not in c or not CELL_ON: return '📏 Room: %g under the sportsbooks (%g at %d books). Real PrizePicks lines with this much room won about %d of 100 this season, so Apex set %d → %d.' % (c['room'], c['book'], c['n_books'], c['to'], c['was'], c['to'])
    t = '📏 Room: %g under the sportsbooks (%g at %d books). Apex rated it %d. Goblins with this much room and this Apex rating won about %d of 100 this season.' % (c['room'], c['book'], c['n_books'], c['was'], c['to'])
    return t + (' ⭐ Best group.' if c.get('best') else ' Not in the best group (%s), so it waits in BACKUPS.' % BEST_WORD if BEST_ONLY else '')
