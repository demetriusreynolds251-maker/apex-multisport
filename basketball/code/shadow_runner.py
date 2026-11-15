#!/usr/bin/env python3
"""APEX BASKETBALL - Phase 8 shadow runner (his go "Go nba shadow", 2026-11-05 12:35 AM CT).
Posts the NO-BOOK Top 3 in the TEST server (#bball-picks) once a day, grades it the next morning (#bball-slips),
keeps the shadow record in shadow_tests/shadow.sqlite, posts TEST PROGRESS every 10 days and the 40-day verdict.
Rule (Phase 6 without book lines, both halves): a pick is either
  (a) HOT + LESS: player's last 5 games average 15%+ above his last-40 average, projection says LESS, stat is not points alone; or
  (b) projection MORE at 80%+ sure.
Ranked by projection chance, one pick per game, 3 needed or "no board today".
Reads only data/collected (PrizePicks lines saved by line_collector.py), the history databases and ESPN box scores. No PrizePicks calls here.
Discord: REST post with the bot token read at run time from secrets/discord_bot_token.txt; never printed.
Run: nohup python3 code/shadow_runner.py --loop  |  python3 code/shadow_runner.py --once --dry [--date YYYY-MM-DD]"""
import argparse, datetime as dt, json, math, os, sqlite3, statistics as ST, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import score_board as SB, espn_results as ER
ROOT = SB.ROOT; CT = SB.CT
DB = os.path.join(ROOT, 'shadow_tests', 'shadow.sqlite'); STATE = os.path.join(ROOT, 'shadow_tests', 'state.json')
TOKEN_FILE = os.path.join(ROOT, 'secrets', 'discord_bot_token.txt'); CHANNEL_FILE = os.path.join(ROOT, 'data', 'discord_channels.json')
PID_FILE = os.path.join(ROOT, 'logs', 'shadow_runner.pid')
POST_HOUR, GRADE_HOUR, TEST_DAYS, BOARD = 16, 5, 40, 3
HOT, SURE = 0.15, 0.80
FOOT = '🧪 SHADOW TEST, not on real money record'
STATS = {'points': ('Points', lambda r: r['points']), 'rebounds': ('Rebounds', lambda r: r['rebounds']), 'assists': ('Assists', lambda r: r['assists']),
         'rebounds+assists': ('Rebs+Asts', lambda r: r['rebounds'] + r['assists']), 'points+rebounds+assists': ('PRA', lambda r: r['points'] + r['rebounds'] + r['assists']),
         'points+rebounds': ('Pts+Rebs', lambda r: r['points'] + r['rebounds']), 'points+assists': ('Pts+Asts', lambda r: r['points'] + r['assists']),
         'fieldGoalsMade': ('FG Made', lambda r: r['fgm'])}
PP = {'points': 'points', 'rebounds': 'rebounds', 'assists': 'assists', 'rebs+asts': 'rebounds+assists', 'rebounds+assists': 'rebounds+assists',
      'pts+rebs+asts': 'points+rebounds+assists', 'pra': 'points+rebounds+assists', 'points+rebounds+assists': 'points+rebounds+assists',
      'pts+rebs': 'points+rebounds', 'points+rebounds': 'points+rebounds', 'pts+asts': 'points+assists', 'points+assists': 'points+assists',
      'fg made': 'fieldGoalsMade', 'field goals made': 'fieldGoalsMade', 'fgm': 'fieldGoalsMade'}
ESPN_VALUE = {'points': lambda r: r[0], 'rebounds': lambda r: r[1], 'assists': lambda r: r[2], 'rebounds+assists': lambda r: r[1] + r[2], 'points+rebounds+assists': lambda r: r[0] + r[1] + r[2],
              'points+rebounds': lambda r: r[0] + r[1], 'points+assists': lambda r: r[0] + r[2], 'fieldGoalsMade': lambda r: r[3]}
def log(m): print('%s %s' % (dt.datetime.now(CT).strftime('%m/%d %H:%M:%S'), m), flush=True)
def ncdf(x): return 0.5 * (1 + math.erf(x / math.sqrt(2)))
def connect():
    os.makedirs(os.path.dirname(DB), exist_ok=True); db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    db.executescript("""create table if not exists picks(game_date text, rank integer, player text, team text, opponent text, stat text, line real, side text, chance real, rule text, why text,
        start_utc text, projection_id text, status text default 'open', value real, graded_at text, primary key(game_date, rank));
      create table if not exists days(game_date text primary key, posted_at text, n_picks integer, result text, legs_won integer, graded_at text);""")
    return db
def load_state():
    try: return json.load(open(STATE))
    except (OSError, ValueError): return {}
