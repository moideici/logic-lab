"""Fresh Go/Hex/Gomoku curriculum, held-out families, immutable shared weights."""
from pathlib import Path
import sys,json,time,random,copy
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from logic_arena.games import make_game
from logic_arena.general import GarryPolicy,FEATURES,GAMES,INPUT_OFFSETS,OUTPUT_OFFSETS
from logic_arena.diversity import arrays,metrics,SoftImitation,family_split,canonical_key,assess,digest,transforms
from logic_arena.go_planner import go_rank
from logic_arena.go_rules import go_action_index
from logic_arena.neural import action_index
def main():
 folder=ROOT/'training/go-6.0.0';folder.mkdir(parents=True,exist_ok=True);base=GarryPolicy.load(ROOT/'web/models/garry.json');base.save(folder/'before.json');model=copy.deepcopy(base);rng=random.Random(171619);started=time.monotonic();cases=[];seen=set();held=set();limits={'go':{'train':320,'validation':80,'test':80},'hex':{'train':160,'validation':50,'test':50},'gomoku':{'train':180,'validation':50,'test':50}};counts={g:{s:0 for s in lim} for g,lim in limits.items()}
 old=json.loads((ROOT/'training/competitive-5.0.0/cases.json').read_text())['cases'];seen.update(canonical_key(c['observation']) for c in old)
 def status(**kw):
  d={'seconds':round(time.monotonic()-started,1),**kw};(folder/'status.json').write_text(json.dumps(d),encoding='utf-8');print(json.dumps(d),flush=True)
 for game in limits:
  for episode in range(20000):
   family=f'go-cycle:171619:{game}:{episode}';split=family_split(family)
   if counts[game][split]>=limits[game][split]:continue
   size=(9,9,13,19)[episode%4];env=make_game(game,episode,{'size':size} if game=='go' else None)
   for step in range(90 if game=='go' else 65):
    if env.done:break
    obs=env.observation();legal=env.legal_actions();key=canonical_key(obs)
    sampled=step%3==episode%3 and key not in seen and counts[game][split]<limits[game][split]
    if sampled:
     target,info=assess(obs,legal,base,nodes=0 if game in ('go','gomoku') else 160)
     case={'id':key,'family':family,'split':split,'source':'mixed_self_play_random_tactical','observation':obs,'legal':legal,'target':target.tolist(),**info};cases.append(case);seen.add(key);counts[game][split]+=1
     if counts[game][split]%40==0:status(state='building',game=game,counts=counts)
    else:info=None
    if counts[game][split]>=limits[game][split]:break
    if game=='go':
     if env.go_state['phase']=='scoring':a={'accept':True}
     else:
      ranked=go_rank(obs['board'],obs['current_player'],obs['go_state'],legal);pool=[v for v in ranked if 'row'in v['action']]
      if not pool:a={'pass':True}
      elif episode%3==0 and rng.random()<.6:a=rng.choice(pool)['action']
      elif episode%3==1 and rng.random()<.35:
       logits=base.for_game('go').logits(obs);a=max(pool,key=lambda v:float(logits[go_action_index(v['action'])]))['action']
      else:
       top=sorted(pool,key=lambda v:v['quality'],reverse=True);a=rng.choice(top[:min(4,len(top))])['action']
    elif rng.random()<.5:a=rng.choice(legal)
    elif info:a=rng.choice([v['action'] for v in info['values'] if action_index(game,v['action']) in info['optimal']])
    else:
     _,info=assess(obs,legal,base,nodes=0 if game=='gomoku' else 100);a=max(info['values'],key=lambda v:tuple(v['quality']))['action']
    env.step(a)
   if counts[game]==limits[game]:break
  assert counts[game]==limits[game],counts
 # Reuse training examples only; previous held-out examples are never fitted.
 train=[c for c in cases if c['split']=='train'];valid=[c for c in cases if c['split']=='validation'];test=[c for c in cases if c['split']=='test']
 train+=[c for c in old if c['split']=='train']
 report={'version':'6.0.0','counts':counts,'games':{},'teacher_scope':'bounded_public_tactics_not_an_optimal_go_oracle'}
 for game in limits:
  before=metrics(model,valid,game);tb=metrics(model,test,game);_,x,y,mask,weight=arrays(train,game);best=copy.deepcopy(model);bm=before;epoch_selected=0;trainer=SoftImitation(model,game,lr=.001)
  oldvalid=[c for c in old if c['split']=='validation' and c['observation']['game']==game];retention=metrics(base,oldvalid,game) if oldvalid else None
  for epoch in range(1,121):
   ids=rng.sample(range(len(x)),len(x))
   for start in range(0,len(ids),32):
    at=ids[start:start+32];trainer.batch(x[at],y[at],mask[at],weight[at])
   m=metrics(model,valid,game);ret=metrics(model,oldvalid,game) if oldvalid else None
   if (not ret or ret['optimal_choice_rate']>=retention['optimal_choice_rate']) and (m['optimal_choice_rate'],-m['soft_cross_entropy'])>(bm['optimal_choice_rate'],-bm['soft_cross_entropy']):best=copy.deepcopy(model);bm=m;epoch_selected=epoch
   if epoch%30==0:status(state='fitting',game=game,epoch=epoch,selected_epoch=epoch_selected)
  model=best;report['games'][game]={'selected_epoch':epoch_selected,'validation_before':before,'validation_after':bm,'test_before':tb,'test_after':metrics(model,test,game),'previous_validation_before':retention,'previous_validation_after':metrics(model,oldvalid,game) if oldvalid else None};status(state='selected',game=game,epoch=epoch_selected,test_before=tb['optimal_choice_rate'],test_after=report['games'][game]['test_after']['optimal_choice_rate'])
 # Exact preservation of every untargeted feature, tag and output.
 changed=set(limits);rows=set();cols=set()
 for game in changed:
  rows.update(range(INPUT_OFFSETS[game],INPUT_OFFSETS[game]+len(__import__('logic_arena.neural',fromlist=['encode']).encode(make_game(game).observation()))));rows.add(FEATURES+GAMES.index(game));cols.update(range(OUTPUT_OFFSETS[game],OUTPUT_OFFSETS[game]+__import__('logic_arena.neural',fromlist=['SPECS']).SPECS[game][1]))
 keep_r=[i for i in range(model.w1.shape[0]) if i not in rows];keep_c=[i for i in range(model.w2.shape[1]) if i not in cols];np.testing.assert_array_equal(model.w1[keep_r],base.w1[keep_r]);np.testing.assert_array_equal(model.w2[:,keep_c],base.w2[:,keep_c]);np.testing.assert_array_equal(model.b2[keep_c],base.b2[keep_c]);np.testing.assert_array_equal(model.b1,base.b1)
 for k in ('w','b'):np.testing.assert_array_equal(model.core[k],base.core[k])
 assert model.position_head==base.position_head and model.search_memory==base.search_memory
 model.save(ROOT/'web/models/garry.json');(folder/'cases.json').write_text(json.dumps({'format':'garry-go-curriculum-v1','cases':cases},separators=(',',':')),encoding='utf-8')
 path=ROOT/'web/models/garry-repertoire.json';bank=json.loads(path.read_text());ids={c['id'] for c in bank['cases']}
 for c in train:
  if c['id'] not in ids:bank['cases'].append({k:c[k] for k in ('id','split','category','observation','target','baseline_error')});ids.add(c['id'])
 path.write_text(json.dumps(bank,separators=(',',':')),encoding='utf-8');report.update(untargeted_eleven_preserved=True,repertoire_size=len(bank['cases']),seconds=round(time.monotonic()-started,2));(folder/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');status(state='completed',repertoire=len(bank['cases']))
if __name__=='__main__':main()
