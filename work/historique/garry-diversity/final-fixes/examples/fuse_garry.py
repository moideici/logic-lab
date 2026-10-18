"""Fusion algébrique des six politiques : aucune réinitialisation des savoirs."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from logic_arena.general import GarryPolicy, INPUT, OUTPUT
from logic_arena.neural import NeuralPolicy, SPECS
from logic_arena.games import make_game


def main():
    root=Path(__file__).resolve().parents[1]
    p=argparse.ArgumentParser()
    p.add_argument('--source',type=Path,default=root/'versions'/'1.0.0'/'web'/'models')
    p.add_argument('--output',type=Path,default=root/'web'/'models'/'garry.json')
    args=p.parse_args()
    models={g:NeuralPolicy.load(args.source/f'{g}.json') for g in SPECS}
    general=GarryPolicy.fuse(models)
    report={'name':'garry','version':'3.1.0','architecture':[INPUT,general.hidden,general.hidden,OUTPUT],
            'method':'algebraic_weight_fusion','training_performed':False,'games':{}}
    for g,old in models.items():
        max_error=0.;samples=0;equal_choices=0
        for seed in range(1500000,1500010):
            env=make_game(g,seed)
            for _ in range(30):
                if env.done:break
                obs=env.observation();legal=env.legal_actions()
                a,b=old.logits(obs),general.for_game(g).logits(obs)
                error=float(np.max(np.abs(a-b)));max_error=max(max_error,error)
                np.testing.assert_allclose(a,b,atol=3e-5,rtol=1e-5)
                samples+=1;equal_choices+=old.choose(obs,legal)==general.for_game(g).choose(obs,legal)
                env.step(env.rng.choice(legal))
        report['games'][g]={'samples':samples,'max_logit_error':max_error,'same_greedy_actions':equal_choices}
    general.save(args.output)
    args.output.with_name('garry-fusion.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
