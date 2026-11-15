#!/usr/bin/env python3
"""Text for every Apex Basketball card and command. No Discord objects here, so all of it runs in the offline test."""
import datetime as dt, json, re
import score_board as SB, bball_tracker as T, bball_pipeline as P, prob_engine as PE
FOOT = ''   # APEX-REMOVETEST-2026-11-10 (owner, "go remove test"): the TEST label is gone from every card
HONEST = '🧪 Win Prob = the engine\'s own chance the side hits. Backtest 11/5 (20,560 lines, unseen half): Goblin/Demon ladder odds hit what they say (85% said = 85% hit); Standard lines are near a coin flip for everyone (engine tier A 59%, books 54%).'
KIND = {'goblin': '🟢 Goblin', 'demon': '🔴 Demon', 'standard': ''}
SLIP_NAME = {'top3': 'Top 3 (3-pick Power)', 'elite5': 'Elite 5 (5-pick Flex)', 'elite6': 'Elite 6 (6-pick Flex)'}
BOARD_CMD = {'bball-top3': 'top3', 'bball-elite5': 'elite5', 'bball-elite6': 'elite6', 'bball-top10': 'top10', 'bball-bestgoblin': 'bestgoblin', 'bball-bestless': 'bestless', 'bball-beststandard': 'beststandard', 'bball-bestdemon': 'bestdemon'}
def _ct(iso, fmt='%-I:%M %p CT'):
    if not iso: return 'never'
    return dt.datetime.fromisoformat(iso.replace('Z', '+00:00')).astimezone(SB.CT).strftime(fmt)
def saved_line(cur):
    """When lines were saved. A line PrizePicks has pulled since then can still show, so it says to check the app."""
    txt = '📥 Lines last saved %s. Check the app before playing: a line may have moved or come down since.' % _ct(cur['lines_saved_at'], '%-m/%-d %-I:%M %p CT')
    try:   # APEX-FEEDALERT-2026-11-10: say it loudly when the saved lines are old
        import datetime as _dt
        age = (_dt.datetime.now(_dt.timezone.utc) - _dt.datetime.fromisoformat(str(cur['lines_saved_at']).replace('Z', '+00:00'))).total_seconds() / 3600
        if age >= 2: txt = '⚠️⚠️ OLD LINES: these lines are %d hours old. PrizePicks has not been pulled since. Wait for a fresh pull before playing.\n' % age + txt
    except Exception: pass
    return txt
def stat_name(r): return SB.STAT_LABEL.get(r.get('stat')) or (PE.STATS.get(r.get('stat')) or ('',))[0] or str(r.get('stat_raw') or '?')
def pick_line(r, n=None, tag=''):
    k = KIND.get(r['kind'], ''); lg = '' if r['league'].upper() == 'NBA' else '[%s] ' % r['league']
    head = '**%s** %s %s %s' % (r['player'], r['side'], r['line'], stat_name(r))
    t = (' · tier %s' % r['tier']) if r.get('tier') else ''; e = (' · edge %d' % r['edge_score']) if r.get('edge_score') is not None else ''
    line = '%s%s%s · %s%%%s%s · %s%sv %s · %s%s' % ('%d. ' % n if n else '• ', lg, head, ('%.0f' % r['win_prob']), t, e, (k + ' · ') if k else '', '', r['opponent'], _ct(r['start']), tag)
    return line + ('\n     ↳ %s' % r['why'] if r.get('why') else '')
def _no_data(): return '🧪 No scored lines yet. The collector has to save lines first, then the bot scores them.\n' + FOOT
def _kind_warn(rows):
    return ['🟢🔴 Goblin and Demon lines are over only; their Win Prob is the engine\'s ladder odds (tested: 85% said = 85% hit).'] if any(r['kind'] != 'standard' for r in rows) else []
