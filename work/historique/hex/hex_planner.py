"""Public connection-distance search, mandatory threat defense and bounded beam."""
from functools import lru_cache
from heapq import heappush,heappop
from copy import deepcopy
from .hex_rules import NEIGHBORS,legal_hex,step_hex,connection_path
@lru_cache(maxsize=8192)
def _distance(flat,color):
    n=7;dist=[1000]*49;queue=[]
    for i in range(n):
        k=i if color==1 else i*n
        if flat[k]!=3-color:dist[k]=int(flat[k]!=color);heappush(queue,(dist[k],k))
    while queue:
        cost,k=heappop(queue)
        if cost!=dist[k]:continue
        r,c=divmod(k,n)
        if (r if color==1 else c)==n-1:return cost
        for dr,dc in NEIGHBORS:
            y,x=r+dr,c+dc;at=y*n+x
            if 0<=y<n and 0<=x<n and flat[at]!=3-color:
                value=cost+int(flat[at]!=color)
                if value<dist[at]:dist[at]=value;heappush(queue,(value,at))
    return 1000
def hex_distance(board,color):return _distance(tuple(v for row in board for v in row),color)
def hex_evaluate(board,color):
    center=sum((1 if v==color else -1)*(6-abs(r-3)-abs(c-3)) for r,row in enumerate(board) for c,v in enumerate(row) if v)
    return 100*(hex_distance(board,3-color)-hex_distance(board,color))+center
def winning_cells(board,color):
    if hex_distance(board,color)!=1:return []
    result=[]
    for r in range(7):
        for c in range(7):
            if board[r][c]:continue
            board[r][c]=color
            try:won=bool(connection_path(board,color))
            finally:board[r][c]=0
            if won:result.append((r,c))
    return result
def hex_values(obs,legal,budget,max_depth=3,beam=10):
    board=obs['board'];root=obs['current_player'];state=obs['hex_state'];heuristic_used=False;beam_used=False
    def child(b,p,a,s):
        after=[row[:] for row in b];result=step_hex(after,p,a,deepcopy(s));return after,result
    def fallback(b,p,a,s):
        after,result=child(b,p,a,s);color=result['state']['colors'][p-1]
        if result['done']:return 100000
        if winning_cells(after,3-color):return -99999
        return hex_evaluate(after,color)
    def visit(b,p,s,depth,alpha,beta,extensions=6):
        nonlocal heuristic_used,beam_used
        budget.tick();color=s['colors'][p-1]
        if winning_cells(b,color):return 100000
        threats=winning_cells(b,3-color)
        if len(threats)>1 and not s['swap_available']:return -99999
        actions=legal_hex(b,s)
        if not actions:return -100000
        forced=bool(threats) and not s['swap_available']
        if depth<=0 and not (forced and extensions>0):heuristic_used=True;return hex_evaluate(b,color)
        if forced:actions=[a for a in actions if (a.get('row'),a.get('col')) in threats]
        ordered=sorted(actions,key=lambda a:fallback(b,p,a,s),reverse=True)
        if len(ordered)>beam and sum(v==0 for row in b for v in row)>6:ordered=ordered[:beam];beam_used=True
        best=-1000000
        for a in ordered:
            after,result=child(b,p,a,s)
            value=100000 if result['done'] else -visit(after,3-p,result['state'],depth-1,-beta,-alpha,extensions-int(depth<=0))
            best=max(best,value);alpha=max(alpha,value)
            if alpha>=beta:break
        return best
    values=[{'action':a,'quality':[fallback(board,root,a,state)]} for a in legal];reached=0;exact=all(abs(v['quality'][0])>=99999 for v in values);won=any(v['quality'][0]==100000 for v in values)
    if not won:
        empty=sum(v==0 for row in board for v in row);limit=max_depth if empty>6 else max(max_depth,empty+int(state['swap_available']))
        for depth in range(1,limit+1):
            updated=[];heuristic_used=False;beam_used=False
            try:
                for a in legal:
                    budget.tick();after,result=child(board,root,a,state);value=100000 if result['done'] else -visit(after,3-root,result['state'],depth-1,-1000000,1000000)
                    updated.append({'action':a,'quality':[value]})
            except Exception as error:
                from .agents import Exhausted
                if not isinstance(error,Exhausted):raise
                break
            values=updated;reached=depth;exact=not heuristic_used and not beam_used
            if exact:break
    return values,{'method':'hex_connections_alpha_beta','depth':reached,'nodes':budget.nodes,'analysis_exact':exact,'optimal':exact or won,'immediate_win':won,'evaluation_scope':'exact_game_outcome' if exact else 'bounded_connections_search'}