def save_state(s): json.dump(s, open(STATE, 'w'), indent=1)
def post(channel, text, dry=False):
    if dry: print('--- would post to #%s ---\n%s\n' % (channel, text)); return True
    try: ch = json.load(open(CHANNEL_FILE)).get(channel); tok = open(TOKEN_FILE).read().strip()
    except (OSError, ValueError): log('NOT POSTED: no channel file or token'); return False
    if not ch: log('NOT POSTED: no channel #%s' % channel); return False
    ok = True
    for part in [text[i:i + 1900] for i in range(0, len(text), 1900)][:4]:
        req = urllib.request.Request('https://discord.com/api/v10/channels/%s/messages' % ch, data=json.dumps({'content': part}).encode(),
                                     headers={'Authorization': 'Bot ' + tok, 'Content-Type': 'application/json', 'User-Agent': 'ApexBasketballShadow/1.0'})
        try:
            with urllib.request.urlopen(req, timeout=30) as r: r.read()
        except Exception as e: log('NOT POSTED #%s: %s' % (channel, type(e).__name__)); ok = False
        time.sleep(1)
    return ok
def project(hist, pid, stat, date, opp_long):
    label, fn = STATS[stat]; H = [h for h in hist.H.get(pid, []) if h['game_date'] < date and h['minutes'] and h['minutes'] > 0]
    try: H = [h for h in H if fn(h) is not None]
    except TypeError: H = []
    if len(H) < 5: return None, 'under 5 earlier games'
    l5, l10, l40 = H[-5:], H[-10:], H[-40:]
    mins = .6 * ST.mean(h['minutes'] for h in l5) + .4 * ST.mean(h['minutes'] for h in l10)
    rate = lambda L: sum(fn(h) for h in L) / max(1.0, sum(h['minutes'] for h in L))
    r = .4 * rate(l5) + .35 * rate(l10) + .25 * rate(l40)
    sd = max(ST.pstdev([fn(h) for h in l10]), 1.0) if len(l10) >= 3 else 1.0
    of = hist.opp_factor(stat, opp_long, date) if stat in SB.STATS else 1.0
    of = max(.8, min(1.2, of)); proj = mins * r * of
    f40 = ST.mean(fn(h) for h in l40); form = (ST.mean(fn(h) for h in l5) / f40 - 1) if f40 else 0
    return dict(proj=proj, sd=sd, form=form, games=len(H), last=H[-1]['game_date']), None
def build(date, hist, now=None, dry=False):
    """Candidates for one CT game date from the saved lines. Returns (picks, n_lines_seen, n_candidates)."""
    now = now or dt.datetime.now(dt.timezone.utc); lines, saved, bad = SB.load_saved_lines(); cands = []; seen = 0
    for r in lines:
        try: st = dt.datetime.fromisoformat(str(r.get('start')).replace('Z', '+00:00')).astimezone(dt.timezone.utc)
        except (ValueError, TypeError): continue
        if st.astimezone(CT).date().isoformat() != date or str(r.get('league') or '') != 'NBA': continue
        if not dry and st <= now: continue
        if str(r.get('odds_type') or 'standard').lower() != 'standard' or r.get('is_promo') or r.get('flash_sale_line') is not None: continue
        stat = PP.get(str(r.get('stat') or '').strip().lower())
        if not stat: continue
        seen += 1; name = str(r.get('player') or '?'); team = SB.abbr(r.get('team')); opp, home = SB.parse_opponent(r.get('opponent'))
        sch = SB._schedule_lookup(team, date)
        if sch: opp = opp or sch[0]
        if not team or not opp or opp not in SB.TEAMS: continue
        pid, why = hist.resolve(name, team)
        if not pid: continue
        try: line = float(r.get('line'))
        except (ValueError, TypeError): continue
        pr, why = project(hist, pid, stat, date, SB.TEAMS[opp][0])
        if not pr: continue
        p_more = 1 - ncdf((line - pr['proj']) / pr['sd']); side = 'MORE' if p_more >= .5 else 'LESS'; p = max(p_more, 1 - p_more)
        rule = None
        if side == 'LESS' and pr['form'] >= HOT and stat != 'points': rule = 'hot_less'; why = 'hot: last 5 games %.0f%% above his average, taking LESS' % (100 * pr['form'])
        elif side == 'MORE' and p >= SURE: rule = 'sure_more'; why = 'projection %.1f, %.0f%% sure of MORE' % (pr['proj'], 100 * p)
        if not rule: continue
        cands.append(dict(game_date=date, player=name, team=team, opponent=opp, stat=stat, line=line, side=side, chance=round(100 * p, 1), rule=rule, why=why,
                          start_utc=st.isoformat(), projection_id=str(r.get('projection_id')), game='-'.join(sorted((team, opp))), proj=pr['proj']))
    cands.sort(key=lambda c: (-c['chance'], c['player'])); picks = []; games = set(); players = set()
    for c in cands:
        if c['game'] in games or c['player'] in players: continue
        picks.append(c); games.add(c['game']); players.add(c['player'])
        if len(picks) == BOARD: break
    return picks, seen, len(cands), saved
