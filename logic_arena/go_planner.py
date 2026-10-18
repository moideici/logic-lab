"""Public Go tactics: captures, atari saves, liberties, eyes and bounded replies."""
from .go_rules import neighbors,group,play_candidate,area_score,legal_go
def go_context(b,p):
    checked=set();save={};attack={};n=len(b)
    for r,row in enumerate(b):
        for c,v in enumerate(row):
            if not v or (r,c) in checked:continue
            stones,libs=group(b,r,c);checked|=stones
            if len(libs)==1:
                at=next(iter(libs));target=save if v==p else attack;target[at]=target.get(at,0)+len(stones)
    return save,attack
def go_rank(b,p,s,legal):
    n=len(b);seen=set(s['seen']);save,attack=go_context(b,p);out=[];occupied=sum(bool(v) for row in b for v in row)
    if s['phase']=='scoring':
        disputed=any(b[i//n][i%n]==p and len(group(b,i//n,i%n)[1])>=2 for i in s['dead'])
        return [{'action':a,'quality':[100. if a.get('resume') and disputed else 10. if a.get('accept') and not disputed else -10000. if a.get('resign') else -100.]} for a in legal]
    for a in legal:
        if a.get('resign'):q=-10000.;after=None
        elif a.get('pass'):
            area=area_score(b,s)['margin']*(1 if p==1 else -1);q=2. if occupied>n*n*.8 else -30.
            if s['passes'] and area>0:q=10000.
            after=None
        else:
            r,c=a['row'],a['col'];result=play_candidate(b,p,r,c,seen)
            if result is None:continue
            after,captured,_=result;stones,libs=group(after,r,c);adj=neighbors(n,r,c);friends=sum(b[y][x]==p for y,x in adj);enemies=sum(b[y][x]==3-p for y,x in adj)
            diagonals=[b[y][x] for y,x in ((r-1,c-1),(r-1,c+1),(r+1,c-1),(r+1,c+1)) if 0<=y<n and 0<=x<n]
            eye=bool(friends==len(adj) and sum(v==3-p for v in diagonals)<=(1 if len(diagonals)==4 else 0))
            saved=save.get((r,c),0) if len(libs)>1 else 0
            star=2 if min(r,n-1-r) in (2,3) and min(c,n-1-c) in (2,3) else 0
            q=100*captured+60*saved-80*len(stones)*(len(libs)==1)-25*eye+min(len(libs),6)*.3+enemies*.5-friends*.25+star
            if occupied<n*2:q+=min(r,c,n-1-r,n-1-c)*.08
            q-=abs(r-(n-1)/2)*.001+abs(c-(n-1)/2)*.001
        out.append({'action':a,'quality':[q]})
    return out
def go_values(o,legal,budget,beam=12):
    b=o['board'];p=o['current_player'];s=o['go_state'];values=go_rank(b,p,s,legal);depth=1;refined=0
    if s['phase']=='play':
        order=sorted((v for v in values if 'row'in v['action']),key=lambda v:v['quality'],reverse=True)[:beam]
        try:
            for v in order:
                budget.tick();a=v['action'];after,captured,key=play_candidate(b,p,a['row'],a['col'],set(s['seen']));child={**s,'seen':s['seen']+[key],'passes':0,'captures':s['captures'][:]};child['captures'][p-1]+=captured
                replies=legal_go(after,3-p,child);ranked=go_rank(after,3-p,child,replies);threat=max((r['quality'][0] for r in ranked if 'row'in r['action']),default=0.)
                # Only the tactical part of an opponent reply is a material threat.
                v['quality'][0]-=.85*max(0.,threat-10.);refined+=1;depth=2
        except Exception as error:
            from .agents import Exhausted
            if not isinstance(error,Exhausted):raise
    return values,{'method':'go_liberties_tactical_search','depth':depth,'nodes':budget.nodes,'roots_refined':refined,'analysis_exact':False,'optimal':False,'evaluation_scope':'bounded_go_tactics','rules':'area_positional_superko_no_suicide_agreed_dead_groups'}
