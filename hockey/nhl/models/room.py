"""APEX-ROOM-2026-11-11 (owner, "Go room all"): NHL Goblins rated by their ROOM under the sportsbooks.
Room = sportsbooks' number (middle of the books saved from SportsGameOdds) minus the PrizePicks Goblin line, in steps (1 shot on goal, 1 point,
1 blocked shot, 1 hit, 3 goalie saves). The number is how often OUR OWN saved, truly labeled Goblin lines with that much room won
(line vault 11/5-11/10/2026, 1,615 Goblins, sportsbooks' number at kickoff): under 1 step 412-290, 1 to 2 steps 667-191,
2+ steps 50-5 (shown as 90 at most). Each stat blends its own record with the all-stats record (weight 30).
Only Goblin MORE picks with 2+ sportsbooks; other picks unchanged. Rebuild the tables weekly as the vault grows.
Test notes: ~/openclaw/_backups/sgo_book_1111/ (books_pull.py, alt/BK_*.jsonl). Turn off: ON = False, restart the sport."""
import statistics as ST
ON = True
MIN_BOOKS = 2; TOP = 90; BLEND = 30.0
UNIT = {'sog': 1, 'points': 1, 'assists': 1, 'saves': 3, 'blocked': 1, 'hits': 1}
# (wins, lines) by steps of room: 0 = under 1 step, 1 = 1 to 2, 2 = 2 to 3, 3 = 3 or more
POOL = {0: (412, 702), 1: (667, 858), 2: (50, 55), 3: (50, 55)}
REC = {'assists': {0: (27, 47), 1: (3, 4)}, 'blocked': {0: (26, 45), 1: (54, 75), 2: (1, 1)}, 'points': {0: (154, 255), 1: (37, 45)}, 'saves': {0: (63, 104), 1: (68, 92), 2: (14, 17)}, 'sog': {0: (142, 251), 1: (505, 642), 2: (35, 37), 3: (35, 37)}}
# APEX-ROOMPLUSAPEX-2026-11-11 (owner, "Go room plus apex", best of the best only): the number now comes from BOTH the room and
# Apex's own rating. CELL[(room steps, Apex band)] = (wins, picks) of this bot's own graded Goblin picks with that room and that Apex
# rating (band 0 = under 70, 1 = 70-79, 2 = 80-89, 3 = 90+), blended (weight 30) with the room record above.
# BEST group = 1 or more steps of room with Apex 80+, or 2 or more steps with Apex 70+ (won 7-0 older half, 47-13 newer; 2+ steps 18-5). BEST_ONLY: only that group takes a numbered board spot
# (Top 3, Elite 5, Elite 6, Top 10, Best Goblin); everything else waits in BACKUPS and boards may be short or empty.
# Test: device ~/room_x_apex.py. Turn off: BEST_ONLY = False (boards refill), CELL_ON = False (room-only number), restart.
CELL_ON = True; BEST_ONLY = True
# 11/11 his 'for score let's raise that 85 and up with the room rule': a numbered spot also needs Apex's own rating BEST_MIN or higher.
# Replay 342 days (1/31/2025-10/30/2026) Top 3: 85+ won 19 lost 3 older half, 30-13 newer; 80+ 32-11, 49-25. Test: ~/openclaw/_backups/nhl_hi_1111. Turn off: BEST_MIN = 0, restart.
BEST_MIN = 85
BEST_WORD = '1+ step of room and Apex 85+'
CELL = {(0, 0): (210, 366), (0, 1): (24, 40), (0, 2): (3, 7), (1, 0): (85, 123), (1, 1): (96, 127), (1, 2): (40, 47), (1, 3): (6, 8), (2, 0): (3, 4), (2, 1): (10, 11), (2, 2): (7, 10), (2, 3): (1, 2)}
def _band(conf): return 0 if conf < 70 else 1 if conf < 80 else 2 if conf < 90 else 3
def is_best(b, band, conf=None): return ((b >= 2 and band >= 1) or (b >= 1 and band >= 2)) and (conf is None or conf >= BEST_MIN)
ABOVE = 45   # a Goblin line above the sportsbooks' number


def room(stat, kind, side, line, books, conf):
    """None, or dict(was, to, room, steps, book, n_books, w, n) when this Goblin has a sportsbook number to measure room against."""
    if not ON or kind != 'goblin' or side != 'MORE' or stat not in UNIT: return None
    bl = [b[0] for b in (books or []) if b and b[0] is not None]
    if len(bl) < MIN_BOOKS: return None
    book = ST.median(bl); rm = book - line; steps = rm / float(UNIT[stat])
    if rm < 0: return dict(was=round(conf), to=ABOVE, room=rm, steps=steps, book=book, n_books=len(bl), w=0, n=0, bucket=-1, band=_band(conf), best=False)
    b = min(3, int(steps + 1e-9)); pw, pn = POOL[b]; w, n = REC.get(stat, {}).get(b, (0, 0))
    base = (w + BLEND * pw / pn) / (n + BLEND); band = _band(conf); room_only = min(TOP, round(100.0 * base))
    if CELL_ON:
        cw, cn = CELL.get((b, band), (0, 0)); to = min(TOP, round(100.0 * (cw + BLEND * base) / (cn + BLEND)))
    else: to = room_only
    return dict(was=round(conf), to=to, room=rm, steps=steps, book=book, n_books=len(bl), w=pw, n=pn, bucket=b, band=band, best=bool(CELL_ON and is_best(b, band, conf)), room_only=room_only)


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
