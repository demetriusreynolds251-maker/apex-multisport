#!/usr/bin/env python3
"""APEX-FREEDATA-2026-11-06 (owner, "Go add the free GitHub ... make our own"): our own NHL collector for the NHL's free public
JSON (api-web.nhle.com). No outside package or code. Saves every finished game's box score in data/free/nhl/box/<game id>.json and
cache/free_nhl.json = per player {team, position, ice time last 5 games, ice time trend, power play goals, goalie starts last 10 team games}.
DATA ONLY: nothing here changes a pick or a board. Never raises."""
import json, os, sys, time, urllib.request, datetime as dt, collections as C
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import common as CM
API = 'https://api-web.nhle.com/v1/'
OUT = os.path.join(ROOT, 'data', 'free', 'nhl'); BOX = os.path.join(OUT, 'box'); ROST = os.path.join(OUT, 'rosters')
DAYS_BACK = 14       # first run fills the last 2 weeks, later runs only add new finished games
PAUSE_S = 0.5        # polite gap between calls


def _get(path):
    req = urllib.request.Request(API + path, headers={'User-Agent': 'ApexSports-NHL-collector'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read(20 * 1024 * 1024).decode('utf-8'))


def _mins(toi):
    try:
        m, s = str(toi).split(':'); return int(m) + int(s) / 60.0
    except Exception:
        return None


def _roster(team, names):
    """playerId -> full name for one team, cached one day."""
    f = os.path.join(ROST, team + '.json')
    try:
        if os.path.exists(f) and time.time() - os.path.getmtime(f) < 86400:
            names.update({int(k): v for k, v in json.load(open(f)).items()}); return
        d = _get('roster/%s/current' % team); time.sleep(PAUSE_S); m = {}
        for grp in ('forwards', 'defensemen', 'goalies'):
            for p in d.get(grp) or []:
                m[int(p['id'])] = '%s %s' % (p['firstName']['default'], p['lastName']['default'])
        json.dump(m, open(f, 'w')); names.update(m)
    except Exception:
        pass


def run():
    for d in (OUT, BOX, ROST):
        os.makedirs(d, exist_ok=True)
    new, bad = 0, []
    today = dt.date.today()
    for k in range(DAYS_BACK, -1, -1):
        day = (today - dt.timedelta(days=k)).isoformat()
        try:
            games = _get('score/%s' % day).get('games') or []; time.sleep(PAUSE_S)
        except Exception as e:
            bad.append('%s schedule (%s)' % (day, type(e).__name__)); continue
        for g in games:
            if g.get('gameState') not in ('OFF', 'FINAL') or g.get('gameType') not in (2, 3):
                continue
            f = os.path.join(BOX, '%s.json' % g['id'])
            if os.path.exists(f):
                continue
            try:
                b = _get('gamecenter/%s/boxscore' % g['id']); time.sleep(PAUSE_S)
                if 'playerByGameStats' not in b:
                    bad.append('%s no player stats' % g['id']); continue
                tmp = f + '.%d.tmp' % os.getpid(); json.dump(b, open(tmp, 'w')); os.replace(tmp, f); new += 1
            except Exception as e:
                bad.append('%s box (%s)' % (g['id'], type(e).__name__))
    # summary from every saved box score
    games = []
    for fn in os.listdir(BOX):
        try: games.append(json.load(open(os.path.join(BOX, fn))))
        except Exception: pass
    games.sort(key=lambda b: b.get('gameDate') or '')
    names = {}
    for t in {b[s]['abbrev'] for b in games for s in ('awayTeam', 'homeTeam')}:
        _roster(t, names)
    T = C.defaultdict(list); team_games = C.defaultdict(list); starts = C.defaultdict(list); pos = {}; tm = {}; ppg = C.Counter()
    for b in games:
        for side in ('awayTeam', 'homeTeam'):
            team = b[side]['abbrev']; team_games[team].append(b['id'])
            st = b['playerByGameStats'][side]
            for grp in ('forwards', 'defense', 'goalies'):
                for p in st.get(grp) or []:
                    pid = int(p['playerId']); m = _mins(p.get('toi'))
                    if m is None: continue
                    pos[pid] = p.get('position'); tm[pid] = team; ppg[pid] += int(p.get('powerPlayGoals') or 0)
                    if grp == 'goalies':
                        if p.get('starter'): starts[pid].append(b['id'])
                    else:
                        T[pid].append(m)
    P = {}
    for pid, v in T.items():
        last5 = v[-5:]; prev = v[-7:-2]
        P[CM.norm(names.get(pid, ''))] = dict(team=tm[pid], pos=pos.get(pid), toi_last5=round(sum(last5) / len(last5), 1),
                                             toi_trend=round(sum(v[-2:]) / len(v[-2:]) - sum(prev) / len(prev), 1) if len(v) >= 4 else None,
                                             games=len(v), pp_goals=ppg[pid])
    for pid, s in starts.items():
        last10 = team_games[tm[pid]][-10:]
        P[CM.norm(names.get(pid, ''))] = dict(team=tm[pid], pos='G', starts_last10=sum(1 for g in s if g in last10), team_games=len(last10))
    P.pop('', None)
    out = dict(at=CM.iso(), games=len(games), players=P, problems=bad[:10])
    tmp = os.path.join(ROOT, 'cache', 'free_nhl.json.tmp'); json.dump(out, open(tmp, 'w')); os.replace(tmp, os.path.join(ROOT, 'cache', 'free_nhl.json'))
    return '🆓 NHL free data: %d new box score%s, %d games on file, %d players%s' % (new, '' if new == 1 else 's', len(games), len(P),
                                                                                 (' · ⚠️ %d problem(s): %s' % (len(bad), '; '.join(bad[:3]))) if bad else '')


if __name__ == '__main__':
    print(run())
