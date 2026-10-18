"""Bootstrap the three added modes, with frozen legacy parameters and held-out states."""
import json,random,sys,hashlib,time
from pathlib import Path
from copy import deepcopy
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from logic_arena.games import make_game
from logic_arena.general import GarryPolicy,INPUT_OFFSETS,OUTPUT_OFFSETS,FEATURES,GAMES
from logic_arena.diversity import canonical_key,family_split,assess,SoftImitation,arrays,metrics

ROOT=Path(__file__).resolve().parents[1]
EXTRAS=('reversi','nim','lightsout')
def main():
    start=time.monotonic();model=GarryPolicy.load(ROOT/'versions/3.2.0/garry.json');original=deepcopy(model);rng=random.Random(1710400)
    cases=[];seen=set();counts={g:{s:0 for s in ('train','validation','test')} for g in EXTRAS}
    limits={'nim':(900,150,150),'lightsout':(600,100,100),'reversi':(320,70,70)}
    def add(env):
        if env.done:return
        o=env.observation();game=o['game'];key=canonical_key(o)
        family=game+':'+(str(sorted(map(sum,env.board))) if game=='nim' else key)
        split=family_split(family);limit=dict(zip(('train','validation','test'),limits[game]))[split]
        if key in seen or counts[game][split]>=limit:return
        target,info=assess(o,env.legal_actions(),original,nodes=3000)
        cases.append({'id':key,'family':family,'split':split,'source':'new_modes_bootstrap','observation':o,'legal':env.legal_actions(),'target':target.tolist(),**info});seen.add(key);counts[game][split]+=1
    for game in EXTRAS:
        for episode in range(10000):
            if all(n>=limit for n,limit in zip(counts[game].values(),limits[game])):break
            env=make_game(game,17100000+episode)
            if game=='nim':
                heaps=[rng.randrange(16) for _ in range(3)]
                if not any(heaps):continue
                env.board=[[1]*n+[0]*(15-n) for n in heaps];add(env)
            elif game=='lightsout':add(env)
            else:
                for step in range(40):
                    if env.done:break
                    add(env);env.step(rng.choice(env.legal_actions()))
        assert tuple(counts[game].values())==limits[game],counts
        print(game,counts[game],flush=True)
    report={'version':'4.0.0','architecture':[2060,48,48,925],'seed':1710400,'counts':counts,'games':{}}
    for game in EXTRAS:
        train=[c for c in cases if c['split']=='train'];valid=[c for c in cases if c['split']=='validation'];test=[c for c in cases if c['split']=='test']
        before=metrics(model,valid,game);baseline_test=metrics(model,test,game)
        local,x,y,mask,importance=arrays(train,game);trainer=SoftImitation(model,game,lr=.002)
        best=deepcopy(model);best_metric=before;best_epoch=0;best_steps=0
        for epoch in range(1,101):
            order=rng.sample(range(len(x)),len(x))
            for at in range(0,len(x),64):
                ids=order[at:at+64];trainer.batch(x[ids],y[ids],mask[ids],importance[ids])
            current=metrics(model,valid,game)
            if current['optimal_choice_rate']>=best_metric['optimal_choice_rate'] and current['soft_cross_entropy']<before['soft_cross_entropy']:
                best=deepcopy(model);best_metric=current;best_epoch=epoch;best_steps=model.game_steps[game]
        model=best
        assert best_epoch>0,game
        report['games'][game]={'epochs_selected':best_epoch,'training_presentations':best_steps,'validation_before':before,'validation_after':best_metric,'test_before':baseline_test,'test_after':metrics(model,test,game)}
        print(game,'validated',best_epoch,round(before['optimal_choice_rate'],3),'->',round(best_metric['optimal_choice_rate'],3),flush=True)
    # All coefficients used by the old games remain bit-for-bit identical.
    np.testing.assert_array_equal(model.w1[:1906],original.w1[:1906]);np.testing.assert_array_equal(model.w1[FEATURES:FEATURES+6],original.w1[FEATURES:FEATURES+6])
    np.testing.assert_array_equal(model.w2[:,:818],original.w2[:,:818]);np.testing.assert_array_equal(model.b2[:818],original.b2[:818]);np.testing.assert_array_equal(model.b1,original.b1)
    for k in ('w','b'):np.testing.assert_array_equal(model.core[k],original.core[k])
    assert model.position_head==original.position_head and model.search_memory==original.search_memory
    model.save(ROOT/'web/models/garry.json')
    dataset={'format':'garry-new-games-curriculum-v1','seed':1710400,'cases':cases}
    (ROOT/'training/new-games-4.0.0').mkdir(parents=True,exist_ok=True)
    (ROOT/'training/new-games-4.0.0/cases.json').write_text(json.dumps(dataset,separators=(',',':')),encoding='utf-8')
    bankpath=ROOT/'web/models/garry-repertoire.json';bank=json.loads(bankpath.read_text());bank['cases']=[c for c in bank['cases'] if c['observation']['game'] not in EXTRAS]
    for game in EXTRAS:
        local=[c for c in cases if c['split']=='train' and c['observation']['game']==game]
        for c in local[:160]:bank['cases'].append({k:c[k] for k in ('id','split','category','observation','target','baseline_error')})
    bankpath.write_text(json.dumps(bank,separators=(',',':')),encoding='utf-8')
    report.update(legacy_parameters_preserved=True,search_memory_preserved=True,position_head_preserved=True,elapsed_seconds=round(time.monotonic()-start,2),repertoire_size=len(bank['cases']))
    (ROOT/'training/new-games-4.0.0/report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({g:{'before':v['test_before']['optimal_choice_rate'],'after':v['test_after']['optimal_choice_rate']} for g,v in report['games'].items()}),flush=True)
if __name__=='__main__':main()
