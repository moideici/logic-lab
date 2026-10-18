"""Stage the compatible 3.2 search feature; preserve every neural parameter."""
from pathlib import Path
import json
root=Path(r'C:\Users\gabor\code\playi');stage=Path(__file__).parent/'product';stage.mkdir(exist_ok=True)
def edit(path,replacements):
    text=(root/path).read_text(encoding='utf-8')
    for old,new in replacements:
        assert old in text,(path,old);text=text.replace(old,new)
    out=stage/path;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(text,encoding='utf-8',newline='\n')
edit('logic_arena/general.py',[
 ('from .value import default_head, validate_head, features','from .value import default_head, validate_head, features\nfrom .search_memory import empty_memory,validate_memory'),
 ('self.position_head = default_head()','self.position_head = default_head()\n        self.search_memory = empty_memory()'),
 ("'position_head':copy.deepcopy(self.position_head)","'position_head':copy.deepcopy(self.position_head),'search_memory':copy.deepcopy(self.search_memory)"),
 ("('garry-mlp-v2','3.1.0')","('garry-mlp-v2','3.1.0'),('garry-mlp-v2','3.2.0')"),
 ("model.position_head=validate_head(data.get('position_head',default_head() if data.get('format')=='garry-mlp-v1' else None))","model.position_head=validate_head(data.get('position_head',default_head() if data.get('format')=='garry-mlp-v1' else None))\n        model.search_memory=validate_memory(data.get('search_memory',empty_memory()))"),
 ('def position_head(self):return self.model.position_head','def position_head(self):return self.model.position_head\n    @property\n    def search_memory(self):return self.model.search_memory')])
edit('web/engine.js',[
 ("import {defaultPositionHead", "import {validateSearchMemory} from './search-memory.js';\nimport {defaultPositionHead"),
 ("['3.0.0','3.1.0']","['3.0.0','3.1.0','3.2.0']"),
 ("this.positionHead=validatePositionHead(d.position_head??(d.format==='garry-mlp-v1'?defaultPositionHead():null));","this.positionHead=validatePositionHead(d.position_head??(d.format==='garry-mlp-v1'?defaultPositionHead():null));\n  this.searchMemory=validateSearchMemory(d.search_memory);"),
 ('position_head:structuredClone(this.positionHead),games:','position_head:structuredClone(this.positionHead),search_memory:structuredClone(this.searchMemory),games:'),
 ('get positionHead(){return this.model.positionHead;}','get positionHead(){return this.model.positionHead;}\n get searchMemory(){return this.model.searchMemory;}')])
edit('web/planner.js',[('positionHead:model.positionHead','positionHead:model.positionHead,searchMemory:model.searchMemory')])
edit('logic_arena/planner.py',[("position_head=getattr(model,'position_head',None)","position_head=getattr(model,'position_head',None),search_memory=getattr(model,'search_memory',None)")])
edit('web/index.html',[('3.1.0','3.2.0')]);edit('pyproject.toml',[('version = "3.1.0"','version = "3.2.0"')])
for name in ('tests/garry.test.mjs','tests/levels.test.mjs','tests/test_versions.py'):edit(name,[('3.1.0','3.2.0')])
manifest=json.loads((root/'web/agents.json').read_text());manifest['version']='3.2.0';manifest['previous_version']='3.1.0'
for a in manifest['agents'].values():a['version']='3.2.0'
(stage/'web/agents.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
model=json.loads((root/'web/models/garry.json').read_text());model['version']='3.2.0';model['search_memory']=json.loads((Path(__file__).parent/'memory.json').read_text())
(stage/'web/models').mkdir(exist_ok=True);(stage/'web/models/garry.json').write_text(json.dumps(model,separators=(',',':'),allow_nan=False),encoding='utf-8')
for src,dest in [('candidate.ts','search/connect4-search.ts'),('candidate.wasm','web/connect4-search.wasm'),('connect4-runtime.js','web/connect4-runtime.js'),('connect4_wasm.py','logic_arena/connect4_wasm.py'),('search-memory.js','web/search-memory.js'),('search_memory.py','logic_arena/search_memory.py')]:
    target=stage/dest;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((Path(__file__).parent/src).read_bytes())
print(json.dumps({'version':'3.2.0','files':len(list(stage.rglob('*.*'))),'memory':len(model['search_memory']['entries'])}))
