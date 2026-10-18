from pathlib import Path
import hashlib,json,shutil
root=Path(r'C:\Users\gabor\code\playi');work=Path(__file__).parent;stage=work/'product'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(root/'web/models/garry.json')==sha(work/'before.json')
assert sha(root/'web/connect4-search.wasm')==sha(work/'before.wasm')
snapshot=root/'versions/3.1.0';snapshot.mkdir(exist_ok=True)
sources={'garry.json':'web/models/garry.json','connect4-search.wasm':'web/connect4-search.wasm','connect4-search.ts':'search/connect4-search.ts','connect4-runtime.js':'web/connect4-runtime.js','connect4_wasm.py':'logic_arena/connect4_wasm.py','agents.json':'web/agents.json'}
for name,path in sources.items():
    dest=snapshot/name
    if dest.exists():assert sha(dest)==sha(root/path)
    else:shutil.copyfile(root/path,dest)
(snapshot/'manifest.json').write_text(json.dumps({'version':'3.1.0','weights_revision':'20261016-repertoire-02','sha256':{name:sha(snapshot/name) for name in sources}},indent=2)+'\n',encoding='utf-8')
before=json.loads((root/'web/models/garry.json').read_text());after=json.loads((stage/'web/models/garry.json').read_text())
for key in ('w1','b1','w2','b2','core','position_head','game_steps','steps','input','hidden','output'):assert before[key]==after[key],key
for path in stage.rglob('*'):
    if path.is_file():
        dest=root/path.relative_to(stage);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
shutil.copyfile(work/'test_certified.py',root/'tests/test_certified.py');shutil.copyfile(work/'certified.test.mjs',root/'tests/certified.test.mjs')
run=root/'training-runs/garry-zero-20261017';run.mkdir(exist_ok=True)
for name in ('audit.json','duels-normal.json','positions.json','positions-heldout.json','opening-explore.json','opening-cache.json','opening-duels.json','memory.json','memory-evidence.json','memory-duels.json'):
    shutil.copyfile(work/name,run/name)
for path in work.glob('*.mjs'):shutil.copyfile(path,run/path.name)
for path in work.glob('*.py'):shutil.copyfile(path,run/path.name)
print(json.dumps({'installed':'3.2.0','search_memory_entries':len(after['search_memory']['entries']),'neural_weights_preserved':True,'model_sha256':sha(root/'web/models/garry.json'),'wasm_sha256':sha(root/'web/connect4-search.wasm')}))
