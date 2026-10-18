"""Install only modes that passed all frozen position and full-game gates."""
import json,hashlib,sys
from pathlib import Path
from collections import Counter,defaultdict
from copy import deepcopy
import numpy as np
sys.path.insert(0,str(Path.cwd()))
from logic_arena.general import GarryPolicy,GAMES
from logic_arena.diversity import metrics,digest,canonical_key
from examples.train_garry_repertoire import copy_mode
from examples.train_garry_guarded import protected_weights_equal
from examples.train_garry_curriculum import atomic_json

root=Path.cwd();run=root/'training-runs/garry-repertoire-20261016-cycle02'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(root/'web/models/garry.json')==sha(run/'source.json'),'Active model changed during the cycle'
data=json.loads((run/'dataset.json').read_text());selection=json.loads((run/'training/selection.json').read_text())
retention=json.loads((run/'retention-test.json').read_text());solo=json.loads((run/'solo-trials.json').read_text());league=json.loads((run/'league.json').read_text())
base=GarryPolicy.load(run/'source.json');model=GarryPolicy.load(run/'finalist.json')
accepted=[g for g in GAMES if retention[g]['finalist']];rejected={g:'position_or_retention_gate' for g in GAMES if g not in accepted}
for g in list(accepted):
    passed=league['passed'] if g=='connect4' else solo['games'][g]['passed'] if g in solo['games'] else True
    if not passed:copy_mode(base,model,g);accepted.remove(g);rejected[g]='paired_full_game_regression'
assert np.array_equal(base.b1,model.b1) and base.position_head==model.position_head
assert all(np.array_equal(base.core[k],model.core[k]) for k in ('w','b'))
for g in GAMES:
    if g not in accepted:
        restored=GarryPolicy.from_dict(model.export());copy_mode(base,restored,g)
        assert np.array_equal(model.w1,restored.w1) and np.array_equal(model.w2,restored.w2) and np.array_equal(model.b2,restored.b2)
# Store a compact, balanced public replay bank from training examples only.
groups=defaultdict(list)
for c in data['cases']:
    if c['split']=='train':groups[c['observation']['game'],c['category']].append(c)
bank=[]
for key,cases in sorted(groups.items()):
    for c in sorted(cases,key=lambda c:digest([c['id'],'browser-cycle02']))[:192]:
        bank.append({k:deepcopy(c[k]) for k in ('id','split','category','source','observation','target','baseline_error')})
assert len({c['id'] for c in bank})==len(bank)
held={canonical_key(c['observation']) for c in data['cases'] if c['split']!='train'}
assert not held&{canonical_key(c['observation']) for c in bank}
bank_summary={g:{'examples':sum(c['observation']['game']==g for c in bank),'categories':dict(Counter(c['category'] for c in bank if c['observation']['game']==g))} for g in GAMES}
public={'format':'garry-repertoire-v1','version':'3.1.0','weights_revision':'20261016-repertoire-02','source_split':'train','cases':bank,'summary':bank_summary}
model.save(run/'installed.json')
if accepted:model.save(root/'web/models/garry.json')
atomic_json(root/'web/models/garry-repertoire.json',public)
test=[c for c in data['cases'] if c['split']=='test']
failures=[c for c in data['cases'] if c['split']=='train' and c['baseline_error']]
atomic_json(run/'training-errors.json',{'eligible_for_training':True,'case_ids':[c['id'] for c in failures]})
atomic_json(run/'quarantined-errors.json',league['failures'])
revision='20261016-repertoire-02' if accepted else '20261016-repertoire-01'
report={'format':'garry-repertoire-cycle-evaluation-v1','software_version':'3.1.0','architecture_changed':False,'weights_revision':revision,'run':run.name,'seed':data['seed'],'counts':dict(Counter(c['split'] for c in data['cases'])),'dataset_summary':data['summary'],'history_audit':data['history_audit'],'bank_examples':len(bank),'bank_summary':bank_summary,'installed_games':accepted,'rejected_games':rejected,'selection':selection,'retention_test':retention,'active_test_metrics':{g:metrics(model,test,g) for g in GAMES},'solo':solo,'league':{k:v for k,v in league.items() if k not in ('samples','failures')},'training_errors':len(failures),'quarantined_loss_trajectories':len(league['failures']),'shared_core_preserved':True,'position_head_preserved':True,'source_sha256':sha(run/'source.json'),'installed_sha256':sha(root/'web/models/garry.json'),'bank_sha256':sha(root/'web/models/garry-repertoire.json'),'zero_defeat_target_met':False,'notes':['Only training examples enter replay. Old validation and test cases remain excluded, including canonical mirrors; new non-TTT trials also exclude old encoded policy data and position-head data.','The finite TTT test fold is repeated, not new.','Position accuracy measures raw policy decisions; it does not establish whole-game invincibility.','All paired full-game results include losses and truncations. Small samples are not proof of statistical superiority.']}
atomic_json(run/'evaluation.json',report);atomic_json(root/'web/models/garry-repertoire-cycle02-evaluation.json',report)
history=json.loads((root/'web/models/garry-training.json').read_text())
history.setdefault('repertoire_cycles',[]).append({k:report[k] for k in ('run','software_version','weights_revision','counts','bank_examples','installed_games','rejected_games','source_sha256','installed_sha256','bank_sha256')})
history['active_model']={'version':'3.1.0','weights_revision':revision,'sha256':report['installed_sha256'],'architecture_changed':False}
atomic_json(root/'web/models/garry-training.json',history)
atomic_json(run/'manifest.json',{'software_version':'3.1.0','weights_revision':revision,'sha256':{str(p.relative_to(root)):sha(p) for p in (run/'source.json',run/'dataset.json',run/'installed.json',root/'web/models/garry.json',root/'web/models/garry-repertoire.json',root/'examples/build_garry_repertoire.py',root/'examples/train_garry_repertoire.py',root/'logic_arena/diversity.py')}})
print(json.dumps({k:report[k] for k in ('installed_games','rejected_games','counts','bank_examples','weights_revision','installed_sha256')}))
