from collections import Counter,defaultdict
from copy import deepcopy
from pathlib import Path
import hashlib,json,random
import numpy as np
from logic_arena.general import GarryPolicy,GAMES,INPUT_OFFSETS,OUTPUT_OFFSETS,FEATURES
from logic_arena.neural import SPECS
from logic_arena.diversity import canonical_key,digest,metrics
from examples.train_garry_repertoire import copy_mode

root=Path.cwd();run=root/'training-runs/garry-diversity-balanced-20261016';data=json.loads((run/'dataset.json').read_text());training=json.loads((run/'training/report.json').read_text());league=json.loads((run/'league.json').read_text());solo=json.loads((run/'solo-trials.json').read_text());before=GarryPolicy.load(root/'versions/3.0.0/garry.json');candidate=GarryPolicy.load(run/'training/candidate.json')
accepted=[g for g in GAMES if training['selection'][g]['accepted']];rejected={g:'held_out_position_regression' for g in GAMES if g not in accepted}
if not league['passed'] and 'connect4' in accepted:accepted.remove('connect4');rejected['connect4']='league_regression';copy_mode(before,candidate,'connect4')
for game,result in solo['games'].items():
    if not result['passed'] and game in accepted:accepted.remove(game);rejected[game]='full_game_control_regression';copy_mode(before,candidate,game)
for key in ('w','b'):assert np.array_equal(before.core[key],candidate.core[key])
assert np.array_equal(before.b1,candidate.b1) and before.position_head==candidate.position_head
for g in set(GAMES)-set(accepted):
    ni,no=SPECS[g];a=INPUT_OFFSETS[g];b=OUTPUT_OFFSETS[g];tag=FEATURES+GAMES.index(g)
    assert np.array_equal(before.w1[a:a+ni],candidate.w1[a:a+ni]);assert np.array_equal(before.w1[tag],candidate.w1[tag]);assert np.array_equal(before.w2[:,b:b+no],candidate.w2[:,b:b+no]);assert np.array_equal(before.b2[b:b+no],candidate.b2[b:b+no])
split_keys={s:{canonical_key(c['observation']) for c in data['cases'] if c['split']==s} for s in ('train','validation','test')};family_keys={s:{c['family'] for c in data['cases'] if c['split']==s} for s in split_keys}
assert all(not(split_keys[a]&split_keys[b] or family_keys[a]&family_keys[b]) for i,a in enumerate(split_keys) for b in list(split_keys)[i+1:])
# Shipped examples are compact, category-balanced and strictly training-only.
groups=defaultdict(list)
for c in data['cases']:
    if c['split']=='train':groups[c['observation']['game'],c['category']].append(c)
bank=[]
for key,cases in sorted(groups.items()):
    # Shuffle by stable content hash to avoid selecting one consecutive trajectory.
    cases=sorted(cases,key=lambda c:digest([c['id'],'browser']))[:128]
    for c in cases:bank.append({k:deepcopy(c[k]) for k in ('id','split','category','source','observation','target','baseline_error')})
public={'format':'garry-repertoire-v1','version':'3.1.0','source_split':'train','cases':bank,'summary':{g:{'examples':sum(c['observation']['game']==g for c in bank),'categories':dict(Counter(c['category'] for c in bank if c['observation']['game']==g))} for g in GAMES}}
(root/'web/models/garry-repertoire.json').write_text(json.dumps(public,separators=(',',':')),encoding='utf-8')
# Errors on training examples can be replayed; errors on held-out trials remain
# quarantined and cannot enter the browser's training bank.
failures=[{'id':c['id'],'game':c['observation']['game'],'category':c['category'],'observation':c['observation'],'target':c['target'],'eligible_for_training':True} for c in data['cases'] if c['split']=='train' and c['baseline_error']]
(run/'training-errors.json').write_text(json.dumps(failures,separators=(',',':')),encoding='utf-8')
(run/'quarantined-errors.json').write_text(json.dumps(league['failures'],separators=(',',':')),encoding='utf-8')
candidate.save(root/'web/models/garry.json');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={'format':'garry-diversity-evaluation-v1','software_version':'3.1.0','architecture_changed':False,'weights_revision':'20261016-repertoire-01','seed':data['seed'],'counts':dict(Counter(c['split'] for c in data['cases'])),'dataset_summary':data['summary'],'bank_summary':public['summary'],'bank_examples':len(bank),'training_error_examples':len(failures),'quarantined_loss_trajectories':len(league['failures']),'overlap_positions':0,'overlap_families':0,'installed_games':accepted,'rejected_games':rejected,'selection':training['selection'],'solo':solo,'league':{k:v for k,v in league.items() if k not in ('failures','samples')},'shared_core_preserved':True,'position_head_preserved':True,'unselected_mode_weights_preserved':True,'source_sha256':sha(root/'versions/3.0.0/garry.json'),'installed_sha256':sha(root/'web/models/garry.json'),'bank_sha256':sha(root/'web/models/garry-repertoire.json'),'zero_defeat_target_met':False,'notes':['Position scores measure policy-only choices against exact or bounded teachers, not whole-game wins.','C4 sound choices are within 24 points of the bounded best without sacrificing a proved result.','League results unchanged: C4 candidate did not pass its position gates and C4 weights stayed frozen.','2048 candidate improved short rollouts but was rejected after full games; original 2048 weights were restored.','These small controls do not establish statistically significant whole-game superiority.']}
heldout=[c for c in data['cases'] if c['split']=='test']
report['active_test_metrics']={g:metrics(candidate,heldout,g) for g in GAMES}
for g,s in report['selection'].items():s['installed']=g in accepted;s['final_reason']='passed_controls' if g in accepted else rejected[g]
(root/'web/models/garry-diversity-evaluation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
history=json.loads((root/'web/models/garry-training.json').read_text());history['diversity_training']={k:v for k,v in report.items() if k not in ('dataset_summary','selection','solo','league')};history['active_model']={'version':'3.1.0','weights_revision':report['weights_revision'],'sha256':report['installed_sha256'],'architecture_changed':False};(root/'web/models/garry-training.json').write_text(json.dumps(history,indent=2)+'\n',encoding='utf-8')
snap=root/'versions/3.0.0';manifest={'version':'3.0.0','sha256':{p.name:sha(p) for p in snap.iterdir() if p.is_file() and p.name!='manifest.json'}};(snap/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'installed_games':accepted,'rejected':rejected,'bank':len(bank),'counts':report['counts'],'training_errors':len(failures),'quarantined_losses':len(league['failures']),'sha256':report['installed_sha256']}))