def board_text(date, picks, seen, ncand, saved, day_no):
    d = dt.date.fromisoformat(date).strftime('%a %-m/%-d'); L = ['🏀 **SHADOW NBA Top 3** (no book lines) · %s · day %d of %d' % (d, day_no, TEST_DAYS)]
    if len(picks) < BOARD:
        L.append('No board today: %d pick%s qualified, 3 needed (%d standard lines looked at). No picks made up.' % (len(picks), '' if len(picks) == 1 else 's', seen))
    for i, c in enumerate(picks, 1):
        L.append('%d. **%s** %s %s %s · %s v %s · %s' % (i, c['player'], c['side'], ('%g' % c['line']), STATS[c['stat']][0], c['team'], c['opponent'], dt.datetime.fromisoformat(c['start_utc']).astimezone(CT).strftime('%-I:%M %p CT')))
        L.append('   ↳ %s' % c['why'])
    L.append('Rule: hot player on LESS (not points) or projection 80%+ MORE; ranked by projection chance; one pick per game. History: 41-128 full-slip days (24%), break-even 17%.')
    L.append('📥 Lines saved %s. Shadow only: nothing to play.' % (dt.datetime.fromisoformat(saved.replace('Z', '+00:00')).astimezone(CT).strftime('%-I:%M %p CT') if saved else 'never'))
    return '\n'.join(L + [FOOT])
def record(db, date, picks, dry=False):
    if dry: return
    db.execute('insert or replace into days(game_date, posted_at, n_picks, result) values(?,?,?,?)', (date, dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), len(picks), 'no_board' if len(picks) < BOARD else 'open'))
    for i, c in enumerate(picks, 1):
        db.execute('insert or replace into picks(game_date, rank, player, team, opponent, stat, line, side, chance, rule, why, start_utc, projection_id) values(?,?,?,?,?,?,?,?,?,?,?,?,?)',
                   (date, i, c['player'], c['team'], c['opponent'], c['stat'], c['line'], c['side'], c['chance'], c['rule'], c['why'], c['start_utc'], c['projection_id']))
    db.commit()
def grade_pick(espn, c):
    g = espn.execute('select event_id from games where game_date=? and final=1 and box_saved=1 and (home_team=? or away_team=?)', (c['game_date'], c['team'], c['team'])).fetchone()
    if not g: return 'open', None
    rows = [r for r in espn.execute('select points,rebounds,assists,fgm,minutes,player from player_games where event_id=? and team=?', (g[0], c['team'])) if SB.norm(r[5]) == SB.norm(c['player'])]
    if not rows: return 'void', None
    r = rows[0]
    if not r[4] or r[4] <= 0: return 'void', None
    try: v = ESPN_VALUE[c['stat']]([x or 0 for x in r[:4]])
    except TypeError: return 'open', None
    if v == c['line']: return 'push', v
    return ('won' if (v > c['line']) == (c['side'] == 'MORE') else 'lost'), v
def records(db):
    days = db.execute("select result, count(*) n from days where result in ('won','lost') group by result").fetchall(); d = {r['result']: r['n'] for r in days}
    legs = db.execute("select status, count(*) n from picks where status in ('won','lost') group by status").fetchall(); l = {r['status']: r['n'] for r in legs}
    return d.get('won', 0), d.get('lost', 0), l.get('won', 0), l.get('lost', 0)
