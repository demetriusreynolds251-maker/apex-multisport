# APEX-NHLBOX-2026-11-08 (owner "Fix all problems"). Official NHL box scores (api-web.nhle.com, our own code) replace
# the wrong SportsGameOdds numbers in NHL history (shots on goal stored 0 in most Jan-Nov 2025 games, saves off by 1-2, some
# points missing). PrizePicks grades on the official NHL numbers, so history lines are regraded the same way.
# Usage: python3 nhlbox.py fetch | apply [dry]      Nightly: run_nightly() (scheduler, before grading): last 3 days, then apply.
def run_nightly():
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fetch(3); fetch_landing(3); msg = apply(False, backup=False)
    return msg
import os, sys, json, glob, time, sqlite3, shutil, unicodedata, urllib.request, datetime as dt, collections as C
API = 'https://api-web.nhle.com/v1/'
BOX = os.path.expanduser('~/openclaw/_backups/_sports_staging/freedata/nhl_hist/box')
# APEX-GRADINGGAPS-2026-11-13 (owner, "Fix grading gaps"): the official box score has power-play GOALS but not power-play
# assists, so PrizePicks "Power Play Points" could never be graded (every one voided). The same free official API's game "landing"
# file lists every goal with its strength and assists; it is saved next to the boxes and gives pp_points_box (PP goals + PP assists).
# Used by grading only (grading/grade.py), never by the projection model. Undo: git checkout before-grading-gaps -- history/nhl_official.py grading/grade.py
LAND = BOX + '_landing'
DONE = os.path.expanduser('~/openclaw/_backups/_sports_staging/fix_1108/nhl_dates_done.json')
DB = os.path.expanduser('~/ApexSports/hockey/nhl/database/history.db')
def get(p):
    req = urllib.request.Request(API + p, headers={'User-Agent': 'ApexSports-NHL-collector'})
    with urllib.request.urlopen(req, timeout=30) as r: return json.loads(r.read(20 * 1024 * 1024).decode('utf-8'))
def norm(s): return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower().replace('.', '').replace("'", '').strip()

def fetch(days_back=None):
    os.makedirs(BOX, exist_ok=True); os.makedirs(os.path.dirname(DONE), exist_ok=True)
    done = set(json.load(open(DONE))) if os.path.exists(DONE) else set()
    db = sqlite3.connect(DB); lo = db.execute('select min(game_date) from player_games').fetchone()[0]
    if days_back: lo = (dt.date.today() - dt.timedelta(days=days_back)).isoformat()
    d = dt.date.fromisoformat(lo[:10]); end = dt.date.today() - dt.timedelta(days=1); n = bad = 0
    while d <= end:
        day = d.isoformat(); d += dt.timedelta(days=1)
        if day in done: continue
        try: games = get('score/%s' % day).get('games') or []; time.sleep(0.3)
        except Exception: bad += 1; continue
        ok = True
        for g in games:
            if g.get('gameType') not in (2, 3): continue
            if g.get('gameState') not in ('OFF', 'FINAL'): ok = False; continue
            f = os.path.join(BOX, '%s.json' % g['id'])
            if os.path.exists(f): continue
            try:
                b = get('gamecenter/%s/boxscore' % g['id']); time.sleep(0.3)
                if 'playerByGameStats' in b: json.dump(b, open(f, 'w')); n += 1
                else: ok = False
            except Exception: bad += 1; ok = False
        if ok: done.add(day)
        if len(done) % 20 == 0: json.dump(sorted(done), open(DONE, 'w'))
    json.dump(sorted(done), open(DONE, 'w'))
    print('new boxes', n, 'errors', bad, 'dates done', len(done)); return n

def fetch_landing(days_back=3, since=None):
    """Saves gamecenter/<id>/landing for every saved box of the last days_back days (or since a date) that has none yet."""
    os.makedirs(LAND, exist_ok=True); lo = since or (dt.date.today() - dt.timedelta(days=days_back)).isoformat(); n = bad = 0
    for f in sorted(glob.glob(os.path.join(BOX, '*.json'))):
        gid = os.path.basename(f)[:-5]; out = os.path.join(LAND, gid + '.json')
        if os.path.exists(out): continue
        try:
            if (json.load(open(f)).get('gameDate') or '') < lo: continue
            j = get('gamecenter/%s/landing' % gid); time.sleep(0.3)
            if isinstance((j.get('summary') or {}).get('scoring'), list): json.dump(j, open(out, 'w')); n += 1
        except Exception: bad += 1
    print('new landing files', n, 'errors', bad); return n

def pp_points(gid):
    """{playerId: power-play points} from the saved landing file, None when there is none."""
    f = os.path.join(LAND, '%s.json' % gid)
    if not os.path.exists(f): return None
    out = C.Counter()
    for per in json.load(open(f))['summary']['scoring']:
        for g in per.get('goals') or []:
            if g.get('strength') != 'pp': continue
            out[g.get('playerId')] += 1
            for a in g.get('assists') or []: out[a.get('playerId')] += 1
    return out

