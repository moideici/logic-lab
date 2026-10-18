"""Entraînement équilibré de Garry, professeurs planificateurs et tests séparés.

Les candidats restent séparés du modèle actif. Les poids et le statut sont
sauvegardés atomiquement. Les compteurs ne changent pas la version logicielle.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from logic_arena.general import GarryPolicy, GAMES, INPUT, OUTPUT, general_encode, OUTPUT_OFFSETS
from logic_arena.neural import action_index
from logic_arena.games import make_game
from logic_arena.planner import plan
from logic_arena.evaluation import evaluate


def atomic_json(path,data):
    path=Path(path);temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(data,indent=2,allow_nan=False),encoding='utf-8')
    os.replace(temporary,path)


def state_key(obs):
    return json.dumps([obs['game'],obs['board'],obs['current_player'],obs.get('givens')],separators=(',',':'))


def ttt_partition(board):
    b=[row[:] for row in board];variants=[]
    for _ in range(4):
        variants.extend([tuple(v for row in b for v in row),tuple(v for row in b for v in row[::-1])])
        b=[list(row) for row in zip(*b[::-1])]
    key=''.join(map(str,min(variants)))
    return int(hashlib.sha256(key.encode()).hexdigest()[:8],16)%5


def ttt_states():
    from logic_arena.planner import _LINES
    seen=set();out=[]
    def visit(board,player):
        if board in seen:return
        seen.add(board)
        if all(board) or any(board[line[0]] and all(board[i]==board[line[0]] for i in line) for line in _LINES):return
        out.append((board,player))
        for i,v in enumerate(board):
            if not v:visit(board[:i]+(player,)+board[i+1:],3-player)
    visit((0,)*9,1)
    return out


def dataset(teacher,count,seed,report,split='train',excluded=None):
    result={};all_keys={};excluded=excluded or {}
    for game in GAMES:
        view=teacher.for_game(game);x=[];y=[];masks=[];episode=0;methods={};seen=set()
        rng=np.random.default_rng(seed+GAMES.index(game)*997)
        pool=None
        if game=='tictactoe':
            pool=[state for state in ttt_states() if (ttt_partition([list(state[0][i:i+3]) for i in (0,3,6)])==0)==(split=='validation')]
            rng.shuffle(pool);count_for_game=min(count,len(pool))
        else:count_for_game=count
        while len(x)<count_for_game:
            if episode>count_for_game*100:raise RuntimeError('Pas assez de positions nouvelles')
            options={'scramble':8+episode%23} if game=='sliding_puzzle' else None
            env=make_game(game,seed+episode,options)
            if pool is not None:
                board,player=pool[episode]
                env.board=[list(board[i:i+3]) for i in (0,3,6)];env.current_player=player;env.moves=sum(v!=0 for v in board)
            elif game=='connect4':
                for _ in range(int(rng.integers(0,30))):
                    if env.done:break
                    env.step(env.rng.choice(env.legal_actions()))
                if rng.random()<.5:env.board=[row[::-1] for row in env.board]
            for step in range(160):
                if env.done or len(x)>=count_for_game:break
                obs,legal=env.observation(),env.legal_actions()
                logits=view.logits(obs)
                fallback=view.choose(obs,legal,logits=logits)
                target,info=plan(obs,legal,view,10,fallback,time_ms=20.,logits=logits)
                if target not in legal:raise RuntimeError('Cible illégale du professeur')
                key=state_key(obs)
                if key not in seen and key not in excluded.get(game,set()):
                    seen.add(key)
                    offset=OUTPUT_OFFSETS[game]
                    mask=np.zeros(OUTPUT,dtype=bool)
                    mask[[offset+action_index(game,a) for a in legal]]=True
                    x.append(general_encode(obs));y.append(offset+action_index(game,target));masks.append(mask)
                    method=info.get('method','unknown');methods[method]=methods.get(method,0)+1
                if pool is not None:break
                # Exposer aussi les états produits par les erreurs de la politique.
                action=view.choose(obs,legal,level=8,rng=teacher.rng,logits=logits) if step%4==3 else target
                env.step(action)
            episode+=1
        result[game]=(np.asarray(x,dtype=np.float32),np.asarray(y,dtype=np.int64),np.asarray(masks,dtype=bool))
        all_keys[game]=seen
        report(game,len(x),episode,methods)
    return result,all_keys


def nll(model,data):
    result={}
    for game,(x,y,mask) in data.items():
        total=0.;correct=0
        for start in range(0,len(x),128):
            xb=x[start:start+128];yb=y[start:start+128];mb=mask[start:start+128]
            e=np.tanh(xb@model.w1+model.b1);h=np.tanh(e@model.core['w']+model.core['b'])
            z=np.where(mb,h@model.w2+model.b2,-1e9)
            z-=z.max(axis=1,keepdims=True)
            p=np.exp(z);p/=p.sum(axis=1,keepdims=True)
            total+=float(-np.log(np.maximum(p[np.arange(len(yb)),yb],1e-12)).sum())
            correct+=int((p.argmax(axis=1)==yb).sum())
        result[game]={'nll':total/len(x),'teacher_agreement':correct/len(x),'samples':len(x)}
    return result


def compare_game(before,after):
    regression=after['wins']<before['wins']
    improvement=after['wins']>before['wins']
    if before['game'] in ('tictactoe','connect4'):
        regression=regression or after['losses']>before['losses']
        improvement=improvement or (after['wins']==before['wins'] and after['losses']<before['losses'])
    elif after['wins']==before['wins']:
        margin=max(.5,abs(before['mean_score'])*.05)
        regression=regression or after['mean_score']<before['mean_score']-margin
        improvement=improvement or after['mean_score']>before['mean_score']+margin
    # Un dépassement de la limite de coups n'est jamais une victoire.
    return {'regression':regression,'improvement':improvement}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=Path('web/models/garry.json'))
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--samples',type=int,default=1024)
    parser.add_argument('--validation-samples',type=int,default=256)
    parser.add_argument('--epochs',type=int,default=60)
    parser.add_argument('--eval-episodes',type=int,default=30)
    parser.add_argument('--learning-rate',type=float,default=.0003)
    parser.add_argument('--patience',type=int,default=10)
    args=parser.parse_args()
    if min(args.samples,args.validation_samples,args.epochs,args.eval_episodes)<1:parser.error('Les comptes doivent être positifs')
    if not math.isfinite(args.learning_rate) or args.learning_rate<=0:parser.error('Taux invalide')
    args.output.mkdir(parents=True,exist_ok=True)
    started=time.monotonic();status={'state':'starting','pid':os.getpid(),'software_version':'3.1.0',
        'source_sha256':hashlib.sha256(args.source.read_bytes()).hexdigest(),
        'settings':{'samples_per_game':args.samples,'validation_samples_per_game':args.validation_samples,'epochs':args.epochs,
                    'learning_rate':args.learning_rate,'teacher_level':10,'teacher_budget_ms':20,'teacher_fraction':.75,'patience':args.patience,
                    'unique_positions':True,'validation_excludes_training_positions':True,'tictactoe_symmetries_separated':True,
                    'training_seed':314159,'validation_seed':271828,'test_seed':9000000,'test_episodes':args.eval_episodes},
        'active_model_replaced':False,'history':[]}
    def update(**changes):
        status.update(changes);status['elapsed_seconds']=round(time.monotonic()-started,1)
        atomic_json(args.output/'status.json',status)
    def log(message):print(message,flush=True)
    try:
        teacher=GarryPolicy.load(args.source)
        teacher.save(args.output/'before.json')
        candidate=GarryPolicy.load(args.source);candidate.rng=np.random.default_rng(314159)
        update(state='collecting_training')
        def progress(game,count,episodes,methods):
            log(f"{status['state']}: {game}, {count} exemples, {episodes} parties")
            update(current_game=game,examples_collected=count,teacher_methods=methods)
        training,training_keys=dataset(teacher,args.samples,314159,progress)
        update(state='collecting_validation')
        validation,validation_keys=dataset(teacher,args.validation_samples,271828,progress,split='validation',excluded=training_keys)
        quality={g:{'training_unique':len(training_keys[g]),'validation_unique':len(validation_keys[g]),
                    'exact_overlap':len(training_keys[g]&validation_keys[g])} for g in GAMES}
        atomic_json(args.output/'data-quality.json',quality)
        if any(q['exact_overlap'] for q in quality.values()):raise RuntimeError('Fuite de positions entre apprentissage et validation')
        np.savez_compressed(args.output/'dataset.npz',**{f'{game}_{name}':part for game,data in training.items() for name,part in zip(('x','y','mask'),data)})
        baseline=nll(teacher,validation)
        update(state='training',baseline_validation=baseline,current_epoch=0)
        # Chaque jeu contribue autant, même si le nombre d'états uniques diffère.
        per_game=min(len(data[0]) for data in training.values())
        best=sum(v['nll'] for v in baseline.values())/len(GAMES);best_epoch=0
        teacher.save(args.output/'best.json')
        for epoch in range(1,args.epochs+1):
            parts=[]
            for game,data in training.items():
                selected=candidate.rng.permutation(len(data[0]))[:per_game]
                parts.append(tuple(part[selected] for part in data))
            x=np.concatenate([p[0] for p in parts]);y=np.concatenate([p[1] for p in parts]);masks=np.concatenate([p[2] for p in parts])
            order=candidate.rng.permutation(len(x))
            lr=args.learning_rate*(.15+.85*(1+math.cos(math.pi*(epoch-1)/args.epochs))/2)
            loss=candidate.fit(x[order],y[order],masks[order],epochs=1,batch_size=64,lr=lr)[0]
            metrics=nll(candidate,validation)
            macro=sum(v['nll'] for v in metrics.values())/len(GAMES)
            if macro<best:
                best=macro;best_epoch=epoch;candidate.save(args.output/'best.json')
            entry={'epoch':epoch,'training_loss':loss,'macro_validation_nll':macro,'per_game':metrics,'learning_rate':lr}
            status['history'].append(entry)
            update(current_epoch=epoch,training_examples=candidate.steps-teacher.steps,best_epoch=best_epoch,best_validation_nll=best)
            log(f"époque {epoch}/{args.epochs}, apprentissage={loss:.4f}, validation={macro:.4f}, meilleure={best_epoch}")
            if epoch%5==0:candidate.save(args.output/'last.json')
            if args.patience>0 and epoch-best_epoch>=args.patience:
                log('Arrêt anticipé : la validation ne progresse plus.')
                break
        candidate.save(args.output/'last.json')
        best_model=GarryPolicy.load(args.output/'best.json')
        update(state='evaluating',candidate_validation=nll(best_model,validation))
        comparison={};regressions=[];improvements=[]
        for game in GAMES:
            # Ces graines ne servent ni aux mises à jour ni au choix de checkpoint.
            before=evaluate(teacher.for_game(game),args.eval_episodes,9000000,max_steps=250,planning=False)
            after=evaluate(best_model.for_game(game),args.eval_episodes,9000000,max_steps=250,planning=False)
            comparison[game]={'before':before,'after':after}
            assessment=compare_game(before,after)
            if assessment['regression']:regressions.append(game)
            if assessment['improvement']:improvements.append(game)
            update(test_results=comparison,current_game=game)
            log(f"test {game}: victoires {before['wins']} -> {after['wins']}, défaites {before['losses']} -> {after['losses']}")
        eligible=not regressions and bool(improvements)
        report={'software_version':'3.1.0','architecture':[INPUT,best_model.hidden,best_model.hidden,OUTPUT],
                'before_steps':teacher.steps,'trained_steps':candidate.steps,'best_steps':best_model.steps,'best_epoch':best_epoch,
                'baseline_validation':baseline,'candidate_validation':nll(best_model,validation),'test_results':comparison,
                'regressions':regressions,'improvements':improvements,'eligible_for_further_validation':eligible,
                'active_model_replaced':False,'note':'Évaluation du réseau seul. Pas une preuve de gain des solveurs ni un taux de victoire contre les anciennes IA. Le modèle actif reste inchangé.'}
        atomic_json(args.output/'report.json',report)
        update(state='completed',regressions=regressions,improvements=improvements,eligible_for_further_validation=eligible)
        log('Terminé. Le modèle actif est conservé ; candidat dans best.json.')
    except BaseException as error:
        update(state='interrupted' if isinstance(error,KeyboardInterrupt) else 'failed',error=str(error))
        traceback.print_exc();raise


if __name__=='__main__':main()
