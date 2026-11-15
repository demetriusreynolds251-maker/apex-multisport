#!/usr/bin/env python3
"""APEX-ONELINE-2026-11-12 (his go: "Proper fix all until it's no data poison"): one PrizePicks line = one pick.
PrizePicks sometimes lists the same player / stat / line / type under two projection ids (twins on the board at once, or a line
taken down and re-issued under a new id). Both used to be saved, graded and counted, and both could take a board spot.
  clean(db)          keeps one saved pick per line and marks the extra copies status='dup' (never counted, never graded);
                     posted boards that pointed at a copy are pointed at the kept pick.
  rows_once(db, rows) keeps one scored row per line before boards are built, and gives it the key of the pick already saved.
Undo: ON = False (extra copies stay marked; restore the database backup to bring them back)."""
ON = True

def _k(r): return (r['player_norm'], r['stat'], float(r['line']), r['kind'], r['game_date'])

def clean(db):
    if not ON: return 0
    groups = db.execute("select player_norm, stat, line, kind, game_date from picks where status != 'dup' group by 1, 2, 3, 4, 5 having count(*) > 1").fetchall()
    if not groups: return 0
    nb = {r[0]: r[1] for r in db.execute("select pick_key, count(*) from boards where role='main' group by 1")}
    n = 0
    for g in groups:
        ps = db.execute("select pick_key, run_id, status from picks where player_norm=? and stat=? and line=? and kind=? and game_date=? and status != 'dup'", tuple(g)).fetchall()
        # keep: the copy that was on a posted board, then a graded one, then the newest
        ps = sorted(ps, key=lambda p: (nb.get(p[0], 0), 1 if p[2] in ('win', 'loss', 'push') else 0, p[1] or 0, p[0]), reverse=True)
        for p in ps[1:]:
            db.execute("update picks set status='dup', hit=null where pick_key=?", (p[0],))
            db.execute('update boards set pick_key=? where pick_key=?', (ps[0][0], p[0])); n += 1
    db.commit(); return n

def rows_once(db, rows):
    if not ON or not rows: return rows
    lo = min(r['game_date'] for r in rows); keep = {}
    for p in db.execute("select pick_key, player_norm, stat, line, kind, game_date from picks where status != 'dup' and game_date >= ?", (lo,)):
        keep[(p[1], p[2], float(p[3]), p[4], p[5])] = p[0]
    out, seen = [], set()
    for r in rows:
        k = _k(r)
        if k in seen: continue
        seen.add(k)
        if k in keep: r['pick_key'] = keep[k]
        out.append(r)
    return out
