"""Adapter un mode de Garry en gelant exactement les poids des autres modes."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from logic_arena.general import GarryPolicy,GAMES,INPUT_OFFSETS,OUTPUT_OFFSETS,FEATURES
from logic_arena.neural import SPECS
from logic_arena.evaluation import evaluate
from examples.train_garry_curriculum import dataset,nll,atomic_json


def fit_guarded_epoch(model,game,x,y,masks,lr,rng):
    # Les gradients privés restent appris ; les poids centraux et leur compteur
    # sont restaurés après chaque minibatch, avant le calcul du gradient suivant.
    if not np.all(x[:,FEATURES+GAMES.index(game)]==1):raise ValueError('Mélange de jeux dans un lot protégé')
    shared=(model.b1.copy(),model.core['w'].copy(),model.core['b'].copy(),model.core['steps'])
    order=rng.permutation(len(x));loss=0.
    for start in range(0,len(x),64):
        at=order[start:start+64]
        loss+=model.fit(x[at],y[at],masks[at],epochs=1,batch_size=64,lr=lr)[0]*len(at)
        model.b1[:]=shared[0];model.core['w'][:]=shared[1];model.core['b'][:]=shared[2];model.core['steps']=shared[3]
    return loss/len(x)


def protected_weights_equal(before,after,game):
    i=GAMES.index(game);a=INPUT_OFFSETS[game];b=OUTPUT_OFFSETS[game];ni,no=SPECS[game]
    rows=np.ones(before.w1.shape[0],dtype=bool);rows[a:a+ni]=False;rows[FEATURES+i]=False
    cols=np.ones(before.w2.shape[1],dtype=bool);cols[b:b+no]=False
    return all((np.array_equal(before.w1[rows],after.w1[rows]),np.array_equal(before.w2[:,cols],after.w2[:,cols]),
                np.array_equal(before.b2[cols],after.b2[cols]),np.array_equal(before.b1,after.b1),
                np.array_equal(before.core['w'],after.core['w']),np.array_equal(before.core['b'],after.core['b'])))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--game',choices=GAMES,default='connect4')
    p.add_argument('--epochs',type=int,default=40)
    args=p.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    started=time.monotonic();source=Path('web/models/garry.json')
    baseline=GarryPolicy.load(source);candidate=GarryPolicy.load(source);candidate.rng=np.random.default_rng(57721)
    baseline.save(args.output/'before.json');archive=np.load(args.dataset)
    x,y,masks=(archive[f'{args.game}_{key}'] for key in ('x','y','mask'))
    validation,_=dataset(baseline,128,1618033,lambda *a:None,split='validation')
    training_rows={row.tobytes() for row in x}
    fresh=np.array([row.tobytes() not in training_rows for row in validation[args.game][0]])
    local={args.game:tuple(part[fresh] for part in validation[args.game])}
    if int(fresh.sum())<32:raise RuntimeError('Pas assez de positions de validation inédites')
    score=nll(candidate,local)[args.game]['nll'];best=score;best_epoch=0;history=[]
    candidate.save(args.output/'best.json')
    for epoch in range(1,args.epochs+1):
        loss=fit_guarded_epoch(candidate,args.game,x,y,masks,.0001,candidate.rng)
        metric=nll(candidate,local)[args.game]
        if metric['nll']<best:
            best=metric['nll'];best_epoch=epoch;candidate.save(args.output/'best.json')
        if not protected_weights_equal(baseline,candidate,args.game):raise RuntimeError('Poids protégés modifiés')
        history.append({'epoch':epoch,'training_loss':loss,'validation':metric})
        atomic_json(args.output/'status.json',{'state':'training','epoch':epoch,'best_epoch':best_epoch,'protected_weights_equal':True,'history':history})
        print(f'Époque {epoch}/{args.epochs}, validation={metric["nll"]:.4f}',flush=True)
    best_model=GarryPolicy.load(args.output/'best.json')
    before=evaluate(baseline.for_game(args.game),200,9100000,max_steps=250,planning=False)
    after=evaluate(best_model.for_game(args.game),200,9100000,max_steps=250,planning=False)
    report={'game':args.game,'software_version':'3.1.0','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'best_epoch':best_epoch,'before_validation_nll':score,'after_validation_nll':best,'validation_samples':int(fresh.sum()),
            'validation_overlap':0,'before':before,'after':after,
            'protected_weights_equal':protected_weights_equal(baseline,best_model,args.game),'active_model_replaced':False,
            'elapsed_seconds':round(time.monotonic()-started,1)}
    atomic_json(args.output/'report.json',report);atomic_json(args.output/'status.json',{'state':'completed',**report})
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':main()
