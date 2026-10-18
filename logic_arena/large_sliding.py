"""Budgeted A* using public board only; cache completed shortest paths."""
from heapq import heappop,heappush
from .puzzle_levels import manhattan
ROUTES={}
DIRS=(('up',-1,0),('down',1,0),('left',0,-1),('right',0,1))
def large_sliding_values(obs,legal,budget):
    n=len(obs['board']);start=tuple(v for row in obs['board'] for v in row);goal=tuple(range(1,n*n))+(0,);h0=manhattan(start,n);solution=ROUTES.get(start);path=None;found=solution is not None
    if solution is None:
        heap=[(h0,0,0,start)];cost={start:0};parent={start:None};serial=0;best=start;best_h=h0
        try:
            while heap:
                budget.tick();_,g,_,board=heappop(heap)
                if g!=cost.get(board):continue
                h=manhattan(board,n)
                if h<best_h:best=board;best_h=h
                if board==goal:best=board;found=True;break
                zero=board.index(0);r,c=divmod(zero,n)
                for d,dr,dc in DIRS:
                    if not (0<=r+dr<n and 0<=c+dc<n):continue
                    at=(r+dr)*n+c+dc;b=list(board);b[zero],b[at]=b[at],0;b=tuple(b)
                    if g+1>=cost.get(b,10**9):continue
                    cost[b]=g+1;parent[b]=(board,d);serial+=1;heappush(heap,(g+1+manhattan(b,n),g+1,serial,b))
        except Exception as error:
            from .agents import Exhausted
            if not isinstance(error,Exhausted):raise
        path=[];at=best
        while parent[at] is not None:prev,d=parent[at];path.append((prev,d));at=prev
        path.reverse();solution=[d for _,d in path] if found else None
        if found:
            if len(ROUTES)>20000:ROUTES.clear()
            for i,(board,_) in enumerate(path):ROUTES[board]=solution[i:]
    recommended=solution[0] if solution else path[0][1] if path else None;zero=start.index(0);r,c=divmod(zero,n);values=[]
    for a in legal:
        dr,dc=next((dr,dc) for d,dr,dc in DIRS if d==a['direction']);at=(r+dr)*n+c+dc;b=list(start);b[zero],b[at]=b[at],0
        values.append({'action':a,'quality':[int(a['direction']==recommended),-manhattan(b,n)]})
    return values,{'method':'public_astar_sliding','analysis_exact':False,'optimal':found,'solution_found':found,'remaining_moves':len(solution) if found else None,'lower_bound':h0,'nodes':budget.nodes,'evaluation_scope':'certified_shortest_path' if found else 'bounded_public_search'}
