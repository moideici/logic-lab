from pathlib import Path
import hashlib,json
from logic_arena.general import GarryPolicy
from logic_arena.value import default_head,features
import numpy as np
root=Path.cwd();run=root/'training-runs/garry-value-20261016';report=json.loads((run/'conservative-validation.json').read_text());before=report['variants']['0'];after=report['variants']['0.5']
assert after['losses']<before['losses'] and after['wins']+after['draws']/2>=before['wins']+before['draws']/2
model=GarryPolicy.load(root/'web/models/garry.json');old=GarryPolicy.load(root/'versions/2.0.0/garry.json')
for key in ('w1','b1','w2','b2'):assert np.array_equal(getattr(model,key),getattr(old,key))
for key in ('w','b'):assert np.array_equal(model.core[key],old.core[key])
raw=json.loads((run/'head.json').read_text());baseline=default_head()['weights'];head={**raw,'weights':[(a+b)/2 for a,b in zip(raw['weights'],baseline)],'revision':'20261016-position-02-mix50','enabled':True};model.position_head=head
data=json.loads((run/'positions.json').read_text());val=[d for d in data if d['group']%5==0];x=np.asarray([d['x'] for d in val]);y=np.asarray([d['y'] for d in val]);rmse=float(np.sqrt(np.mean((x@head['weights']-y)**2)))
model.save(root/'web/models/garry.json')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
metrics=json.loads((run/'metrics.json').read_text());training=json.loads((root/'web/models/garry-training.json').read_text())
training['position_training']={'software_version':'3.0.0','architecture_change':'Added compact 32-feature position-value branch; existing policy matrices unchanged','weights_revision':head['revision'],'mix':.5,'samples':head['samples'],'source_metrics':metrics,'installed_head_rmse':rmse,'duels':report,'validation_seed':7800000,'policy_weights_unchanged':True,'non_connect4_behavior_unchanged_by_value_head':True,'source_sha256':sha(root/'versions/2.0.0/garry.json'),'installed_sha256':sha(root/'web/models/garry.json'),'zero_defeat_target_met':False,'extended_experiment':'1600 trajectories, 9963 train and 2527 validation positions; not selected; more training did not improve the selection matches'}
(root/'web/models/garry-training.json').write_text(json.dumps(training,indent=2)+'\n',encoding='utf-8')
public={**report,'installed_head':head['revision'],'mix':.5,'source_metrics':metrics,'installed_head_rmse':rmse,'source_sha256':sha(root/'versions/2.0.0/garry.json'),'installed_sha256':sha(root/'web/models/garry.json'),'wasm_sha256':sha(root/'web/connect4-search.wasm'),'zero_defeat_target_met':False,'note':'Measured reduction of defeats on one fixed-node sample; no claim of statistically established superiority or universal invincibility. Raw-head and extended-data trials are retained separately.'}
(root/'web/models/garry-strength-evaluation.json').write_text(json.dumps(public,indent=2)+'\n',encoding='utf-8')
snapshot=root/'versions/2.0.0';manifest={'version':'2.0.0','description':'Frozen policy weights, learned-policy training report and compiled search engine before the position-value branch','sha256':{p.name:sha(p) for p in snapshot.iterdir() if p.is_file() and p.name!='manifest.json'}}
(snapshot/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'revision':head['revision'],'rmse':rmse,'duels_before':before,'duels_after':after,'sha256':sha(root/'web/models/garry.json')}))
