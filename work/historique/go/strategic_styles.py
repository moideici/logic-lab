"""Style preferences for bounded strategic evaluations; proofs stay unchanged."""
def preference(o,a,style):
    if style=='balanced':return 0.
    b=o['board'];n=len(b);p=o['current_player'];r,c=a.get('to',a.get('dead',(a.get('row'),a.get('col'))))
    if r is None or c is None:return 0.
    if o['game']=='hex':p=o['hex_state']['colors'][p-1]
    if o['game']=='gomoku':p=o['gomoku_state']['colors'][p-1] or 1
    stones=[(y,x,v) for y,row in enumerate(b) for x,v in enumerate(row) if v]
    owner=lambda v:(v-1)%2+1 if o['game']=='draughts' else v
    friend=min((abs(r-y)+abs(c-x) for y,x,v in stones if owner(v)==p),default=n)
    enemy=min((abs(r-y)+abs(c-x) for y,x,v in stones if owner(v)!=p),default=n)
    center=1-(abs(r-(n-1)/2)+abs(c-(n-1)/2))/max(1,n-1)
    edge=min(r,c,n-1-r,n-1-c)/max(1,(n-1)/2)
    if style=='aggressive':return 2/(1+enemy)+center*.5
    if style=='defensive':return 2/(1+friend)+(1-edge)*.3
    if style=='positional':return center+max(0,1-abs(friend-3)/max(1,n))
    if style=='greedy':return 2/(1+enemy)+(1-edge)*.7
    # Deterministic novelty varies the preferred zone, without random mistakes.
    return ((r*37+c*17+o.get('moves',0)*13)%97)/97+min(friend,enemy)/max(1,n)
def apply_styles(o,values,style,exact=False):
    if style=='balanced' or exact:return values,False
    game=o['game'];params={'go':(20,3),'gomoku':(500,12),'hex':(99990,8),'draughts':(99990,3),'breakthrough':(99990,4),'reversi':(99990,2)}
    if game not in params:return values,False
    cap,scale=params[game]
    # A tactical win/capture or forced defense keeps its original ordering.
    if game in ('go','gomoku') and max(v['quality'][0] for v in values)>=cap:return values,False
    out=[];changed=False
    for v in values:
        q=v['quality'];a=v['action'];adjust=scale*preference(o,a,style) if abs(q[0])<cap and not any(k in a for k in ('resign','pass','accept','resume')) else 0.
        out.append({**v,'quality':[q[0]+adjust,*q[1:]],**({'base_quality':q} if adjust else {})});changed|=bool(adjust)
    return out,changed
