#!/usr/bin/env python3
"""APEX-FULLMATCHUP-2026-11-08 (owner "Go full matchup"). Full-team shots allowed for the soccer Matchup step.
Our old matchup added up only the players who had a PrizePicks line, so Bayern looked like an average defense. This pulls
ESPN's free team box scores (every team's total shots and shots on target, every game, 11 leagues) and stores, for each team,
how many shots its opponents took compared with a normal team in that league. models/projection.py reads cache/espn_matchup.json.
Run: python3 history/espn_team.py [full]   (scheduler runs it every morning; 'full' re-pulls everything since 2024-07)"""
import os, sys, csv, glob, json, time, gzip, bisect, datetime as dt, statistics as ST, collections as C, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
ROWS = os.path.join(ROOT, 'cache', 'espn_team_rows.json'); OUT = os.path.join(ROOT, 'cache', 'espn_matchup.json'); TC = os.path.join(ROOT, 'cache', 'team_canon.json')
IDX = '/Volumes/2TB Drive/SportsData/sportsgameodds/index'
LG = {'LIGA_MX': 'mex.1', 'UEFA_EUROPA_LEAGUE': 'uefa.europa', 'IT_SERIE_A': 'ita.1', 'BUNDESLIGA': 'ger.1', 'BR_SERIE_A': 'bra.1',
      'LA_LIGA': 'esp.1', 'FR_LIGUE_1': 'fra.1', 'MLS': 'usa.1', 'EPL': 'eng.1', 'UEFA_CHAMPIONS_LEAGUE': 'uefa.champions', 'EREDIVISIE': 'ned.1'}

def _get(u):
    r = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'apex', 'Accept-Encoding': 'gzip'}), timeout=30).read()
    try: r = gzip.decompress(r)
    except OSError: pass
    return json.loads(r)

def _months(full):
    t = dt.date.today(); y, m = (2024, 7) if full else ((t.year, t.month - 1) if t.month > 1 else (t.year - 1, 12)); out = []
    while (y, m) <= (t.year, t.month):
        out.append('%d%02d' % (y, m)); m += 1
        if m == 13: y, m = y + 1, 1
    return out

def _num(v):
    try: return float(v)
    except (TypeError, ValueError): return None

def pull(full=False):
    old = {} if full or not os.path.exists(ROWS) else {(r['id'], r['tid']): r for r in json.load(open(ROWS))}
    fails = 0; n0 = len(old)
    for L, p in LG.items():
        for mo in _months(full or not old):
            try: j = _get('https://site.api.espn.com/apis/site/v2/sports/soccer/%s/scoreboard?dates=%s&limit=900' % (p, mo))
            except Exception: fails += 1; continue
            for e in j.get('events') or []:
                c = (e.get('competitions') or [{}])[0]
                if not ((c.get('status') or {}).get('type') or {}).get('completed'): continue
                ts = c.get('competitors') or []
                if len(ts) != 2: continue
                st = []
                for t in ts:
                    s = {x['name']: x.get('displayValue') for x in t.get('statistics') or []}
                    st.append((str(t['team'].get('id')), t['team'].get('abbreviation'), t.get('homeAway'), _num(s.get('totalShots')), _num(s.get('shotsOnTarget'))))
                for a, b in ((0, 1), (1, 0)):
                    old[(e['id'], st[a][0])] = dict(league=L, date=e['date'][:10], id=e['id'], tid=st[a][0], ab=st[a][1], ha=st[a][2],
                                                    oid=st[b][0], oab=st[b][1], shots=st[a][3], sot=st[a][4])
            time.sleep(0.25)
    rows = sorted(old.values(), key=lambda r: (r['date'], r['id'], r['tid']))
    json.dump(rows, open(ROWS + '.tmp', 'w')); os.replace(ROWS + '.tmp', ROWS)
    return rows, len(rows) - n0, fails

