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
    from .quality import select_quality, sudoku_values
    from .agents import Budget, ReferenceAgent
    from .neural import SPECS
    game=obs['game'];logits=model.logits(obs) if logits is None else logits
    budget_ms=TIMES[-1] if time_ms is None else time_ms
    budget=Budget(LIMITS[-1],budget_ms);info={}
    if game=='tictactoe':
        board=tuple(v for row in obs['board'] for v in row);values=[]
        for a in legal:
            i=a['row']*3+a['col'];v,n=_ttt_value(board[:i]+(obs['current_player'],)+board[i+1:],3-obs['current_player']);v=-v;n+=1
            values.append({'action':a,'quality':[v,n if v==-1 else -n],'outcome':v,'remaining_moves':n})
        info={'method':'exact_minimax_distance','optimal':True,'analysis_exact':True}
    elif game=='sliding_puzzle':
        r,c=next((r,c) for r in range(3) for c in range(3) if not obs['board'][r][c]);values=[]
        for a in legal:
            dr,dc={'up':(-1,0),'down':(1,0),'left':(0,-1),'right':(0,1)}[a['direction']];b=[row[:] for row in obs['board']];b[r][c],b[r+dr][c+dc]=b[r+dr][c+dc],0;d=sliding_distance(b)
            values.append({'action':a,'quality':[-d if d!=255 else -1000],'remaining_moves':d+1})
        info={'method':'exact_shortest_path','optimal':sliding_distance(obs['board'])!=255,'analysis_exact':True,'solution_found':True}
    elif game=='connect4':
        from .connect4_wasm import search,CONNECT_LIMITS,CONNECT_TIMES
        _,info=search(obs,legal,Budget(CONNECT_LIMITS[-1],CONNECT_TIMES[-1] if time_ms is None else time_ms),logits=logits,analyze=True,position_head=getattr(model,'position_head',None))
        values=info.pop('action_values')
    elif game=='2048':
        from .tiles import search
        _,info=search(obs,legal,logits,budget,max_depth=2,critical_depth=3);values=info.pop('action_values')
    elif game=='sudoku':values,info=sudoku_values(obs,legal,logits,budget)
    elif game=='minesweeper':
        agent=ReferenceAgent(10,time_ms=budget_ms);agent.mines(obs,legal,budget,fallback);values=agent._mine_values
        info={'method':'public_constraints_ranking','optimal':False,'nodes':budget.nodes}
    else:return fallback,{}
    selected,ranking=select_quality(values,level,logits,game)
    extra={k:v for k,v in selected.items() if k not in ('action','quality')}
    if game=='connect4':
        v=selected['quality'][0];extra.update(value=v,forced_win=v>999957,forced_loss=v< -999957,remaining_moves=1000000-abs(v) if abs(v)>999957 else None)
        info['optimal']=v in (999999,999997) or info.get('optimal',False)
    return selected['action'],{'agent':'neural+planner',**info,**extra,**ranking,'optimal':ranking['selected_is_best'] and info.get('optimal',False),
                              'evaluation_scope':'exact_legal_move_values' if info.get('analysis_exact') else info.get('evaluation_scope','bounded_public_analysis'),'objective':'win_then_fewest_moves'}
