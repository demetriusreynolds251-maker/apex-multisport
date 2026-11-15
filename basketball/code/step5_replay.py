#!/usr/bin/env python3
"""Step 5: replay Top 3, Elite 5, Elite 6 from Step 3 picks. Read only, no network. Rank = Win Prob + 5 x book room signal,
book = median of books last updated before the start (book_lines_json with pp_before_start=1), never closing lines. One per game.
(a) lines as saved. (b) ESTIMATE: MORE lowered a fixed amount, not real Goblins. Choices made on the tune half, then checked."""
import sqlite3,json,collections as C,os,statistics as st,sys
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d=sqlite3.connect('file:%s/data/processed/step3_predictions.sqlite?mode=ro'%R,uri=True);d.row_factory=sqlite3.Row
h=sqlite3.connect('file:%s/data/processed/nba_history.sqlite?mode=ro'%R,uri=True);h.row_factory=sqlite3.Row
L={}
for r in h.execute("select event_id,player_id,stat,book_lines_json,pp_before_start from prop_lines"):
    v=None
    if r['pp_before_start'] and r['book_lines_json']:
        try:v=[float(x[0]) for x in json.loads(r['book_lines_json']).values()]
        except Exception:v=None
    L[(r['event_id'],r['player_id'],r['stat'])]=st.median(v) if v else None
N=st.NormalDist();OFF={'points':3,'points+rebounds+assists':3,'rebounds+assists':2,'rebounds':1,'fieldGoalsMade':1}
COIN={'rebounds','fieldGoalsMade'}
A=[];B=[]
for r in d.execute("select * from predictions where won is not null"):
    x=dict(r);bk=L.get((x['event_id'],x['player_id'],x['stat']));x['sig']=0
    if bk is not None and bk!=x['pp_line']:
        x['sig']=1 if (bk>x['pp_line'])==(x['side']=='MORE') else -1
    x['line']=x['pp_line'];x['rank']=x['win_prob']+5*x['sig'];A.append(x)
    if x['side']=='MORE':
        z=N.inv_cdf(min(.995,x['win_prob']/100))
        if z>.05:
            s=abs(x['projected']-x['pp_line'])/z;l=x['pp_line']-OFF[x['stat']]
            if s>0 and l>0 and x['result']!=l:
                y=dict(x);y['line']=l;y['win_prob']=100*N.cdf((x['projected']-l)/s);y['won']=int(x['result']>l);y['sig']=0;y['rank']=y['win_prob'];B.append(y)
PAY={'a':{3:lambda w:100 if w==3 else -20,5:lambda w:{5:180,4:20,3:-12}.get(w,-20),6:lambda w:{6:480,5:20,4:-12}.get(w,-20)},
     'b':{3:lambda w:24 if w==3 else -20,5:lambda w:{5:30,4:0,3:-12}.get(w,-20),6:lambda w:None}}
def play(P,ver,F,n,half=None,month=False):
    days=C.defaultdict(list)
    for x in P:
        if F(x) and (half is None or x['half']==half):days[x['game_date']].append(x)
    won=pl=m=0;lw=ll=0;mo=C.defaultdict(lambda:[0,0,0])
    for dd,Q in sorted(days.items()):
        S=[];u=set()
        for x in sorted(Q,key=lambda y:-y['rank']):
            if x['event_id'] in u:continue
            u.add(x['event_id']);S.append(x)
            if len(S)==n:break
        if len(S)<n:continue
        w=sum(x['won'] for x in S);pl+=1;won+=w==n;lw+=w;ll+=n-w;p=PAY[ver][n](w)
        m+=p or 0;mo[dd[:7]][0]+=w==n;mo[dd[:7]][1]+=1;mo[dd[:7]][2]+=p or 0
    return dict(won=won,pl=pl,m=m,lw=lw,ll=ll,mo=dict(mo))
def line(r,dollars=True):return f"{r['won']} of {r['pl']} days"+(f", ${r['m']:+d}" if dollars else "")+f", picks {r['lw']}-{r['ll']}"
def cfg(ver):
    out=[]
    for f in((0,55,57,60,65) if ver=='a' else (60,65,70,75,80)):
        for hold in(False,True):
            for sig in((None,1) if ver=='a' else (None,)):
                out.append((f,hold,sig))
    return out
for ver,P,name in(('a',A,'(a) Standard lines as saved'),('b',B,'(b) ESTIMATE lowered MORE lines, Goblin-like pay')):
    print('\n=====',name,len(P))
    best={}
    for n in(3,5,6):
        for f,hold,sig in cfg(ver):
            F=lambda x,f=f,hold=hold,sig=sig:x['win_prob']>=f and (not hold or x['stat'] not in COIN) and (sig is None or x['sig']==sig)
            t,c=play(P,ver,F,n,'tune'),play(P,ver,F,n,'check')
            d_=ver=='a' or n<6
            print(f"{n}-pick floor {f} hold coin-flips {hold} book-agree-only {sig is not None} | tune {line(t,d_)} | check {line(c,d_)}")
            if t['pl']>=20 and (n not in best or t['m']>best[n][0]['m'] or (not d_ and t['won']/t['pl']>best[n][0]['won']/best[n][0]['pl'])):best[n]=(t,c,f,hold,sig)
    for n,(t,c,f,hold,sig) in best.items():
        print(f"CHOSEN ON TUNE {n}-pick floor {f} hold {hold} agree {sig}: tune {line(t)} | check {line(c)}");print('  check months',c['mo'])
