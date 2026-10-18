"""Exclude public positions from earlier league trials before this cycle trains."""
import sys,json
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path.cwd()))
from logic_arena.diversity import canonical_key,SPLITS,GAMES
from examples.train_garry_curriculum import atomic_json
run=Path('training-runs/garry-repertoire-20261016-cycle02');data=json.loads((run/'dataset.json').read_text())
forbidden=set();sources=[]
def walk(value):
    if isinstance(value,dict):
        if 'game' in value and 'board' in value:forbidden.add(canonical_key(value));return
        for child in value.values():walk(child)
    elif isinstance(value,list):
        for child in value:walk(child)
for name in ('garry-diversity-20261016','garry-diversity-balanced-20261016'):
    for filename in ('league.json','quarantined-errors.json'):
        p=run.parent/name/filename
        if p.is_file():walk(json.loads(p.read_text()));sources.append(str(p))
removed=Counter(c['split'] for c in data['cases'] if c['id'] in forbidden)
data['cases']=[c for c in data['cases'] if c['id'] not in forbidden]
for g in GAMES:
    for s in SPLITS:
        selected=[c for c in data['cases'] if c['observation']['game']==g and c['split']==s]
        data['summary'][g][s].update(samples=len(selected),families=len({c['family'] for c in selected}),categories=dict(Counter(c['category'] for c in selected)),phases=dict(Counter(c.get('phase','not_applicable') for c in selected)),sources=dict(Counter(c['source'] for c in selected)),teacher_action_mass=[sum(c['target'][i] for c in selected) for i in range(len(selected[0]['target']))])
data['history_audit'].update(quarantine_sources=sources,quarantined_public_states=len(forbidden),quarantined_states_removed=dict(removed),quarantine_overlap_after_filter=0)
(run/'dataset.json').replace(run/'generated-dataset.json');atomic_json(run/'dataset.json',data)
print(json.dumps({'cases':len(data['cases']),'quarantined':len(forbidden),'removed':dict(removed),'audit':data['history_audit']}))
