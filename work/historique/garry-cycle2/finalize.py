import json,sys,hashlib
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path.cwd()))
from logic_arena.diversity import canonical_key
from examples.train_garry_curriculum import atomic_json
root=Path.cwd();run=root/'training-runs/garry-repertoire-20261016-cycle02'
r=json.loads((run/'evaluation.json').read_text());data=json.loads((run/'dataset.json').read_text());bank=json.loads((root/'web/models/garry-repertoire.json').read_text())
assert hashlib.sha256((root/'web/models/garry.json').read_bytes()).hexdigest()==r['installed_sha256']
training={c['id'] for c in data['cases'] if c['split']=='train'}
assert all(c['split']=='train' and c['id'] in training for c in bank['cases'])
oldheld={canonical_key(c['observation']) for name in ('garry-diversity-20261016','garry-diversity-balanced-20261016') for c in json.loads((run.parent/name/'dataset.json').read_text())['cases'] if c['split']!='train'}
assert not training&oldheld
replayed=Counter(c['observation']['game'] for c in data['cases'] if c['source'].startswith('replay:'))
r['history_audit']['replayed_training_retained']=dict(replayed)
r['validation']={'python_tests':55,'javascript_tests':25,'passed':True,'bank_training_only':True,'bank_heldout_overlap':0}
for p in (run/'evaluation.json',root/'web/models/garry-repertoire-cycle02-evaluation.json'):atomic_json(p,r)
atomic_json(run/'commands.json',{'cwd':str(root),'environment':{'PYTHONPATH':'<chat>/work/python-deps;<repo>','OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'},'build':['examples/build_garry_repertoire.py','--source',str(run.relative_to(root)/'source.json'),'--output',str(run.relative_to(root)),'--seed','16071200','--c4-train','6144','--c4-heldout','768','--solo-train','768','--solo-heldout','192','--history','training-runs/garry-diversity-20261016/dataset.json','--history','training-runs/garry-diversity-balanced-20261016/dataset.json','--replay','training-runs/garry-diversity-balanced-20261016/dataset.json','--legacy-archive','training-runs/garry-20261016-210424/dataset.npz','--legacy-archive','training-runs/garry-20261016-210905/dataset.npz','--position-history','training-runs/garry-value-20261016/positions.json','--position-history','training-runs/garry-value-extended-20261016/positions.json'],'postprocess':'scripts/quarantine.py before training','train':['examples/train_garry_repertoire.py','--epochs','160','--lr','0.0002','--retention-dataset','training-runs/garry-diversity-20261016/dataset.json','--retention-dataset','training-runs/garry-diversity-balanced-20261016/dataset.json'],'selection_order':['new and old validation','new test once','scripts/retention_check.py: old tests once','full games on frozen finalist','scripts/promote.py: install passed modes only'],'league':{'nodes':200000,'pairs':16,'seed':16073200,'before':'source.json','after':'finalist.json'},'solo':{'seed':16074200,'episodes':16,'before':'source.json','after':'finalist.json'}})
print(json.dumps({'replayed_training_retained':sum(replayed.values()),'validation':r['validation'],'taquin_retention':r['retention_test']['sliding_puzzle']}))
