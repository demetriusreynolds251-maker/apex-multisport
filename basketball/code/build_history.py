#!/usr/bin/env python3
"""Builds the NBA player history table.
Inputs: raw SportsGameOdds NBA files on the 2TB drive (read only).
Outputs: data/processed/nba_history.sqlite and reports/latest_step1_data_check.md.
Offline: makes no API calls and touches nothing in Apex. Run: python3 code/build_history.py"""
import csv, glob, gzip, json, os, re, sqlite3, collections as C, statistics as ST
from datetime import datetime as D, date
from zoneinfo import ZoneInfo
SRC = '/Volumes/2TB Drive/SportsData/sportsgameodds/events/BASKETBALL/NBA'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, 'data', 'processed', 'nba_history.sqlite')
os.makedirs(os.path.dirname(DB), exist_ok=True)
CT = ZoneInfo('America/Chicago')
BOOKS = ('pinnacle', 'fanduel', 'draftkings', 'betmgm', 'caesars', 'bet365', 'fanatics', 'espnbet', 'bovada', 'betonline', 'betrivers')
STATCOL = {'points': 'points', 'rebounds': 'rebounds', 'assists': 'assists', 'threePointersMade': 'threes', 'steals': 'steals', 'blocks': 'blocks', 'turnovers': 'turnovers'}
def T(s): return D.fromisoformat(s.replace('Z', '+00:00'))
def fl(x):
    try: return float(x)
    except (TypeError, ValueError): return None
def season(d):
    y, m = int(d[:4]), int(d[5:7]); return '%d-%02d' % ((y, (y + 1) % 100) if m >= 8 else (y - 1, y % 100))
if os.path.exists(DB): os.remove(DB)
db = sqlite3.connect(DB)
db.executescript("""
create table games(event_id text primary key, season text, game_date text, start_utc text, home text, away text, home_pts real, away_pts real,
  close_spread_home real, open_spread_home real, close_total real, open_total real, final integer);
create table player_games(event_id text, player_id text, player text, team text, opponent text, home integer, game_date text, season text,
  minutes real, points real, rebounds real, assists real, threes real, steals real, blocks real, turnovers real,
  rest_days integer, back_to_back integer, primary key(event_id, player_id));
create table prop_lines(event_id text, player_id text, stat text, game_date text, season text, pp_line real, pp_before_start integer,
  open_line real, close_line real, close_fair real, close_fair_over_odds text, books_before_start integer, books_later integer,
  pinnacle_before_start real, book_lines_json text, result real, more_won integer, less_won integer, primary key(event_id, player_id, stat));
create index ix_pg on player_games(player_id, game_date); create index ix_pl on prop_lines(stat, season);
""")
Ev = 0; Cnt = C.defaultdict(C.Counter); Leak = C.defaultdict(list); pg = []
for f in glob.iglob(SRC + '/*/*/*.json.gz'):
    with gzip.open(f, 'rt') as z: e = json.load(z)
    s = e.get('status') or {}; st = T(s['startsAt']); day = st.astimezone(CT).date().isoformat(); se = season(day); Ev += 1
    cut = min([st] + [T(x) for x in s.get('previousStartsAt') or []]); res = e.get('results') or {}; rg = res.get('game') or {}
    o = e.get('odds') or {}; hm, aw = e['teams']['home'], e['teams']['away']
    fin = bool(s.get('finalized')) and not s.get('cancelled')
    sp = o.get('points-home-game-sp-home') or {}; tt = o.get('points-all-game-ou-over') or {}
    hp, ap = fl((rg.get('home') or {}).get('points')), fl((rg.get('away') or {}).get('points'))
    db.execute('insert or replace into games values(?,?,?,?,?,?,?,?,?,?,?,?,?)', (e['eventID'], se, day, s['startsAt'], hm['names'].get('long'), aw['names'].get('long'), hp, ap,
               fl(sp.get('closeBookSpread')), fl(sp.get('openBookSpread')), fl(tt.get('closeBookOverUnder')), fl(tt.get('openBookOverUnder')), int(fin)))
    if not fin: continue
    Cnt[se]['finished games'] += 1
    if hp is not None and ap is not None and fl(tt.get('closeBookOverUnder')) is not None:
        Leak[se].append((abs(fl(tt['closeBookOverUnder']) - hp - ap), abs(fl(tt.get('openBookOverUnder') or tt['closeBookOverUnder']) - hp - ap)))
    players = e.get('players') or {}
    for pid, r in rg.items():
        if pid in ('home', 'away', 'all') or not isinstance(r, dict) or 'points' not in r: continue
        p = players.get(pid) or {}; team = p.get('teamID'); ishome = team == hm.get('teamID')
        pg.append([e['eventID'], pid, p.get('name'), team, (aw if ishome else hm)['names'].get('long'), int(ishome), day, se, (fl(r.get('secondsPlayed')) or 0) / 60.0,
                   *[fl(r.get(k)) for k in ('points', 'rebounds', 'assists', 'threePointersMade', 'steals', 'blocks', 'turnovers')], None, None])
    for k, x in o.items():
        ent = x.get('statEntityID')
        if x.get('sideID') != 'over' or x.get('betTypeID') != 'ou' or x.get('periodID') != 'game' or ent in ('all', 'home', 'away', None): continue
        stat = x.get('statID'); bb = x.get('byBookmaker') or {}; pp = bb.get('prizepicks'); ppl = fl(pp.get('overUnder')) if pp else None
        ppre = int(bool(pp and pp.get('lastUpdatedAt') and T(pp['lastUpdatedAt']) <= st))
        pre, later, bl = 0, 0, {}
        for b, v in bb.items():
            if b == 'prizepicks' or not v.get('lastUpdatedAt'): continue
            if T(v['lastUpdatedAt']) <= cut: pre += 1; bl[b] = [fl(v.get('overUnder')), v.get('odds')]
            else: later += 1
        sc = rg.get(ent, {}).get(stat) if isinstance(rg.get(ent), dict) else None
        if sc is None and '+' in stat and isinstance(rg.get(ent), dict):
            pts = [rg[ent].get(q) for q in stat.split('+')]; sc = sum(pts) if None not in pts else None
        sc = fl(x.get('score')) if fl(x.get('score')) is not None else fl(sc)
        mw = None if ppl is None or sc is None else int(sc > ppl); lw = None if ppl is None or sc is None else int(sc < ppl)
        db.execute('insert or replace into prop_lines values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (e['eventID'], ent, stat, day, se, ppl, ppre, fl(x.get('openBookOverUnder')), fl(x.get('closeBookOverUnder')),
                   fl(x.get('closeFairOverUnder')), x.get('closeFairOdds'), pre, later, (bl.get('pinnacle') or [None])[0], json.dumps(bl), sc, mw, lw))
        c = Cnt[se]; c['player lines'] += 1; c['lines with result'] += sc is not None; c['with PP'] += ppl is not None; c['PP before start'] += bool(ppre)
        if ppre and sc is not None and pre: c['ALL THREE'] += 1; Cnt['stat:' + stat]['ALL THREE'] += 1
        if ppre and sc is not None: Cnt['stat:' + stat]['PP + result'] += 1
        Cnt['stat:' + stat]['lines'] += 1
        for b in bl: Cnt['books'][b] += 1
