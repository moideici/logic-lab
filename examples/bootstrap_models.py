"""Génère les six modèles initiaux et un rapport d'apprentissage reproductible."""
import json
from functools import lru_cache
from pathlib import Path
import time

import numpy as np

from logic_arena.games import GAMES, make_game
from logic_arena.neural import NeuralPolicy, action_index, demonstration_data, encode


def ttt_data():
    wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]

    def terminal(b):
        return any(b[a] and b[a] == b[c] == b[d] for a,c,d in wins)

    @lru_cache(None)
    def value(b, player):
        if terminal(b):
            return -1
        free = [i for i,v in enumerate(b) if not v]
        if not free:
            return 0
        return max(-value(b[:i]+(player,)+b[i+1:], 3-player) for i in free)

    states = set()
    def visit(b, player):
        if (b,player) in states or terminal(b) or all(b):
            return
        states.add((b,player))
        for i,v in enumerate(b):
            if not v:
                visit(b[:i]+(player,)+b[i+1:],3-player)
    visit((0,)*9,1)
    x,y,masks=[],[],[]
    for b,p in sorted(states):
        free=[i for i,v in enumerate(b) if not v]
        # Choisir centre puis coins en cas d'égalité de valeur minimax.
        best=max(free,key=lambda i:(-value(b[:i]+(p,)+b[i+1:],3-p),i==4,i in (0,2,6,8),-i))
        obs={"game":"tictactoe","board":[list(b[i:i+3]) for i in (0,3,6)],"current_player":p}
        x.append(encode(obs));y.append(best)
        mask=np.zeros(9,dtype=bool);mask[free]=True;masks.append(mask)
    return np.array(x),np.array(y),np.array(masks)


def main():
    directory=Path(__file__).resolve().parents[1]/"web"/"models"
    directory.mkdir(parents=True,exist_ok=True)
    report={}
    datasets={}
    models={}
    core=None
    for game in GAMES:
        started=time.monotonic()
        print(f"collect {game}",flush=True)
        x,y,masks=ttt_data() if game=="tictactoe" else demonstration_data(game,episodes=35,seed=1234,max_steps=100,level=4)
        model=NeuralPolicy(game,seed=42,core=core)
        core=model.core
        datasets[game]=(x,y,masks)
        models[game]=model
        losses=model.fit(x,y,masks,epochs=60 if game=="tictactoe" else 20)
        report[game]={"samples":len(x),"epochs":len(losses),"training_steps":model.steps,"initial_loss":losses[0],"final_loss":losses[-1],"losses":losses,"seconds":round(time.monotonic()-started,2),"method":"imitation_minimax_exhaustive" if game=="tictactoe" else "imitation_reference","evaluation":"training_loss_only"}
        (directory/"report.json").write_text(json.dumps(report,indent=2))
        print(game,{k:v for k,v in report[game].items() if k!='losses'},flush=True)
    print('joint multitask rehearsal',flush=True)
    # Alternance de minibatches de chaque jeu : tous modifient le même tronc.
    for epoch in range(50):
        for game,model in models.items():
            losses=model.fit(*datasets[game],epochs=1,lr=.0008)
            report[game]['losses'].extend(losses)
    for game,model in models.items():
        model.save(directory/f'{game}.json')
        report[game]['final_loss']=report[game]['losses'][-1]
        report[game]['epochs']=len(report[game]['losses'])
        report[game]['training_steps']=model.steps
        report[game]['shared_steps']=core['steps']
    (directory/'report.json').write_text(json.dumps(report,indent=2))
    print('saved six models with one shared core',flush=True)


if __name__=="__main__":
    main()
