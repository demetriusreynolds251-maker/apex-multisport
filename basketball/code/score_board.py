#!/usr/bin/env python3
"""Scores saved PrizePicks lines with the Step 3 Win Probability method (code/win_probability.py).
Inputs: data/collected/*.jsonl (written only by line_collector.py), data/processed/nba_history.sqlite, nba_fgm.sqlite, espn_games.sqlite.
No PrizePicks calls, no book lines, no Apex imports. Only games on earlier dates feed a pick. Only the 5 tested NBA stats get a number.
Tuning numbers are copied from reports/latest_step3_numbers.md (tuned on dates before 2025-11-28).
One-time cache of field goals made, 2TB drive needed: python3 code/score_board.py --build-fgm"""
import bisect, collections as C, datetime as dt, glob, gzip, json, math, os, re, sqlite3, statistics as ST, unicodedata
from zoneinfo import ZoneInfo
ROOT = os.environ.get('BBALL_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, 'data', 'processed'); COLLECTED = os.path.join(ROOT, 'data', 'collected')
HIST_DB = os.path.join(PROC, 'nba_history.sqlite'); FGM_DB = os.path.join(PROC, 'nba_fgm.sqlite'); ESPN_DB = os.path.join(PROC, 'espn_games.sqlite')
RAW = '/Volumes/2TB Drive/SportsData/sportsgameodds/events/BASKETBALL/NBA'
CT = ZoneInfo('America/Chicago')
STATS = {'points': lambda r: r['points'], 'rebounds': lambda r: r['rebounds'], 'rebounds+assists': lambda r: r['rebounds'] + r['assists'],
         'points+rebounds+assists': lambda r: r['points'] + r['rebounds'] + r['assists'], 'fieldGoalsMade': lambda r: r['fgm']}
STAT_LABEL = {'points': 'Points', 'rebounds': 'Rebounds', 'rebounds+assists': 'Rebs+Asts', 'points+rebounds+assists': 'PRA', 'fieldGoalsMade': 'FG Made'}
PP_STATS = {'points': 'points', 'rebounds': 'rebounds', 'rebs+asts': 'rebounds+assists', 'rebounds+assists': 'rebounds+assists', 'pts+rebs+asts': 'points+rebounds+assists',
            'points+rebounds+assists': 'points+rebounds+assists', 'fg made': 'fieldGoalsMade', 'field goals made': 'fieldGoalsMade', 'fgm': 'fieldGoalsMade'}
MIN_GAMES = 10
# Step 3 fit: k per stat and adj by (back_to_back, home). Copied, not re-tuned here.
FIT = {'points': (4.0, {(0, 1): .987, (1, 0): .893, (1, 1): 1.042, (0, 0): .997}),
       'rebounds': (4.0, {(0, 1): 1.009, (1, 0): .983, (1, 1): .92, (0, 0): .986}),
       'rebounds+assists': (4.0, {(0, 1): 1.052, (1, 0): .94, (1, 1): 1.001, (0, 0): 1.011}),
       'points+rebounds+assists': (4.0, {(0, 1): .999, (1, 0): .977, (1, 1): 1.031, (0, 0): .992}),
       'fieldGoalsMade': (4.0, {(0, 1): 1.035, (1, 0): 1.14, (1, 1): .978, (0, 0): 1.088})}
OPP_WEIGHT = .5
# abbreviation -> (long name in history, SportsGameOdds team id). ESPN's short forms are in ALIAS.
TEAMS = {a: (n, n.upper().replace(' ', '_') + '_NBA') for a, n in dict(ATL='Atlanta Hawks', BOS='Boston Celtics', BKN='Brooklyn Nets', CHA='Charlotte Hornets', CHI='Chicago Bulls', CLE='Cleveland Cavaliers',
    DAL='Dallas Mavericks', DEN='Denver Nuggets', DET='Detroit Pistons', GSW='Golden State Warriors', HOU='Houston Rockets', IND='Indiana Pacers', LAL='Los Angeles Lakers', MEM='Memphis Grizzlies',
    MIA='Miami Heat', MIL='Milwaukee Bucks', MIN='Minnesota Timberwolves', NOP='New Orleans Pelicans', NYK='New York Knicks', OKC='Oklahoma City Thunder', ORL='Orlando Magic', PHI='Philadelphia 76ers',
    PHX='Phoenix Suns', POR='Portland Trail Blazers', SAC='Sacramento Kings', SAS='San Antonio Spurs', TOR='Toronto Raptors', UTA='Utah Jazz', WAS='Washington Wizards').items()}
TEAMS['LAC'] = ('Los Angeles Clippers', 'LA_CLIPPERS_NBA')
ALIAS = {'GS': 'GSW', 'NO': 'NOP', 'NY': 'NYK', 'SA': 'SAS', 'UTAH': 'UTA', 'WSH': 'WAS', 'BRK': 'BKN', 'PHO': 'PHX', 'NOR': 'NOP'}
def abbr(s):
    s = re.sub(r'[^A-Z]', '', str(s or '').upper()); s = ALIAS.get(s, s)
    return s if s in TEAMS else None
def parse_opponent(desc):
    """PrizePicks description -> (abbreviation or None, home 1/0/None). '@ LAL' is away, 'vs LAL' is home, 'LAL' says nothing."""
    d = str(desc or '').strip(); home = 0 if d.startswith('@') or d.lower().startswith('at ') else (1 if d.lower().startswith('vs') else None)
    d = re.sub(r'^(@|at |vs\.?)\s*', '', d, flags=re.I).strip()
    return abbr(d), home
def norm(name):
    s = unicodedata.normalize('NFKD', str(name or '')).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r"[.'`-]", '', s); s = re.sub(r'\b(jr|sr|ii|iii|iv)\b', '', s)
    return ' '.join(s.split())
