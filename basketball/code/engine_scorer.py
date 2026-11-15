#!/usr/bin/env python3
"""Apex Basketball - decision layer of the production pipeline (his 11/5 2:19 PM ask: run like Apex Tennis, the probability engine decides).
Turns the saved PrizePicks lines into scored rows for bball_pipeline / bball_tracker / the bot, in the same row shape the old Step 3
scorer made, with the engine's numbers: Win Prob = the engine's own chance the side hits, tier A-D, EDGE SCORE, plain reasons.
Rules, applied to every line the same way:
  - NBA only; lines not started; promo / flash-sale lines marked (off boards).
  - Board stats: Points, Rebounds, Assists, PRA, Pts+Rebs, Pts+Asts, Rebs+Asts. 3PTM / steals / blocks / turnovers / fantasy are scored
    but marked off-board (his 11/5 6:49 AM direction).
  - Goblin and Demon lines are MORE only (PrizePicks rule). Standard lines take the engine's side.
  - Books (The Odds API) are one factor; the PrizePicks standard line anchors the projection (fitted share); teammates out from the ESPN feed.
No PrizePicks call here: it reads data/collected only. Separate from Apex Tennis.
"""
import os, collections as C, datetime as dt, statistics as ST
import score_board as SB, prob_engine as PE, room_edge as RE, room_check as RC

QUESTIONABLE = ('Questionable', 'Day-To-Day', 'Game Time Decision')
# APEX-INJURYHOLD-2026-11-11 (owner, "Go injury hold", after Tyler Herro (knee, Day-To-Day) sat at #1 with no warning and
# PrizePicks pulled his lines): the player's OWN injury status was skipped (only teammates were read). Now a player listed Out,
# Doubtful, Questionable, Day-To-Day or Game Time Decision gets facts['own_inj'] + row['inj_hold']: a warning on the card and no
# numbered board spot (he waits in BACKUPS until the report clears him). Nothing is blocked for good. Turn off: INJ_HOLD = False, restart.
INJ_HOLD = True
HOLD_STATUS = ('Out', 'Doubtful') + QUESTIONABLE
_INJ_LATEST = {}
def _own_status(inj_day, team, player, date):
    """The player's own last status in that day's injury report; when that day has no report yet (tomorrow's game), the newest earlier report."""
    def find(m):
        for p, s in (m.get(team) or {}).items():
            if RC.norm(p) == RC.norm(player): return s
        return None
    if inj_day: return find(inj_day)
    if date not in _INJ_LATEST:
        import glob
        d = os.path.join(PE.ROOT, 'data', 'collected', 'injuries'); fs = sorted(os.path.basename(x)[:-6] for x in glob.glob(os.path.join(d, '*.jsonl')) if os.path.basename(x)[:-6] <= date)
        _INJ_LATEST[date] = PE.injuries(fs[-1]) if fs else {}
    return find(_INJ_LATEST[date])
# APEX-REASONSALL-2026-11-14 ("I said fix all"): the Matchup reason always shows, even under 1 point. Display only.
SHORT = {'Base projection': 'base', 'Recent form': 'form', 'Minutes trend': 'minutes', 'Matchup': 'matchup', 'Pace / blowout': 'pace', 'Rest / home': 'rest', 'Teammates out': 'teammates', 'PrizePicks standard line': 'line anchor', 'Market consensus': 'books'}

def _row(r, st, now):
    date = st.astimezone(SB.CT).date().isoformat(); league = str(r.get('league') or '?'); name = str(r.get('player') or '?')
    team = SB.abbr(r.get('team')); opp, home = SB.parse_opponent(r.get('opponent')); promo = bool(r.get('is_promo')) or r.get('flash_sale_line') is not None
    return dict(projection_id=str(r.get('projection_id')), league=league, player=name, team=team or r.get('team'), opponent=opp or r.get('opponent'), stat_raw=r.get('stat'), stat=None, line=r.get('line'),
                kind=SB._kind(r), start=st.isoformat(), game_date=date, seen=r.get('seen'), last_seen=r.get('last_seen') or r.get('seen'), side=None, win_prob=None, projected=None, promo=promo, reason=None, tier=None, edge_score=None, why='',
                room=0, onboard=False, nbooks=0, home=home, game_key='%s|%s|%s' % (league, date, '-'.join(sorted(str(x) for x in (team or r.get('team'), opp or r.get('opponent')))))), team, opp, home

