"""Quality quantiles: same analysis budget at every difficulty level."""
import math
from .games import sudoku_candidates
from .neural import action_index

def select_quality(values,level,logits,game):
    if type(level) is not int or not 0<=level<=10:raise ValueError('Le niveau doit être un entier de 0 à 10')
    if not values:raise ValueError('Aucun coup évalué')
    ordered=sorted(values,key=lambda v:(tuple(v['quality']),float(logits[action_index(game,v['action'])])))
    rank=math.floor(level*(len(ordered)-1)/10+.5);selected=ordered[rank]
    return selected,{'level':level,'quality_rank':rank,'legal_count':len(ordered),'quality':selected['quality'],
                     'selected_is_best':selected['quality']==ordered[-1]['quality'],'selected_is_worst':selected['quality']==ordered[0]['quality'],
                     'level_semantics':'legal_move_quality_quantile'}

_SUDOKU={}
def sudoku_values(obs,legal,logits,budget):
    from .agents import Exhausted
    key=tuple(tuple(r) for r in obs['board']);result=_SUDOKU.get(key)
    if result is None:
        from .sudoku_rules import solve_sudoku
        solutions,complete=solve_sudoku(obs['board'],tick=budget.tick)
        result=solutions,complete,complete and len(solutions)==1
        if complete:
            if len(_SUDOKU)>1000:_SUDOKU.clear()
            _SUDOKU[key]=result
    solutions,complete,unique=result;unsat=complete and not solutions;values=[]
    for a in legal:
        q=0;proved=False
        if a.get('undo'):q=2 if unsat else -1;proved=bool(unsat or solutions)
        elif any(b[a['row']][a['col']]==a['value'] for b in solutions):q=1;proved=True
        elif unique or unsat:q=-2;proved=True
        else:
            b=[r[:] for r in obs['board']];b[a['row']][a['col']]=a['value']
            if any(not b[r][c] and not sudoku_candidates(b,r,c) for r in range(9) for c in range(9)):q=-2;proved=True
        values.append({'action':a,'quality':[q],'proved':proved})
    return values,{'method':'sudoku_completion_ranking','optimal':bool(solutions),'analysis_exact':bool(unique or unsat),'nodes':budget.nodes,'solution_found':bool(solutions),'unique_solution':unique,'remaining_moves':sum(v==0 for r in obs['board'] for v in r)}
