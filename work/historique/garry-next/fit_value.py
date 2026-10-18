"""Refit from saved trajectories, enforce reflection symmetry by construction."""
import argparse,json
from pathlib import Path
import numpy as np
from logic_arena.value import default_head

def fit(data):
    x=np.asarray([d['x'] for d in data]);y=np.asarray([d['y'] for d in data]);val=np.asarray([d['group']%5==0 for d in data]);base=np.asarray(default_head()['weights'])
    diag=(x[:,12:18]+x[:,18:24])/2;x[:,12:18]=diag;x[:,18:24]=diag
    train=~val;tune=np.asarray([d['group']%5==1 for d in data]);subset=train&~tune;candidates=[]
    for ridge in (10,100,1000,10000):
        w=np.linalg.solve(x[subset].T@x[subset]+ridge*np.eye(32),x[subset].T@y[subset]+ridge*base)
        candidates.append((float(np.mean((x[tune]@w-y[tune])**2)),ridge))
    _,ridge=min(candidates);w=np.linalg.solve(x[train].T@x[train]+ridge*np.eye(32),x[train].T@y[train]+ridge*base)
    # Avoid sub-ULP asymmetry caused by solving the linear system.
    diagonal=(w[12:18]+w[18:24])/2;w[12:18]=diagonal;w[18:24]=diagonal
    head=default_head();head.update(weights=w.tolist(),samples=int(train.sum()),revision='20261016-position-02',enabled=True)
    metrics={'train':int(train.sum()),'validation':int(val.sum()),'ridge':ridge,'baseline_rmse':float(np.sqrt(np.mean((x[val]@base-y[val])**2))),'candidate_rmse':float(np.sqrt(np.mean((x[val]@w-y[val])**2))),'target':'depth-9 bounded search centipoints, non-mate positions','split':'whole game trajectories; validation not used for fitting or hyperparameters','reflection_invariant':True}
    return head,metrics
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('run');args=ap.parse_args();out=Path(args.run)
    head,metrics=fit(json.loads((out/'positions.json').read_text()))
    (out/'head.json').write_text(json.dumps(head));(out/'metrics.json').write_text(json.dumps(metrics,indent=2));print(json.dumps(metrics))
