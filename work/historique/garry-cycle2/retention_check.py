"""Open locked retention tests once, then freeze a finalist for full games."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from logic_arena.general import GarryPolicy,GAMES
from logic_arena.diversity import metrics
from examples.train_garry_repertoire import allowed,copy_mode
from examples.train_garry_curriculum import atomic_json

run=Path('training-runs/garry-repertoire-20261016-cycle02')
base=GarryPolicy.load(run/'source.json');candidate=GarryPolicy.load(run/'training/candidate.json')
selection=json.loads((run/'training/selection.json').read_text())
old={c['id']:c for name in ('garry-diversity-20261016','garry-diversity-balanced-20261016') for c in json.loads((run.parent/name/'dataset.json').read_text())['cases'] if c['split']=='test'}
old=list(old.values());report={}
for g in GAMES:
    before=metrics(base,old,g);after=metrics(candidate,old,g)
    accepted=selection[g]['accepted'] and allowed(before,after)
    report[g]={'before':before,'after':after,'passed':allowed(before,after),'finalist':accepted}
    if not accepted:copy_mode(base,candidate,g)
candidate.save(run/'finalist.json');atomic_json(run/'retention-test.json',report)
print(json.dumps({g:{'before':v['before']['sound_choice_rate'],'after':v['after']['sound_choice_rate'],'finalist':v['finalist']} for g,v in report.items()}))
