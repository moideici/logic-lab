"""Timed local self-play and guarded imitation, with a live public board."""
from pathlib import Path
import argparse,copy,hashlib,json,os,random,sys,time
from datetime import datetime,timezone
import numpy as np
from .games import make_game
from .general import GarryPolicy,GAMES,FEATURES,INPUT_OFFSETS,OUTPUT_OFFSETS
from .neural import SPECS,action_index
from .diversity import arrays,metrics,SoftImitation,assess,canonical_key,family_split
ROOT=Path(__file__).resolve().parents[1]
def atomic_json(path,value):
 temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(value,ensure_ascii=False,separators=(',',':')),encoding='utf-8');os.replace(temporary,path)
def file_hash(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def should_promote(before,after,fresh_before,fresh_after):
 return (after['optimal_choice_rate']>=before['optimal_choice_rate'] and fresh_after['optimal_choice_rate']>=fresh_before['optimal_choice_rate'] and ((after['optimal_choice_rate'],fresh_after['optimal_choice_rate'],-after['soft_cross_entropy'],-fresh_after['soft_cross_entropy'])>(before['optimal_choice_rate'],fresh_before['optimal_choice_rate'],-before['soft_cross_entropy'],-fresh_before['soft_cross_entropy'])))
def run(output,seconds=3600):
 if type(seconds)is not int or not 1<=seconds<=3600:raise ValueError('Durée entre 1 et 3600 secondes')
 output=Path(output);output.mkdir(parents=True,exist_ok=True);start=time.monotonic();deadline=start+seconds;path=ROOT/'web/models/garry.json';champion=GarryPolicy.load(path);champion.save(output/'initial.json');expected_hash=file_hash(path);rng=random.Random(171601);target_games=['go','hex','gomoku'];all_cases=[]
 for source in ('training/go-6.0.0/cases.json','training/competitive-5.0.0/cases.json'):
  all_cases.extend(json.loads((ROOT/source).read_text(encoding='utf-8'))['cases'])
 history={canonical_key(c['observation']) for c in all_cases};training=[c for c in all_cases if c['split']=='train'];validation=[c for c in all_cases if c['split']=='validation'];testing=[c for c in all_cases if c['split']=='test'];fresh=[];fresh_valid={g:[] for g in target_games};fresh_test=[]
 state={'state':'running','phase':'starting','started_at':datetime.now(timezone.utc).isoformat(),'ends_at':datetime.fromtimestamp(time.time()+seconds,timezone.utc).isoformat(),'duration_seconds':seconds,'elapsed_seconds':0,'remaining_seconds':seconds,'pid':os.getpid(),'cycles':0,'promotions':0,'moves_total':0,'fresh_samples':0,'game':'go','observation':None,'action':None,'model_sha256':expected_hash,'assessment':'bounded_teacher_agreement_not_certified_playing_strength'};last_write=0.;episode=0
 def emit(force=False,**changes):
  nonlocal last_write
  state.update(changes);now=time.monotonic()
  if force or now-last_write>=.1:
   state.update(elapsed_seconds=round(now-start,2),remaining_seconds=max(0,round(deadline-now,2)),updated_at=datetime.now(timezone.utc).isoformat());atomic_json(output/'status.json',state);last_write=now
 def stopped():return time.monotonic()>=deadline or (output/'stop.json').exists()
 try:
  emit(True)
  while not stopped():
   game=target_games[state['cycles']%len(target_games)];new=[];new_validation=[]
   for match in range(3):
    if stopped():break
    family=f'continuous:{output.name}:{episode}';episode+=1;split=family_split(family);size=(9,13,19)[(state['cycles']//3+match)%3];env=make_game(game,episode,{'size':size} if game=='go' else None)
    for ply in range(120 if game=='go' else 70):
     if stopped() or env.done:break
     obs=env.observation();legal=env.legal_actions();key=canonical_key(obs);info=None
     if ply%4==0 and key not in history:
      target,info=assess(obs,legal,champion,nodes=0);case={'id':key,'family':family,'split':split,'source':'continuous_self_play','observation':obs,'legal':legal,'target':target.tolist(),**info};history.add(key)
      with (output/'cases.jsonl').open('a',encoding='utf-8')as stream:stream.write(json.dumps(case,separators=(',',':'))+'\n')
      if split=='train':new.append(case)
      elif split=='validation':new_validation.append(case)
      else:fresh_test.append(case)
      state['fresh_samples']+=1
     if game=='go' and env.go_state['phase']=='scoring':action={'accept':True}
     elif rng.random()<.20:action=rng.choice([a for a in legal if not a.get('resign')])
     elif rng.random()<.5:action=champion.for_game(game).choose(obs,legal,10).action
     else:
      if info is None:_,info=assess(obs,legal,champion,nodes=0)
      action=max(info['values'],key=lambda v:tuple(v['quality']))['action']
     env.step(action);state['moves_total']+=1;emit(phase='playing',game=game,observation=env.observation(),action=action,episode=episode)
   training.extend(new);fresh_valid[game].extend(new_validation);state['cycles']+=1
   if stopped():break
   fixed=[c for c in validation if c['observation']['game']==game];recent=fresh_valid[game][-80:]
   # New held-out families are required before any model promotion.
   if len(recent)<8:emit(True,phase='collecting_validation');continue
   before=metrics(champion,fixed,game);fb=metrics(champion,recent,game);candidate=copy.deepcopy(champion);teacher=SoftImitation(candidate,game,lr=.0002);replay=[c for c in training if c['observation']['game']==game];pool=rng.sample(replay,min(420,len(replay)));_,x,y,mask,weight=arrays(pool,game);emit(True,phase='fitting')
   for epoch in range(8):
    if stopped():break
    order=rng.sample(range(len(x)),len(x))
    for at in range(0,len(order),32):
     ids=order[at:at+32];teacher.batch(x[ids],y[ids],mask[ids],weight[ids])
   if stopped():break
   emit(True,phase='validating');after=metrics(candidate,fixed,game);fa=metrics(candidate,recent,game);promote=should_promote(before,after,fb,fa)
   if promote:
    # SoftImitation modifies this game's private rows, tag and head only.
    ni,no=SPECS[game];a=INPUT_OFFSETS[game];b=OUTPUT_OFFSETS[game];rows=set(range(a,a+ni))|{FEATURES+GAMES.index(game)};keep=[i for i in range(candidate.w1.shape[0]) if i not in rows];np.testing.assert_array_equal(candidate.w1[keep],champion.w1[keep]);np.testing.assert_array_equal(candidate.w2[:,:b],champion.w2[:,:b]);np.testing.assert_array_equal(candidate.w2[:,b+no:],champion.w2[:,b+no:]);np.testing.assert_array_equal(candidate.b1,champion.b1)
    for k in ('w','b'):np.testing.assert_array_equal(candidate.core[k],champion.core[k])
    if file_hash(path)!=expected_hash:raise RuntimeError('Le modèle a changé ailleurs : arrêt pour préserver ces changements')
    candidate.save(path);champion=candidate;expected_hash=file_hash(path);state['promotions']+=1;champion.save(output/'latest-accepted.json');state['model_sha256']=expected_hash
   state['last_evaluation']={'game':game,'accepted':promote,'fixed_validation_before':before['optimal_choice_rate'],'fixed_validation_after':after['optimal_choice_rate'],'fresh_validation_before':fb['optimal_choice_rate'],'fresh_validation_after':fa['optimal_choice_rate']}
   with (output/'evaluations.jsonl').open('a',encoding='utf-8')as stream:stream.write(json.dumps(state['last_evaluation'])+'\n')
   emit(True,phase='checkpoint')
  emit(True,phase='final_evaluation')
  # Test results are reported only after selection ends, never used for fitting.
  initial=GarryPolicy.load(output/'initial.json');report={'before':{},'after':{},'fresh_tests':len(fresh_test)}
  for game in target_games:report['before'][game]=metrics(initial,testing+fresh_test,game);report['after'][game]=metrics(champion,testing+fresh_test,game)
  atomic_json(output/'report.json',report);emit(True,state='stopped' if (output/'stop.json').exists() else 'completed',phase='finished',finished_at=datetime.now(timezone.utc).isoformat())
 except Exception as error:
  emit(True,state='error',phase='failed',error=str(error));raise
 return state
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);p.add_argument('--seconds',type=int,default=3600);args=p.parse_args();run(args.output,args.seconds)
