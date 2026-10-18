"""Un seul algorithme de recherche, guidé par le réseau, pour sudoku et taquin."""
import heapq
import itertools
import json
import time
import base64
from functools import lru_cache
from pathlib import Path

from .neural import action_index
from .games import sudoku_candidates

LIMITS = (16,50,150,500,1500,4000,10000,25000,50000,100000)
TIMES = (.5,1,2,3,5,8,12,16,22,30)
_PATHS = {}
_FACT = (1,1,2,6,24,120,720,5040,40320)


@lru_cache(maxsize=1)
def _sliding_table():
    path=Path(__file__).resolve().parents[1]/"web"/"models"/"sliding-distances.json"
    return base64.b64decode(json.loads(path.read_text())["data"])


def sliding_distance(board):
    b=tuple(v for row in board for v in row)
    rank=sum(sum(v<b[i] for v in b[i+1:])*_FACT[8-i] for i in range(8))
    return _sliding_table()[rank]


_LINES=((0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6))


def _ttt_key(value):
    outcome,plies=value
    return outcome, plies if outcome==-1 else -plies


@lru_cache(maxsize=6000)
def _ttt_value(board,player):
    if any(all(board[i]==3-player for i in line) for line in _LINES):return -1,0
    free=[i for i,v in enumerate(board) if not v]
    if not free:return 0,0
    values=[]
    for i in free:
        value,plies=_ttt_value(board[:i]+(player,)+board[i+1:],3-player)
        values.append((-value,plies+1))
    return max(values,key=_ttt_key)


def _board_key(obs):
    return tuple(tuple(row) for row in obs["board"])


def plan(obs, legal, model, level, fallback, time_ms=None, logits=None):
    game = obs["game"]
    started = time.monotonic()
    budget_ms = TIMES[level-1] if time_ms is None else time_ms
    deadline = started+budget_ms/1000
    if logits is None:
        logits = model.logits(obs)
    if game=="tictactoe":
        board=tuple(v for row in obs["board"] for v in row)
        options=[]
        for a in legal:
            i=a["row"]*3+a["col"]
            value,plies=_ttt_value(board[:i]+(obs["current_player"],)+board[i+1:],3-obs["current_player"])
            options.append(((-value,plies+1),float(logits[i]),a))
        value,_,action=max(options,key=lambda p:(_ttt_key(p[0]),p[1]))
        return action,{"agent":"neural+planner","method":"exact_minimax_distance","optimal":True,
                       "outcome":value[0],"remaining_moves":value[1],"objective":"win_then_fewest_moves"}
    if game=="sliding_puzzle":
        distance=sliding_distance(obs["board"])
        r,c=next((r,c) for r in range(3) for c in range(3) if not obs["board"][r][c])
        options=[]
        for a in legal:
            dr,dc={"up":(-1,0),"down":(1,0),"left":(0,-1),"right":(0,1)}[a["direction"]]
            b=[row[:] for row in obs["board"]]
            b[r][c],b[r+dr][c+dc]=b[r+dr][c+dc],0
            if sliding_distance(b)==distance-1:options.append(a)
        action=max(options,key=lambda a:logits[action_index(game,a)]) if options else fallback
        return action,{"agent":"neural+planner","method":"exact_shortest_path","optimal":distance!=255,
                       "remaining_moves":distance,"nodes":len(legal),"solution_found":bool(options),"objective":"win_then_fewest_moves"}
    if game=="2048":
        from .agents import Budget
        from .tiles import search
        action,info=search(obs,legal,logits,Budget(LIMITS[level-1],budget_ms),max_depth=2 if level>=8 else 1,critical_depth=3 if level>=9 else None)
        return action,{"agent":"neural+planner","objective":"win_then_fewest_moves",**info}
    if game=="connect4":
        from .agents import Budget
        from .connect4 import search
        action,info=search(obs,legal,Budget(LIMITS[level-1],budget_ms),logits=logits)
        return action,{"agent":"neural+planner","objective":"win_then_fewest_moves",**info}
    if game=="minesweeper":
        from .agents import Budget, ReferenceAgent
        agent=ReferenceAgent(level,time_ms=budget_ms)
        budget=Budget(LIMITS[level-1],budget_ms)
        ordered=sorted(legal,key=lambda a:-logits[action_index(game,a)])
        solver={"connect4":agent.line_game,"minesweeper":agent.mines}[game]
        action=solver(obs,ordered,budget,fallback)
        return action,{"agent":"neural+planner","method":{"connect4":"neural_alpha_beta","2048":"neural_expectimax","minesweeper":"public_constraints_flood"}[game],
                       "optimal":False,"nodes":budget.nodes,"objective":"win_then_fewest_moves"}
    if game!="sudoku":return fallback,{}
    cache=_PATHS.get(_board_key(obs))
    if cache and cache[0] in legal:
        return cache[0],{"agent":"neural+planner","method":"shared_search_cached","optimal":True,"remaining_moves":cache[1],"nodes":0,"solution_found":True}

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
    queue=[(distance(obs["board"]),next(serial),0,obs["board"],None,[])]
    seen={json.dumps(obs["board"]):0}
    best,best_h,nodes,solved=fallback,distance(obs["board"]),0,False
    while queue and nodes<LIMITS[level-1] and time.monotonic()<deadline:
        _,_,cost,board,first,path=heapq.heappop(queue)
        nodes+=1
        h=distance(board)
        if first and h<best_h:
            best,best_h=first,h
        if not h:
            solved=True;best=first or best
            if len(_PATHS)>5000:_PATHS.clear()
            for i,(state,action) in enumerate(path):_PATHS[tuple(tuple(row) for row in state)]=(action,len(path)-i)
            break
        moves=children(board)
        if len(moves)>1:
            branch_logits=logits if cost==0 else model.logits({**obs,"board":board})
            moves.sort(key=lambda p:-branch_logits[action_index(game,p[0])])
        for i,(action,b) in enumerate(moves):
            key=json.dumps(b)
            if cost+1>=seen.get(key,float("inf")):continue
            seen[key]=cost+1
            priority=distance(b)+(0 if game=="sudoku" else cost+1)+i*.001
            heapq.heappush(queue,(priority,next(serial),cost+1,b,first or action,path+[(board,action)]))
    if not solved and not queue and {"undo":True} in legal:best={"undo":True}
    return best,{"agent":"neural+planner","method":"shared_best_first","nodes":nodes,"node_limit":LIMITS[level-1],
                 "budget_ms":budget_ms,"planning_ms":(time.monotonic()-started)*1000,"solution_found":solved,
                 "optimal":solved,"remaining_moves":distance(obs["board"]) if solved else None,"objective":"win_then_fewest_moves"}