RULE = '━━━━━━━━━━━━━━━━━━━━━━━━'
KIND_FULL = {'goblin': '🟢 Goblin', 'demon': '🔴 Demon', 'standard': '⚪ Standard'}
TIER_BAND = {'A': (70, 101), 'B': (65, 70), 'C': (60, 65), 'D': (0, 60)}
BACKTEST = {'A': (85, 85), 'B': (70, 70), 'C': (64, 64), 'D': (57, 57)}   # 11/5 unseen half, ladder lines: (said, hit)
ENGINE_SINCE = '2026-11-05T20:30:00'   # picks scored before this came from the old Step 3 scorer: not the engine's record
def real_record(r):
    """Graded basketball picks of this tier and line kind since the engine went live, else the backtest line."""
    lo, hi = TIER_BAND.get(r.get('tier') or 'D'); db = T.connect()
    if r.get('gless'):   # APEX-GOBLINLESS-NBA-2026-11-12: Goblin LESS picks have their own record
        try: x = db.execute("select sum(status='win'), sum(status='loss') from picks where league='NBA' and pick_key like '%|gless'").fetchone()
        finally: db.close()
        w, l = x[0] or 0, x[1] or 0
        return ('Real record: Goblin LESS picks won %d of %d since 11/12' % (w, w + l)) if w + l else 'Real record: no graded Goblin LESS picks yet (new 11/12). The numbers above are from past games.'
    try: x = db.execute("select sum(status='win'), sum(status='loss') from picks where league='NBA' and win_prob>=? and win_prob<? and kind=? and first_scored>=? and pick_key not like '%|gless'", (lo, hi, r['kind'], ENGINE_SINCE)).fetchone()
    finally: db.close()
    w, l = x[0] or 0, x[1] or 0
    if w + l: return 'Real record: tier %s %s picks hit %d of %d on past boards' % (r.get('tier'), KIND_FULL.get(r['kind'], r['kind']).split()[-1], w, w + l)
    said, hit = BACKTEST.get(r.get('tier') or 'D', (0, 0))
    return 'Real record: no graded tier %s %s picks yet · backtest: said %d%%, hit %d%%' % (r.get('tier'), KIND_FULL.get(r['kind'], r['kind']).split()[-1], said, hit)
LADDER_KEY = '🪜 Ladder = this player\'s other lines on the same stat, lowest up to the first Demon. P = Apex probability. HP = honest probability: how often past picks at that kind and chance really hit (– = under 20 graded yet). Bold = this pick.'

