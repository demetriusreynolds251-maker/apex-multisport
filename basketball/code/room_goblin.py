"""APEX-ROOM-2026-11-11 (owner, "Go room all"): NBA Goblins rated by their ROOM under the sportsbooks.
Room = sportsbooks' number (middle of the books saved from SportsGameOdds) minus the PrizePicks Goblin line, in steps
(2 points, 1 rebound, 1 assist, 3 on Pts+Rebs+Asts, 2 on Pts+Rebs and Pts+Asts, 1 on Rebs+Asts). The number is how often OUR OWN saved,
truly labeled Goblin lines with that much room won (line vault 11/4-11/10/2026, 13,837 Goblins, sportsbooks' number at tip-off):
under 1 step 2201-2044, 1 to 2 steps 3046-1746, 2 to 3 steps 2199-791, 3+ steps 1359-364. Each stat blends its own record with the
all-stats record (weight 30). Only Goblin MORE picks with 2+ sportsbooks; other picks unchanged. Row key is 'groom' ('room' is the
Room Edge level on this bot). Rebuild the tables weekly as the vault grows. Turn off: ON = False, restart the NBA bot."""
import statistics as ST
ON = True
MIN_BOOKS = 2; TOP = 90; BLEND = 30.0
UNIT = {'points': 2, 'rebounds': 1, 'assists': 1, 'points+rebounds+assists': 3, 'points+rebounds': 2, 'points+assists': 2, 'rebounds+assists': 1, 'threePointersMade': 1, 'steals': 1, 'blocks': 1, 'blocks+steals': 1}
# (wins, lines) by steps of room: 0 = under 1 step, 1 = 1 to 2, 2 = 2 to 3, 3 = 3 or more
POOL = {0: (2201, 4245), 1: (3046, 4792), 2: (2199, 2990), 3: (1359, 1723)}
REC = {'points': {0: (372, 718), 1: (545, 846), 2: (502, 686), 3: (268, 337)}, 'rebounds': {0: (120, 231), 1: (358, 567), 2: (296, 392), 3: (113, 135)}, 'assists': {0: (112, 222), 1: (300, 443), 2: (151, 191), 3: (26, 30)}, 'points+rebounds+assists': {0: (487, 942), 1: (367, 588), 2: (351, 459), 3: (60, 69)}, 'points+rebounds': {0: (325, 666), 1: (335, 554), 2: (376, 511), 3: (389, 491)}, 'points+assists': {0: (271, 531), 1: (261, 458), 2: (245, 345), 3: (273, 352)}, 'rebounds+assists': {0: (91, 180), 1: (255, 449), 2: (250, 373), 3: (230, 309)}, 'threePointersMade': {0: (107, 198), 1: (297, 399), 2: (22, 23)}, 'steals': {0: (133, 240), 1: (111, 165)}, 'blocks+steals': {0: (121, 217), 1: (195, 282), 2: (5, 9)}, 'blocks': {0: (62, 100), 1: (22, 41)}}
# APEX-ROOMPLUSAPEX-2026-11-11 (owner, "Go room plus apex", best of the best only): the number now comes from BOTH the room and
# Apex's own rating. CELL[(room steps, Apex band)] = (wins, picks) of this bot's own graded Goblin picks with that room and that Apex
# rating (band 0 = under 70, 1 = 70-79, 2 = 80-89, 3 = 90+), blended (weight 30) with the room record above.
# BEST group = 2 or more steps of room and Apex 70+ (won 840-282 older half, 2201-695 newer half). BEST_ONLY: only that group takes a numbered board spot
# (Top 3, Elite 5, Elite 6, Top 10, Best Goblin); everything else waits in BACKUPS and boards may be short or empty.
# Test: device ~/room_x_apex.py. Turn off: BEST_ONLY = False (boards refill), CELL_ON = False (room-only number), restart.
CELL_ON = True; BEST_ONLY = True
BEST_WORD = '2+ steps of room and Apex 70+'
CELL = {(0, 0): (1658, 3302), (0, 1): (24, 41), (0, 2): (3, 3), (1, 0): (1870, 3082), (1, 1): (461, 699), (1, 2): (80, 108), (1, 3): (3, 4), (2, 0): (518, 744), (2, 1): (1201, 1633), (2, 2): (448, 590), (2, 3): (13, 15), (3, 0): (120, 144), (3, 1): (781, 1016), (3, 2): (575, 737), (3, 3): (23, 27)}
def _band(conf): return 0 if conf < 70 else 1 if conf < 80 else 2 if conf < 90 else 3
def is_best(b, band): return b >= 2 and band >= 1
ABOVE = 31   # a Goblin line above the sportsbooks' number: won 27 of 87


def room(stat, kind, side, line, books, conf):
    """None, or dict(was, to, room, steps, book, n_books, w, n) when this Goblin has a sportsbook number to measure room against."""
    if not ON or kind != 'goblin' or side != 'MORE' or stat not in UNIT: return None
    bl = [b[0] for b in (books or []) if b and b[0] is not None]
    if len(bl) < MIN_BOOKS: return None
    book = ST.median(bl); rm = book - line; steps = rm / float(UNIT[stat])
    if rm < 0: return dict(was=round(conf), to=ABOVE, room=rm, steps=steps, book=book, n_books=len(bl), w=27, n=87, bucket=-1, band=_band(conf), best=False)
    b = min(3, int(steps + 1e-9)); pw, pn = POOL[b]; w, n = REC.get(stat, {}).get(b, (0, 0))
    base = (w + BLEND * pw / pn) / (n + BLEND); band = _band(conf); room_only = min(TOP, round(100.0 * base))
    if CELL_ON:
        cw, cn = CELL.get((b, band), (0, 0)); to = min(TOP, round(100.0 * (cw + BLEND * base) / (cn + BLEND)))
    else: to = room_only
    return dict(was=round(conf), to=to, room=rm, steps=steps, book=book, n_books=len(bl), w=pw, n=pn, bucket=b, band=band, best=bool(CELL_ON and is_best(b, band)), room_only=room_only)


def card_line(row):
    c = row.get('groom')
    if not c: return None
    if c.get('less'):   # APEX-GOBLINLESS-NBA-2026-11-12
        import goblin_less as GL; return GL.card_line(c)
    if c['bucket'] < 0: return '📏 Room: none. This line is %g ABOVE the sportsbooks (%g at %d books). Lines above the books won about %d of 100 this season, so Apex set %d → %d.' % (-c['room'], c['book'], c['n_books'], c['to'], c['was'], c['to'])
    if 'band' not in c or not CELL_ON: return '📏 Room: %g under the sportsbooks (%g at %d books). Real PrizePicks lines with this much room won about %d of 100 this season, so Apex set %d → %d.' % (c['room'], c['book'], c['n_books'], c['to'], c['was'], c['to'])
    t = '📏 Room: %g under the sportsbooks (%g at %d books). Apex rated it %d. Goblins with this much room and this Apex rating won about %d of 100 this season.' % (c['room'], c['book'], c['n_books'], c['was'], c['to'])
    return t + (' ⭐ Best group.' if c.get('best') else ' Not in the best group (%s), so it waits in BACKUPS.' % BEST_WORD if BEST_ONLY else '')
