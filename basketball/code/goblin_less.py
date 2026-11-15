"""APEX-GOBLINLESS-NBA-2026-11-12 (owner, "Go goblin less nba ... shouldn't it have apex"): PrizePicks sells LESS as a Goblin on
some Demon lines (feed field allowed_wager_types = under_or_over, saved by the line collector in data/wager/DATE.jsonl). Each such
line now also becomes a Goblin LESS pick, rated by BOTH its GAP above the sportsbooks (PrizePicks line minus the sportsbooks' number, in
steps: 2 points, 1 rebound, 1 assist, 3 on Pts+Rebs+Asts, 2 on Pts+Rebs and Pts+Asts, 1 on Rebs+Asts) AND Apex's own LESS rating.
Record = this bot's own graded Demon picks 11/4-11/10/2026 matched to the sportsbooks' number (16,695 picks; LESS won when MORE lost;
did-not-play left out; older days then newer days agree):
  below the books 114-135   same as the books 689-524 (57 of 100)   under 1 step above 1299-803 (62)
  1 to 2 steps 2086-941 (69)   2 to 3 steps 1578-367 (81)   3+ steps 7702-457 (shown as 90 at most)
CELL[(gap group, Apex band)] = (LESS wins, picks); gap group 0 = same as / below the books, 1 = under 1 step, 2 = 1 to 2 steps, 3 = 2 or more;
Apex band 0 = Apex LESS under 60, 1 = 60-74, 2 = 75-89, 3 = 90+. Blended (weight 30) with the gap record.
BEST group = 1 full step or more above the books AND 70 of 100 or better: only those take numbered board spots; the rest wait in BACKUPS.
No sportsbook number (before the 12:45 PM CT book pull, or a stat the books do not carry) = not proven = BACKUPS.
Test: ~/openclaw/_backups/goblin_less_1112/gl_apex_nba.py. Turn off: ON = False, restart the NBA bot."""
import glob, json, os, statistics as ST
ON = True
MIN_BOOKS = 2; TOP = 90; BEST_STEPS = 1; BEST_MIN = 80; APEX_MIN = 75; BLEND = 30.0; CELL_ON = True
# APEX-LESSFLOOR-2026-11-12 (owner: "It need to be limit minimum on these props, I want the best of the best, I don't care if the boards are short"):
# a Goblin LESS takes a numbered spot only when it is a full step or more above the sportsbooks, its number is 80 of 100 or better AND Apex itself rates
# LESS 75 or higher. Everything else waits in BACKUPS. Was 70 with no Apex minimum. Undo: BEST_MIN = 70; APEX_MIN = 0, restart.
UNIT = {'points': 2, 'rebounds': 1, 'assists': 1, 'points+rebounds+assists': 3, 'points+rebounds': 2, 'points+assists': 2, 'rebounds+assists': 1}
REC = {-1: (114, 249), 0: (689, 1213), 1: (1299, 2102), 2: (2086, 3027), 3: (1578, 1945), 4: (7702, 8159)}
WORD = {-1: 'below the sportsbooks', 0: 'the same as the sportsbooks', 1: 'under 1 step above the sportsbooks', 2: '1 to 2 steps above the sportsbooks', 3: '2 to 3 steps above the sportsbooks', 4: '3 or more steps above the sportsbooks'}
CELL = {(0, 0): (685, 1242), (0, 1): (104, 199), (0, 2): (11, 18), (0, 3): (3, 3), (1, 0): (1131, 1837), (1, 1): (165, 258), (1, 2): (3, 7), (2, 0): (698, 1060), (2, 1): (1183, 1692), (2, 2): (195, 261), (2, 3): (10, 14),
        (3, 0): (48, 66), (3, 1): (785, 991), (3, 2): (2520, 2887), (3, 3): (5927, 6160)}
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def _band(up): return 0 if up < 60 else 1 if up < 75 else 2 if up < 90 else 3


def sold(days=4):
    """{(projection_id, line)} of Demon lines whose latest saved state sells LESS too (last few day files, oldest first)."""
    if not ON: return set()
    try:
        last = {}
        for f in sorted(glob.glob(os.path.join(ROOT, 'data', 'wager', '*.jsonl')))[-days:]:
            for l in open(f):
                try: r = json.loads(l)
                except ValueError: continue
                last[str(r.get('projection_id'))] = r
        return {(pid, float(r['line'])) for pid, r in last.items() if r.get('odds_type') == 'demon' and r.get('wager') == 'under_or_over' and r.get('line') is not None}
    except Exception: return set()

def rate(stat, line, books, under_p):
    """None (no sportsbook number), or the gap + Apex record for a Goblin LESS on this line. Same keys as room_goblin.room()."""
    if not ON or stat not in UNIT: return None
    bl = [b[0] for b in (books or []) if b and b[0] is not None]
    if len(bl) < MIN_BOOKS: return None
    book = ST.median(bl); gap = line - book; steps = gap / float(UNIT[stat])
    b = -1 if gap < -1e-9 else 0 if gap < 1e-9 else 1 if steps < 1 - 1e-9 else 2 if steps < 2 - 1e-9 else 3 if steps < 3 - 1e-9 else 4
    w, n = REC[b]; gap_only = min(TOP, round(100.0 * w / n)); to = gap_only; band = _band(under_p); cw = cn = 0
    if CELL_ON:
        cw, cn = CELL.get((0 if b <= 0 else 1 if b == 1 else 2 if b == 2 else 3, band), (0, 0))
        to = min(TOP, round(100.0 * (cw + BLEND * w / float(n)) / (cn + BLEND)))
    return dict(less=True, was=round(under_p), to=to, room=gap, steps=steps, book=book, n_books=len(bl), w=w, n=n, bucket=b, band=band, best=bool(steps >= BEST_STEPS - 1e-9 and to >= BEST_MIN and under_p >= APEX_MIN), room_only=gap_only, cw=cw, cn=cn)

def card_line(c):
    t = '📏 Gap: this line is %s (PrizePicks %g, sportsbooks %g at %d books). LESS on lines with this gap won %s of %s this season. Apex itself rated LESS %d%s. Together: about %d of 100.' % (WORD[c['bucket']], c['book'] + c['room'], c['book'], c['n_books'], format(c['w'], ','), format(c['n'], ','), c['was'], (', and with that rating too it won %s of %s' % (format(c['cw'], ','), format(c['cn'], ','))) if c.get('cn') else '', c['to'])
    return t + (' ⭐ Best group.' if c.get('best') else ' Not in the best group (a full step or more above the sportsbooks, %d of 100 or better, and Apex %d or higher on LESS), so it waits in BACKUPS.' % (BEST_MIN, APEX_MIN))