LADDER_MIN = 20   # graded picks a band needs before its real hit rate shows
_HON = {}
def _band(p): return min(int(p // 10) * 10, 90)
def _honest_from(rows):
    """rows of (kind, side, chance, status) -> {(kind, band of the MORE chance): [hits, graded]}. A LESS pick counts as the MORE side flipped."""
    d = {}
    for kind, side, p, status in rows:
        if p is None or status not in ('win', 'loss'): continue
        more = side != 'LESS'; mp = p if more else 100 - p; hit = (status == 'win') == more
        x = d.setdefault((kind, _band(mp)), [0, 0]); x[0] += hit; x[1] += 1
    return d

# APEX-LESSREPORT-2026-11-12 (owner, "go less report ... needs the ladder as well"): Goblin LESS cards carry the same report as the Best 6 of 6 card:
# a gap line on top of each card, the ladder (numbers shown for the LESS side), and a ranked list at the top of the Best Goblin LESS board. Display only.
def _is_gless(x): return bool(x.get('gless')) or str(x.get('pick_key') or '').endswith('|gless')
def _less_c(r):
    c = r.get('groom'); return c if isinstance(c, dict) and c.get('less') and c.get('book') is not None else None
def _lg(v): return ('%.1f' % v).rstrip('0').rstrip('.')
def less_head(r):
    c = _less_c(r) if _is_gless(r) else None
    if not c: return []
    g = 'Elite' if c['steps'] >= 3 else 'Strong' if c['steps'] >= 2 else 'Solid' if c['steps'] >= 1 - 1e-9 else 'Thin'
    return ['📏 PrizePicks line %s · Sportsbook line %s · Gap +%s above · Gap grade: %s · Apex score on LESS %d' % (_lg(float(r['line'])), _lg(c['book']), _lg(c['room']), g, round(c['was']))]
def less_report(main):
    L = ['📋 **RANKED LIST** (best first)']
    for i, r in enumerate(main, 1):
        c = _less_c(r)
        L.append('%d. (%d) %s %s %s LESS%s' % (i, round(_num(r)), r['player'], _lbl(r), _lg(float(r['line'])), (' · Sportsbook line %s · Gap +%s · Apex score %d' % (_lg(c['book']), _lg(c['room']), round(c['was']))) if c else ''))
    L.append('Gap = the PrizePicks line minus the sportsbook line. For a LESS pick, the higher the line sits above the sportsbooks, the better. Gap grades: Solid (1 step), Strong (2 steps), Elite (3 or more steps). Apex score = Apex\'s own rating of LESS. The number in ( ) = how often LESS picks with that gap and score won, out of 100.')
    L.append('🪜 On a LESS card the ladder numbers are for the LESS side: P = Apex chance the player stays under that line, HP = how often that really happened.')
    return L
def _num(r): return r['win_prob']
def _lbl(r): return stat_name(r)
def ladder_line(r, rows, over_of, honest):
    """🪜 one short line: this player's lines on the same stat and day (MORE), lowest up to the first Demon, each Apex % / real %."""
    try:
        less = _is_gless(r)
        if not rows or (r.get('side') != 'MORE' and not less): return None
        mine = float(r['line']); same = {}
        for x in rows:
            if _is_gless(x) or x.get('promo') or x.get('player') != r.get('player') or x.get('stat') != r.get('stat') or x.get('game_date') != r.get('game_date'): continue
            op = over_of(x)
            if op is None: continue
            try: ln = float(x['line'])
            except (TypeError, ValueError): continue
            if ln not in same or x.get('kind') == 'standard': same[ln] = (x.get('kind'), op)
        demons = [ln for ln, v in same.items() if v[0] == 'demon']
        top = max(min(demons), mine) if demons else max(same)
        steps = [ln for ln in sorted(same) if ln <= top]; steps = steps[-7:] if less else steps[:7]
        if len(steps) < 2: return None
        hon = honest(); out = []
        for ln in steps:
            kind, op = same[ln]; h, n = hon.get((kind, _band(op)), (0, 0)); hp = (100.0 * h / n) if n >= LADDER_MIN else None; icon = {'goblin': '🟢', 'demon': '🔴'}.get(kind, '⚪')
            if less: op = 100 - op; hp = None if hp is None else 100 - hp; icon = '🟢' if ln == mine else icon
            txt = '%s%g P%.0f/HP%s' % (icon, ln, op, ('%.0f' % hp) if hp is not None else '–')
            out.append('**%s**' % txt if ln == mine else txt)
        return ('🪜 LESS side: ' if less else '🪜 ') + ' · '.join(out)
    except Exception: return None

def _bb_over(x):
    if x.get('win_prob') is None or x.get('side') not in ('MORE', 'LESS'): return None
    return x['win_prob'] if x['side'] == 'MORE' else 100 - x['win_prob']
def _bb_honest():
    import time
    if _HON.get('at', 0) > time.time() - 1800: return _HON['d']
    db = T.connect()
    try: rows = db.execute("select kind, side, win_prob, status from picks where league='NBA' and first_scored>=? and status in ('win','loss') and pick_key not like '%|gless'", (ENGINE_SINCE,)).fetchall()
    finally: db.close()
    _HON.update(at=time.time(), d=_honest_from([tuple(x) for x in rows])); return _HON['d']

def pick_card(r, n, tag='', rows=None):
    """One pick in the tennis card style: one fact per line."""
    opp = SB.TEAMS.get(r.get('opponent'), (r.get('opponent') or '?',))[0]; f = r.get('facts') or {}; m = r.get('market')
    L = ['🔸 **#%d · %s** (%s) v %s%s' % (n, r['player'], r.get('team') or '?', opp, tag)]
    L.append('🕐 **Starts %s**' % _ct(r['start'], '%a %-m/%-d, %-I:%M %p CT'))
    if r.get('last_seen') or r.get('seen'): L.append('👀 Seen on PrizePicks %s' % _ct(r.get('last_seen') or r.get('seen'), '%-I:%M %p CT'))
    u = r.get('used') if r.get('used') is not None else (r.get('projected') or 0); own = r.get('projected') or 0
    L.append('📊 %s %s 📈 **%s** · %s · Apex projects **%.1f** (give or take %.1f)%s' % (stat_name(r), r['line'], r['side'], KIND_FULL.get(r['kind'], r['kind']), u, r.get('spread') or 0, (' · stats alone %.1f' % own) if abs(u - own) >= 0.1 else ''))
    L.append('🎯 Win Probability: **%.0f%%** · 🏆 Tier %s · ⚡ Edge Score %s' % (r['win_prob'], r.get('tier') or '-', r.get('edge_score') if r.get('edge_score') is not None else '-'))
    try:   # APEX-HONEST-NBA-2026-11-07
        import nba_honest_live as HN; hl = HN.card_line(r)
        if hl: L.append(hl)
    except Exception: pass
    try:   # APEX-ROOM-2026-11-11
        import room_goblin as RG; _rl = RG.card_line(r)
        if _rl: L.append(_rl)
    except Exception: pass
    if r.get('gless') and not r.get('groom'): L.append('📏 Gap: no sportsbook number for this line yet (NBA sportsbook lines arrive 12:45 PM CT). Not proven, so it waits in BACKUPS. The number above is Apex alone.')   # APEX-GOBLINLESS-NBA-2026-11-12
    if m: L.append('📗 Books: %g at %d book%s (over %.0f%%) · PrizePicks %g · Room Edge %d' % (m['line'], m['n'], 's' if m['n'] != 1 else '', 100 * m['p'], r['line'], r.get('room') or 0))
    else: L.append('📗 Books: no book line on this stat yet')
    if f: L.append('📈 Form: last 5 %.1f · last 10 %.1f · season %.1f · %.0f min lately (%.0f usual)' % (f['l5'], f['l10'], f['base'], f['mins'], f['mins_usual']))
    if f.get('matchup'): L.append('🆚 Matchup: %s' % f['matchup'])
    if f.get('rest') is not None:
        where = ' · home' if r.get('home') == 1 else (' · away' if r.get('home') == 0 else '')
        L.append(('📅 Back-to-back: played yesterday ⚠️' if f['rest'] == 1 else '📅 Rest: %d days' % f['rest']) + where)
    if r.get('own_inj'): L.append('⚠️ **INJURY REPORT: %s is listed %s.** Held out of numbered spots until he is cleared. PrizePicks may pull his lines.' % (r['player'], 'Questionable (day-to-day)' if r['own_inj'] == 'Day-To-Day' else r['own_inj']))   # APEX-INJURYHOLD-2026-11-11
    if f.get('outs'): L.append('🏥 Teammates out: ' + ', '.join(f['outs'][:4]))
    if f.get('quest'): L.append('⚠️ Questionable teammates: ' + ', '.join(f['quest'][:3]))
    sig = r.get('signals') or []
    if sig: L.append('🧮 Signals: ' + ' · '.join('%s %+.0f' % (nm, d) for nm, d in sig) + ' → %.0f%%' % r['win_prob'])
    lad = ladder_line(r, rows, _bb_over, _bb_honest)
    if lad: L.append(lad)
    L.append('🧾 ' + real_record(r))
    return '\n'.join(L)
def board_text(name, cur=None):
    cur = cur or P.current()
    if not cur: return _no_data()
    c = P.BOARDS[name]; b = cur['boards'][name]; day = dt.datetime.now(SB.CT).strftime('%a %-m/%-d')
    L = ['🏀 **%s** %s · %s' % (c['title'], ('(%s)' % c['note']) if c['note'] else '', day), saved_line(cur), RULE]
    fl = c.get('floor', P.FLOOR)
    if not b['main']: L.append('Nothing reached Win Prob %d on this board. No picks, and none made up.' % fl)
    if name == 'bestless' and b['main']: L += less_report(b['main']) + [RULE]   # APEX-LESSREPORT-2026-11-12
    for i, r in enumerate(b['main'], 1): L += less_head(r) + [pick_card(r, i, rows=cur.get('rows')), RULE]
    if b['main'] and len(b['main']) < c['size']: L.append('Only %d of %d spots filled at %d+ (one per game), so no full slip.' % (len(b['main']), c['size'], fl))
    if b['backups']: L.append('BACKUPS: %d, see /bball-%sbackups' % (len(b['backups']), name.replace('best', '')))
    return '\n'.join(L + _kind_warn(b['main']) + ([LADDER_KEY] if any('🪜' in x for x in L) else []) + [HONEST, FOOT])
def backups_text(name, cur=None):
    cur = cur or P.current()
    if not cur: return _no_data()
    c = P.BOARDS[name]; b = cur['boards'][name]; games = {r['game_key'] for r in b['main']}; L = ['🏀 **%s BACKUPS**' % c['title'], saved_line(cur), RULE]
    if not b['backups']: L.append('No backups: nothing else reached Win Prob %d.' % c.get('floor', P.FLOOR))
    for i, r in enumerate(b['backups'], 1): L += [pick_card(r, i, ' · same game as a board pick' if r['game_key'] in games else '', rows=cur.get('rows')), RULE]
    return '\n'.join(L + [FOOT])
def allprops_text(cur=None):
    """Every line not yet started. floor first, then the rest with numbers, then lines with no number and why."""
    cur = cur or P.current()
    if not cur: return _no_data()
    rows = cur['rows']; bans = cur['bans']; sc = sorted([r for r in rows if r['win_prob'] is not None], key=P.rank_key); no = [r for r in rows if r['win_prob'] is None]
    L = ['🏀 **ALL PROPS**: %d lines, %d with a number, %d at %d+' % (len(rows), len(sc), sum(r['win_prob'] >= P.FLOOR for r in sc), P.FLOOR), saved_line(cur)]
    tag = lambda r: (' · 🏷️ promo, off boards' if r.get('promo') else '') + (' · banned' if SB.norm(r['player']) in bans else '')
    hi = [r for r in sc if r['win_prob'] >= P.FLOOR]; lo = [r for r in sc if r['win_prob'] < P.FLOOR]
    L += ['**At %d+**' % P.FLOOR] + ([pick_line(r, i, tag(r)) for i, r in enumerate(hi, 1)] or ['None.'])
    if lo: L += ['**Under %d: not on any board**' % P.FLOOR] + [pick_line(r, None, tag(r)) for r in lo]
    if no:
        L.append('**No number**')
        for why in sorted({r['reason'] or '?' for r in no}):
            g = [r for r in no if r['reason'] == why]; L.append('%s: %d lines' % (why, len(g)))
            L += ['• [%s] %s %s %s' % (r['league'], r['player'], r['line'], stat_name(r)) for r in g[:400]]
    return '\n'.join(L + [HONEST, FOOT])
def board_diag_text(cur=None):
    """/bball-board: what is saved, nothing more."""
    lines, saved, bad = SB.load_saved_lines(); cur = cur or P.current(); pull = P.last_collector_pull()
    L = ['🏀 **SAVED LINES**', 'Collector last finished a pull: %s' % (_ct(pull.isoformat(), '%-m/%-d %-I:%M %p CT') if pull else 'never'), 'Newest saved line: %s. Saved lines in all: %d.' % (_ct(saved, '%-m/%-d %-I:%M %p CT'), len(lines))]
    if bad: L.append('⚠️ %d saved rows could not be read.' % bad)
    if cur:
        rows = cur['rows']; L.append('Not started yet: %d. With a number: %d. At %d+: %d.' % (len(rows), sum(r['win_prob'] is not None for r in rows), P.FLOOR, sum((r['win_prob'] or 0) >= P.FLOOR for r in rows)))
        for lab, key in (('League', 'league'), ('Type', 'kind')):
            cnt = {}
            for r in rows: cnt[r[key]] = cnt.get(r[key], 0) + 1
            L.append('%s: %s' % (lab, ', '.join('%s %d' % x for x in sorted(cnt.items())) or 'none'))
    else: L.append('Nothing scored yet.')
    return '\n'.join(L + [FOOT])
def fetch_report(s, trigger, t0=None):
    """APEX-FETCHDETAIL-2026-11-13 (owner 11/13, "Go fetch detail"): the tennis-style NEW PROPS SCORED message from ~/ApexSports/_shared/fetch_report.py
    for /bball-fetch AND every automatic re-score. Display only. None on any error (the caller keeps its old line)."""
    try:
        import os as _os, sys as _sys
        _p = _os.path.expanduser('~/ApexSports/_shared')
        if _p not in _sys.path: _sys.path.append(_p)
        import fetch_report as FR
        return FR.report_nba(s, trigger, P, T, SB, t0=t0) if FR.ON else None
    except Exception as e:
        print('[cards] fetch report failed: %s: %s' % (type(e).__name__, e)); return None
def fetch_result_text(s):
    if s.get('cancelled'): return '🛑 Stopped. Nothing was saved from this run.\n' + FOOT
    if s['no_lines']: return '🧪 No saved lines yet, so nothing to score. No call was made to PrizePicks; the collector saves lines on its own.\n' + FOOT
    return ((s['report'] + '\n\n') if s.get('report') else '') + '\n'.join(['🏀 **Re-scored from saved lines.** No call was made to PrizePicks.', 'Lines last saved %s.' % _ct(s['lines_saved_at'], '%-m/%-d %-I:%M %p CT'),
                      'Not started yet: %d. With a number: %d. At %d+: %d.' % (s['n_lines'], s['n_scored'], P.FLOOR, s['n_70']), 'Player results through %s.' % s['last_game'], FOOT])
def _leg_text(db, keys):
    L = []
    for i, k in enumerate(keys, 1):
        p = db.execute('select * from picks where pick_key=?', (k,)).fetchone()
        if not p: continue
        mark = {'win': '✅', 'loss': '❌', 'void': '⚪ void', 'push': '⚪ push', 'open': '⏳'}.get(p['status'], '')
        L.append(pick_line(dict(p, start=p['start_utc']), i, ' %s%s' % (mark, '' if p['result'] is None else ' (%g)' % p['result'])))
    return L
def slip_card(db, s):
    st = {'pending': '⏳ pending', 'won': '✅ won', 'lost': '❌ lost', 'all_hit': '✅ all legs hit', 'partial': '🟡 %s of %s legs' % (s['legs_won'], len(json.loads(s['legs_json']))), 'check_app': '⚪ a leg voided or pushed: pay depends on the app'}[s['status']]
    L = ['🧪 **%s** · %s · %s' % (SLIP_NAME[s['board']], s['day'], st)] + _leg_text(db, json.loads(s['legs_json']))
    if s['pnl'] is not None: L.append('Paper: $%.0f at %.2fx = %s$%.2f' % (s['stake'], s['payout_mult'] or 0, '+' if s['pnl'] >= 0 else '-', abs(s['pnl'])))
    return '\n'.join(L + [FOOT])
def slips_text():
    db = T.connect()
    try:
        rows = db.execute('select * from slips order by day desc, id desc limit 12').fetchall()
        if not rows: return '🧪 No slips yet. A slip needs a full board above the floor, one pick per game. With Step 3 that will be rare.\n' + FOOT
        return '\n\n'.join(slip_card(db, s) for s in rows)
    finally: db.close()
def pnl_text(view='daily', now=None):
    today = (now or dt.datetime.now(dt.timezone.utc)).astimezone(SB.CT).date(); since = {'daily': today, 'week': today - dt.timedelta(days=today.weekday()), 'month': today.replace(day=1)}[view]
    db = T.connect()
    try: a, b = T.pnl(db, since.isoformat(), today.isoformat()), T.pnl(db)
    finally: db.close()
    f = lambda x: '%s$%.2f' % ('+' if x >= 0 else '-', abs(x))
    return '\n'.join(['💰 **BBALL P&L**, %s (paper $20 Top 3 Power only)' % view, '%s: %s, %d won, %d lost' % (view.capitalize(), f(a['net']), a['won'], a['lost']), 'All time: %s, %d won, %d lost' % (f(b['net']), b['won'], b['lost']),
                      'Elite 5 and Elite 6 have no dollars: no Flex pay table is loaded here. See /bball-counters.', 'Paper only. Not in the tennis ledger or tennis #pnl.' if a or b else '', FOOT])
def counters_text():
    db = T.connect()
    try: c = T.counters(db)
    finally: db.close()
    L = ['🏀 **COUNTERS**: whole slip record']
    for b, x in c.items(): L.append('%s: %d won, %d lost, %d void or push, %d pending. Legs %d won, %d lost.' % (SLIP_NAME[b], x['won'], x['lost'], x['check'], x['pending'], x['legs_won'], x['legs_lost']))
    if not any(x['won'] + x['lost'] + x['check'] + x['pending'] for x in c.values()): L.append('No slips yet.')
    return '\n'.join(L + [FOOT])
def besttime_text():
    db = T.connect()
    try: bt = T.besttime(db)
    finally: db.close()
    L = ['🏀 **BEST TIME**: boards by the hour lines were saved']
    if not bt: return '\n'.join(L + ['No answer yet: no full board has every leg graded. No replay exists for basketball.', FOOT])
    for (b, h), (w, l) in sorted(bt.items()): L.append('%s at %s: %d of %d full boards hit' % (SLIP_NAME[b], h, w, w + l))
    return '\n'.join(L + ['Small samples: read these as counts, not a rule.', FOOT])
def soon_text(cur=None, now=None):
    cur = cur or P.current()
    if not cur: return _no_data()
    seen, rows = set(), []
    for b in cur['boards'].values():
        for r in b['main'] + b['backups'][:1]:
            k = T.pick_key(r)
            if k not in seen: seen.add(k); rows.append(r)
    rows.sort(key=lambda r: r['start']); L = ['🏀 **SOON**: board picks, soonest first', saved_line(cur)]
    return '\n'.join(L + ([pick_line(r, i) for i, r in enumerate(rows, 1)] or ['Nothing on the boards.']) + [FOOT])
def soon_card(name, cur=None, now=None, hours=6):
    """Next 6 hours only. Same floor and one per game as the boards."""
    cur = cur or P.current()
    if not cur: return _no_data()
    now = now or dt.datetime.now(dt.timezone.utc); cut = (now + dt.timedelta(hours=hours)).isoformat(timespec='seconds'); size = {'top3': 3, 'elite6': 6}[name]
    near = [r for r in cur['rows'] if r['start'] <= cut]; main = P.build_boards(near, cur['bans'])[name]['main']; L = ['🏀 **%s SOON**: starting in the next %d hours' % (P.BOARDS[name]['title'], hours), saved_line(cur)]
    L += [pick_line(r, i) for i, r in enumerate(main, 1)] or ['Nothing above the floor starts in the next %d hours.' % hours]
    if main and len(main) < size: L.append('Only %d of %d: not a full slip.' % (len(main), size))
    return '\n'.join(L + [FOOT])
def _games_line(h, stat=None):
    return '%s v %s: %g pts, %g reb, %g ast in %.0f min' % (h['game_date'], h['opponent'], h['points'] or 0, h['rebounds'] or 0, h['assists'] or 0, h['minutes'] or 0)
def h2h_text(q, hist=None, cur=None):
    """One player: last games against today's opponent. 'A vs B': games when the two players were on opposite teams."""
    hist = hist or P.history(); parts = re.split(r'\s+(?:vs\.?|v\.?)\s+', q.strip(), flags=re.I)
    if len(parts) == 2:
        a, why = hist.resolve(parts[0], None); b, why2 = hist.resolve(parts[1], None)
        if not a or not b: return '🧪 %s: %s\n%s' % (parts[0] if not a else parts[1], why or why2, FOOT)
        them = {h['event_id']: h for h in hist.H[b]}; rows = [(h, them[h['event_id']]) for h in hist.H[a] if h['event_id'] in them and them[h['event_id']]['team'] != h['team']][-10:]
        L = ['🤝 **%s vs %s**: %d recent games against each other' % (parts[0], parts[1], len(rows))]
        L += ['%s: %s %g pts %g reb %g ast | %s %g pts %g reb %g ast' % (x['game_date'], parts[0], x['points'] or 0, x['rebounds'] or 0, x['assists'] or 0, parts[1], y['points'] or 0, y['rebounds'] or 0, y['assists'] or 0) for x, y in rows[::-1]] or ['They have no game against each other in the history.']
        return '\n'.join(L + [FOOT])
    cur = cur or P.current(); row = next((r for r in (cur or {}).get('rows', []) if SB.norm(r['player']) == SB.norm(q) and r['opponent'] in SB.TEAMS), None)
    if not row: return '🧪 %s has no saved line today, so no opponent to compare. Try "Player A vs Player B".\n%s' % (q, FOOT)
    pid, why = hist.resolve(row['player'], row['team'])
    if not pid: return '🧪 %s: %s\n%s' % (q, why, FOOT)
    opp = SB.TEAMS[row['opponent']][0]; g = [h for h in hist.H[pid] if h['opponent'] == opp][-10:]
    return '\n'.join(['🤝 **%s v %s**: last %d meetings' % (row['player'], opp, len(g))] + ([_games_line(h) for h in g[::-1]] or ['No earlier game against them in the history.']) + [FOOT])
def banned_text():
    db = T.connect()
    try: b = T.banned(db)
    finally: db.close()
    return '\n'.join(['🚫 **BANNED**'] + (['• %s%s' % (x['player'], ' (%s)' % x['why'] if x['why'] else '') for x in b.values()] or ['Nobody.']) + [FOOT])
def ban_text(player, why=''):
    db = T.connect()
    try: T.ban(db, player, why)
    finally: db.close()
    return '🚫 %s is off every basketball board and slip not yet started. Only this player, not the whole game.\n%s' % (player, banned_text())
def unban_text(player):
    db = T.connect()
    try: n = T.unban(db, player)
    finally: db.close()
    return ('✅ %s is off the banned list.\n' % player if n else '🧪 %s was not on the list.\n' % player) + banned_text()
def status_line(now=None):
    """9 AM line. Says what is wrong rather than staying quiet."""
    now = now or dt.datetime.now(dt.timezone.utc); pull = P.last_collector_pull(); cur = P.current(now); db = T.connect()
    try:
        o = db.execute("select count(*) from picks where status='open'").fetchone()[0]; g = db.execute("select count(*) from picks where status in ('win','loss')").fetchone()[0]
    finally: db.close()
    hrs = None if not pull else (now - pull).total_seconds() / 3600; warn = '' if hrs is not None and hrs <= 26 else ' ⚠️ collector silent'
    n70 = sum((r['win_prob'] or 0) >= P.FLOOR for r in cur['rows']) if cur else 0; nl = len(cur['rows']) if cur else 0
    return '🧪 BBALL 9 AM%s: last pull %s. %d lines not started, %d at %d+. Picks %d open, %d graded. %s' % (warn, 'never' if pull is None else '%.0f hours ago' % hrs, nl, n70, P.FLOOR, o, g, FOOT)
def learning_text():
    db = T.connect()
    try: c = T.calibration(db)
    finally: db.close()
    L = ['📚 **BBALL LEARNING**: do picks hit what the number says?']
    for a, b, w, l in c:
        if w + l: L.append('%d to %d: %d won, %d lost, %d out of 10' % (a, min(b - 1, 100), w, l, round(10 * w / (w + l))))
    if len(L) == 1: L.append('Nothing graded yet.')
    return '\n'.join(L + ['No rule changes from this card. Changes need his go.', FOOT])
def chunks(text, size=1900):
    out, cur = [], ''
    for l in text.split('\n'):
        while len(l) > size: out.append(l[:size]); l = l[size:]
        if len(cur) + len(l) + 1 > size: out.append(cur); cur = ''
        cur += l + '\n'
    if cur.strip(): out.append(cur)
    return out
