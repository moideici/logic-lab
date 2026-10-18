from pathlib import Path
import json
OUT=Path(__file__).parent/'stage';ROOT=Path(r'C:\Users\gabor\code\playi')
def edit(p,fn):
    f=OUT/p;f.write_text(fn(f.read_text(encoding='utf-8')),encoding='utf-8',newline='\n')
edit('web/engine.js',lambda s:s.replace('const {selected,info}=selectQuality(values,level,z,this.game),max=', 'const ranked=selectQuality(values,level,z,this.game),ties=values.filter(v=>v.quality[0]===ranked.selected.quality[0]),selected=ties[Math.min(ties.length-1,Math.floor(random()*ties.length))],info=ranked.info,max=').replace(' export(){const d={format:', " positionValue(o){if(o.game!==this.positionHead.game)return null;return positionFeatures(o).reduce((s,v,i)=>s+v*this.positionHead.weights[i],0);}\n export(){const d={format:"))
edit('logic_arena/neural.py',lambda s:s.replace("return selected['action']", "ties=[v['action'] for v in values if v['quality']==selected['quality']]\n        generator=self.rng if rng is None else rng\n        return ties[int(generator.integers(len(ties)))]"))
edit('web/connect4-runtime.js',lambda s:s.replace('&&depth===0',''))
edit('logic_arena/connect4_wasm.py',lambda s:s.replace(' and depth == 0',''))
# The learned head is installed only after evaluation; policy matrices stay
# bit-for-bit unchanged. Keep new architecture exports backwards compatible.
data=json.loads((ROOT/'web/models/garry.json').read_text())
from importlib.util import spec_from_file_location,module_from_spec
spec=spec_from_file_location('value',Path(__file__).parent/'value.py');m=module_from_spec(spec);spec.loader.exec_module(m)
data.update(format='garry-mlp-v2',version='3.0.0',position_head=m.default_head())
(OUT/'web/models').mkdir(exist_ok=True)
(OUT/'web/models/garry.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')
# Version assertions follow architecture, not a performance threshold.
for p in ('tests/garry.test.mjs','tests/test_versions.py'):
    f=OUT/p;f.parent.mkdir(exist_ok=True);f.write_text((ROOT/p).read_text(encoding='utf-8').replace("'2.0.0'","'3.0.0'"),encoding='utf-8')
