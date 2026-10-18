"""Fresh, quarantined positions against a mixed league for existing strategy modes."""
import json,random,sys,time
from pathlib import Path
from collections import Counter
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from logic_arena.games import make_game
from logic_arena.general import GarryPolicy
from logic_arena.agents import Budget
from logic_arena.strategy_planner import strategy_values,evaluate_strategy
from logic_arena.strategy_rules import step_strategy
from logic_arena.neural import action_index
from logic_arena.diversity import digest,family_split,soft_targets,canonical_key
from examples.train_garry_curriculum import atomic_json
from copy import deepcopy
ROOT=Path(__file__).resolve().parents[1]
PROFILES=('random','captures','policy','search')
def quarantine_key(obs):
    b=obs['board'];n=len(b);p=obs['current_player'];s=obs.get('draughts_state',{});forced=s.get('forced_piece');pending=s.get('pending_captures',[])
    raw=[b,p,forced,sorted(pending)]
    swap=lambda v:0 if not v else v+1 if v%2 else v-1
    rotated=[[[swap(v) for v in row[::-1]] for row in b[::-1]],3-p,[n-1-forced[0],n-1-forced[1]] if forced else None,sorted([n-1-r,n-1-c] for r,c in pending)]
    variants=[raw,rotated]
    if obs['game']=='breakthrough':variants+=[[[row[::-1] for row in variant[0]],variant[1],None,[]] for variant in variants[:]]
    return digest([obs['game'],min(json.dumps(v,sort_keys=True) for v in variants)])
def profile_action(env,profile,model,rng):
    legal=env.legal_actions();obs=env.observation()
    if profile=='random' or rng.random()<.15:return rng.choice(legal)
    if profile=='policy':return model.for_game(env.name).choose(obs,legal,10,rng=np.random.default_rng(rng.randrange(1<<32)))
    if profile=='search':values,_=strategy_values(obs,legal,Budget(250,10000),max_depth=2)
    else:
        values=[]
        for action in legal:
            board=deepcopy(env.board);state=step_strategy(env.name,board,env.current_player,action,deepcopy(env.draughts_state));value=100000 if state['done'] and state['winner']==env.current_player else evaluate_strategy(env.name,board,env.current_player)
            values.append({'action':action,'quality':[value]})
    best=max(tuple(v['quality']) for v in values);return rng.choice([v['action'] for v in values if tuple(v['quality'])==best])
def main():
    out=ROOT/'training/strategy-cycle02';out.mkdir(parents=True,exist_ok=True);base=GarryPolicy.load(ROOT/'web/models/garry.json');base.save(out/'before.json')
    old=json.loads((ROOT/'training/strategy-4.0.0/cases.json').read_text())['cases'];blocked={quarantine_key(c['observation']) for c in old};seen=set(blocked);rng=random.Random(17110123);cases=[];counts={g:{s:0 for s in ('train','validation','test')} for g in ('draughts','breakthrough')};limits={'train':300,'validation':80,'test':80};categories=Counter();start=time.monotonic()
    for game in counts:
        for episode in range(10000):
            family=f'league02:{game}:{17110123+episode}';split=family_split(family)
            if counts[game][split]>=limits[split]:continue
            env=make_game(game,episode);pair=[PROFILES[episode%4],PROFILES[(episode//4)%4]]
            for ply in range(200):
                if env.done:break
                obs=env.observation();legal=env.legal_actions();key=quarantine_key(obs)
                if counts[game][split]<limits[split] and key not in seen and (ply%3==episode%3 or obs.get('draughts_state',{}).get('forced_piece')):
                    forced=bool(obs.get('draughts_state',{}).get('forced_piece'));pieces=sum(bool(v) for row in env.board for v in row)
                    category='rafle' if forced else 'endgame' if pieces<=8 else 'opening' if ply<16 else 'middle'
                    if len(legal)>1 or categories[game,split,'forced']<max(5,limits[split]//8):
                        values,info=strategy_values(obs,legal,Budget(2000,10000),max_depth=4);target=soft_targets(game,legal,values);best=max(tuple(v['quality']) for v in values);good=[action_index(game,v['action']) for v in values if tuple(v['quality'])==best];z=base.for_game(game).logits(obs);choice=max(legal,key=lambda a:float(z[action_index(game,a)]))
                        cases.append({'id':canonical_key(obs),'family':family,'split':split,'source':' / '.join(pair),'observation':obs,'legal':legal,'target':target.tolist(),'category':category,'optimal':good,'sound':good,'baseline_error':action_index(game,choice) not in good,'analysis_depth':info['depth'],'analysis_nodes':info['nodes']});seen.add(key);counts[game][split]+=1;categories[game,split,'forced' if len(legal)==1 else category]+=1
                        if counts[game][split]%40==0:
                            atomic_json(out/'status.json',{'state':'building','counts':counts,'seconds':time.monotonic()-start});print(game,split,counts[game][split],flush=True)
                env.step(profile_action(env,pair[env.current_player-1],base,rng))
            if all(counts[game][s]>=limits[s] for s in limits):break
        assert counts[game]==limits,counts
    # Replay only earlier training; old validation/test states never become labels.
    replay=[c for c in old if c['split']=='train'];summary={'fresh_counts':counts,'profiles':list(PROFILES),'teacher_nodes':2000,'teacher_depth':4,'quarantine':'board, actor and capture continuation, including role-swap symmetries; history counters ignored conservatively','old_training_replayed':len(replay),'fresh_positions':len(cases),'seconds':time.monotonic()-start}
    atomic_json(out/'cases.json',{'format':'garry-strategy-league-v1','summary':summary,'cases':cases+replay});atomic_json(out/'status.json',{'state':'completed',**summary});print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