def score_lines(lines, E, now=None):
    """Every saved line not started -> one row. NBA lines the engine can read get Win Prob, tier, edge score and reasons; the rest say why not."""
    now = now or dt.datetime.now(dt.timezone.utc); cfg = E.cfg; out, pre = [], []
    for r in lines:
        try: st = dt.datetime.fromisoformat(str(r.get('start')).replace('Z', '+00:00')).astimezone(dt.timezone.utc)
        except (ValueError, TypeError): continue
        if st <= now or str(r.get('status') or 'pre_game') != 'pre_game': continue
        row, team, opp, home = _row(r, st, now); out.append(row); date = row['game_date']
        if row['league'].upper() != 'NBA': row['reason'] = 'not NBA: no engine for this league yet'; continue
        stat = PE.PP.get(str(r.get('stat') or '').strip().lower()); row['stat'] = stat
        if '+' in row['player']: row['reason'] = 'two players in one line: not scored'; continue
        if not stat: row['reason'] = 'stat the engine does not score'; continue
        try: line = float(r.get('line'))
        except (ValueError, TypeError): row['reason'] = 'no number on the line'; continue
        sch = SB._schedule_lookup(team, date)
        if sch:
            opp = opp or sch[0]; home = sch[1] if home is None else home; row['opponent'] = opp; row['home'] = home
            row['game_key'] = '%s|%s|%s' % (row['league'], date, '-'.join(sorted((str(team), str(opp)))))
        if not team or team not in SB.TEAMS or not opp or opp not in SB.TEAMS: row['reason'] = 'team or opponent not understood'; continue
        pid, why = E.hist.resolve(row['player'], team)
        if not pid: row['reason'] = why; continue
        pre.append((row, pid, stat, line, team, opp, home))
    std = C.defaultdict(list)
    for row, pid, stat, line, *_ in pre:
        if row['kind'] == 'standard': std[(pid, stat, row['game_date'])].append(line)
    books, inj, proj, proj_outs = {}, {}, {}, {}
    extra = []
    try:   # APEX-GOBLINLESS-NBA-2026-11-12: Demon lines where PrizePicks also sells LESS (as a Goblin)
        import goblin_less as GL; gl_sold = GL.sold()
    except Exception: GL = None; gl_sold = set()
    for row, pid, stat, line, team, opp, home in pre:
        date = row['game_date']; lab, fn, floor, onboard, ukind = PE.STATS[stat]; row['onboard'] = onboard
        if date not in books: books[date] = PE.book_lines(date); inj[date] = PE.injuries(date)
        k = (pid, stat, date)
        if k not in proj:
            reg = E.regulars(SB.TEAMS[team][1], date); outs, quest = [], []
            for p, s in inj[date].get(team, {}).items():
                if RC.norm(p) == RC.norm(row['player']): continue
                ids = [i for i in reg if RC.norm(E.name_of.get(i, '')) == RC.norm(p)]
                if s in ('Out', 'Doubtful') and ids: outs.append((p, reg[ids[0]]))
                elif s in QUESTIONABLE and ids: quest.append(p)
            hist = E.H.get(pid, []); last = [h for h in hist if h['game_date'] < date]
            rest = (dt.date.fromisoformat(date) - dt.date.fromisoformat(last[-1]['game_date'])).days if last else None
            pr = E.project(pid, stat, date, SB.TEAMS[opp][0], home, None, None, sum(x[1] for x in outs), rest, [x[0] for x in outs])
            proj[k] = (pr, quest, rest); proj_outs[k] = outs
        pr, quest, rest = proj[k]
        try: own_inj = _own_status(inj[date], team, row['player'], date) if INJ_HOLD else None
        except Exception: own_inj = None
        row['inj_hold'] = bool(own_inj in HOLD_STATUS); row['own_inj'] = own_inj if own_inj in HOLD_STATUS else None
        if not pr: row['reason'] = 'under %d earlier games for this stat' % cfg['min_games']; continue
        bl = books[date].get((PE.MARKET[stat], RC.norm(row['player'])), []); anchor = ST.median(std[k]) if std.get(k) else None
        ev = PE.evaluate(pr, line, bl, cfg, anchor)
        side = 'MORE' if row['kind'] != 'standard' or ev['side'] == 'over' else 'LESS'; p = ev['over'] if side == 'MORE' else ev['under']
        e = RE.room_edge(line, [b[0] for b in bl]) if bl else dict(edge=0, side=None)
        room = e['edge'] if e.get('side') and str(e['side']).upper().startswith(side[0]) else 0
        grm = None
        try:   # APEX-ROOM-2026-11-11: Goblins rated by their room under the sportsbooks (our own labeled Goblin lines)
            import room_goblin as RG
            grm = RG.room(stat, row['kind'], side, line, bl, p)
            if grm: p = grm['to'] + grm['was'] / 1000.0   # same room number: the pick Apex itself rated higher goes first
        except Exception: grm = None
        sgn = 1 if side == 'MORE' else -1; why = []
        for nm, d, note in ev['contrib']:
            d *= sgn
            if abs(d) >= 1 or nm == 'Matchup' or (nm in ('Market consensus', 'Teammates out') and note not in ('no book line', 'no regular out')): why.append('%s %+.0f%%: %s' % (nm, d, note))
        if quest: why.append('⚠ questionable teammates: ' + ', '.join(quest[:3]))
        if rest == 1: why.append('📅 back-to-back')
        if grm: why.append('Room %+.0f%%: %g under the books' % (grm['to'] - grm['was'], grm['room']))
        if not onboard: why.append('not a board stat')
        mk = ev.get('market'); market = dict(line=mk[1], n=mk[2], p=mk[3]) if mk else None
        facts = dict(l5=pr['l5'], l10=pr['l10'], base=pr['base'], mins=pr['mins'], mins_usual=pr.get('mins_usual', pr['mins']), matchup=pr['steps'][3][2], rest=rest, outs=[x[0] for x in proj_outs.get(k, [])], quest=quest, own_inj=row.get('own_inj'))
        signals = [(SHORT.get(nm, nm), d * sgn) for nm, d, note in ev['contrib'] if abs(d) >= 0.5]
        row.update(side=side, win_prob=round(p, 3) if grm else round(p, 1), projected=round(pr['mean'], 2), used=round(ev.get('mean_used', pr['mean']), 2), spread=round(pr['sd'], 1), games=pr['games'], tier=PE.tier(p, cfg), room=room, nbooks=len(bl), market=market, facts=facts, signals=signals,
                   edge_score=PE.edge_score(dict(ev, side='over' if side == 'MORE' else 'under', conf=p), room), why=' · '.join(why))
        try:   # APEX-HONEST-NBA-2026-11-07
            import nba_honest_live as HN; row['honest'] = HN.honest(row)
        except Exception: row['honest'] = None
        row['groom'] = grm
        if grm: row['honest'] = dict(pct=float(grm['to']), n=grm['n'], src='room', all_stats=True)
        try:   # APEX-GOBLINLESS-NBA-2026-11-12: the LESS side of this Demon line is its own Goblin LESS pick, rated by gap above the books + Apex's LESS rating
            if GL and row['kind'] == 'demon' and (row['projection_id'], float(line)) in gl_sold:
                up = ev['under']; glc = GL.rate(stat, line, bl, up); p2 = (glc['to'] + glc['was'] / 1000.0) if glc else up; c = dict(row); why2 = []
                for nm, d, note in ev['contrib']:
                    if abs(d) >= 1 or nm == 'Matchup' or (nm in ('Market consensus', 'Teammates out') and note not in ('no book line', 'no regular out')): why2.append('%s %+.0f%%: %s' % (nm, -d, note))
                if quest: why2.append('⚠ questionable teammates: ' + ', '.join(quest[:3]))
                if rest == 1: why2.append('📅 back-to-back')
                why2.append(('Gap %+.0f%%: %g above the books' % (glc['to'] - glc['was'], glc['room'])) if glc else 'no sportsbook number yet: not proven')
                c.update(_pick_key='%s|%s|gless' % (row['projection_id'], row['line']), kind='goblin', side='LESS', gless=True, win_prob=round(p2, 3) if glc else round(up, 1), tier=PE.tier(p2, cfg), room=0, groom=glc,
                         signals=[(nm, -d) for nm, d in (row.get('signals') or [])], edge_score=PE.edge_score(dict(ev, side='under', conf=p2), 0), why=' · '.join(why2),
                         honest=dict(pct=float(glc['to']), n=glc['n'], src='gap', all_stats=True) if glc else None)
                extra.append(c)
        except Exception: pass
    return out + extra