def official():
    B = C.defaultdict(list); teams = set()
    for f in glob.glob(os.path.join(BOX, '*.json')):
        j = json.load(open(f)); d = j.get('gameDate'); ppp = pp_points(j.get('id'))
        for side in ('homeTeam', 'awayTeam'):
            ab = j[side]['abbrev']; teams.add((d, ab))
            for grp in ('forwards', 'defense', 'goalies'):
                for p in j['playerByGameStats'][side].get(grp) or []:
                    if ppp is not None and p.get('position') != 'G': p = dict(p, _pp=float(ppp.get(p.get('playerId'), 0)))
                    nm = norm(p['name']['default']); ini, last = nm.split(' ', 1) if ' ' in nm else ('', nm)
                    B[(d, ab, ini[:1], last)].append(p)
    return B, teams

def stats_of(p):
    if p.get('position') == 'G':
        return {'saves': float(p.get('saves') or 0), 'goals_against': float(p.get('goalsAgainst') or 0), 'goals': 0.0, 'assists': 0.0, 'points_raw': 0.0}
    s = {'shots': float(p.get('sog') or 0), 'goals': float(p.get('goals') or 0), 'assists': float(p.get('assists') or 0),
         'points_raw': float(p.get('points') or 0), 'hits': float(p.get('hits') or 0), 'blocked': float(p.get('blockedShots') or 0)}
    if '_pp' in p: s['pp_points_box'] = p['_pp']   # APEX-GRADINGGAPS-2026-11-13
    return s

AL = {'LA': 'LAK', 'NJ': 'NJD', 'SJ': 'SJS', 'TB': 'TBL', 'BBR': 'BOS', 'UMA': 'UTA'}   # our stored code -> NHL code
PL = {'sog': 'shots', 'goals': 'goals', 'assists': 'assists', 'points': 'points_raw', 'saves': 'saves', 'hits': 'hits', 'blocked': 'blocked', 'goals_against': 'goals_against'}

def apply(dry, backup=True):
    B, teams = official()
    db = sqlite3.connect(DB)
    if not dry and backup:
        bk = os.path.expanduser('~/openclaw/_backups/_sports_staging/fix_1108/history_nhl.db.before-nhl-box-scores')
        if not os.path.exists(bk): shutil.copy2(DB, bk)
    chg = C.Counter(); rem = []; amb = 0; matched = 0; nomatch = 0
    rows = db.execute('select rowid, event_id, player, player_norm, team, game_date, stats_json, source from player_games').fetchall()
    upd = []
    for rid, ev, pl, pn, team, d, sj, src in rows:
        nm = norm(pl).split(' ', 1)
        if len(nm) < 2: continue
        hit = B.get((d[:10], AL.get(team, team), nm[0][:1], nm[1]))
        if not hit:
            if (d[:10], AL.get(team, team)) in teams:
                st = json.loads(sj or '{}'); vals = [v for k, v in st.items() if isinstance(v, (int, float)) and not k.startswith('_')]
                if src == 'sgo' and vals and all(v == 0 for v in vals): rem.append(rid)
                else: nomatch += 1
            continue
        if len(hit) > 1: amb += 1; continue
        matched += 1; st = json.loads(sj or '{}'); new = dict(st); off = stats_of(hit[0])
        for k, v in off.items():
            if k not in st or abs((st.get(k) or 0) - v) > 1e-9:
                chg[k] += 1; new[k] = v
        if new != st: new['_box'] = 'nhl'; upd.append((json.dumps(new), rid))
    print('player games matched to official box', matched, 'ambiguous skipped', amb, 'no official row (kept)', nomatch)
    print('values changed', dict(chg), 'rows changed', len(upd))
    print('all-zero rows for players not in the official box that day (did not play) to remove', len(rem))
    # regrade PrizePicks history lines
    pg = C.Counter(); flips = C.Counter(); regr = []
    for rid, d, pl, team, stat, line, res in db.execute('select rowid, game_date, player, team, stat, pp_line, result from prop_lines where result is not null'):
        if stat not in PL: continue
        nm = norm(pl).split(' ', 1)
        if len(nm) < 2: continue
        hit = B.get((d[:10], AL.get(team, team), nm[0][:1], nm[1]))
        if not hit or len(hit) != 1: continue
        v = stats_of(hit[0]).get(PL[stat])
        if v is None or abs(v - res) < 1e-9: continue
        pg[stat] += 1
        if line is not None and ((res > line) != (v > line) or (res < line) != (v < line)): flips[stat] += 1
        regr.append((v, rid))
    print('history lines regraded', dict(pg), 'MORE/LESS outcome flipped', dict(flips))
    if dry: return
    db.execute('create table if not exists player_games_removed as select * from player_games where 0')
    for rid in rem:
        db.execute('insert into player_games_removed select * from player_games where rowid=?', (rid,)); db.execute('delete from player_games where rowid=?', (rid,))
    db.executemany('update player_games set stats_json=? where rowid=?', upd)
    db.executemany('update prop_lines set result=? where rowid=?', regr)
    db.commit(); print('APPLIED'); return '🏒 Official NHL box scores: %d player games checked, %d corrected, %d history lines regraded' % (matched, len(upd), len(regr))

if __name__ == '__main__':
    if sys.argv[1] == 'fetch': fetch()
    elif sys.argv[1] == 'landing': fetch_landing(since=sys.argv[2] if len(sys.argv) > 2 else None)
    else: apply('dry' in sys.argv)
