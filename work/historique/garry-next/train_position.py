"""Deterministic search distillation; game trajectories never cross the split."""
import argparse, json, random, time
from pathlib import Path
import numpy as np
from logic_arena.games import make_game
from logic_arena.agents import Budget
from logic_arena.connect4_wasm import _runtime, search
from logic_arena.value import features, default_head

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--games',type=int,default=600);ap.add_argument('--output',required=True)
    args=ap.parse_args();out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    rng=random.Random(312017);data=[];seen=set();started=time.monotonic()
    store,rt=_runtime()
    for episode in range(args.games):
        env=make_game('connect4',312017+episode)
        for ply in range(40):
            if env.done:break
            obs=env.observation();legal=env.legal_actions()
            # Same node/depth budget, no clock-dependent labels.
            action,info=search(obs,legal,Budget(80000,10000),max_depth=9)
            score=rt['getValue'](store)
            key=min(str(obs['board']),str([row[::-1] for row in obs['board']]))
            # The learned head evaluates calm horizons; mates stay symbolic.
            if ply>=4 and key not in seen and abs(score)<900000 and info['depth']>=6:
                seen.add(key);data.append({'x':features(obs).tolist(),'y':score,'group':episode,'obs':obs})
            env.step(rng.choice(legal) if rng.random()<.4 else action)
        if episode%10==0:
            (out/'status.json').write_text(json.dumps({'episode':episode,'samples':len(data),'seconds':time.monotonic()-started}))
    (out/'positions.json').write_text(json.dumps(data,separators=(',',':')))
    x=np.asarray([d['x'] for d in data]);y=np.asarray([d['y'] for d in data]);val=np.asarray([d['group']%5==0 for d in data]);base=np.asarray(default_head()['weights'])
    # Ridge toward the old evaluator. Hyperparameters use training groups only;
    # final validation games are excluded from fitting and tuning.
    train=~val;tune=np.asarray([d['group']%5==1 for d in data]);fit=train&~tune
    candidates=[]
    for ridge in (10,100,1000,10000):
        w=np.linalg.solve(x[fit].T@x[fit]+ridge*np.eye(32),x[fit].T@y[fit]+ridge*base)
        candidates.append((float(np.mean((x[tune]@w-y[tune])**2)),ridge))
    _,ridge=min(candidates)
    w=np.linalg.solve(x[train].T@x[train]+ridge*np.eye(32),x[train].T@y[train]+ridge*base)
    head=default_head();head.update(weights=w.tolist(),samples=int(train.sum()),revision='20261016-position-01',enabled=True)
    metrics={'train':int(train.sum()),'validation':int(val.sum()),'ridge':ridge,'baseline_rmse':float(np.sqrt(np.mean((x[val]@base-y[val])**2))),'candidate_rmse':float(np.sqrt(np.mean((x[val]@w-y[val])**2))),'seconds':time.monotonic()-started,'target':'depth-9 bounded search centipoints, non-mate positions','split':'whole game trajectories; held-out validation not used for tuning'}
    (out/'head.json').write_text(json.dumps(head));(out/'metrics.json').write_text(json.dumps(metrics,indent=2));(out/'status.json').write_text(json.dumps({'complete':True,**metrics}));print(json.dumps(metrics),flush=True)
if __name__=='__main__':main()
