"""APEX-TDTOUCHES-2026-11-10 (owner, "go td touches"): a "no touchdown" pick (Rush+Rec TDs LESS on the regular line) is rated by
how busy the player is. Apex's touchdown math looks only at past touchdowns, so a lead back on a dry spell got 90+.
History test (every graded Rush+Rec TDs 0.5 line, Apex 90+ LESS, touches = rush attempts + catches, average of his last 5 games):
  12+ touches a game: won 21 of 34 (older half 12 of 19, newer half 9 of 15)   -> rated no higher than 62
  6 to 12 touches:    won 68 of 97 (older 30 of 46, newer 38 of 51)            -> rated no higher than 70
  under 6 touches:    won 782 of 891 (88 of 100 in both halves)                -> no change
One rule for every NFL player and board. Test script: ~/openclaw/_backups/td_lead_1110/t.py. Turn off: ON = False, restart NFL."""
import json

ON = True
STAT = 'anytime_td'
CAPS = ((12.0, 62, 'about 6 of 10'), (6.0, 70, 'about 7 of 10'))   # (touches a game at least, highest rating, plain words)
_C = {}


def touches(db, player_norm, day):
    """Average rush attempts + catches over his last 5 games before `day` (needs 3+), else None."""
    k = (player_norm, day)
    if k not in _C:
        g = {}
        for r in db.execute('select game_date, stats_json from player_games where player_norm=? and game_date<? order by game_date desc limit 12', (player_norm, day)):
            try: s = json.loads(r['stats_json'] or '{}')
            except ValueError: continue
            t = (s.get('rushing_attempts') or 0) + (s.get('receptions') or 0)
            g[r['game_date']] = max(g.get(r['game_date'], 0), t)
        v = [g[d] for d in sorted(g, reverse=True)[:5]]
        _C[k] = (sum(v) / len(v)) if len(v) >= 3 else None
    return _C[k]


def cap(db, player_norm, stat, kind, side, day, conf):
    """None, or dict(t=touches, was=old rating, to=new rating, words=...) when the rating must come down."""
    if not ON or stat != STAT or kind != 'standard' or side != 'LESS': return None
    t = touches(db, player_norm, day)
    if t is None: return None
    for need, top, words in CAPS:
        if t >= need:
            return dict(t=round(t, 1), was=round(conf), to=top, words=words) if conf > top else None
    return None


def card_line(row):
    c = row.get('td_touches')
    if not c: return None
    return '✋ Busy player: about %.0f touches a game. "No touchdown" on players this busy really wins %s, so Apex lowered %d → %d.' % (c['t'], c['words'], c['was'], c['to'])
