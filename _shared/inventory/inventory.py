#!/usr/bin/env python3
"""All-sports data inventory. No picks or grading.
Inputs: raw SportsGameOdds files on the 2TB drive (read only).
Outputs: reports/latest_inventory.md, per league: player lines, books, PrizePicks lines, before or after start, results, dates.
Run: python3 inventory.py"""
import gzip,glob,json,collections as C
from datetime import datetime as D
ROOT='/Volumes/2TB Drive/SportsData/sportsgameodds/events'
def T(s):return D.fromisoformat(s.replace('Z','+00:00'))
I=C.defaultdict(lambda:dict(ev=0,fin=0,withp=0,odds=0,score=0,pp=0,pp_pre=0,pp_score=0,pre=C.Counter(),post=C.Counter(),stats=C.Counter(),first=None,last=None,sport=None))
for f in glob.iglob(ROOT+'/*/*/*/*/*.gz'):
    a=f.split('/');lg,sp=a[-4],a[-5];x=I[lg];x['sport']=sp
    try:
        with gzip.open(f,'rt') as z:e=json.load(z)
    except Exception:continue
    s=e.get('status') or {};x['ev']+=1
    if not s.get('finalized') or s.get('cancelled'):continue
    x['fin']+=1
    st=T(s['startsAt']);cut=min([st]+[T(q) for q in s.get('previousStartsAt') or []]);has=False
    for o in (e.get('odds') or {}).values():
        if o.get('sideID')!='over' or o.get('betTypeID')!='ou' or o.get('statEntityID') in('all','home','away',None):continue
        has=True;x['odds']+=1;x['stats'][o.get('statID')]+=1
        sc=o.get('score') is not None;x['score']+=sc
        for b,v in (o.get('byBookmaker') or {}).items():
            if not v.get('lastUpdatedAt'):continue
            (x['pre'] if T(v['lastUpdatedAt'])<=cut else x['post'])[b]+=1
        pp=(o.get('byBookmaker') or {}).get('prizepicks')
        if pp:
            x['pp']+=1
            if pp.get('lastUpdatedAt') and T(pp['lastUpdatedAt'])<=st:
                x['pp_pre']+=1;x['pp_score']+=sc
    if has:
        x['withp']+=1;d=s['startsAt'][:10]
        x['first']=min(x['first'] or d,d);x['last']=max(x['last'] or d,d)
L=['# SportsGameOdds data inventory','','Finished games only. No picks or grading. "Before start" = last updated before the earliest start SGO listed; a book stores only its latest number, so the rest may be mid-game.','']
for lg,x in sorted(I.items(),key=lambda z:(z[1]['sport'] or '',z[0])):
    if not x['odds']:
        L.append(f"- **{x['sport']} {lg}**: {x['ev']} games, {x['fin']} finished, no player prop lines.");continue
    tot=x['pre']+x['post']
    top=[f"{b} {x['pre'][b]} before start, {x['post'][b]} later" for b,_ in tot.most_common(7) if b!='prizepicks']
    L.append(f"- **{x['sport']} {lg}**: {x['ev']} games, {x['withp']} finished with player props, {x['first']} to {x['last']}. Player lines {x['odds']}, with player result {x['score']}. PrizePicks on {x['pp']}, before start {x['pp_pre']}, with result {x['pp_score']}. Books: {'; '.join(top)}. Stats: {', '.join(k for k,_ in x['stats'].most_common(10))}.")
open(__import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)),'reports','latest_inventory.md'),'w').write('\n'.join(L)+'\n');print('done',len(I))
