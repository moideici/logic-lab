"""Go 9/13/19: area scoring, positional superko, no suicide, agreed dead groups.

Two passes enter scoring. Either player can mark whole dead groups, accept the
proposal, or resume play. Two distinct acceptances finalize the area score.
"""
from copy import deepcopy
GO_SPECS={'go':(1816,365)}
SIZES=(9,13,19)
def neighbors(n,r,c):
    return [(y,x) for y,x in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)) if 0<=y<n and 0<=x<n]
def board_key(b):return ''.join(str(v) for row in b for v in row)
def group(b,r,c):
    n=len(b);color=b[r][c];stones={(r,c)};liberties=set();stack=[(r,c)]
    while stack:
        y,x=stack.pop()
        for q in neighbors(n,y,x):
            v=b[q[0]][q[1]]
            if not v:liberties.add(q)
            elif v==color and q not in stones:stones.add(q);stack.append(q)
    return stones,liberties
def new_go(size=19,komi=7.5):
    if type(size) is not int or size not in SIZES:raise ValueError('Le Go accepte les tailles 9, 13 ou 19')
    import math
    if type(komi) not in (int,float) or not math.isfinite(komi) or not -20<=komi<=20:raise ValueError('Komi invalide')
    b=[[0]*size for _ in range(size)]
    return b,{'size':size,'komi':float(komi),'passes':0,'captures':[0,0],'seen':[board_key(b)],'phase':'play','dead':[],'accepted':[],'resume_player':1,'final_score':None}
def play_candidate(b,player,r,c,seen):
    n=len(b)
    if not 0<=r<n or not 0<=c<n or b[r][c]:return None
    after=[row[:] for row in b];after[r][c]=player;captured=[];checked=set()
    for y,x in neighbors(n,r,c):
        if after[y][x]!=3-player or (y,x) in checked:continue
        stones,liberties=group(after,y,x);checked|=stones
        if not liberties:
            captured.extend(stones)
            for a,d in stones:after[a][d]=0
    _,liberties=group(after,r,c)
    if not liberties:return None
    key=board_key(after)
    if key in seen:return None
    return after,len(captured),key
def legal_go(b,player,state):
    if state['phase']=='finished':return []
    if state['phase']=='scoring':
        return [{'dead':[r,c]} for r,row in enumerate(b) for c,v in enumerate(row) if v]+[{'accept':True},{'resume':True},{'resign':True}]
    seen=set(state['seen']);out=[]
    for r,row in enumerate(b):
        for c,v in enumerate(row):
            if not v and play_candidate(b,player,r,c,seen) is not None:out.append({'row':r,'col':c})
    return out+[{'pass':True},{'resign':True}]
def area_score(b,state):
    n=len(b);dead=set(state['dead']);after=[[0 if r*n+c in dead else v for c,v in enumerate(row)] for r,row in enumerate(b)];stones=[sum(v==color for row in after for v in row) for color in (1,2)];territory=[0,0];visited=set()
    for r in range(n):
        for c in range(n):
            if after[r][c] or (r,c) in visited:continue
            region={(r,c)};border=set();stack=[(r,c)];visited.add((r,c))
            while stack:
                y,x=stack.pop()
                for a,d in neighbors(n,y,x):
                    if after[a][d]:border.add(after[a][d])
                    elif (a,d) not in visited:visited.add((a,d));region.add((a,d));stack.append((a,d))
            if len(border)==1:territory[next(iter(border))-1]+=len(region)
    black=stones[0]+territory[0];white=stones[1]+territory[1]+state['komi']
    return {'black':black,'white':white,'komi':state['komi'],'stones':stones,'territory':territory,'margin':black-white}
def step_go(b,player,a,state):
    reward=0.;done=False;winner=None;score=0.
    if a.get('resign'):
        state['phase']='finished';done=True;winner=3-player;reward=-1.
    elif state['phase']=='scoring':
        if a.get('resume'):
            state.update(phase='play',passes=0,dead=[],accepted=[])
            return {'player':state['resume_player'],'done':False,'winner':None,'score':0.,'reward':0.,'state':state}
        elif a.get('accept'):
            if player not in state['accepted']:state['accepted'].append(player)
            if len(state['accepted'])==2:
                result=area_score(b,state);state.update(phase='finished',final_score=result);score=result['margin'];done=True;winner=1 if score>0 else 2 if score<0 else 0;reward=0. if not winner else 1. if winner==player else -1.
        else:
            r,c=a['dead'];stones,_=group(b,r,c);ids={y*len(b)+x for y,x in stones};dead=set(state['dead']);dead=dead-ids if ids<=dead else dead|ids;state.update(dead=sorted(dead),accepted=[])
    elif a.get('pass'):
        state['passes']+=1
        if state['passes']==2:state.update(phase='scoring',resume_player=3-player,dead=[],accepted=[])
    else:
        r,c=a['row'],a['col'];result=play_candidate(b,player,r,c,set(state['seen']))
        if result is None:raise ValueError('Coup de Go illégal')
        after,captured,key=result;b[:]=after;state['seen'].append(key);state['captures'][player-1]+=captured;state['passes']=0
    return {'player':player if done else 3-player,'done':done,'winner':winner,'score':score,'reward':reward,'state':state}
def encode_go(o):
    b=o['board'];n=len(b);s=o['go_state'];own=o['current_player'];dead=set(s['dead']);x=[0.]*1816;checked=set()
    for r,row in enumerate(b):
        for c,v in enumerate(row):
            if not v:continue
            at=(r*19+c)*5;x[at+(v!=own)]=1.;x[at+4]=float(r*n+c in dead)
            if (r,c) not in checked:
                stones,libs=group(b,r,c);checked|=stones
                if len(libs) in (1,2):
                    for y,d in stones:x[(y*19+d)*5+1+len(libs)]=1.
    x[1805:]=[float(n==9),float(n==13),float(n==19),s['komi']/20,s['passes']/2,float(s['phase']=='scoring'),float(own==1),float(own in s['accepted']),float(3-own in s['accepted']),s['captures'][own-1]/361,s['captures'][2-own]/361]
    return x
def go_action_index(a):
    if a.get('pass'):return 361
    if a.get('accept'):return 362
    if a.get('resume'):return 363
    if a.get('resign'):return 364
    r,c=a['dead'] if 'dead'in a else (a['row'],a['col']);return r*19+c
