#!/usr/bin/env python3
import re
"""Discord text for this sport: pick cards (one fact per line), boards (Top 3 / Elite 5 / Elite 6 / Best lines) and the tier report
(Tier A / B / C sections) in the format owner asked for: player, prop, line, projection, over %, under %, confidence, edge score, reasons, tier."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as CM

RULE = '━━━━━━━━━━━━━━━━━━━━━━━━'
KIND = {'standard': '⚪ Standard', 'goblin': '🟢 Goblin', 'demon': '🔴 Demon'}
def foot(): return '🧪 TEST · %s · Win Prob = the engine\'s own chance the side hits (history, form, matchup, home/away, rest%s). Check the app before playing.' % (CM.cfg()['name'], ', books' if CM.cfg().get('odds_api', {}).get('sport_keys') else '')

LADDER_KEY = '🪜 Ladder = this player\'s other lines on the same stat, lowest up to the first Demon. P = Apex probability. HP = honest probability: how often picks at that kind and chance really hit (live graded picks, past seasons until 20 are graded; – = not enough yet). Bold = this pick.'

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
    c = r.get('room'); return c if isinstance(c, dict) and c.get('less') and c.get('book') is not None else None
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
def _num(r): return r['confidence']
def _lbl(r): return r.get('label') or r.get('stat')
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

def _sp_over(x):
    if x.get('over_p') is None or x.get('no_play'): return None
    return x['over_p']
def _sp_honest():
    import time
    if _HON.get('at', 0) > time.time() - 1800: return _HON['d']
    try:
        from database import db as DBM
        db = DBM.connect(); rows = db.execute("select kind, side, confidence, status from picks where status in ('win','loss')").fetchall(); db.close()
        d = _honest_from([tuple(x) for x in rows])
        try:   # past seasons fill in until 20 live picks are graded (his 11/6 go)
            hist = CM.read_json(os.path.join(CM.CACHE, 'history_hp.json'), {}).get('rates', {})
            for k, v in hist.items():
                kind, b = k.split('|'); key = (kind, int(b))
                if d.get(key, (0, 0))[1] < LADDER_MIN and v[1] >= LADDER_MIN: d[key] = list(v)
        except Exception: pass
        _HON.update(at=time.time(), d=d)
    except Exception: _HON.update(at=time.time(), d={})
    return _HON['d']

def pick_card(r, n=None, tag='', rows=None):
    c = CM.cfg(); L = []
    L.append('🔸 **%s%s** (%s) v %s%s' % ('#%d · ' % n if n else '', r['player'], r['team'] or '?', r['opponent'] or '?', ' ' + tag if tag else ''))
    L.append('🕐 **Starts %s**' % CM.fmt_ct(r['start'], '%a %-m/%-d, %-I:%M %p CT'))
    if r.get('last_seen'): L.append('👀 Seen on PrizePicks %s' % CM.fmt_ct(r['last_seen'], '%-I:%M %p CT'))
    u = r.get('used') if r.get('used') is not None else r['projection']
    L.append('📊 %s %g %s **%s** · %s · Apex projects **%.1f** (give or take %.1f)%s' % (r['label'], r['line'], '📈' if r['side'] == 'MORE' else '📉', r['side'], KIND.get(r['kind'], r['kind']), u, r['sd'], (' · stats alone %.1f' % r['projection']) if abs(u - r['projection']) >= 0.1 else ''))
    L.append('🎯 Over **%.0f%%** · Under **%.0f%%** · Confidence **%.0f%%** · 🏆 Tier %s · ⚡ Edge Score %+d' % (r['over_p'], r['under_p'], r['confidence'], r['tier'], r['edge_score']))
    try:   # APEX-HONEST-2026-11-07
        from tracking import honest as HN
        hl = HN.card_line(r)
        if hl: L.append(hl)
    except Exception: pass
    try:   # APEX-ROOM-2026-11-11
        from models import room as RM
        _rl = RM.card_line(r)
        if _rl: L.append(_rl)
    except Exception: pass
    if r.get('market'): L.append('📗 Books: %g at %d book%s (over %.0f%%)' % (r['market']['line'], r['market']['n'], '' if r['market']['n'] == 1 else 's', 100 * r['market']['p']))
    L.append('📈 Form: last 5 %.1f · last 10 %.1f · season %.1f · %d games' % (r['l5'], r['l10'], r['base'], r['games']))
    try:   # APEX-MATCHUPLINE-2026-11-08 (owner "Go matchup line"): display only, says what the Matchup step did
        _m = [x for x in (r.get('reasons') or []) if x[0] == 'Matchup']
        if _m:
            _d, _note = _m[0][1], _m[0][2]
            _g = re.match(r'^(.+?) allows ([+-]?\d+)% (.+?) vs league \(last (\d+)\)', _note or '')
            if _g:
                _pct = int(_g.group(2))
                _txt = '%s allows %d%% %s %s than average (last %s games)' % (_g.group(1), abs(_pct), 'more' if _pct >= 0 else 'fewer', _g.group(3), _g.group(4)) if _pct else '%s allows an average amount of %s (last %s games)' % (_g.group(1), _g.group(3), _g.group(4))
            else:
                _txt = _note
            L.append('🆚 Matchup: %s → %s this %s (%+d)' % (_txt, 'helps' if _d > 0 else 'hurts' if _d < 0 else 'no effect on', r['side'], _d))
        else:
            L.append('🆚 Matchup: no real effect on this pick (under 1 point, or %s not in our history yet)' % (r.get('opponent') or 'opponent'))
    except Exception: pass
    if r.get('rest') is not None: L.append('📅 Rest: %d day%s · %s' % (r['rest'], '' if r['rest'] == 1 else 's', 'home' if r.get('home') else 'away' if r.get('home') == 0 else 'home/away unknown'))
    if r.get('injury') and r['injury'].get('status') in ('Out', 'Doubtful', 'Questionable', 'Day-To-Day', 'Game Time Decision', 'Injured Reserve', 'IR', 'Suspended'): L.append('🏥 Listed %s (impact %d of 100, updated %s)' % (r['injury']['status'], injury_impact(r['injury']['status']), CM.fmt_ct(r['injury'].get('at')) if r['injury'].get('at') else '?'))
    if r.get('reasons'): L.append('🧮 Reasons: ' + ' · '.join('%s %+d' % (nm, d) for nm, d, note in r['reasons']) + ' → %.0f%%' % r['confidence'])
    try:
        from tracking import boards as TB; rr = TB.real_record_line(r)
        if rr: L.append(rr)
    except Exception: pass
    lad = ladder_line(r, rows, _sp_over, _sp_honest)
    if lad: L.append(lad)
    if r.get('avail_hold'): L.append('⚠️ ' + r['avail_hold'])   # APEX-COLLEGEHOLD-2026-11-13
    if r.get('unproven'): L.append('⚠️⚠️ Not proven yet: Apex has no graded picks of this kind, so it stays in BACKUPS until real results prove it.')   # APEX-HONESTBOARDS
    if r.get('no_play'): L.append('⚠️ No play: %s' % r['no_play'])
    return '\n'.join(L)

IMPACT = {'out': 100, 'injured reserve': 100, 'ir': 100, 'suspended': 100, 'doubtful': 75, 'questionable': 50, 'game time decision': 50, 'day-to-day': 25, 'probable': 10}
def injury_impact(status): return IMPACT.get(str(status or '').strip().lower(), 0)
def injury_feed_line():
    """One line for every board: no feed for this league, or how fresh the feed is. Never silent."""
    c = CM.cfg()
    if not c.get('espn', {}).get('injuries', True): return '🏥 No injury feed for this league. Check each player is playing before you bet.'
    try:
        from database import db as DBM
        db = DBM.connect(); t = DBM.kv_get(db, 'espn_last_pull')
        if not t: return '🏥 Injury feed has not run yet. Check each player is playing before you bet.'
        age = (CM.now_utc() - CM.parse_iso(t)).total_seconds() / 3600
        return '🏥 Injuries checked %s.' % CM.fmt_ct(t) if age < 3 else '⚠️ Injury feed is %d hours old. Check each player is playing before you bet.' % age
    except Exception: return '🏥 Injury feed could not be read. Check each player is playing before you bet.'

def board_text(name, d, s):
    c = CM.cfg(); day = CM.now_ct().strftime('%a %-m/%-d'); L = ['%s **%s** %s · %s' % (c['emoji'], d['title'], d['note'], day)]
    L.append('📥 Lines last saved %s.' % CM.fmt_ct(s.get('lines_saved_at')) if s.get('lines_saved_at') else '📥 No PrizePicks lines saved yet.')
    if name == 'bestless' and d['main']: L += less_report(d['main'])   # APEX-LESSREPORT-2026-11-12
    if len(d['main']) >= d['size']: L.append(injury_feed_line())
    if len(d['main']) < d['size']:                      # never show an undersized board under a full board's name
        L.append('🚫 Not enough qualified picks today. (%d of the %d picks this board needs reached %d+, one per game.)' % (len(d['main']), d['size'], d['floor']))
        if d['main']:   # APEX-SHOWQUALIFIED-2026-11-09 (owner, "go show qualified"): still show the picks that did fight their way to the floor, clearly marked as not a full slip
            L.append('👀 **Qualified so far — not a full slip, %d of %d.** Same rules as a full board, ranked best first.' % (len(d['main']), d['size']))
            for i, r in enumerate(d['main'], 1): L += [RULE] + less_head(r) + [pick_card(r, i, rows=s.get('rows'))]
            if any('🪜' in x for x in L): L.append(LADDER_KEY)
        L.append(foot()); return '\n'.join(L)
    for i, r in enumerate(d['main'], 1): L += [RULE] + less_head(r) + [pick_card(r, i, rows=s.get('rows'))]
    if any('🪜' in x for x in L): L.append(LADDER_KEY)
    if d['backups']: L.append('BACKUPS: %d more at %d+ (/%s-backups)' % (len(d['backups']), d['floor'], c['prefix']))
    L.append(foot()); return '\n'.join(L)

def tier_report(s, top=12):
    c = CM.cfg(); rows = [r for r in s['rows'] if not r.get('no_play')]; rows.sort(key=lambda r: (-r['confidence'], -r['edge_score']))
    L = ['%s **%s PICKS** · %s · %d lines scored, %d at %d+' % (c['emoji'], c['name'].upper(), CM.now_ct().strftime('%a %-m/%-d'), s['n_scored'], s['n_floor'], c['rules']['floor'])]
    for t, lab in (('A', 'TIER A (70%+)'), ('B', 'TIER B (65-69%)'), ('C', 'TIER C (60-64%)')):
        R = [r for r in rows if r['tier'] == t][:top]
        if not R: continue
        L += [RULE, '🏆 **%s** · %d pick%s' % (lab, len(R), '' if len(R) == 1 else 's')]
        for r in R: L += ['', pick_card(r, rows=s.get('rows'))]   # APEX-LADDERALL-2026-11-12: ladder on these cards too
    if len(L) == 1: L.append('No pick reached tier C today.')
    L.append(foot()); return '\n'.join(L)

def fetch_summary(s, trigger='fetch'):
    """APEX-FETCHSUMMARY-2026-11-09 (owner, "go fetch summary"): the whole fetch in plain counts, like the tennis /fetch report. Never raises."""
    try:
        c = CM.cfg(); f = s.get('funnel') or {}; floor = c['rules']['floor']; boards = s.get('boards') or {}
        L = ['%s **FETCH COMPLETE** · %s · %s' % (c['emoji'], c['name'], CM.now_ct().strftime('%a %-m/%-d %-I:%M %p CT'))]
        if not f:
            L.append('📥 %d lines not started, %d scored, %d at %d+.' % (s.get('n_lines', 0), s.get('n_scored', 0), s.get('n_floor', 0), floor)); return '\n'.join(L)
        L.append('')
        L.append('📋 **ON PRIZEPICKS**')
        L.append('Lines on the board: %d (pulled %s)' % (f.get('on_board', 0), CM.fmt_ct(f['pull_at']) if f.get('pull_at') else 'never'))
        L.append('Already started: %d' % f.get('started', 0))
        if f.get('gone'): L.append('Taken down since the last pull: %d' % f['gone'])
        L.append('Not started, sent to the engine: %d' % f.get('not_started', 0))
        L.append('')
        L.append('🧠 **ENGINE**')
        dropped = f.get('dropped') or []
        L.append('Dropped before scoring: %d' % sum(n for _, n in dropped))
        for why, n in dropped: L.append(' · %s: %d' % (why, n))
        L.append('Scored: %d' % f.get('scored', 0))
        k = f.get('kinds') or {}
        if k: L.append(' · ' + ' · '.join('%s %d' % (KIND.get(x, x), n) for x, n in sorted(k.items(), key=lambda kv: -kv[1])))
        np = f.get('no_play') or []
        L.append('No play, kept off boards: %d' % sum(n for _, n in np))
        for why, n in np[:8]: L.append(' · %s: %d' % (why, n))
        L.append('Reached %d+: %d' % (floor, f.get('at_floor', 0)))
        per = f.get('per_board') or {}
        L.append('On a board: %d' % f.get('on_boards', 0) + (' (' + ' · '.join('%s %d of %d' % (boards[b]['title'] if b in boards else b, n, boards[b]['size'] if b in boards else 0) for b, n in per.items() if n) + ')' if any(per.values()) else ''))
        L.append('')
        L.append('Changed boards post to #%s-picks. (%s)' % (c['prefix'], trigger))
        return '\n'.join(L)
    except Exception as e:
        return '📥 Fetched. %d lines not started, %d scored, %d at %d+. (summary failed: %s)' % (s.get('n_lines', 0), s.get('n_scored', 0), s.get('n_floor', 0), CM.cfg()['rules']['floor'], e)


def system_line(s, trigger):
    c = CM.cfg(); return '🧪 %s scored %d lines not started: %d with a number, %d at %d+. Lines saved %s. (%s)' % (c['name'], s['n_lines'], s['n_scored'], s['n_floor'], c['rules']['floor'], CM.fmt_ct(s.get('lines_saved_at')) if s.get('lines_saved_at') else 'never', trigger)


def fetch_report(s, trigger, t0=None):
    """APEX-FETCHDETAIL-2026-11-13 (owner 11/13, "Go fetch detail"): the tennis-style NEW PROPS SCORED message (new props since the last run, best new
    pick, new props per game, every board's changes, Top 3 now, lines saved, next pull) from ~/ApexSports/_shared/fetch_report.py,
    for the typed fetch AND every automatic pull. Display only. Falls back to the old one line on any error, or when fetch_report.ON is False."""
    try:
        p = os.path.expanduser('~/ApexSports/_shared')
        if p not in sys.path: sys.path.append(p)
        import fetch_report as FR
        if FR.ON: return FR.report_9(s, trigger, CM, t0=t0)
    except Exception as e:
        CM.log('cards', 'fetch report failed, old line used: %s: %s' % (type(e).__name__, e))
    return system_line(s, trigger)


def quiet_report(trigger, added, state=None):
    """APEX-FETCHDETAIL-2026-11-13: one line when an automatic PrizePicks read gave scoring nothing to do, so a pull is never silent. None = already said today (off season)."""
    try:
        p = os.path.expanduser('~/ApexSports/_shared')
        if p not in sys.path: sys.path.append(p)
        import fetch_report as FR
        if FR.ON: return FR.quiet_9(CM, trigger, added, state)
    except Exception as e:
        CM.log('cards', 'quiet line failed: %s: %s' % (type(e).__name__, e))
    return '🔁 %s PrizePicks read (%s): nothing new to score, boards unchanged.' % (CM.cfg()['name'], trigger)
