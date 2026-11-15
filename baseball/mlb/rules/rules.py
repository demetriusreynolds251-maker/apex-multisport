#!/usr/bin/env python3
"""Rules for this sport: what is a valid pick, what is a no-play, and how the boards are filled.
Rules live in config['rules'] and config['boards']; this file applies them the same way to every pick on every board.
No play when: the player is listed Out / Doubtful, the stat is not a board stat, the line is a promo or flash sale, the player is banned,
the game has started, the player has too few games, or the number is under the board floor. Goblin / Demon lines: MORE only (PrizePicks rule)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as CM

OUT_STATUSES = ('Out', 'Doubtful', 'Injured Reserve', 'Suspension', 'Suspended', 'IR')
SHAKY = ('Questionable', 'Day-To-Day', 'Game Time Decision', 'Probable')

def no_play_reason(row, injuries, banned):
    """Returns the plain reason a pick is not allowed, or None when it is a valid pick."""
    c = CM.cfg(); r = c['rules']
    if row.get('promo'): return 'promo or flash sale line'
    if row.get('stat') is None: return 'stat the engine does not score'
    if not c['stats'][row['stat']].get('board', True): return 'not a board stat'
    if row['player_norm'] in banned: return 'banned player'
    st = (injuries.get(row['player_norm']) or {}).get('status')
    if st in OUT_STATUSES: return 'listed %s' % st
    if row['kind'] in ('goblin', 'demon') and row['side'] != 'MORE': return 'Goblin / Demon lines are over only'
    if row.get('games', 0) < r.get('min_games', 6): return 'under %d games of history' % r.get('min_games', 6)
    if r.get('no_shaky_on_board') and st in SHAKY: return 'listed %s' % st
    if row.get('no_play_hint'): return row['no_play_hint']
    return None

HONEST_BOARDS = True   # APEX-HONESTBOARDS-2026-11-07 (owner): no honest number = no numbered spot, BACKUPS with a warning
def _proven(r):
    h = r.get('honest')
    return isinstance(h, dict) and h.get('pct') is not None

BOARDS_OFF = True   # APEX-MLBOFF-2026-11-09 (owner, "keep everything off of mlb ... nothing on mlb boards" until he finds the issue): every MLB board posts empty
HONEST_RANK = True     # APEX-HONESTRANK-2026-11-09 (owner, "MLB honest rank"): numbered spots need honest 75+ and are ranked by the honest number; tested both halves 11/9 (Top 3 49/40% -> 53/54%, Elite 5 28/19 -> 37/37)
HONEST_MIN = 75.0
def _hp(r):
    h = r.get('honest'); return h.get('pct') if isinstance(h, dict) and h.get('pct') is not None else -1
def rank_key(r):
    if HONEST_RANK: return (-_hp(r), -r['confidence'], -r['edge_score'], r['start'] or '', r['player'], r['stat'])   # APEX-HONESTRANK-2026-11-09
    return (-r['confidence'], -r['edge_score'], r['start'] or '', r['player'], r['stat'])

def build_boards(rows, injuries=None, banned=()):
    """rows = scored lines. Returns {board: dict(main=[rows], backups=[rows], floor=..)}. One pick per game on numbered boards."""
    c = CM.cfg(); injuries = injuries or {}; pool = []; unproven = []
    if BOARDS_OFF: return {name: dict(main=[], backups=[], floor=b.get('floor', c['rules']['floor']), title=b['title'], size=b['size'], note=b.get('note', '')) for name, b in c['boards'].items()}   # APEX-MLBOFF-2026-11-09
    for r in rows:
        r['no_play'] = no_play_reason(r, injuries, banned)
        if not r['no_play']:
            if HONEST_BOARDS and not _proven(r): r['unproven'] = True; unproven.append(r)   # APEX-HONESTBOARDS-2026-11-07
            else: pool.append(r)
    pool.sort(key=rank_key); out = {}
    for name, b in c['boards'].items():
        fl = b.get('floor', c['rules']['floor']); cand = [r for r in pool if r['confidence'] >= fl and (not b.get('kind') or r['kind'] == b['kind'])]
        low = []
        if HONEST_RANK: low = [r for r in cand if _hp(r) < HONEST_MIN]; cand = [r for r in cand if _hp(r) >= HONEST_MIN]   # APEX-HONESTRANK-2026-11-09: honest under 75 goes to BACKUPS
        main, games, back = [], set(), []
        for r in cand:
            g = r.get('game_key') or (r['team'], r['game_date'])
            if len(main) < b['size'] and g not in games: main.append(r); games.add(g)
            else: back.append(r)
        back += low   # APEX-HONESTRANK-2026-11-09
        unp = [r for r in unproven if r['confidence'] >= fl and (not b.get('kind') or r['kind'] == b['kind'])]   # APEX-HONESTBOARDS: shown last, with a warning
        out[name] = dict(main=main, backups=back[:b.get('backups', 10)] + unp[:5], floor=fl, title=b['title'], size=b['size'], note=b.get('note', ''))
    return out
