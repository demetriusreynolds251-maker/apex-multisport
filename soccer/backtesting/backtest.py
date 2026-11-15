#!/usr/bin/env python3
"""Backtest for this sport on its own history (prop_lines + player_games). Fits the spread scale and the PrizePicks-line anchor per stat on the
FIRST HALF of the dates only, then checks the second half: calibration (stated % vs hit %), by tier, by stat, ladder lines (Goblin / Demon style,
line moved -3..+3 steps), and a Top 3 board test. Writes reports/<date>_backtest.md and database.fits.
  python3 backtesting/backtest.py [--pre-only]   (default: PrizePicks lines saved before the start only, no history book lines; --all-lines and --books widen it, both leak)"""
import collections as C, datetime as dt, json, math, os, statistics as ST, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as CM
from database import db as DBM
from models import projection as PJ, probability as PB

def run(pre_only=True, out_md=None, use_books=False):
    """use_books=False: history book lines are each book's LATEST number (often after the game), so they leak the result; they are ignored in the fit and the check."""
    c = CM.cfg(); db = DBM.connect(); E = PJ.Engine(db); E.fits = {}; t0 = dt.datetime.now()
    rows = [dict(r) for r in db.execute('select * from prop_lines where pp_line is not null and result is not null' + (' and pp_before_start=1' if pre_only else '') + ' order by game_date')]
    P = []; skipped = C.Counter()
    for r in rows:
        if r['stat'] not in c['stats']: skipped['stat not configured'] += 1; continue
        pr = E.project(r['player_norm'], r['stat'], r['game_date'], r['opponent'], r['home'], dict(team=r['team'], team_code=r['team'], game_date=r['game_date'], event_id=r['event_id']))
        if not pr: skipped['under %d games' % c.get('min_games', 6)] += 1; continue
        books = [(v[0], v[1], None) for v in json.loads(r['book_lines_json'] or '{}').values() if v and v[0] is not None] if use_books else []
        P.append(dict(stat=r['stat'], date=r['game_date'], line=r['pp_line'], res=r['result'], m=pr['mean'], sd_raw=pr['sd_raw'], dist=pr['dist'], books=books, pid=r['player_norm'], ev=r['event_id'], board=c['stats'][r['stat']].get('board', True)))
    if len(P) < 50:
        txt = '# %s backtest - %s\n\nOnly %d graded PrizePicks lines with enough player history (%s). Not enough to fit or judge anything yet. The collectors are saving lines and results now; this report fills in as they grade.' % (c['name'], CM.now_ct().strftime('%Y-%m-%d %-I:%M %p CT'), len(P), ', '.join('%s %d' % kv for kv in skipped.most_common()))
        return _write(txt, out_md)
    mid = P[len(P) // 2]['date']; first = [x for x in P if x['date'] < mid]; second = [x for x in P if x['date'] >= mid]
    def pov(x, k, a, w, ln=None):
        ln = x['line'] if ln is None else ln; sd = x['sd_raw'] * k; m = x['m'] + a * (x['line'] - x['m']); p = PB.p_over(m, sd, ln, x['dist'])
        if w and x['books']:
            mk = PB.market_mean(x['books'], sd, x['dist'])
            if mk: ww = w * min(1.0, mk[2] / 3.0); p = (1 - ww) * p + ww * PB.p_over(mk[0], sd, ln, x['dist'])
        return min(max(p, .02), .98)
    def ll(S, k, a, w):
        tot = 0.0
        for x in S:
            for off in (0, -1, 1):
                ln = x['line'] + off
                if ln < 0.5: continue
                p = pov(x, k, a, w, ln); tot -= math.log(p if x['res'] > ln else 1 - p) if x['res'] != ln else 0
        return tot / max(1, len(S))
    fits = {}
    for s in c['stats']:
        S = [x for x in first if x['stat'] == s]
        if len(S) < 150: fits[s] = dict(sd_k=1.0, anchor=0.5 if len(S) < 40 else 0.0, props=len(S)); 
        if len(S) < 150: continue
        best = min(((k / 10.0, a / 10.0) for k in range(5, 26) for a in range(0, 10)), key=lambda ka: ll(S, ka[0], ka[1], 0)); fits[s] = dict(sd_k=best[0], anchor=best[1], props=len(S))
    for x in P: x['k'] = fits[x['stat']]['sd_k']; x['a'] = fits[x['stat']]['anchor']
    withb = [x for x in first if x['books']]
    wbest = min((w / 10.0 for w in range(0, 11)), key=lambda w: sum(-math.log(pov(x, x['k'], x['a'], w) if x['res'] > x['line'] else 1 - pov(x, x['k'], x['a'], w)) for x in withb if x['res'] != x['line'])) if len(withb) >= 100 else c.get('market_weight', 0.5)
    for x in P:
        p = pov(x, x['k'], x['a'], wbest); x['p'] = p; x['side'] = 'over' if p >= .5 else 'under'; x['conf'] = 100 * max(p, 1 - p); x['tier'] = PB.tier(x['conf'])
        x['won'] = int((x['res'] > x['line']) == (x['side'] == 'over')) if x['res'] != x['line'] else None
    now = CM.iso()
    for s, f in fits.items(): db.execute('insert into fits values(?,?,?,?,?,?,?) on conflict(stat) do update set sd_k=excluded.sd_k, anchor=excluded.anchor, market_weight=excluded.market_weight, fitted=excluded.fitted, mode=excluded.mode, props=excluded.props', (s, f['sd_k'], f['anchor'], wbest, now, 'pre' if pre_only else 'all', f['props']))
    db.commit()
    def rec(S): S = [x for x in S if x['won'] is not None]; w = sum(x['won'] for x in S); return w, len(S) - w
    def pct(w, l): return '%.0f%%' % (100 * w / (w + l)) if w + l else '-'
    L = ['# %s probability engine backtest - %s' % (c['name'], CM.now_ct().strftime('%Y-%m-%d %-I:%M %p CT')), '',
         'Every graded PrizePicks %s line in this sport\'s history with %d+ earlier games for the player: **%d props**, %s to %s.%s' % (c['name'], c.get('min_games', 6), len(P), P[0]['date'], P[-1]['date'], ' Pre-start PrizePicks lines only.' if pre_only else ''),
         'Skipped: ' + (', '.join('%s %d' % kv for kv in skipped.most_common()) or 'none') + '.',
         'First half = before %s (%d props), second half = %s onward (%d props). Spread scale and PrizePicks-line anchor per stat are FIT ON THE FIRST HALF ONLY, then checked on the second half.' % (mid, len(first), mid, len(second)), '',
         '## Fit (first half only)', '', ', '.join('%s: spread x%.1f, anchor %.1f' % (c['stats'][s]['label'], f['sd_k'], f['anchor']) for s, f in fits.items() if f['props'] >= 150) + '. Book weight %.1f.' % wbest, '']
    for name, S in (('First half (fit half)', first), ('Second half (unseen)', second)):
        L += ['## ' + name, '', '### Stated confidence vs what happened', '', '| stated | props | hit rate |', '|---|---|---|']
        for lo, hi in ((50, 55), (55, 60), (60, 65), (65, 70), (70, 75), (75, 80), (80, 101)):
            B = [x for x in S if lo <= x['conf'] < hi]; w, l = rec(B); L.append('| %d-%d%% | %d | %s |' % (lo, min(hi - 1, 99), len(B), pct(w, l)))
        L += ['', '### By tier', '', '| tier | props | won-lost | hit rate |', '|---|---|---|---|']
        for t in 'ABCD':
            B = [x for x in S if x['tier'] == t]; w, l = rec(B); L.append('| %s | %d | %d-%d | %s |' % (t, len(B), w, l, pct(w, l)))
        L += ['', '### Tier A and B by stat', '', '| stat | props | won-lost | hit rate |', '|---|---|---|---|']
        for s in c['stats']:
            B = [x for x in S if x['stat'] == s and x['tier'] in 'AB']; w, l = rec(B)
            if B: L.append('| %s | %d | %d-%d | %s |' % (c['stats'][s]['label'], len(B), w, l, pct(w, l)))
        Bk = [x for x in S if x['books']]
        if Bk:
            w1, l1 = rec([dict(x, won=int((x['res'] > x['line']) == (ST.median(b[0] for b in x['books']) > x['line'])) if ST.median(b[0] for b in x['books']) != x['line'] and x['res'] != x['line'] else None) for x in Bk])
            w3, l3 = rec([x for x in Bk if x['tier'] in 'AB'])
            L += ['', '### Baseline on the %d lines that had a book line' % len(Bk), '', '- Books only (take the side the book line points to): %d-%d (%s)' % (w1, l1, pct(w1, l1)), '- Engine tier A+B on the same lines: %d-%d (%s)' % (w3, l3, pct(w3, l3))]
        L += ['', '### Ladder check (Goblin / Demon style lines around the PrizePicks line)', '', '| stated over % | lines | over hit |', '|---|---|---|']
        LD = C.defaultdict(lambda: [0, 0]); step = 1.0
        for x in S:
            for off in (-3, -2, -1, 1, 2, 3):
                ln = x['line'] + off * step
                if ln < 0.5: continue
                p = pov(x, x['k'], x['a'], wbest, ln); b = min(int(p * 10) * 10, 90); LD[b][0] += 1; LD[b][1] += int(x['res'] > ln)
        for b in sorted(LD): L.append('| %d-%d%% | %d | %.0f%% |' % (b, b + 9, LD[b][0], 100 * LD[b][1] / LD[b][0]))
        days = C.defaultdict(list)
        for x in S:
            if x['board'] and x['won'] is not None and x['tier'] in 'AB': days[x['date']].append(x)
        res = C.Counter(); legs = [0, 0]
        for d, xs in sorted(days.items()):
            xs.sort(key=lambda x: -x['conf']); top, evs = [], set()
            for x in xs:
                if x['ev'] not in evs: top.append(x); evs.add(x['ev'])
                if len(top) == 3: break
            if len(top) < 3: res['no board'] += 1; continue
            w = sum(x['won'] for x in top); legs[0] += w; legs[1] += 3 - w; res['won' if w == 3 else 'lost'] += 1
        L += ['', '### Top 3 board test (board stats, tier A then B, best 3 by confidence, one per game)', '', '- Days with a full board: %d, no board: %d.' % (res['won'] + res['lost'], res['no board']),
              '- Whole board won-lost: **%d-%d** (%s). Legs %d-%d (%s).' % (res['won'], res['lost'], pct(res['won'], res['lost']), legs[0], legs[1], pct(*legs)), '']
    L += ['## Honest notes', '', '- A result exactly on the line is a push and is not counted.', '- History book lines are each book\'s latest saved number, which can be after the start; live, lines are saved before the start.',
          '- Factors not yet fed by live data are listed in README.md as pending.', '', 'Ran in %.0f seconds.' % (dt.datetime.now() - t0).total_seconds()]
    return _write('\n'.join(L), out_md)
def _write(txt, out_md):
    out_md = out_md or os.path.join(CM.REPORTS, '%s_backtest.md' % CM.now_ct().strftime('%Y-%m-%d')); os.makedirs(CM.REPORTS, exist_ok=True); open(out_md, 'w').write(txt); return txt

if __name__ == '__main__': print(run(pre_only='--all-lines' not in sys.argv, use_books='--books' in sys.argv))
