import sys,time,random,json
from pathlib import Path
sys.path.insert(0,r'C:\Users\gabor\code\playi')
import wasmtime
from logic_arena.games import make_game
from tests.test_deep import oracle,winner
path=Path(__file__).parent
engine=wasmtime.Engine();store=wasmtime.Store(engine);module=wasmtime.Module.from_file(engine,str(path/'candidate.wasm'))
imports={'now':wasmtime.Func(store,wasmtime.FuncType([], [wasmtime.ValType.f64()]),lambda:time.monotonic()*1000),'abort':wasmtime.Func(store,wasmtime.FuncType([wasmtime.ValType.i32()]*4,[]),lambda *a:None)}
rt=wasmtime.Instance(store,module,[imports[i.name] for i in module.imports]).exports(store)
rng=random.Random(170017);checked=0;states={}
for seed in range(1000):
    env=make_game('connect4',seed)
    for ply in range(28+seed%7):
        b=tuple(v for row in env.board for v in row);options=[]
        for a in env.legal_actions():
            c=a['column'];r=max(r for r in range(6) if not b[r*7+c]);child=b[:r*7+c]+(env.current_player,)+b[r*7+c+1:]
            if not winner(child,env.current_player):options.append(a)
        if not options:break
        env.step(rng.choice(options))
    if env.moves<28:continue
    b=tuple(v for row in env.board for v in row);p=env.current_player;expected=oracle(b,p);bits=[0,0,0]
    for r,row in enumerate(env.board):
        for c,v in enumerate(row):
            if v:bits[v]|=1<<(c*7+5-r)
    c=rt['certify'](store,bits[1],bits[2],p,10000000,5000.);state=rt['getProofState'](store)
    assert state in (1,2,3,4),(state,seed)
    assert {2:1,3:0,4:-1}.get(state,expected)==expected,(seed,expected,state)
    env.step({'column':c});actual=1 if env.winner==p else 0 if env.winner==0 else -oracle(tuple(v for row in env.board for v in row),env.current_player)
    assert actual==expected,(seed,actual,expected,state)
    states[state]=states.get(state,0)+1;checked+=1
    if checked==200:break
assert checked==200
print(json.dumps({'checked':checked,'states':states,'independent_oracle':True}),flush=True)
