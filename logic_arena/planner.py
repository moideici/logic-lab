"""Un seul algorithme de recherche, guidé par le réseau, pour sudoku et taquin."""
import heapq
import itertools
import json
import time

from .neural import action_index
from .games import sudoku_candidates

LIMITS = (8,20,50,100,250,600,1500,4000,10000,25000)
TIMES = (1,2,4,7,12,20,35,55,90,150)


def plan(obs, legal, model, level, fallback, time_ms=None):
    game = obs["game"]
    if game not in ("sudoku", "sliding_puzzle"):
        return fallback, {}
    started = time.monotonic()
    budget_ms = TIMES[level-1] if time_ms is None else time_ms
    deadline = started+budget_ms/1000

    def distance(board):
        if game == "sudoku":
            return sum(v == 0 for row in board for v in row)
        return sum(abs(r-(v-1)//3)+abs(c-(v-1)%3) for r,row in enumerate(board) for c,v in enumerate(row) if v)

    def children(board):
        if game == "sudoku":
            cells = [(sudoku_candidates(board,r,c),r,c) for r in range(9) for c in range(9) if not board[r][c]]
            if not cells:return []
            vals,r,c = min(cells,key=lambda x:len(x[0]))
            out=[]
            for value in vals:
                b=[row[:] for row in board];b[r][c]=value
                out.append(({"row":r,"col":c,"value":value},b))
            return out
        r,c=next((r,c) for r in range(3) for c in range(3) if not board[r][c])
        out=[]
        for d,dr,dc in (("up",-1,0),("down",1,0),("left",0,-1),("right",0,1)):
            if 0<=r+dr<3 and 0<=c+dc<3:
                b=[row[:] for row in board];b[r][c],b[r+dr][c+dc]=b[r+dr][c+dc],0
                out.append(({"direction":d},b))
        return out

    serial=itertools.count()
    queue=[(distance(obs["board"]),next(serial),0,obs["board"],None)]
    seen={json.dumps(obs["board"]):0}
    best,best_h,nodes,solved=fallback,distance(obs["board"]),0,False
    while queue and nodes<LIMITS[level-1] and time.monotonic()<deadline:
        _,_,cost,board,first=heapq.heappop(queue)
        nodes+=1
        h=distance(board)
        if first and h<best_h:
            best,best_h=first,h
        if not h:
            solved=True;best=first or best;break
        moves=children(board)
        if len(moves)>1:
            logits=model.logits({**obs,"board":board})
            moves.sort(key=lambda p:-logits[action_index(game,p[0])])
        for i,(action,b) in enumerate(moves):
            key=json.dumps(b)
            if cost+1>=seen.get(key,float("inf")):continue
            seen[key]=cost+1
            priority=distance(b)+(0 if game=="sudoku" else cost+1)+i*.001
            heapq.heappush(queue,(priority,next(serial),cost+1,b,first or action))
    return best,{"agent":"neural+planner","method":"shared_best_first","nodes":nodes,"node_limit":LIMITS[level-1],
                 "budget_ms":budget_ms,"planning_ms":(time.monotonic()-started)*1000,"solution_found":solved}
