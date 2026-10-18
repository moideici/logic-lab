"""Build a six-game repertoire with quarantined validation and test families."""
import argparse
from collections import Counter
from copy import deepcopy
import json,math,random,sys,time
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from logic_arena.diversity import *
from logic_arena.general import GarryPolicy
from logic_arena.planner import sliding_distance
from examples.train_garry_curriculum import ttt_states,atomic_json

def profile_move(env,profile,model,rng,legacy):
    o=env.observation();legal=env.legal_actions()
    if profile=='random':return rng.choice(legal)
    if profile in ('center','edges'):
        weights=[math.exp((1 if profile=='edges' else -1)*abs(a['column']-3)) for a in legal]
        return rng.choices(legal,weights)[0]
    if profile=='current_policy':return model.for_game('connect4').choose(o,legal)
    if profile=='legacy_policy':return legacy.choose(o,legal)
    if profile=='tactical':
        t=c4_tactics(o);cols=t['immediate'] or t['forks'] or t['safe'] or [a['column'] for a in legal]
        return {'column':rng.choice(cols)}
    from logic_arena.connect4_wasm import search
    return search(o,legal,Budget(4096,10000),max_depth=7,position_head=model.position_head if profile=='champion' else None)[0]

def build(model,counts,seed,notify):
    banks={g:{s:[] for s in SPLITS} for g in GAMES};seen=set();category_counts=Counter();families={s:set() for s in SPLITS}
    def full(game):return all(len(banks[game][s])>=counts[game][s] for s in SPLITS)
    def add(env,family,source,nodes=50000):
        o=env.observation();g=o['game'];split=family_split(family);key=canonical_key(o)
        if env.done or not env.legal_actions() or key in seen or len(banks[g][split])>=counts[g][split]:return None
        if g in ('connect4','2048','minesweeper','sliding_puzzle'):
            if g=='connect4':cat=c4_tactics(o)['category'];fraction=.22
            elif g=='2048':
                spaces=sum(v==0 for row in o['board'] for v in row);largest=max(map(max,o['board']));cat='goal' if largest>=1024 else 'cramped' if spaces<=3 else 'middle' if largest>=64 else 'opening';fraction=.35
            elif g=='sliding_puzzle':
                d=sliding_distance(o['board']);cat='short' if d<=10 else 'medium' if d<=20 else 'long';fraction=.45
            else:
                _,tmp=assess(o,env.legal_actions(),model);cat=tmp['category'];fraction=.65 if cat=='safe_frontier' else 1.
            if category_counts[g,split,cat]>=max(8,math.ceil(counts[g][split]*fraction)):return None
        case=example(env,model,family,source,nodes);seen.add(key);banks[g][split].append(case);families[split].add(str(family));category_counts[g,split,case['category']]+=1
        if len(banks[g][split])%128==0:notify(g,split,len(banks[g][split]))
        return case
    legacy=NeuralPolicy.load(Path(__file__).resolve().parents[1]/'versions/1.0.0/web/models/connect4.json')
    # Do not convert permanent hand-written tactical regressions into training.
    for c in json.loads((Path(__file__).resolve().parents[1]/'tests/fixtures/connect4-positions.json').read_text()):
        e=make_game('connect4')
        for col in c['history']:e.step({'column':col})
        seen.add(canonical_key(e.observation()))
    for game in GAMES:
        rng=random.Random(seed+GAMES.index(game)*100003);episode=0
        if game=='tictactoe':
            states=ttt_states();rng.shuffle(states)
            for b,p in states:
                env=make_game(game);env.board=[list(b[i:i+3]) for i in (0,3,6)];env.current_player=p;env.moves=sum(bool(v) for v in b)
                add(env,'ttt:'+canonical_key(env.observation()),'exhaustive_oracle')
            continue
        while not full(game):
            if episode>sum(counts[game].values())*100:raise RuntimeError(f'Coverage exhausted: {game}')
            runseed=seed+GAMES.index(game)*100003+episode;family=f'{game}:{runseed}';split=family_split(family)
            if game!='sudoku' and len(banks[game][split])>=counts[game][split]:episode+=1;continue
            if game=='sudoku':
                env,solution=new_sudoku(runseed,(28,34,40,46)[episode%4]);family='sudoku:'+sudoku_family(env.givens);split=family_split(family)
                if len(banks[game][split])>=counts[game][split]:episode+=1;continue
                for step in range(4):
                    if env.done:break
                    case=add(env,family,'new_unique_grid')
                    legal=env.legal_actions();sound=[a for a in legal if not a.get('undo') and a['value']==solution[a['row']][a['col']]]
                    if step==2:
                        wrong=[a for a in legal if not a.get('undo') and a['value']!=solution[a['row']][a['col']]]
                        if wrong:
                            env.step(rng.choice(wrong));add(env,family,'repair_wrong_assumption');env.step({'undo':True})
                    env.step(rng.choice(sound))
                remaining=[(r,c) for r in range(9) for c in range(9) if not env.board[r][c]];rng.shuffle(remaining)
                for r,c in remaining[:-8]:env.step({'row':r,'col':c,'value':solution[r][c]})
                for step in range(4):
                    if env.done:break
                    add(env,family,'finish_new_grid');empty=[a for a in env.legal_actions() if not a.get('undo') and a['value']==solution[a['row']][a['col']]];env.step(rng.choice(empty))
            elif game=='connect4':
                env=make_game(game,runseed);profile=PROFILES[episode%len(PROFILES)];other=PROFILES[(episode//len(PROFILES))%len(PROFILES)];survival=episode%5==0
                for step in range(42):
                    if env.done:break
                    if not survival or env.moves>=22:add(env,family,'survival_endgame' if survival else profile+' / '+other)
                    if survival:
                        wins=c4_tactics(env.observation())['immediate'];moves=[a for a in env.legal_actions() if a['column'] not in wins]
                        if not moves:break
                        env.step(rng.choice(moves))
                    else:env.step(profile_move(env,profile if env.current_player==1 else other,model,rng,legacy))
            elif game=='sliding_puzzle':
                env=make_game(game,runseed);flat=list(range(9));rng.shuffle(flat)
                inv=sum(flat[i] and flat[j] and flat[i]>flat[j] for i in range(9) for j in range(i+1,9))
                if inv%2:
                    a,b=[i for i,v in enumerate(flat) if v][:2];flat[a],flat[b]=flat[b],flat[a]
                if episode%2:env=make_game(game,runseed,{'scramble':2+(episode%14)})
                else:env.board=[flat[r:r+3] for r in (0,3,6)]
                if sliding_distance(env.board)==0:episode+=1;continue
                add(env,family,'uniform_solvable_permutation')
            elif game=='minesweeper':
                env=make_game(game,runseed);openings=((0,0),(0,3),(3,3),(7,7),(7,4),(4,7));r,c=openings[episode%len(openings)];add(env,family,'protected_opening');env.step({'row':r,'col':c})
                for step in range(54):
                    if env.done:break
                    case=add(env,family,'public_frontier')
                    if case:
                        options=[a for a in env.legal_actions() if action_index(game,a) in case['optimal']];action=rng.choice(options)
                    else:
                        _,info=assess(env.observation(),env.legal_actions(),model);action=rng.choice([v['action'] for v in info['values'] if action_index(game,v['action']) in info['optimal']])
                    if episode%3==0 and rng.random()<.35:
                        _,info=assess(env.observation(),env.legal_actions(),model);public_choices=[v['action'] for v in info['values'] if -v['quality'][0]<1];action=rng.choice(public_choices or env.legal_actions())
                    env.step(action)
            else:
                env=make_game('2048',runseed);kind=episode%4
                if kind in (2,3):
                    ranks=[rng.choices(range(1,11),[30,20,15,10,8,6,4,3,2,1])[0] for _ in range(16)];env.board=[[2**ranks[r*4+c] for c in range(4)] for r in range(4)]
                    if kind==3:env.board[0][:2]=[1024,1024]
                    env.moves=0
                for step in range(40 if kind<2 else 8):
                    if env.done or not env.legal_actions():break
                    case=add(env,family,('reachable_search','reachable_random','synthetic_cramped','synthetic_goal')[kind])
                    if kind==1:action=rng.choice(env.legal_actions())
                    elif case:action=rng.choice([a for a in env.legal_actions() if action_index(game,a) in case['optimal']])
                    else:
                        _,info=assess(env.observation(),env.legal_actions(),model);action=max(info['values'],key=lambda v:v['quality'])['action']
                    env.step(action)
            episode+=1
        notify(game,'complete',{s:len(banks[game][s]) for s in SPLITS})
    cases=[c for g in GAMES for s in SPLITS for c in banks[g][s]]
    split_keys={s:{c['id'] for c in cases if c['split']==s} for s in SPLITS}
    assert not any(split_keys[a]&split_keys[b] or families[a]&families[b] for i,a in enumerate(SPLITS) for b in SPLITS[i+1:])
    summary={g:{s:{'samples':len(banks[g][s]),'families':len({c['family'] for c in banks[g][s]}),'categories':dict(Counter(c['category'] for c in banks[g][s])),'phases':dict(Counter(c.get('phase','not_applicable') for c in banks[g][s])),'sources':dict(Counter(c['source'] for c in banks[g][s])),'teacher_action_mass':np.sum([c['target'] for c in banks[g][s]],axis=0).tolist()} for s in SPLITS} for g in GAMES}
    return cases,summary

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',default='web/models/garry.json');ap.add_argument('--output',required=True,type=Path);ap.add_argument('--c4-train',type=int,default=3072);ap.add_argument('--c4-heldout',type=int,default=384);ap.add_argument('--solo-train',type=int,default=256);ap.add_argument('--solo-heldout',type=int,default=64);ap.add_argument('--seed',type=int,default=16035100);args=ap.parse_args()
    if min(args.c4_train,args.c4_heldout,args.solo_train,args.solo_heldout)<=0:ap.error('Positive counts required')
    args.output.mkdir(parents=True,exist_ok=True);started=time.monotonic();model=GarryPolicy.load(args.source)
    counts={g:{'train':args.solo_train,'validation':args.solo_heldout,'test':args.solo_heldout} for g in GAMES};counts['connect4']={'train':args.c4_train,'validation':args.c4_heldout,'test':args.c4_heldout};counts['tictactoe']={s:5000 for s in SPLITS}
    def notify(game,split,count):
        status={'state':'building','game':game,'split':split,'count':count,'seconds':time.monotonic()-started};atomic_json(args.output/'status.json',status);print(json.dumps(status),flush=True)
    cases,summary=build(model,counts,args.seed,notify)
    atomic_json(args.output/'dataset.json',{'format':'garry-repertoire-v1','seed':args.seed,'cases':cases,'summary':summary})
    atomic_json(args.output/'status.json',{'state':'completed','summary':summary,'seconds':time.monotonic()-started})
    print(json.dumps({'completed':len(cases),'seconds':time.monotonic()-started}),flush=True)
if __name__=='__main__':main()