def build(rows):
    # league normal: average shots a team takes in that league over the 120 days before the game
    lgv = C.defaultdict(list)
    for r in rows:
        for s in ('shots', 'sot'):
            if r[s] is not None: lgv[(r['league'], s)].append((r['date'], r[s]))
    for v in lgv.values(): v.sort()
    def norm(L, s, d):
        v = lgv[(L, s)]; D = [x[0] for x in v]; i = bisect.bisect_left(D, d)
        j = bisect.bisect_left(D, (dt.date.fromisoformat(d) - dt.timedelta(days=120)).isoformat())
        w = [x[1] for x in v[j:i]]
        if len(w) < 30: w = [x[1] for x in v[max(0, i - 200):i]]
        return ST.mean(w) if len(w) >= 30 else None
    teams = C.defaultdict(list); names = {}
    for r in rows:   # what each team ALLOWED: the other side's shots that game, vs that league's normal
        names[r['oid']] = r['oab']; ns, nt = norm(r['league'], 'shots', r['date']), norm(r['league'], 'sot', r['date'])
        teams[r['oid']].append([r['date'], round(r['shots'] / ns, 4) if r['shots'] is not None and ns else None,
                                round(r['sot'] / nt, 4) if r['sot'] is not None and nt else None, r['league']])
    for v in teams.values(): v.sort()
    # our team codes -> ESPN team ids: our games vs ESPN games in the same league within a day, most votes win (one code per team)
    from database import db as DBM
    db = DBM.connect(); lg = {}
    for f in glob.glob(os.path.join(IDX, '*_events.csv')):
        L = os.path.basename(f)[:-11]
        if L in LG:
            for r in csv.DictReader(open(f, encoding='utf-8', errors='ignore')): lg[r['eventID']] = L
    ours = {}
    for e, t, o, h, d in db.execute('select event_id, team, opponent, home, game_date from player_games'):
        if t and o and h is not None and e in lg: ours[e] = (d[:10], t, o) if h == 1 else (d[:10], o, t)
    EG = C.defaultdict(list)
    for r in rows:
        if r['ha'] == 'home': EG[(r['league'], r['date'])].append((r['tid'], r['oid']))
    vote = C.defaultdict(C.Counter); last = {}
    for e, (d, H, A) in ours.items():
        L = lg[e]; day = dt.date.fromisoformat(d); cands = []
        for k in (-1, 0, 1): cands += EG.get((L, (day + dt.timedelta(days=k)).isoformat()), [])
        for h, a in cands: vote[(L, H)][h] += 1; vote[(L, A)][a] += 1
        for c in (H, A): last[(L, c)] = max(last.get((L, c), ''), d)
    LM = {}; used = set()
    for v, L, code, tid in sorted(((v, k[0], k[1], t) for k, c in vote.items() for t, v in c.items()), reverse=True):
        if v < 3 or (L, code) in LM: continue   # one club may have two codes in one league; the game check below drops wrong ones
        LM[(L, code)] = tid; used.add((L, tid))
    GS = {(L, d, h, a) for (L, d), gl in EG.items() for h, a in gl}; ok = C.Counter(); tot = C.Counter()
    for e, (d, H, A) in ours.items():
        L = lg[e]
        if (L, H) not in LM or (L, A) not in LM: continue
        day = dt.date.fromisoformat(d); hit = any((L, (day + dt.timedelta(days=k)).isoformat(), LM[(L, H)], LM[(L, A)]) in GS for k in (-1, 0, 1))
        for c in (H, A): tot[(L, c)] += 1; ok[(L, c)] += hit
    LM = {k: v for k, v in LM.items() if tot[k] and ok[k] / tot[k] >= 0.6}
    cmap = {}   # a code used in two leagues for two different teams: the league it played in most recently wins
    for (L, code), tid in sorted(LM.items(), key=lambda kv: last.get(kv[0], '')): cmap[code] = tid
    if not cmap and os.path.exists(OUT):   # 2TB drive not mounted: keep yesterday's code map
        try: cmap = json.load(open(OUT)).get('map') or {}
        except Exception: pass
    # APEX-TEAMCANON-2026-11-08: one code per real club. SportsGameOdds used different codes per competition (Lyon OL / LYON /
    # LYO) and one code for two clubs (FCB = Bayern and Barcelona); ESPN uses MUN for Bayern while SGO used MUN for Man Utd.
    # Every stored code is turned into the club's ESPN code (with the league added when two clubs share it).
    lgof = C.defaultdict(C.Counter); abof = {}
    for r in rows: lgof[r['tid']][r['league']] += 1; abof[r['tid']] = r['ab']
    SH = {'LIGA_MX': 'MX', 'UEFA_EUROPA_LEAGUE': 'UEL', 'IT_SERIE_A': 'ITA', 'BUNDESLIGA': 'GER', 'BR_SERIE_A': 'BRA', 'LA_LIGA': 'ESP',
          'FR_LIGUE_1': 'FRA', 'MLS': 'MLS', 'EPL': 'ENG', 'UEFA_CHAMPIONS_LEAGUE': 'UCL', 'EREDIVISIE': 'NED'}
    byab = C.defaultdict(set)
    for t, a in abof.items(): byab[a].add(t)
    canon = {}
    for t, a in abof.items():
        if len(byab[a]) == 1: canon[t] = a
        else:
            tag = SH.get(lgof[t].most_common(1)[0][0], 'X'); same = [x for x in byab[a] if SH.get(lgof[x].most_common(1)[0][0], 'X') == tag]
            canon[t] = '%s-%s' % (a, tag) if len(same) == 1 else '%s-%s' % (a, t)
    evmap = C.defaultdict(dict)
    for e, (d, H, A) in ours.items():
        L = lg[e]
        for c in (H, A):
            if (L, c) in LM: evmap[e][c] = canon[LM[(L, c)]]
    for r in rows: evmap[r['id']][r['ab']] = canon[r['tid']]
    # games from cups / leagues ESPN does not list (DFB Pokal, Club World Cup, Ligue 2 ...): the club its players were at in
    # their nearest known games (30 days), when 3+ players and 60%+ agree. National teams split across clubs, so they stay as they are.
    import bisect as _b
    known = C.defaultdict(list); grp = C.defaultdict(list)
    for e, pn, t, d in db.execute('select event_id, player_norm, team, game_date from player_games'):
        if not t: continue
        c = (evmap.get(e) or {}).get(t)
        if c: known[pn].append((d[:10], c))
        else: grp[(e, t)].append((pn, d[:10]))
    for v in known.values(): v.sort()
    for (e, t), ps in grp.items():
        vt = C.Counter()
        for pn, d in ps:
            L = known.get(pn) or []
            if not L: continue
            i = _b.bisect_left([x[0] for x in L], d); best = None
            for j in (i - 1, i):
                if 0 <= j < len(L):
                    gap = abs((dt.date.fromisoformat(L[j][0]) - dt.date.fromisoformat(d)).days)
                    if gap <= 30 and (best is None or gap < best[0]): best = (gap, L[j][1])
            if best: vt[best[1]] += 1
        if vt:
            c, n = vt.most_common(1)[0]
            if n >= 3 and n >= 0.6 * sum(vt.values()): evmap[e][t] = c
    codemap = {c: canon[t] for c, t in cmap.items()}
    for t, c in canon.items(): codemap.setdefault(abof[t] if len(byab[abof[t]]) == 1 else c, c); codemap[c] = c
    json.dump(dict(built=dt.datetime.now().isoformat(timespec='seconds'), ev=evmap, code=codemap), open(TC + '.tmp', 'w')); os.replace(TC + '.tmp', TC)
    for t, c in canon.items(): cmap[c] = t
    out = dict(built=dt.datetime.now().isoformat(timespec='seconds'), map=cmap, names=names, teams=teams,
               checked='%d of %d games' % (sum(ok.values()) // 2, sum(tot.values()) // 2))
    json.dump(out, open(OUT + '.tmp', 'w')); os.replace(OUT + '.tmp', OUT)
    return out

def run(full=False):
    rows, new, fails = pull(full); out = build(rows)
    return '🆚 Soccer full-team matchup data: %d team games (%d new), %d of our teams matched to ESPN, %s check out%s' % (
        len(rows), new, len(out['map']), out['checked'], (', %d ESPN pulls failed' % fails) if fails else '')

if __name__ == '__main__':
    print(run('full' in sys.argv[1:]))
