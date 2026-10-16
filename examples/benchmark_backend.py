"""Mesure 2048 Python et compare éventuellement un ancien checkout local.

Exemple : python examples/benchmark_backend.py --episodes 5 --seed 42
         --baseline /tmp/ancien-code --output web/models/backend-evaluation.json
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

EXPERIMENT = r'''
import json,sys,time
from logic_arena.games import make_game
from logic_arena.neural import NeuralAgent
args=json.loads(sys.argv[1]);samples=[]
for i in range(args['episodes']):
    env=make_game('2048',args['seed']+i);agent=NeuralAgent(level=10)
    started=time.perf_counter()
    while not env.done and env.moves<2500:
        env.step(agent.choose(env.observation(),env.legal_actions()).action)
    samples.append({'seed':args['seed']+i,'winner':env.winner,'moves':env.moves,
                    'max_tile':max(map(max,env.board)),'ms':(time.perf_counter()-started)*1000})
elapsed=sum(s['ms'] for s in samples);moves=sum(s['moves'] for s in samples)
print(json.dumps({'episodes':len(samples),'wins':sum(s['winner']==1 for s in samples),
    'mean_ms':elapsed/len(samples),'mean_moves':moves/len(samples),
    'ms_per_move':elapsed/max(1,moves),'samples':samples}))
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--episodes',type=int,default=5)
    parser.add_argument('--seed',type=int,default=42)
    parser.add_argument('--baseline',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if not 1<=args.episodes<=1000:
        parser.error('episodes doit être entre 1 et 1000')
    root=Path(__file__).resolve().parents[1]
    variants={'current':root}
    if args.baseline is not None:
        variants={'baseline':args.baseline.resolve(),**variants}
    report={'game':'2048','level':10,'teacher_used':False,'episodes':args.episodes,
            'seed':args.seed,'runtime':sys.version.split()[0],
            'note':'Petit échantillon local. Les recherches ont un budget mural de 30 ms ; les résultats dépendent de la machine.',
            'variants':{}}
    for label,directory in variants.items():
        command=subprocess.run([sys.executable,'-c',EXPERIMENT,json.dumps({'episodes':args.episodes,'seed':args.seed})],
            cwd=directory,capture_output=True,text=True,check=True,
            env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1'))
        report['variants'][label]=json.loads(command.stdout)
        print(label,json.dumps({k:v for k,v in report['variants'][label].items() if k!='samples'}),flush=True)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2),encoding='utf-8')


if __name__=='__main__':
    main()