def grade(db, dates, dry=False):
    """Grades open shadow days. Posts one card per graded day in #bball-slips."""
    try: ER.update(sorted(dates), pause=1.0)
    except Exception as e: log('ESPN update failed: %s' % type(e).__name__)
    espn = sqlite3.connect('file:%s?mode=ro' % ER.ESPN_DB, uri=True); out = []
    for day in db.execute("select * from days where result='open' order by game_date").fetchall():
        picks = db.execute('select * from picks where game_date=? order by rank', (day['game_date'],)).fetchall(); st = []
        for c in picks:
            s, v = grade_pick(espn, dict(c)); st.append(s)
            if s != 'open': db.execute("update picks set status=?, value=?, graded_at=? where game_date=? and rank=?", (s, v, dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), c['game_date'], c['rank']))
        if 'open' in st: db.commit(); continue
        live = [s for s in st if s in ('won', 'lost')]; result = 'void' if not live else ('won' if all(s == 'won' for s in live) else 'lost')
        db.execute("update days set result=?, legs_won=?, graded_at=? where game_date=?", (result, st.count('won'), dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), day['game_date'])); db.commit()
        dw, dl, lw, ll = records(db); mark = {'won': '✅', 'lost': '❌', 'push': '➖ push', 'void': '⚪ void (did not play)'}
        L = ['🏀 **SHADOW NBA Top 3 result** · %s · %s' % (dt.date.fromisoformat(day['game_date']).strftime('%a %-m/%-d'), {'won': 'DAY WON ✅', 'lost': 'day lost ❌', 'void': 'void'}[result])]
        for c, s in zip(picks, st):
            L.append('%d. %s %s %g %s: %s %s' % (c['rank'], c['player'], c['side'], c['line'], STATS[c['stat']][0], ('%g' % c['value']) if c['value'] is not None else '-', mark[s]))
        L.append('Shadow record: days %d-%d, legs %d-%d (need 1 win in 6 days to break even at 6x; target 1 in 4).' % (dw, dl, lw, ll))
        post('bball-slips', '\n'.join(L + [FOOT]), dry); out.append((day['game_date'], result))
        n = dw + dl
        if n and n % 10 == 0: post('bball-system', '🧪 TEST PROGRESS · SHADOW NBA Top 3 · %d of %d board days: days %d-%d, legs %d-%d. %d days to go.\n%s' % (n, TEST_DAYS, dw, dl, lw, ll, TEST_DAYS - n, FOOT), dry)
        if n == TEST_DAYS:
            ok = dw >= n / 4
            post('bball-system', ('🟢 PROMOTION CANDIDATE' if ok else ('🔴 TEST FAILURE' if dw < n / 6 else '🟡 TEST PROGRESS: break-even but under target')) + ' · SHADOW NBA Top 3 · days %d-%d, legs %d-%d over %d board days. Nothing changes without your go.\n%s' % (dw, dl, lw, ll, n, FOOT), dry)
    espn.close(); return out
def run_once(dry=False, date=None, force=False):
    db = connect(); s = load_state(); now = dt.datetime.now(CT); today = date or now.date().isoformat()
    if date or force or (now.hour >= POST_HOUR and s.get('posted') != today):
        hist = SB.History(); picks, seen, ncand, saved = build(today, hist, dry=dry or bool(date))
        day_no = db.execute("select count(*) from days where result!='no_board'").fetchone()[0] + (0 if len(picks) < BOARD else 1)
        text = board_text(today, picks, seen, ncand, saved, day_no)
        if post('bball-picks', text, dry): record(db, today, picks, dry or bool(date)); s['posted'] = today; (not dry and not date) and save_state(s)
        post('bball-system', '🧪 Shadow runner: %s, %d standard lines looked at, %d qualified, %d pick%s posted.' % (today, seen, ncand, len(picks), '' if len(picks) == 1 else 's'), dry)
        log('posted %s: %d picks of %d candidates' % (today, len(picks), ncand))
    if force or (now.hour >= GRADE_HOUR and s.get('graded') != today):
        yd = (now.date() - dt.timedelta(days=1)).isoformat()
        open_dates = {r[0] for r in db.execute("select game_date from days where result='open'")} | {yd}
        g = grade(db, open_dates, dry)
        if not dry: s['graded'] = today; save_state(s)
        if g: post('bball-system', '🧪 Shadow grading: %s.' % ', '.join('%s %s' % x for x in g), dry)
    db.close()
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--loop', action='store_true'); ap.add_argument('--once', action='store_true'); ap.add_argument('--dry', action='store_true')
    ap.add_argument('--date'); ap.add_argument('--force', action='store_true'); a = ap.parse_args()
    if a.loop:
        os.makedirs(os.path.dirname(PID_FILE), exist_ok=True); open(PID_FILE, 'w').write(str(os.getpid())); log('shadow runner started pid %d: board after %d:00 CT, grading after %d:00 CT' % (os.getpid(), POST_HOUR, GRADE_HOUR))
        post('bball-system', '🧪 Shadow runner started: SHADOW NBA Top 3 (no book lines) posts here daily after %d:00 CT, graded after %d:00 CT. %s' % (POST_HOUR, GRADE_HOUR, FOOT))
        while True:
            try: run_once()
            except Exception as e:
                log('run failed %s: %s' % (type(e).__name__, e)); post('bball-alerts', '⚠️ Shadow runner failed: %s: %s\n%s' % (type(e).__name__, str(e)[:200], FOOT))
            time.sleep(300)
    else: run_once(dry=a.dry, date=a.date, force=a.force)
if __name__ == '__main__': main()
