#!/usr/bin/env python3
"""APEX BASKETBALL - Room Edge qualification layer (his direction 2026-11-05 6:49 AM CT).
Room = PrizePicks line minus the middle (median) sportsbook line before tip.
  Room Edge 2: PP higher than books by 1+ -> LESS; PP lower than books by 2+ -> MORE   (board picks)
  Room Edge 1: PP lower than books by 1 (1 to 1.5) -> MORE                                (backups only)
  Room Edge 0: same line, half-point gap, or no book line                                 (no edge)
Prop types allowed on room boards: points, rebounds, assists, PRA, PR, PA, RA, FG made. Excluded: 3PM, steals, blocks, turnovers, FT attempts (history does not support them)."""
import statistics as st
BOARD_STATS = ('points', 'rebounds', 'assists', 'points+rebounds+assists', 'points+rebounds', 'points+assists', 'rebounds+assists', 'fieldGoalsMade')
EXCLUDED = ('threePointersMade', 'steals', 'blocks', 'turnovers', 'freeThrowsAttempted', 'blocks+steals')
def room(pp_line, book_lines):
    """PrizePicks line minus the middle book line, or None without a book line."""
    bl = [float(b) for b in (book_lines or []) if b is not None]
    return (float(pp_line) - st.median(bl)) if bl else None
def room_edge(pp_line, book_lines):
    """Returns dict(edge=0/1/2, side='MORE'/'LESS'/None, room=float or None, text=plain words for the card)."""
    r = room(pp_line, book_lines)
    if r is None: return dict(edge=0, side=None, room=None, text='Room Edge 0: no book line to compare')
    if r >= 1: return dict(edge=2, side='LESS', room=r, text='Room Edge 2: PrizePicks line %g above the books, LESS' % r)
    if r <= -2: return dict(edge=2, side='MORE', room=r, text='Room Edge 2: PrizePicks line %g below the books, MORE' % -r)
    if r <= -1: return dict(edge=1, side='MORE', room=r, text='Room Edge 1: PrizePicks line %g below the books, MORE (backup only)' % -r)
    if r == 0: return dict(edge=0, side=None, room=0.0, text='Room Edge 0: same line as the books')
    return dict(edge=0, side=None, room=r, text='Room Edge 0: half a point %s the books, no edge' % ('above' if r > 0 else 'below'))
def stat_allowed(stat): return stat in BOARD_STATS
if __name__ == '__main__':
    for pp, bl in [(24.5, [25.5, 26.5]), (7.5, [9.5]), (7.5, [8.5]), (7.5, [8.0]), (7.5, [7.5]), (7.5, [])]: print(pp, bl, room_edge(pp, bl))