def phi(z): return .5 * math.erfc(-z / math.sqrt(2))
def season(d):
    y, m = int(d[:4]), int(d[5:7]); return '%d-%02d' % ((y, (y + 1) % 100) if m >= 8 else (y - 1, y % 100))

class History:
    """Same inputs Step 3 builds at the top of win_probability.py, plus finished ESPN games newer than the download."""
    def __init__(self, hist_db=None, fgm_db=None, espn_db=None):
        hist_db, fgm_db, espn_db = hist_db or HIST_DB, fgm_db or FGM_DB, espn_db or ESPN_DB
        db = sqlite3.connect('file:%s?mode=ro' % hist_db, uri=True); db.row_factory = sqlite3.Row
        fgm = {}; self.has_fgm = os.path.exists(fgm_db)
        if self.has_fgm:
            f = sqlite3.connect('file:%s?mode=ro' % fgm_db, uri=True)
            fgm = {(a, b): c for a, b, c in f.execute('select event_id, player_id, fgm from fgm')}; f.close()
        rows = [dict(r) for r in db.execute('select * from player_games where minutes>0 and points is not null order by game_date')]
        for r in rows: r['fgm'] = fgm.get((r['event_id'], r['player_id']))
        game_dates = {g['event_id']: g['game_date'] for g in db.execute('select event_id, game_date from games where final=1')}
        db.close()
        have = {(r['game_date'], r['team']) for r in rows}
        self.names = C.defaultdict(set); self.latest = {}
        for r in rows:
            self.names[norm(r['player'])].add(r['player_id']); self.latest[r['player_id']] = (r['game_date'], r['team'])
        self.espn_rows = 0
        if os.path.exists(espn_db):
            e = sqlite3.connect('file:%s?mode=ro' % espn_db, uri=True); e.row_factory = sqlite3.Row
            try: new = [dict(r) for r in e.execute('select p.*, g.game_date gd from player_games p join games g using(event_id) where g.final=1 and p.minutes>0 and p.points is not null order by g.game_date')]
            except sqlite3.OperationalError: new = []
            e.close()
            for x in new:
                if x['team'] not in TEAMS or x['opponent'] not in TEAMS: continue
                sid = TEAMS[x['team']][1]
                if (x['gd'], sid) in have: continue   # the download already has this team's game
                r = dict(event_id='espn:%s' % x['event_id'], player_id=self._espn_id(x['player'], sid, x['athlete_id']), player=x['player'], team=sid, opponent=TEAMS[x['opponent']][0], home=x['home'],
                         game_date=x['gd'], season=season(x['gd']), minutes=x['minutes'], points=x['points'], rebounds=x['rebounds'], assists=x['assists'], fgm=x['fgm'])
                rows.append(r); game_dates[r['event_id']] = r['game_date']; self.names[norm(r['player'])].add(r['player_id']); self.latest[r['player_id']] = (r['game_date'], sid); self.espn_rows += 1
            rows.sort(key=lambda r: r['game_date'])
        self.H = C.defaultdict(list); Allow = C.defaultdict(lambda: C.defaultdict(float))
        for r in rows:
            for k in ('rebounds', 'assists'): r[k] = r[k] or 0
            self.H[r['player_id']].append(r)
            for s, fn in STATS.items():
                try: Allow[(r['event_id'], r['opponent'])][s] += fn(r)
                except TypeError: pass
        self.TeamG = C.defaultdict(list)
        for (eid, team), v in Allow.items():
            d = game_dates.get(eid)
            if d: self.TeamG[team].append((d, dict(v)))
        for v in self.TeamG.values(): v.sort(key=lambda x: x[0])
        self.Lg = C.defaultdict(list)
        for v in self.TeamG.values():
            for d, a in v:
                for s, x in a.items(): self.Lg[s].append((d, x))
        for v in self.Lg.values(): v.sort(key=lambda x: x[0])
        self.last_game = rows[-1]['game_date'] if rows else None; self._of = {}
    def _espn_id(self, name, team_id, athlete_id):
        ids = self.names.get(norm(name), ())
        match = [i for i in ids if len(ids) == 1 or self.latest.get(i, (0, 0))[1] == team_id]
        return match[0] if len(match) == 1 else 'espn:%s' % athlete_id
    def resolve(self, name, team_abbr):
        """Player id for a PrizePicks name, or (None, reason). Two people with one name need the team to separate them."""
        ids = self.names.get(norm(name))
        if not ids: return None, 'no game history for this name'
        if len(ids) == 1: return next(iter(ids)), None
        t = TEAMS.get(abbr(team_abbr) or '', (0, 0))[1]; m = [i for i in ids if self.latest[i][1] == t]
        return (m[0], None) if len(m) == 1 else (None, 'two players share this name')
    def lg_mean(self, s, d):
        v = self.Lg[s]; i = bisect.bisect_left(v, (d,)); w = v[max(0, i - 400):i]
        return ST.mean(x for _, x in w) if len(w) >= 50 else None
    def opp_factor(self, s, team, d):
        k = (s, team, d)
        if k not in self._of:
            a = [x[1].get(s) for x in self.TeamG.get(team, []) if x[0] < d][-15:]
            a = [x for x in a if x is not None]; m = self.lg_mean(s, d)
            self._of[k] = ST.mean(a) / m if len(a) >= 5 and m else 1.0
        return self._of[k]
    def project(self, pid, stat, date, line, opponent, b2b=None, home=None):
        """Step 3's formula for one line. Returns (dict, None) or (None, reason). home None = home or away unknown: the two adjustments are averaged."""
        fn = STATS[stat]; hist = self.H.get(pid, []); i = bisect.bisect_left([h['game_date'] for h in hist], date)
        past = [h for h in hist[:i] if fn(h) is not None] if stat == 'fieldGoalsMade' else hist[:i]
        if len(past) < MIN_GAMES: return None, 'under 10 earlier games'
        rate = lambda L: sum(fn(h) for h in L) / max(1.0, sum(h['minutes'] for h in L))
        l5, l10 = past[-5:], past[-10:]; sea = [h for h in past if h['season'] == season(date)] or past[-30:]
        mins = .6 * ST.mean(h['minutes'] for h in l5) + .4 * ST.mean(h['minutes'] for h in l10); r = .4 * rate(l5) + .35 * rate(l10) + .25 * rate(sea)
        sd = max(ST.pstdev([fn(h) - r * h['minutes'] for h in past[-20:]]), 1.0)
        if b2b is None:
            last = hist[:i][-1]['game_date'] if hist[:i] else None
            b2b = int(bool(last) and (dt.date.fromisoformat(date) - dt.date.fromisoformat(last)).days == 1)
        k, adj = FIT[stat]; of = self.opp_factor(stat, opponent, date)
        a = adj[(b2b, home)] if home is not None else (adj[(b2b, 0)] + adj[(b2b, 1)]) / 2
        m = r * mins * (1 + OPP_WEIGHT * (of - 1)) * a; pm = phi((m - line) / (sd * k))
        return dict(projected=m, p_more=pm, sd=sd, b2b=b2b, games=len(past), minutes=mins), None

