"""Distill frozen 2.0 search into the compact position head; never auto-promote."""
import argparse,hashlib,json,random,time
from pathlib import Path
import wasmtime
from logic_arena.games import make_game
from logic_arena.value import features
from fit_garry_value import fit

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--games',type=int,default=1600);ap.add_argument('--output',required=True);ap.add_argument('--reuse',action='store_true')
    args=ap.parse_args()
    if args.games<10:ap.error('Au moins dix trajectoires pour la séparation des jeux')
    root=Path(__file__).resolve().parents[1];out=Path(args.output);out.mkdir(parents=True,exist_ok=True);started=time.monotonic()
    def save(name,data):
        temporary=out/(name+'.tmp');temporary.write_text(json.dumps(data,separators=(',',':')),encoding='utf-8');temporary.replace(out/name)
    binary=(root/'versions/2.0.0/connect4-search.wasm').read_bytes();sha=hashlib.sha256(binary).hexdigest()
    if args.reuse:data=json.loads((out/'positions.json').read_text())
    else:
        engine=wasmtime.Engine();store=wasmtime.Store(engine);module=wasmtime.Module(engine,binary)
        imports={'now':wasmtime.Func(store,wasmtime.FuncType([], [wasmtime.ValType.f64()]),lambda:time.monotonic()*1000),
                 'abort':wasmtime.Func(store,wasmtime.FuncType([wasmtime.ValType.i32()]*4,[]),lambda *a:(_ for _ in ()).throw(RuntimeError('WASM abort')))}
        rt=wasmtime.Instance(store,module,[imports[i.name] for i in module.imports]).exports(store)
        for rank,c in enumerate((3,2,4,1,5,0,6)):rt['setPrior'](store,c,7-rank)
        rng=random.Random(312017);data=[];seen=set()
        for episode in range(args.games):
            env=make_game('connect4',312017+episode)
            for ply in range(40):
                if env.done:break
                obs=env.observation();legal=env.legal_actions();bits=[0,0,0]
                for r,row in enumerate(obs['board']):
                    for c,p in enumerate(row):
                        if p:bits[p]|=1<<(c*7+5-r)
                c=rt['decide'](store,bits[1],bits[2],obs['current_player'],80000,10000.,9)
                score=rt['getValue'](store);depth=rt['getDepth'](store);key=min(str(obs['board']),str([r[::-1] for r in obs['board']]))
                if ply>=4 and key not in seen and abs(score)<900000 and depth>=6:
                    seen.add(key);data.append({'x':features(obs).tolist(),'y':score,'group':episode,'obs':obs})
                env.step(rng.choice(legal) if rng.random()<.4 else {'column':c})
            if episode%10==0:save('status.json',{'episode':episode,'samples':len(data),'seconds':time.monotonic()-started,'complete':False})
        save('positions.json',data)
    head,metrics=fit(data);metrics.update(teacher_sha256=sha,seconds=time.monotonic()-started,games=args.games,seed=312017)
    save('head.json',head);save('metrics.json',metrics);save('status.json',{'complete':True,**metrics});print(json.dumps(metrics),flush=True)
if __name__=='__main__':main()
