import json
from pathlib import Path
base=Path(r'C:\Users\gabor\code\playi\training\continuous')
current='19159dcbbae2412c876e1c729a3b606f'
historical={};counts={}
for folder in base.iterdir():
 if folder.name==current or not (folder/'cases.jsonl').is_file():continue
 n=0
 with (folder/'cases.jsonl').open(encoding='utf-8') as stream:
  for line in stream:
   c=json.loads(line);historical.setdefault(c['id'],set()).add(c['split']);n+=1
 counts[folder.name]=n
overlaps={};examples=[];n=0
with (base/current/'cases.jsonl').open(encoding='utf-8') as stream:
 for line in stream:
  try:c=json.loads(line)
  except json.JSONDecodeError:continue
  n+=1
  for split in historical.get(c['id'],set()):
   key=split+'->'+c['split'];overlaps[key]=overlaps.get(key,0)+1
   if split in ('test','validation') and c['split']=='train' and len(examples)<5:examples.append({'id':c['id'],'old_split':split,'current_split':c['split'],'game':c['observation']['game']})
report={'prior_cases':counts,'current_cases':n,'overlaps':overlaps,'heldout_to_train_examples':examples}
Path(r'C:\Users\gabor\code\logic-lab\outputs\audit-splits-continuous.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
