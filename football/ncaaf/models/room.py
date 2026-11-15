"""APEX-ROOM-2026-11-11 (owner, "Go room all"): college football Goblins rated by their ROOM under the sportsbooks.
Room = sportsbooks' number (middle of the books saved from SportsGameOdds) minus the PrizePicks Goblin line, in steps (1 catch, 10 yards,
2 rush attempts, 25 pass yards ...). The number is how often OUR OWN saved, truly labeled Goblin lines with that much room won
(line vault 11/5-11/10/2026, 2,498 Goblins, sportsbooks' number at kickoff): under 1 step 552-390, 1 to 2 steps 538-228,
2 to 3 steps 412-97, 3+ steps 183-25 (shown as 90 at most). Each stat blends its own record with the all-stats record (weight 30).
Only Goblin MORE picks with 2+ sportsbooks; other picks unchanged. Rebuild the tables weekly as the vault grows.
Test notes: ~/openclaw/_backups/sgo_book_1111/ (books_pull.py, alt/BK_*.jsonl). Turn off: ON = False, restart the sport."""
import statistics as ST
ON = True
MIN_BOOKS = 2; TOP = 90; BLEND = 30.0
UNIT = {'receptions': 1, 'rec_yds': 10, 'rush_yds': 10, 'rush_att': 2, 'pass_yds': 25, 'pass_att': 3, 'completions': 2, 'tackles_ast': 1, 'long_rec': 3, 'long_rush': 2, 'rush_rec_yds': 10, 'pass_rush_yds': 25}
# (wins, lines) by steps of room: 0 = under 1 step, 1 = 1 to 2, 2 = 2 to 3, 3 = 3 or more
POOL = {0: (552, 942), 1: (538, 766), 2: (412, 509), 3: (183, 208)}
REC = {'completions': {0: (18, 26), 1: (18, 23), 2: (2, 2)}, 'pass_att': {0: (29, 37), 1: (24, 29)}, 'pass_rush_yds': {0: (30, 56), 1: (6, 7), 2: (18, 24), 3: (17, 17)}, 'pass_yds': {0: (76, 128), 1: (35, 54), 2: (69, 79), 3: (16, 20)}, 'rec_yds': {0: (200, 336), 1: (197, 265), 2: (154, 189), 3: (63, 66)}, 'receptions': {0: (48, 77), 1: (131, 182), 2: (67, 81), 3: (3, 4)}, 'rush_att': {0: (20, 34), 1: (13, 28)}, 'rush_yds': {0: (109, 206), 1: (112, 175), 2: (102, 134), 3: (84, 101)}, 'long_rec': {0: (9, 20)}, 'long_rush': {0: (5, 12), 1: (1, 1)}}
# APEX-ROOMPLUSAPEX-2026-11-11 (owner, "Go room plus apex", best of the best only): the number now comes from BOTH the room and
# Apex's own rating. CELL[(room steps, Apex band)] = (wins, picks) of this bot's own graded Goblin picks with that room and that Apex
# rating (band 0 = under 70, 1 = 70-79, 2 = 80-89, 3 = 90+), blended (weight 30) with the room record above.
# BEST group = 2 or more steps of room and Apex 70+ (won 14-0 older half, 141-23 newer half). BEST_ONLY: only that group takes a numbered board spot
# (Top 3, Elite 5, Elite 6, Top 10, Best Goblin); everything else waits in BACKUPS and boards may be short or empty.
# Test: device ~/room_x_apex.py. Turn off: BEST_ONLY = False (boards refill), CELL_ON = False (room-only number), restart.
CELL_ON = True; BEST_ONLY = True
BEST_WORD = '2+ steps of room and Apex 70+'
CELL = {(0, 0): (236, 413), (0, 1): (9, 12), (0, 2): (2, 2), (1, 0): (201, 278), (1, 1): (39, 47), (1, 2): (6, 6), (2, 0): (108, 143), (2, 1): (61, 73), (2, 2): (22, 24), (2, 3): (4, 4), (3, 0): (37, 46), (3, 1): (54, 59), (3, 2): (10, 14), (3, 3): (4, 4)}
def _band(conf): return 0 if conf < 70 else 1 if conf < 80 else 2 if conf < 90 else 3
def is_best(b, band): return b >= 2 and band >= 1
ABOVE = 50   # a Goblin line above the sportsbooks' number


def room(stat, kind, side, line, books, conf):
    """None, or dict(was, to, room, steps, book, n_books, w, n) when this Goblin has a sportsbook number to measure room against."""
    if not ON or kind != 'goblin' or side != 'MORE' or stat not in UNIT: return None
    bl = [b[0] for b in (books or []) if b and b[0] is not None]
    if len(bl) < MIN_BOOKS: return None
    book = ST.median(bl); rm = book - line; steps = rm / float(UNIT[stat])
    if rm < 0: return dict(was=round(conf), to=ABOVE, room=rm, steps=steps, book=book, n_books=len(bl), w=37, n=73, bucket=-1, band=_band(conf), best=False)
    b = min(3, int(steps + 1e-9)); pw, pn = POOL[b]; w, n = REC.get(stat, {}).get(b, (0, 0))
    base = (w + BLEND * pw / pn) / (n + BLEND); band = _band(conf); room_only = min(TOP, round(100.0 * base))
    if CELL_ON:
        cw, cn = CELL.get((b, band), (0, 0)); to = min(TOP, round(100.0 * (cw + BLEND * base) / (cn + BLEND)))
    else: to = room_only
    return dict(was=round(conf), to=to, room=rm, steps=steps, book=book, n_books=len(bl), w=pw, n=pn, bucket=b, band=band, best=bool(CELL_ON and is_best(b, band)), room_only=room_only)


def card_line(row):
    c = row.get('room')
    if not c: return None
    if c.get('truth'):   # APEX-COLLEGETRUTH-2026-11-13: the true number, with its count, no cap
        from models import truth as TR
        return '📏 Room: %g under the sportsbooks (%g at %d books). Apex rated it %d.%s\n%s' % (c['room'], c['book'], c['n_books'], c['was'], ' ⭐ Best group.' if c.get('best') else '', TR.card_line(c))
    if c.get('less'):   # APEX-GOBLINLESS-2026-11-12
        from models import goblin_less as GL
        return GL.card_line(c)
    if c['bucket'] < 0: return '📏 Room: none. This line is %g ABOVE the sportsbooks (%g at %d books). Lines above the books won about %d of 100 this season, so Apex set %d → %d.' % (-c['room'], c['book'], c['n_books'], c['to'], c['was'], c['to'])
    if 'band' not in c or not CELL_ON: return '📏 Room: %g under the sportsbooks (%g at %d books). Real PrizePicks lines with this much room won about %d of 100 this season, so Apex set %d → %d.' % (c['room'], c['book'], c['n_books'], c['to'], c['was'], c['to'])
    t = '📏 Room: %g under the sportsbooks (%g at %d books). Apex rated it %d. Goblins with this much room and this Apex rating won about %d of 100 this season.' % (c['room'], c['book'], c['n_books'], c['was'], c['to'])
    return t + (' ⭐ Best group.' if c.get('best') else ' Not in the best group (%s), so it waits in BACKUPS.' % BEST_WORD if BEST_ONLY else '')
