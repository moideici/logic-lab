"""Bounded adversarial search, including complete forced multi-captures."""
from copy import deepcopy
from .strategy_rules import legal_strategy,step_strategy,owner,new_state
def evaluate_strategy(name,board,player):
    score=0
    for r,row in enumerate(board):
        for c,v in enumerate(row):
            if not v:continue
            p=owner(v);advance=(len(board)-1-r) if p==1 else r
            value=(320 if v>2 else 100+advance*3)+min(c,len(board)-1-c)*2 if name=='draughts' else 100+advance*12+advance*advance*3
            score+=(1 if p==player else -1)*value
    return score
def strategy_values(obs,legal,budget,max_depth=6):
    name=obs['game'];root=obs['current_player'];state=obs.get('draughts_state') or new_state();all_exact=True
    def child(b,p,a,s):
        board=[r[:] for r in b];new=step_strategy(name,board,p,a,deepcopy(s));return board,new
    def terminal(result,p):return 0 if result['winner']==0 else 100000 if result['winner']==p else -100000
    def visit(b,p,s,depth,alpha,beta,ply=0):
        nonlocal all_exact
        budget.tick();actions=legal_strategy(name,b,p,s)
        if not actions:return -100000
        if depth<=0 and not s.get('forced_piece'):all_exact=False;return evaluate_strategy(name,b,p)
        # Try material gains and advancement first; every root move is scored.
        actions.sort(key=lambda a:(-int(bool(b[a['to'][0]][a['to'][1]])),-abs(a['to'][0]-a['from'][0])))
        best=-1000000
        for a in actions:
            after,result=child(b,p,a,s)
            if result['done']:value=terminal(result,p)
            elif result['player']==p:value=visit(after,p,result['state'],depth,alpha,beta,ply+1)
            else:value=-visit(after,3-p,result['state'],depth-1,-beta,-alpha,ply+1)
            best=max(best,value);alpha=max(alpha,value)
            if alpha>=beta:break
        return best
    values=[]
    for a in legal:
        after,result=child(obs['board'],root,a,state)
        values.append({'action':a,'quality':[terminal(result,root) if result['done'] else evaluate_strategy(name,after,root)]})
    reached=0;exact=False
    for depth in range(1,max_depth+1):
        updated=[];all_exact=True
        try:
            for a in legal:
                budget.tick();after,result=child(obs['board'],root,a,state)
                value=terminal(result,root) if result['done'] else visit(after,root,result['state'],depth,-1000000,1000000) if result['player']==root else -visit(after,3-root,result['state'],depth-1,-1000000,1000000)
                updated.append({'action':a,'quality':[value]})
        except Exception as error:
            from .agents import Exhausted
            if not isinstance(error,Exhausted):raise
            break
        values=updated;reached=depth;exact=all_exact
        if exact:break
    return values,{'method':name+'_alpha_beta','depth':reached,'nodes':budget.nodes,'analysis_exact':exact,'optimal':exact,'evaluation_scope':'exact_game_outcome' if exact else 'bounded_adversarial_search'}
