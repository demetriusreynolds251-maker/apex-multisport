#!/usr/bin/env python3
"""APEX-DATAALERTS-2026-11-08 (owner, "Go data alerts"): nightly data check, posts to #alerts only. NEVER changes a pick or board.
Per running sport: (1) games from the last 2 days with incomplete box scores (team total under a quarter of normal),
(2) live props whose opponent was not found, (3) live props on a name two players share (two teams on the same/next day),
(4) live props where the player's last 5 games are all 0 after real numbers (looks like missing data).
Read-only on every sport database.  python3 data_alerts.py [--dry]"""
import collections as C, datetime as dt, json, os, sqlite3, statistics as ST, sys
R = os.path.expanduser('~/ApexSports'); DRY = '--dry' in sys.argv
SPORTS = [('NFL', 'football/nfl'), ('College Football', 'football/ncaaf'), ('NHL', 'hockey/nhl'), ('Soccer', 'soccer'),
          ('College Basketball', 'basketball/ncaab'), ('WNBA', 'basketball/wnba'), ('MLB', 'baseball/mlb'), ('AFL', 'afl')]
def check(name, rel):
    root = os.path.join(R, rel)
    if not os.path.exists(os.path.join(root, 'database', 'history.db')) or os.path.exists(os.path.join(root, 'INACTIVE')): return None
    SC = json.load(open(os.path.join(root, 'config', 'sport.json')))['stats']
    db = sqlite3.connect('file:' + os.path.join(root, 'database', 'history.db') + '?mode=ro', uri=True)
    G = C.defaultdict(dict); meta = {}
    for e, pn, t, d, sj in db.execute('select event_id, player_norm, team, game_date, stats_json from player_games order by game_date, source'):
        G[(e, pn)].update({k: v for k, v in json.loads(sj or '{}').items() if isinstance(v, (int, float)) and not k.startswith('_')}); meta[(e, pn)] = (t, (d or '')[:10])
    hist = C.defaultdict(list); tt = C.defaultdict(lambda: C.defaultdict(float)); tdate = {}
    for (e, pn), st in G.items():
        t, d = meta[(e, pn)]; hist[pn].append((d, t, st)); tdate[(e, t)] = d
        for k, v in st.items(): tt[(e, t)][k] += v
    for L in hist.values(): L.sort(key=lambda x: x[0])
    bkeys = C.Counter()
    for k, v in SC.items():
        if v.get('board', True):
            for f in v.get('formula') or []: bkeys[f[0] if isinstance(f, list) else f] += 1
    keyn = C.Counter(k for v in tt.values() for k in v if k in bkeys)
    main = [k for k, n in keyn.most_common(6) if n >= 0.3 * max(1, len(tt))]
    anchor = max(main, key=lambda k: ST.median([v.get(k, 0) for v in tt.values()]) or 0) if main else None
    out = []
    if anchor:
        byteam = C.defaultdict(list)
        for (e, t), v in tt.items(): byteam[t].append(v.get(anchor, 0))
        tmed = {t: ST.median(L) for t, L in byteam.items() if len(L) >= 5}
        since = (dt.date.today() - dt.timedelta(days=2)).isoformat()
        bad = sorted({'%s (%s)' % (t or '?', tdate[(e, t)]) for (e, t), v in tt.items() if tdate[(e, t)] >= since and tmed.get(t) and v.get(anchor, 0) < 0.25 * tmed[t]})
        if bad: out.append('%d team box score%s from the last 2 days look incomplete (%s far below that team\'s normal): %s' % (len(bad), '' if len(bad) == 1 else 's', anchor.replace('_', ' '), ', '.join(bad[:8]) + (' …' if len(bad) > 8 else '')))
    try: rows = json.load(open(os.path.join(root, 'cache', 'latest_scored.json'))).get('rows') or []
    except Exception: rows = []
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    live = [r for r in rows if (r.get('start') or '9') >= now[:16]]
    noopp = sorted({r.get('player') for r in live if not r.get('opponent')})
    if noopp: out.append('%d player%s with props tonight/tomorrow have no opponent found (matchup can\'t count): %s' % (len(noopp), '' if len(noopp) == 1 else 's', ', '.join(noopp[:8])))
    def clash(pn):
        L = sorted((d, t) for d, t, _ in hist.get(pn, []) if t and d); n = 0
        for (d1, t1), (d2, t2) in zip(L, L[1:]):
            if t1 != t2 and (dt.date.fromisoformat(d2) - dt.date.fromisoformat(d1)).days <= 1: n += 1
        return n >= 2
    shared = sorted({r.get('player') for r in live if clash(r.get('player_norm'))})
    if shared: out.append('%d name%s shared by two different players (their history may be mixed): %s' % (len(shared), '' if len(shared) == 1 else 's', ', '.join(shared[:8])))
    def val(st, s):
        tot = 0.0
        for k in SC.get(s, {}).get('formula') or []:
            w = 1.0
            if isinstance(k, list): k, w = k
            if st.get(k) is None: return None
            tot += w * st[k]
        return tot
    zero = set()
    for r in live:
        v = [val(st, r.get('stat')) for d, t, st in hist.get(r.get('player_norm'), [])]; v = [x for x in v if x is not None]
        if len(v) >= 8 and all(x == 0 for x in v[-5:]) and sum(v[:-5]) / len(v[:-5]) >= 1.5: zero.add('%s (%s)' % (r.get('player'), SC.get(r.get('stat'), {}).get('label', r.get('stat'))))
    if zero: out.append('%d prop%s where the player\'s last 5 games are all 0 after real numbers (missing data?): %s' % (len(zero), '' if len(zero) == 1 else 's', ', '.join(sorted(zero)[:8])))
    return out
def run():
    parts = []
    for name, rel in SPORTS:
        try: o = check(name, rel)
        except Exception as e: o = ['data check failed: %s' % type(e).__name__]
        if o: parts.append('**%s**\n' % name + '\n'.join('• ' + x for x in o))
    if not parts:
        return '✅ Nightly data check: no data problems found in any running sport. Nothing on the boards was changed.'
    return ('🧪 Nightly data check (info only, no pick or board was changed):\n' + '\n'.join(parts) +
            '\n👉 What to do: tell Claude which ones look wrong and I\'ll fix the data at the root.')[:1900]
if __name__ == '__main__':
    txt = run()
    if DRY: print(txt); sys.exit()
    sys.path.insert(0, os.path.expanduser('~/openclaw'))
    import apex_ops as ops
    print('posted' if ops.send_discord('alerts', txt) else 'post failed'); print(txt)
