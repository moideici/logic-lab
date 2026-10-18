from pathlib import Path
import json,sys
sys.path.insert(0,r'C:\Users\gabor\code\playi')
from logic_arena.continuous_history import historical_case_ids
base=Path(r'C:\Users\gabor\code\playi\training\continuous');folder=base/'5ed011499eae4dac96a63e9c83244eff'
prior,sources=historical_case_ids(base,folder);checked=0;collisions=[];partial=0
with (folder/'cases.jsonl').open(encoding='utf-8') as stream:
 for line in stream:
  try:case=json.loads(line)
  except json.JSONDecodeError:partial+=1;continue
  checked+=1
  if case['id'] in prior:collisions.append({'id':case['id'],'split':case['split']})
status=json.loads((folder/'status.json').read_text(encoding='utf-8'))
report={'ok':not collisions,'job':folder.name,'historical_unique_states':len(prior),'new_states_checked':checked,'collisions':collisions,'partial_line_skipped':partial,'state':status['state'],'moves_total':status['moves_total'],'promotions':status['promotions'],'remaining_seconds':status['remaining_seconds'],'ends_at':status['ends_at']}
Path(r'C:\Users\gabor\code\logic-lab\outputs\verification-quarantaine-entrainement.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if collisions:raise SystemExit(1)
