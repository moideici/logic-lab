"""Même binaire de recherche dans Python et le navigateur ; état par thread."""
from functools import lru_cache
from pathlib import Path
import threading
import time
from .search_memory import lookup_memory,memory_decision

CONNECT_LIMITS = (64,256,1024,4096,20000,100000,500000,2000000,10000000,200000000)
CONNECT_TIMES = (1,2,4,8,16,30,60,100,180,2000)
_LOCAL = threading.local()


@lru_cache(maxsize=1)
def _compiled():
    import wasmtime
    engine = wasmtime.Engine()
    module = wasmtime.Module.from_file(engine, str(Path(__file__).resolve().parents[1] / 'web' / 'connect4-search.wasm'))
    return engine, module


def _runtime():
    import wasmtime
    if not hasattr(_LOCAL, 'runtime'):
        engine, module = _compiled()
        store = wasmtime.Store(engine)
        clock = wasmtime.Func(store, wasmtime.FuncType([], [wasmtime.ValType.f64()]), lambda: time.monotonic()*1000)
        def abort(*args):
            raise RuntimeError('Erreur du moteur Garry')
        stop = wasmtime.Func(store, wasmtime.FuncType([wasmtime.ValType.i32()]*4, []), abort)
        imports = {'now': clock, 'abort': stop}
        instance = wasmtime.Instance(store, module, [imports[item.name] for item in module.imports])
        _LOCAL.runtime = store, instance.exports(store)
    return _LOCAL.runtime


def search(obs, legal, budget, logits=None, weights=None, max_depth=40, analyze=False, position_head=None,search_memory=None):
    if not analyze:
        entry=lookup_memory(obs,legal,search_memory)
        if entry is not None:return memory_decision(entry,42-sum(bool(v) for row in obs['board'] for v in row))
    try:
        store, runtime = _runtime()
    except ImportError:
        from .connect4 import search as fallback
        if analyze:return _fallback_analysis(obs,legal,budget,logits,weights,max_depth)
        action, info = fallback(obs, legal, budget, logits, weights, max_depth)
        return action, {**info, 'runtime': 'python'}
    runtime['enableValue'](store, int(bool(position_head and position_head.get('enabled'))))
    if position_head and position_head.get('enabled'):
        for i,value in enumerate(position_head['weights']):runtime['setValueWeight'](store,i,float(value))
    bits = [0, 0, 0]
    for r, row in enumerate(obs['board']):
        for c, player in enumerate(row):
            if player:
                bits[player] |= 1 << (c*7+5-r)
    order = sorted([3,2,4,1,5,0,6], key=lambda c: float(logits[c]) if logits is not None else -abs(c-3), reverse=True)
    for rank, column in enumerate(order):
        runtime['setPrior'](store, column, 7-rank)
    remaining_ms = max(0., (budget.deadline-time.monotonic())*1000)
    column = runtime['analyze' if analyze else 'decideVerified'](store, bits[1], bits[2], obs['current_player'], max(0,budget.limit-budget.nodes), remaining_ms, max_depth)
    budget.nodes += runtime['getNodes'](store)
    depth, value = runtime['getDepth'](store), runtime['getValue'](store)
    action = {'column': column}
    if action not in legal:
        raise RuntimeError('Décision Garry illégale')
    certificate=0 if analyze else runtime['getProofState'](store)
    tactical = not certificate and value in (999999, 999997)
    remaining=42-sum(bool(v) for r in obs['board'] for v in r)
    proof='win' if value>999957 else 'loss' if value< -999957 else 'draw' if certificate==3 else 'non_loss' if certificate==1 else 'draw' if depth>=remaining else None
    exact_outcome=certificate>=2 or abs(value)>999957 or depth>=remaining;certified_non_loss=1<=certificate<=3 or value>999957 or proof=='draw'
    count=runtime['traceProof' if 0<certificate<4 else 'trace'](store,bits[1],bits[2],obs['current_player'],column,remaining if certificate else max(depth,1))
    principal=[runtime['getPrincipal'](store,i) for i in range(count)]
    info = {'method': 'exact_wdl_search' if certificate else ('tactical_win' if value == 999999 else 'tactical_fork') if tactical else 'bitboard_alpha_beta',
            'runtime': 'wasm', 'principal_variation':principal,'proof':proof,'search_complete':proof is not None and proof!='non_loss','outcome_proven':exact_outcome,'certified_non_loss':certified_non_loss,'certificate_nodes':0 if analyze else runtime['getProofNodes'](store),'solved_horizon':remaining if exact_outcome else None,'mate_distance_known':not bool(certificate) and abs(value)>999957,'value':value,'learned_value':bool(position_head and position_head.get('enabled')),'evaluation_scope':'exact_game_outcome' if exact_outcome else 'certified_non_loss' if certified_non_loss else 'bounded_adversarial_search','nodes': budget.nodes, 'depth': depth, 'forced_win': value > 999957,
            'forced_loss': value < -999957, 'optimal': not certificate and (tactical or value>999957 or depth>=remaining),'outcome_optimal':exact_outcome}
    if tactical:
        info['remaining_moves'] = 1000000-value
    if analyze:info['action_values']=[{'action':a,'quality':[runtime['getScore'](store,a['column'])]} for a in legal]
    return action, info


def _fallback_analysis(obs,legal,budget,logits,weights,max_depth):
    from .connect4 import search, _won
    from .agents import Budget
    values=[]
    for a in legal:
        board=[row[:] for row in obs['board']];c=a['column'];r=max(r for r in range(6) if not board[r][c]);board[r][c]=obs['current_player']
        mine=sum(1<<(c*7+5-r) for r in range(6) for c in range(7) if board[r][c]==obs['current_player'])
        if _won(mine):value=999999
        else:
            children=[{'column':c} for c in range(7) if not board[0][c]]
            if not children:value=0
            else:
                child={**obs,'board':board,'current_player':3-obs['current_player']}
                local=Budget(max(1,(budget.limit-budget.nodes)//len(legal)),max(.1,(budget.deadline-time.monotonic())*1000/len(legal)))
                _,info=search(child,children,local,None,weights,max_depth);budget.nodes+=local.nodes
                value=-(1000000-info['remaining_moves'] if info.get('optimal') and info.get('remaining_moves') else info.get('value',0))
        values.append({'action':a,'quality':[value]})
    best=max(values,key=lambda v:(v['quality'],float(logits[v['action']['column']]) if logits is not None else 0))
    return best['action'],{'runtime':'python','method':'python_root_analysis','nodes':budget.nodes,'optimal':best['quality']==[999999],'action_values':values,'evaluation_scope':'bounded_adversarial_search'}
