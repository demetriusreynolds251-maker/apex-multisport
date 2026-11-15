#!/usr/bin/env python3
"""APEX-FREEDATA-2026-11-06 (owner, "Go add the free GitHub ... make our own, don't just push theirs"): our own NFL collector for the
free public nflverse data files (plain CSV downloads from github.com/nflverse/nflverse-data releases). No nflverse code or package is used.
Saves: data/free/nflverse/<file>.csv (latest), injuries snapshot per day, and cache/free_nfl.json = per player {injury, practice,
depth rank, snap share last 3 weeks}. DATA ONLY: nothing here changes a pick or a board. Never raises."""
import csv, io, json, os, sys, urllib.request, datetime as dt, collections as C
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import common as CM
BASE = 'https://github.com/nflverse/nflverse-data/releases/download/'
FILES = {  # name: (release path, columns we require, max MB)
    'injuries': ('injuries/injuries_%d.csv', ('season', 'week', 'full_name', 'team', 'report_status'), 20),
    'depth_charts': ('depth_charts/depth_charts_%d.csv', ('team',), 200),
    'snap_counts': ('snap_counts/snap_counts_%d.csv', ('season', 'week', 'player', 'team', 'offense_pct'), 50),
}
OUT = os.path.join(ROOT, 'data', 'free', 'nflverse')


def _season():
    n = dt.date.today()
    return n.year if n.month >= 8 else n.year - 1


def _get(url, max_mb):
    req = urllib.request.Request(url, headers={'User-Agent': 'ApexSports-NFL-collector'})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read(max_mb * 1024 * 1024 + 1)
    if len(data) > max_mb * 1024 * 1024:
        raise ValueError('file bigger than %d MB' % max_mb)
    return data.decode('utf-8', errors='replace')


def _norm(n):
    try:
        return CM.norm(n)
    except Exception:
        return ' '.join(str(n or '').lower().replace('.', '').replace("'", '').split())


def run():
    """Download, check, save, summarize. Returns one plain line for the system channel."""
    os.makedirs(OUT, exist_ok=True); yr = _season(); got, bad = {}, []
    for name, (path, need, mb) in FILES.items():
        try:
            txt = _get(BASE + path % yr, mb)
            rows = list(csv.DictReader(io.StringIO(txt)))
            miss = [c for c in need if rows and c not in rows[0]]
            if not rows or miss:
                bad.append('%s (%s)' % (name, 'empty' if not rows else 'missing ' + ','.join(miss))); continue
            tmp = os.path.join(OUT, name + '.csv.tmp'); open(tmp, 'w').write(txt); os.replace(tmp, os.path.join(OUT, name + '.csv'))
            got[name] = rows
        except Exception as e:
            bad.append('%s (%s)' % (name, type(e).__name__))
    if 'injuries' in got:
        open(os.path.join(OUT, 'injuries_%s.csv' % dt.date.today().isoformat()), 'w').write(
            open(os.path.join(OUT, 'injuries.csv')).read())
    P = C.defaultdict(dict)
    inj = got.get('injuries') or []
    if inj:
        wk = max(int(r.get('week') or 0) for r in inj)
        for r in inj:
            if int(r.get('week') or 0) == wk:
                P[_norm(r.get('full_name'))].update(team=r.get('team'), injury=r.get('report_status') or '', practice=r.get('practice_status') or '',
                                                    injury_part=r.get('report_primary_injury') or '', injury_week=wk)
    dc = got.get('depth_charts') or []
    if dc:
        key = 'dt' if 'dt' in dc[0] else ('week' if 'week' in dc[0] else None)
        last = max((r.get(key) or '') for r in dc) if key else None
        for r in dc:
            if key and (r.get(key) or '') != last:
                continue
            nm = r.get('player_name') or r.get('full_name') or ''
            rank = r.get('pos_rank') or r.get('depth_team') or ''
            if nm:
                P[_norm(nm)].update(depth_pos=r.get('pos_abb') or r.get('position') or r.get('depth_position') or '', depth_rank=rank)
    sc = got.get('snap_counts') or []
    if sc:
        wks = sorted({int(r.get('week') or 0) for r in sc})[-3:]
        S = C.defaultdict(list)
        for r in sc:
            if int(r.get('week') or 0) in wks:
                try: S[_norm(r.get('player'))].append(float(r.get('offense_pct') or 0))
                except ValueError: pass
        for n, v in S.items():
            P[n].update(snap_share_3wk=round(100 * sum(v) / len(v), 1) if max(v) <= 1.0 else round(sum(v) / len(v), 1))
        A = C.defaultdict(list)   # APEX-ROLERULES-2026-11-06: snap jump = last game vs the 3 before (same as the 11/6 role test)
        for r in sc:
            try: A[_norm(r.get('player'))].append((int(r.get('week') or 0), float(r.get('offense_pct') or 0)))
            except ValueError: pass
        for n, v in A.items():
            v.sort(); s = [x[1] * (100 if max(y[1] for y in v) <= 1.0 else 1) for x in v]
            if len(s) >= 4: P[n].update(snap_last=round(s[-1], 1), snap_jump=round(s[-1] - sum(s[-4:-1]) / 3, 1))
    out = dict(at=CM.iso(), season=yr, players=P, files={k: len(v) for k, v in got.items()}, problems=bad)
    if got:
        tmp = os.path.join(ROOT, 'cache', 'free_nfl.json.tmp'); json.dump(out, open(tmp, 'w')); os.replace(tmp, os.path.join(ROOT, 'cache', 'free_nfl.json'))
    return '🆓 NFL free data: %s%s' % (', '.join('%s %d rows' % (k, len(v)) for k, v in got.items()) or 'nothing saved',
                                     (' · ⚠️ problems: ' + '; '.join(bad)) if bad else '')


if __name__ == '__main__':
    print(run())
