import sys,json,hashlib
from pathlib import Path
import numpy as np
sys.path.insert(0,r'C:\Users\gabor\code\playi')
from logic_arena.general import GarryPolicy,GAMES,FEATURES,INPUT_OFFSETS,OUTPUT_OFFSETS
from logic_arena.neural import SPECS
from logic_arena.continuous_history import historical_case_ids
root=Path(r'C:\Users\gabor\code\playi');folder=root/'training/continuous/8a996a3b756d469aa0ff2be307fb554b';prior,_=historical_case_ids(folder.parent,folder)
for source in ('training/go-6.0.0/cases.json','training/competitive-5.0.0/cases.json'):prior.update(c['id'] for c in json.loads((root/source).read_text(encoding='utf-8'))['cases'])
counts={};overlaps=[];derived=0;checked=0
with (folder/'cases.jsonl').open(encoding='utf-8') as stream:
 for line in stream:
  try:c=json.loads(line)
  except json.JSONDecodeError:continue
  checked+=1;counts[c['split']]=counts.get(c['split'],0)+1
  if c['id'] in prior:overlaps.append(c['id'])
  if c['source']=='training_position_continuation':
   derived+=1
   if c['split']!='train':raise RuntimeError('Départ ciblé employé hors du train')
raw=(root/'web/models/garry.json').read_bytes();active=GarryPolicy.from_dict(json.loads(raw));initial=GarryPolicy.load(folder/'initial.json');targets=('go','hex','gomoku');changed_rows=set();changed_cols=set()
for game in targets:
 ni,no=SPECS[game];a=INPUT_OFFSETS[game];b=OUTPUT_OFFSETS[game];changed_rows.update(range(a,a+ni));changed_rows.add(FEATURES+GAMES.index(game));changed_cols.update(range(b,b+no))
rows=[i for i in range(active.w1.shape[0]) if i not in changed_rows];cols=[i for i in range(active.w2.shape[1]) if i not in changed_cols]
np.testing.assert_array_equal(active.w1[rows],initial.w1[rows]);np.testing.assert_array_equal(active.w2[:,cols],initial.w2[:,cols]);np.testing.assert_array_equal(active.b2[cols],initial.b2[cols]);np.testing.assert_array_equal(active.b1,initial.b1)
for k in ('w','b'):np.testing.assert_array_equal(active.core[k],initial.core[k])
assert active.position_head==initial.position_head and active.search_memory==initial.search_memory
for game in GAMES:
 if game not in targets:assert active.game_steps[game]==initial.game_steps[game]
state=json.loads((folder/'status.json').read_text(encoding='utf-8'));promotions=[]
if (folder/'evaluations.jsonl').is_file():
 with (folder/'evaluations.jsonl').open(encoding='utf-8') as stream:
  for line in stream:
   try:e=json.loads(line)
   except json.JSONDecodeError:continue
   if e['accepted']:promotions.append(e)
report={'ok':not overlaps,'job':folder.name,'pid':state['pid'],'started_at':state['started_at'],'ends_at':state['ends_at'],'duration_seconds':state['duration_seconds'],'state':state['state'],'stage':state.get('programme_stage'),'moves_total':state['moves_total'],'cycles':state['cycles'],'promotions':state['promotions'],'historical_quarantine':state['history_quarantined_cases'],'checked_new_cases':checked,'splits':counts,'historical_overlaps':overlaps,'derived_train_cases':derived,'preserved_games':[g for g in GAMES if g not in targets],'preservation_exact':True,'active_model_sha256':hashlib.sha256(raw).hexdigest(),'accepted_validations':promotions,'remaining_seconds':state['remaining_seconds']}
Path(r'C:\Users\gabor\code\logic-lab\outputs\verification-garry-30min.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='accepted_validations'}))
if overlaps:raise SystemExit(1)
