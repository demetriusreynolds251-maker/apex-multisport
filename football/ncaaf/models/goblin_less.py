"""APEX-GOBLINLESS-2026-11-12 (owner, "Go goblin less gap"): PrizePicks sells LESS as a Goblin on some Demon lines (feed field
allowed_wager_types = under_or_over, saved by the collector in pp_wager). Apex was blind to that side. Each such line now also becomes a
Goblin LESS pick, rated by its GAP above the sportsbooks: PrizePicks line minus the sportsbooks' number, in steps (1 catch, 10 yards, 1 shot ...).
The number is how often LESS really won on real PrizePicks Demon lines with that gap, 11/5-11/10/2026 (line vault x sportsbook numbers,
did-not-play left out; older days then newer days agree):
  same as the books 83-62 (57 of 100)   under 1 step above 376-314 (54)   1 to 2 steps 512-296 (63)
  2 to 3 steps 222-72 (76)               3+ steps 849-38 (shown as 90 at most)   below the books 11-12 (48)
BEST group = 1 full step or more above the books AND a record of 70 of 100 or better: only those take numbered board spots; the rest wait in BACKUPS. No sportsbook number =
not proven = BACKUPS. Test: ~/openclaw/_backups/goblin_less_1112/gl_room.py. Turn off: ON = False, restart."""
import statistics as ST
ON = True
MIN_BOOKS = 2; TOP = 90; BEST_STEPS = 1; BEST_MIN = 80; APEX_MIN = 75
# APEX-LESSFLOOR-2026-11-12 (owner: "It need to be limit minimum on these props, I want the best of the best, I don't care if the boards are short"):
# a Goblin LESS takes a numbered spot only when it is a full step or more above the sportsbooks, its number is 80 of 100 or better AND Apex itself rates
# LESS 75 or higher. Everything else waits in BACKUPS. Was 70 with no Apex minimum. Undo: BEST_MIN = 70; APEX_MIN = 0, restart.
# bucket: -1 below the books, 0 same as the books, 1 under 1 step above, 2 = 1 to 2 steps, 3 = 2 to 3 steps, 4 = 3 or more
REC = {-1: (11, 23), 0: (83, 145), 1: (376, 690), 2: (512, 808), 3: (222, 294), 4: (849, 887)}
WORD = {-1: 'below the sportsbooks', 0: 'the same as the sportsbooks', 1: 'under 1 step above the sportsbooks', 2: '1 to 2 steps above the sportsbooks', 3: '2 to 3 steps above the sportsbooks', 4: '3 or more steps above the sportsbooks'}

# APEX-LESSPLUSAPEX-2026-11-12 (owner, "Go less plus apex"): the number now comes from BOTH the gap and Apex's own LESS rating.
# CELL[(gap group, Apex band)] = (LESS wins, picks) of this bot's own graded Demon picks since 11/5 matched to the sportsbooks' number
# (gap group 0 = same as / below the books, 1 = under 1 step above, 2 = 1 to 2 steps, 3 = 2 or more; Apex band 0 = under 60, 1 = 60-74,
# 2 = 75-89, 3 = 90+), blended (weight 30) with the gap record above. Test: ~/openclaw/_backups/goblin_less_1112/gl_apex2.py.
# Turn off: CELL_ON = False (gap-only number), restart.
CELL_ON = True; BLEND = 30.0
CELL = {(0, 0): (28, 48), (1, 0): (131, 250), (1, 1): (42, 81), (2, 0): (126, 196), (2, 1): (86, 142), (2, 2): (16, 32), (3, 0): (33, 38), (3, 1): (92, 115), (3, 2): (195, 212), (3, 3): (352, 363)}
def _band(up): return 0 if up < 60 else 1 if up < 75 else 2 if up < 90 else 3


def sold(db):
    """{(projection_id, line)} of Demon lines whose latest saved state sells LESS too."""
    if not ON: return set()
    try:
        out = set()
        for pid, line, wager in db.execute("select w.projection_id, w.line, w.wager from pp_wager w join (select projection_id, line, max(last_seen) m from pp_wager where kind='demon' group by 1, 2) x on x.projection_id=w.projection_id and x.line=w.line and x.m=w.last_seen where w.kind='demon'"):
            if wager == 'under_or_over': out.add((str(pid), float(line)))
        return out
    except Exception: return set()

def rate(stat, line, books, under_p, unit):
    """None (no sportsbook number), or the gap record for a Goblin LESS on this line. Same keys as models/room.py so cards and the Best 6 card read it."""
    if not ON or stat not in unit: return None
    bl = [b[0] for b in (books or []) if b and b[0] is not None]
    if len(bl) < MIN_BOOKS: return None
    book = ST.median(bl); gap = line - book; steps = gap / float(unit[stat])
    b = -1 if gap < -1e-9 else 0 if gap < 1e-9 else 1 if steps < 1 - 1e-9 else 2 if steps < 2 - 1e-9 else 3 if steps < 3 - 1e-9 else 4
    w, n = REC[b]; gap_only = min(TOP, round(100.0 * w / n)); to = gap_only; band = _band(under_p); cw = cn = 0
    if CELL_ON:
        cw, cn = CELL.get((0 if b <= 0 else 1 if b == 1 else 2 if b == 2 else 3, band), (0, 0))
        to = min(TOP, round(100.0 * (cw + BLEND * w / float(n)) / (cn + BLEND)))
    return dict(less=True, was=round(under_p), to=to, room=gap, steps=steps, book=book, n_books=len(bl), w=w, n=n, bucket=b, band=band, best=bool(steps >= BEST_STEPS - 1e-9 and to >= BEST_MIN and under_p >= APEX_MIN), room_only=gap_only, cw=cw, cn=cn)

def card_line(c):
    t = '📏 Gap: this line is %s (PrizePicks %g, sportsbooks %g at %d books). LESS on lines with this gap won %d of %d this season. Apex itself rated LESS %d%s. Together: about %d of 100.' % (WORD[c['bucket']], c['book'] + c['room'], c['book'], c['n_books'], c['w'], c['n'], c['was'], (', and with that rating too it won %d of %d' % (c['cw'], c['cn'])) if c.get('cn') else '', c['to'])
    return t + (' ⭐ Best group.' if c.get('best') else ' Not in the best group (a full step or more above the sportsbooks, %d of 100 or better, and Apex %d or higher on LESS), so it waits in BACKUPS.' % (BEST_MIN, APEX_MIN))
