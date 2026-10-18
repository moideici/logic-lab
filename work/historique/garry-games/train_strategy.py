"""Teach international draughts and Breakthrough, keeping all previous modes frozen."""
import json,random,sys,time
from pathlib import Path
from copy import deepcopy
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from logic_arena.games import make_game
from logic_arena.general import GarryPolicy,FEATURES
from logic_arena.diversity import canonical_key,family_split,assess,arrays,metrics,SoftImitation
ROOT=Path(__file__).resolve().parents[1]
def main():
    start=time.monotonic();base=GarryPolicy.load(ROOT/'web/models/garry.json');model=deepcopy(base);rng=random.Random(1710711);cases=[];seen=set();counts={g:{s:0 for s in ('train','validation','test')} for g in ('draughts','breakthrough')};limits={'train':180,'validation':40,'test':40}
    for game in counts:
        for episode in range(3000):
            family=f'{game}:1710711:{episode}';split=family_split(family)
            if counts[game][split]>=limits[split]:continue
            env=make_game(game,episode)
            for step in range(150):
                if env.done:break
                obs=env.observation();key=canonical_key(obs)
                # Include openings, exchanges, capture continuations and endgames.
                if key not in seen and counts[game][split]<limits[split] and (step%3==episode%3 or obs.get('draughts_state',{}).get('forced_piece')):
                    target,info=assess(obs,env.legal_actions(),base,nodes=600)
                    case={'id':key,'family':family,'split':split,'source':'mixed_capture_and_race_play','observation':obs,'legal':env.legal_actions(),'target':target.tolist(),**info};cases.append(case);seen.add(key);counts[game][split]+=1
                # Vary trajectories without using test labels to guide play.
                env.step(rng.choice(env.legal_actions()))
            if all(counts[game][s]>=limits[s] for s in limits):break
        assert counts[game]==limits,counts
        print(game,counts[game],flush=True)
    report={'version':'4.0.0','architecture':[2494,48,48,3617],'seed':1710711,'counts':counts,'games':{},'label_scope':'bounded_public_search_600_nodes_depth_3'}
    train=[c for c in cases if c['split']=='train'];valid=[c for c in cases if c['split']=='validation'];test=[c for c in cases if c['split']=='test']
    for game in counts:
        before=metrics(model,valid,game);test_before=metrics(model,test,game);local,x,y,mask,weight=arrays(train,game);trainer=SoftImitation(model,game,lr=.001);best=deepcopy(model);best_metric=before;best_epoch=0
        for epoch in range(1,101):
            ids=rng.sample(range(len(x)),len(x))
            for i in range(0,len(x),32):
                at=ids[i:i+32];trainer.batch(x[at],y[at],mask[at],weight[at])
            result=metrics(model,valid,game)
            if (result['optimal_choice_rate'],-result['soft_cross_entropy'])>(best_metric['optimal_choice_rate'],-best_metric['soft_cross_entropy']):best=deepcopy(model);best_metric=result;best_epoch=epoch
        model=best;assert best_epoch>0,game
        report['games'][game]={'selected_epoch':best_epoch,'training_presentations':model.game_steps[game],'validation_before':before,'validation_after':best_metric,'test_before':test_before,'test_after':metrics(model,test,game)}
        print(game,'selected',best_epoch,round(before['optimal_choice_rate'],3),'->',round(best_metric['optimal_choice_rate'],3),flush=True)
    # Nine-game retention is exact, including moved game identifier rows.
    np.testing.assert_array_equal(model.w1[:2051],base.w1[:2051]);np.testing.assert_array_equal(model.w1[FEATURES:FEATURES+9],base.w1[FEATURES:FEATURES+9]);np.testing.assert_array_equal(model.w2[:,:925],base.w2[:,:925]);np.testing.assert_array_equal(model.b2[:925],base.b2[:925]);np.testing.assert_array_equal(model.b1,base.b1)
    for k in ('w','b'):np.testing.assert_array_equal(model.core[k],base.core[k])
    assert model.search_memory==base.search_memory and model.position_head==base.position_head
    model.save(ROOT/'web/models/garry.json')
    path=ROOT/'training/strategy-4.0.0';path.mkdir(parents=True,exist_ok=True)
    (path/'cases.json').write_text(json.dumps({'format':'garry-strategy-curriculum-v1','cases':cases},separators=(',',':')),encoding='utf-8')
    p=ROOT/'web/models/garry-repertoire.json';bank=json.loads(p.read_text());bank['cases']=[c for c in bank['cases'] if c['observation']['game'] not in counts]
    for c in train:bank['cases'].append({k:c[k] for k in ('id','split','category','observation','target','baseline_error')})
    p.write_text(json.dumps(bank,separators=(',',':')),encoding='utf-8');report.update(previous_nine_modes_preserved=True,elapsed_seconds=round(time.monotonic()-start,2),repertoire_size=len(bank['cases']))
    (path/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({g:{'before':v['test_before']['optimal_choice_rate'],'after':v['test_after']['optimal_choice_rate']} for g,v in report['games'].items()}),flush=True)
if __name__=='__main__':main()
