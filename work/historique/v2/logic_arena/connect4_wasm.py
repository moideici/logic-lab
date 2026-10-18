"""Même binaire de recherche dans Python et le navigateur ; état par thread."""
from functools import lru_cache
from pathlib import Path
import threading
import time

CONNECT_LIMITS = (64,256,1024,4096,20000,100000,500000,2000000,10000000,30000000)
CONNECT_TIMES = (1,2,4,8,16,30,60,100,180,300)
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
            raise RuntimeError('Erreur du moteur BASTION')
        stop = wasmtime.Func(store, wasmtime.FuncType([wasmtime.ValType.i32()]*4, []), abort)
        imports = {'now': clock, 'abort': stop}
        instance = wasmtime.Instance(store, module, [imports[item.name] for item in module.imports])
        _LOCAL.runtime = store, instance.exports(store)
    return _LOCAL.runtime


def search(obs, legal, budget, logits=None, weights=None, max_depth=40):
    try:
        store, runtime = _runtime()
    except ImportError:
        from .connect4 import search as fallback
        action, info = fallback(obs, legal, budget, logits, weights, max_depth)
        return action, {**info, 'runtime': 'python'}
    bits = [0, 0, 0]
    for r, row in enumerate(obs['board']):
        for c, player in enumerate(row):
            if player:
                bits[player] |= 1 << (c*7+5-r)
    order = sorted([3,2,4,1,5,0,6], key=lambda c: float(logits[c]) if logits is not None else -abs(c-3), reverse=True)
    for rank, column in enumerate(order):
        runtime['setPrior'](store, column, 7-rank)
    remaining_ms = max(0, (budget.deadline-time.monotonic())*1000)
    column = runtime['decide'](store, bits[1], bits[2], obs['current_player'], max(0,budget.limit-budget.nodes), remaining_ms, max_depth)
    budget.nodes += runtime['getNodes'](store)
    depth, value = runtime['getDepth'](store), runtime['getValue'](store)
    action = {'column': column}
    if action not in legal:
        raise RuntimeError('Décision BASTION illégale')
    tactical = value in (999999, 999997) and depth == 0
    info = {'method': ('tactical_win' if value == 999999 else 'tactical_fork') if tactical else 'bitboard_alpha_beta',
            'runtime': 'wasm', 'nodes': budget.nodes, 'depth': depth, 'forced_win': value > 999957,
            'forced_loss': value < -999957, 'optimal': tactical}
    if tactical:
        info['remaining_moves'] = 1000000-value
    return action, info