def load_saved_lines(folder=None):
    """Newest saved record per PrizePicks projection. The collector only writes new or changed lines, so a line pulled by
    PrizePicks after the last save can still be here: cards say when lines were saved. Returns (lines, last_saved, bad_rows)."""
    latest, last, bad = {}, None, 0
    for fn in sorted(glob.glob(os.path.join(folder or COLLECTED, '*.jsonl'))):
        with open(fn) as f:
            for l in f:
                try: r = json.loads(l); k = str(r['projection_id']); seen = r['seen']
                except (ValueError, KeyError, TypeError): bad += 1; continue
                if k not in latest or seen >= latest[k]['seen']: latest[k] = r
                if last is None or seen > last: last = seen
    lp = os.path.join(folder or COLLECTED, 'last_pull_ids.json')   # fresh lines: only what the latest full pull still had (his 11/6 go)
    if os.path.exists(lp):
        try:
            d = json.load(open(lp)); keep = set(d['ids'])
            latest = {k: dict(r, last_seen=d['at']) for k, r in latest.items() if k in keep}; last = d['at']
        except (ValueError, KeyError, TypeError, OSError): pass
    return list(latest.values()), last, bad
def collector_signature(folder=None):
    lp = os.path.join(folder or COLLECTED, 'last_pull_ids.json')
    return [(os.path.basename(f), os.path.getsize(f)) for f in sorted(glob.glob(os.path.join(folder or COLLECTED, '*.jsonl')))] + ([('last_pull_ids', os.path.getmtime(lp))] if os.path.exists(lp) else [])
