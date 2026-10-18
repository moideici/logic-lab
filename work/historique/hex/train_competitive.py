"""Bootstrap Hex and competitive Swap2 Gomoku, with eleven-mode retention."""
from pathlib import Path
import sys,json,random,time
from copy import deepcopy
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from logic_arena.games import make_game
from logic_arena.general import GarryPolicy,FEATURES
from logic_arena.diversity import assess,arrays,metrics,SoftImitation,family_split,canonical_key,digest
from logic_arena.neural import action_index
ROOT=Path(__file__).resolve().parents[1]
def main():
    folder=ROOT/'training/competitive-5.0.0';folder.mkdir(parents=True,exist_ok=True);base=GarryPolicy.load(ROOT/'web/models/garry.json');base.save(folder/'before.json');model=deepcopy(base);rng=random.Random(1713513);seen=set();cases=[];limits={'train':180,'validation':50,'test':50};counts={g:{s:0 for s in limits} for g in ('hex','gomoku')};start=time.monotonic()
    for game in counts:
        for episode in range(10000):
            family=f'competitive:{game}:1713513:{episode}';split=family_split(family)
            if counts[game][split]>=limits[split]:continue
            env=make_game(game,episode)
            for step in range(100):
                if env.done:break
                o=env.observation();legal=env.legal_actions();key=canonical_key(o)
                if key not in seen and counts[game][split]<limits[split] and step%2==episode%2:
                    target,info=assess(o,legal,base,nodes=350 if game=='hex' else 0);case={'id':key,'family':family,'split':split,'source':'mixed_random_and_teacher','observation':o,'legal':legal,'target':target.tolist(),**info};cases.append(case);seen.add(key);counts[game][split]+=1
                    if counts[game][split]%30==0:print(game,split,counts[game][split],flush=True)
                else:case=None
                if rng.random()<.45:
                    if case:action=rng.choice([a for a in legal if action_index(game,a) in case['optimal']])
                    else:
                        _,info=assess(o,legal,base,nodes=100 if game=='hex' else 0);action=max(info['values'],key=lambda v:tuple(v['quality']))['action']
                else:action=rng.choice(legal)
                env.step(action)
            if counts[game]==limits:break
        assert counts[game]==limits,counts
    report={'version':'5.0.0','architecture':[3055,48,48,3894],'counts':counts,'games':{},'teacher_scope':'bounded_hex_connections_and_gomoku_tactics'}
    train=[c for c in cases if c['split']=='train'];valid=[c for c in cases if c['split']=='validation'];test=[c for c in cases if c['split']=='test']
    for game in counts:
        before=metrics(model,valid,game);test_before=metrics(model,test,game);_,x,y,mask,weight=arrays(train,game);trainer=SoftImitation(model,game,lr=.001);best=deepcopy(model);best_metric=before;best_epoch=0
        for epoch in range(1,101):
            ids=rng.sample(range(len(x)),len(x))
            for i in range(0,len(x),32):
                at=ids[i:i+32];trainer.batch(x[at],y[at],mask[at],weight[at])
            metric=metrics(model,valid,game)
            if (metric['optimal_choice_rate'],-metric['soft_cross_entropy'])>(best_metric['optimal_choice_rate'],-best_metric['soft_cross_entropy']):best=deepcopy(model);best_metric=metric;best_epoch=epoch
        assert best_epoch>0,game
        model=best;report['games'][game]={'selected_epoch':best_epoch,'presentations':model.game_steps[game],'validation_before':before,'validation_after':best_metric,'test_before':test_before,'test_after':metrics(model,test,game)}
        print(game,'selected',best_epoch,'test',test_before['optimal_choice_rate'],'->',report['games'][game]['test_after']['optimal_choice_rate'],flush=True)
    np.testing.assert_array_equal(model.w1[:2483],base.w1[:2483]);np.testing.assert_array_equal(model.w1[FEATURES:FEATURES+11],base.w1[FEATURES:FEATURES+11]);np.testing.assert_array_equal(model.w2[:,:3617],base.w2[:,:3617]);np.testing.assert_array_equal(model.b2[:3617],base.b2[:3617]);np.testing.assert_array_equal(model.b1,base.b1)
    for k in ('w','b'):np.testing.assert_array_equal(model.core[k],base.core[k])
    assert model.search_memory==base.search_memory and model.position_head==base.position_head
    model.save(ROOT/'web/models/garry.json');(folder/'cases.json').write_text(json.dumps({'format':'garry-competitive-curriculum-v1','cases':cases},separators=(',',':')),encoding='utf-8')
    path=ROOT/'web/models/garry-repertoire.json';bank=json.loads(path.read_text());bank['cases']=[c for c in bank['cases'] if c['observation']['game'] not in counts]
    for c in train:bank['cases'].append({k:c[k] for k in ('id','split','category','observation','target','baseline_error')})
    # More varied earlier strategy training is replayed; held-out cases stay out.
    league=json.loads((ROOT/'training/strategy-cycle02/cases.json').read_text())['cases'];ids={c['id'] for c in bank['cases']}
    for c in league:
        if c['split']=='train' and c['id'] not in ids:bank['cases'].append({k:c[k] for k in ('id','split','category','observation','target','baseline_error')});ids.add(c['id'])
    path.write_text(json.dumps(bank,separators=(',',':')),encoding='utf-8');report.update(earlier_eleven_modes_preserved=True,repertoire_size=len(bank['cases']),elapsed_seconds=round(time.monotonic()-start,2));(folder/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({'state':'completed','repertoire':len(bank['cases'])}),flush=True)
if __name__=='__main__':main()
