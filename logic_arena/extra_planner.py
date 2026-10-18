"""Exact impartial/puzzle analysis and bounded public Reversi search."""
from functools import lru_cache
from .extra_rules import legal_extra,step_extra,reversi_moves
@lru_cache(None)
def nim_value(heaps):
    if not any(heaps):return -1,0
    best=(-2,0)
    for p,n in enumerate(heaps):
        for take in range(1,n+1):
            child=list(heaps);child[p]-=take;v,plies=nim_value(tuple(child));option=(-v,plies+1)
            if option[0]>best[0] or option[0]==best[0] and (option[1]<best[1] if option[0]==1 else option[1]>best[1]):best=option
    return best
def light_solutions(board):
    rows=[]
    for r in range(5):
        for c in range(5):
            row=(board[r][c]&1)<<25
            for y,x in ((r,c),(r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if 0<=y<5 and 0<=x<5:row|=1<<(y*5+x)
            rows.append(row)
    pivots=[];at=0
    for col in range(25):
        pivot=next((i for i in range(at,25) if rows[i]>>col&1),None)
        if pivot is None:continue
        rows[at],rows[pivot]=rows[pivot],rows[at]
        for i in range(25):
            if i!=at and rows[i]>>col&1:rows[i]^=rows[at]
        pivots.append(col);at+=1
    if any(not (r&((1<<25)-1)) and r>>25&1 for r in rows):raise ValueError('Grille Lights Out insoluble')
    particular=sum((rows[i]>>25&1)<<col for i,col in enumerate(pivots));basis=[]
    for col in set(range(25))-set(pivots):basis.append((1<<col)|sum((rows[i]>>col&1)<<p for i,p in enumerate(pivots)))
    solutions=[particular]
    for v in basis:solutions += [s^v for s in solutions[:]]
    return sorted(solutions,key=lambda s:(s.bit_count(),s))
def reversi_evaluate(board,player):
    enemy=3-player;diff=sum(v==player for row in board for v in row)-sum(v==enemy for row in board for v in row)
    corners=[(0,0),(0,5),(5,0),(5,5)];corner=sum((board[r][c]==player)-(board[r][c]==enemy) for r,c in corners)
    risky=0
    for r,c in corners:
        if not board[r][c]:
            for y in (r,1 if r==0 else 4):
                for x in (c,1 if c==0 else 4):
                    if (y,x)!=(r,c):risky+=(board[y][x]==player)-(board[y][x]==enemy)
    return 2*diff+80*corner-25*risky+5*(len(reversi_moves(board,player))-len(reversi_moves(board,enemy)))
def extra_values(obs,legal,budget,max_depth=None):
    name=obs['game'];board=obs['board'];player=obs['current_player']
    if name=='nim':
        heaps=tuple(map(sum,board));values=[]
        for a in legal:
            child=list(heaps);child[a['pile']]-=a['take'];v,n=nim_value(tuple(child));v=-v;n+=1
            values.append({'action':a,'quality':[v,-n if v==1 else n],'outcome':v,'remaining_moves':n})
        return values,{'method':'exact_nim','analysis_exact':True,'optimal':True,'nodes':0}
    if name=='lightsout':
        solutions=light_solutions(board);values=[]
        for a in legal:
            bit=1<<(a['row']*5+a['col']);distance=min((s^bit).bit_count() for s in solutions)
            values.append({'action':a,'quality':[-distance],'remaining_moves':distance+1})
        return values,{'method':'exact_lights_out','analysis_exact':True,'optimal':True,'solution_found':True,'nodes':25}
    def child(a,p,b):
        after=[r[:] for r in b];state=step_extra(name,after,p,a);return after,state
    def terminal(b,p):
        d=sum(v==p for row in b for v in row)-sum(v==3-p for row in b for v in row)
        return (100000 if d>0 else -100000 if d<0 else 0)+d
    def visit(b,p,depth,alpha,beta):
        budget.tick();actions=legal_extra(name,b,p)
        if not actions:return terminal(b,p)
        if depth<=0:return reversi_evaluate(b,p)
        best=-1000000
        actions.sort(key=lambda a:0 if a.get('pass') else -int(a['row'] in (0,5) and a['col'] in (0,5)))
        for a in actions:
            after,state=child(a,p,b)
            v=terminal(after,p) if state[1] else -visit(after,3-p,depth-(not a.get('pass')), -beta,-alpha)
            best=max(best,v);alpha=max(alpha,v)
            if alpha>=beta:break
        return best
    values=[]
    for a in legal:
        after,state=child(a,player,board);v=terminal(after,player) if state[1] else -reversi_evaluate(after,3-player)
        values.append({'action':a,'quality':[v]})
    empty=sum(v==0 for row in board for v in row);limit=(empty if empty<=10 else 6) if max_depth is None else max_depth;reached=0
    for depth in range(1,max(1,limit)+1):
        updated=[]
        try:
            for a in legal:
                after,state=child(a,player,board);v=terminal(after,player) if state[1] else -visit(after,3-player,depth-(not a.get('pass')),-1000000,1000000)
                updated.append({'action':a,'quality':[v]})
        except Exception as e:
            from .agents import Exhausted
            if not isinstance(e,Exhausted):raise
            break
        values=updated;reached=depth
    return values,{'method':'reversi_alpha_beta','analysis_exact':reached>=empty,'optimal':reached>=empty,'depth':reached,'nodes':budget.nodes,'evaluation_scope':'exact_game_outcome' if reached>=empty else 'bounded_adversarial_search'}