def _kind(rec):
    o = str(rec.get('odds_type') or 'standard').lower()
    return o if o in ('goblin', 'demon') else 'standard'
def _schedule_lookup(team, date, espn_db=None):
    p = espn_db or ESPN_DB
    if not team or not os.path.exists(p): return None
    db = sqlite3.connect('file:%s?mode=ro' % p, uri=True)
    try: x = db.execute('select home_team, away_team from games where game_date=? and (home_team=? or away_team=?)', (date, team, team)).fetchone()
    except sqlite3.OperationalError: x = None
    db.close()
    return None if not x else ((x[1], 1) if x[0] == team else (x[0], 0))
def score_lines(lines, history, now=None, espn_db=None):
    """Every saved line that has not started becomes one row. NBA lines on a tested stat get a Win Probability; every other row says why not."""
    now = now or dt.datetime.now(dt.timezone.utc); out = []
    for r in lines:
        try: st = dt.datetime.fromisoformat(str(r.get('start')).replace('Z', '+00:00')).astimezone(dt.timezone.utc)
        except (ValueError, TypeError): continue
        if st <= now or str(r.get('status') or 'pre_game') != 'pre_game': continue
        date = st.astimezone(CT).date().isoformat(); league = str(r.get('league') or '?'); kind = _kind(r); name = str(r.get('player') or '?')
        team = abbr(r.get('team')); opp, home = parse_opponent(r.get('opponent')); promo = bool(r.get('is_promo')) or r.get('flash_sale_line') is not None
        row = dict(projection_id=str(r.get('projection_id')), league=league, player=name, team=team or r.get('team'), opponent=opp or r.get('opponent'), stat_raw=r.get('stat'), stat=None, line=r.get('line'), kind=kind,
                   start=st.isoformat(), game_date=date, seen=r.get('seen'), side=None, win_prob=None, projected=None, promo=promo, reason=None,
                   game_key='%s|%s|%s' % (league, date, '-'.join(sorted(str(x) for x in (team or r.get('team'), opp or r.get('opponent'))))))
        out.append(row)
        if league.upper() != 'NBA': row['reason'] = '🧪 no tested history yet for %s' % league; continue
        stat = PP_STATS.get(str(r.get('stat') or '').strip().lower()); row['stat'] = stat
        if '+' in name or 'combo' in str(r.get('stat') or '').lower(): row['reason'] = 'combo line: no tested method'; continue
        if not stat: row['reason'] = 'stat not tested in Step 3'; continue
        if stat == 'fieldGoalsMade' and not history.has_fgm: row['reason'] = 'field goals file not built'; continue
        try: line = float(r.get('line'))
        except (ValueError, TypeError): row['reason'] = 'no number on the line'; continue
        sch = _schedule_lookup(team, date, espn_db)
        if sch:
            opp = opp or sch[0]; home = sch[1] if home is None else home
            row['opponent'] = opp; row['game_key'] = '%s|%s|%s' % (league, date, '-'.join(sorted((team, opp))))
        if not opp or opp not in TEAMS: row['reason'] = 'opponent not understood'; continue
        pid, why = history.resolve(name, team)
        if not pid: row['reason'] = why; continue
        res, why = history.project(pid, stat, date, line, TEAMS[opp][0], home=home)
        if not res: row['reason'] = why; continue
        side = 'MORE' if kind != 'standard' or res['p_more'] >= .5 else 'LESS'   # Goblin and Demon lines are MORE only
        p = res['p_more'] if side == 'MORE' else 1 - res['p_more']
        row.update(side=side, win_prob=round(100 * p, 1), projected=round(res['projected'], 2), home=home, b2b=res['b2b'], games=res['games'])
    return out

def build_fgm(raw=RAW, out=FGM_DB):
    """Field goals made per player per game from the raw files, same read as Step 3. Kept apart from nba_history.sqlite, which build_history.py replaces."""
    os.makedirs(os.path.dirname(out), exist_ok=True); tmp = out + '.tmp'
    if os.path.exists(tmp): os.remove(tmp)
    db = sqlite3.connect(tmp); db.execute('create table fgm(event_id text, player_id text, fgm real, primary key(event_id, player_id))'); n = 0
    for f in glob.iglob(raw + '/*/*/*.json.gz'):
        with gzip.open(f, 'rt') as z: e = json.load(z)
        for pid, r in ((e.get('results') or {}).get('game') or {}).items():
            if isinstance(r, dict) and 'fieldGoalsMade' in r:
                db.execute('insert or replace into fgm values(?,?,?)', (e['eventID'], pid, r['fieldGoalsMade'])); n += 1
    db.commit(); db.close(); os.replace(tmp, out); return n
if __name__ == '__main__':
    import sys
    if '--build-fgm' in sys.argv: print('fgm rows', build_fgm())
    else: print(__doc__)