pg.sort(key=lambda r: (r[1], r[6])); last = {}; seen = set(); rows = []
for r in pg:
    k = (r[0], r[1])
    if k in seen: continue
    seen.add(k); prev = last.get(r[1])
    if r[8] and r[8] > 0:
        if prev is not None:
            r[16] = (date.fromisoformat(r[6]) - prev).days - 1; r[17] = int(r[16] == 0)
        last[r[1]] = date.fromisoformat(r[6])
    rows.append(r)
db.executemany('insert or replace into player_games values(%s)' % ','.join('?' * 18), rows); db.commit()
L = ['# NBA Step 1 counts', '', 'Files: %d. ALL THREE = PrizePicks line before start, 1+ book line last updated before the start, and a final result.' % Ev, '']
for k in sorted(k for k in Cnt if not k.startswith('stat:') and k != 'books'): L.append('Season %s: %s' % (k, dict(Cnt[k])))
L += ['', 'By prop type:'] + ['%s: %s' % (k[5:], dict(v)) for k, v in sorted(Cnt.items(), key=lambda z: -z[1]['ALL THREE']) if k.startswith('stat:')][:30]
L += ['', 'Books before start: %s' % Cnt['books'].most_common(25), '', 'Close vs open, avg miss on game total (a low close means it knew the result):']
for k, v in sorted(Leak.items()): L.append('%s: %d games, close %.1f, open %.1f' % (k, len(v), ST.mean(a for a, _ in v), ST.mean(b for _, b in v)))
L += ['', 'player_games rows %d, prop_lines rows %d, games %d, dates %s to %s' % (len(rows), db.execute('select count(*) from prop_lines').fetchone()[0], db.execute('select count(*) from games').fetchone()[0], *db.execute('select min(game_date),max(game_date) from games where final=1').fetchone())]
open(os.path.join(ROOT, 'reports', 'latest_step1_data_check.md'), 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
