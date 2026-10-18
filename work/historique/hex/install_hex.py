from pathlib import Path
import shutil,json,hashlib
ROOT=Path(r'C:\Users\gabor\code\playi');HERE=Path(__file__).parent
def edit(file,pairs):
    p=ROOT/file;s=p.read_text(encoding='utf-8')
    for old,new in pairs:
        if old not in s:raise RuntimeError(f'Missing marker {file}: {old[:70]}')
        s=s.replace(old,new)
    p.write_text(s,encoding='utf-8')
archive=ROOT/'versions/4.0.0'
if not archive.exists():
    archive.mkdir()
    for rel in ('web/models/garry.json','web/engine.js','web/agents.json','web/strategy-planner.js','web/strategy-games.js','logic_arena/strategy_planner.py','logic_arena/strategy_rules.py','logic_arena/general.py','web/connect4-search.wasm'):
        shutil.copy2(ROOT/rel,archive/Path(rel).name)
    manifest={'version':'4.0.0','architecture':[2494,48,48,3617],'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in archive.iterdir()}}
    (archive/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
for f,target in [('hex_rules.py','logic_arena/hex_rules.py'),('hex_planner.py','logic_arena/hex_planner.py'),('hex-games.js','web/hex-games.js'),('hex-planner.js','web/hex-planner.js')]:shutil.copy2(HERE/f,ROOT/target)
edit('logic_arena/games.py',[("GAMES = {g.name:",'''class Hex(Game):
    name='hex'
    players=2
    def __init__(self,seed=0,options=None):
        super().__init__(seed,options)
        from .hex_rules import new_hex
        self.board,self.hex_state=new_hex()
    def observation(self):
        return {**super().observation(),'hex_state':deepcopy(self.hex_state)}
    def legal_actions(self):
        from .hex_rules import legal_hex
        return [] if self.done else legal_hex(self.board,self.hex_state)
    def apply(self,action):
        from .hex_rules import step_hex
        result=step_hex(self.board,self.current_player,action,self.hex_state)
        self.current_player=result['player'];self.done=result['done'];self.winner=result['winner'];self.score=result['score'];self.hex_state=result['state']
        return result['reward']

GAMES = {g.name:'''),('Draughts, Breakthrough)}','Draughts, Breakthrough, Hex)}')])
edit('logic_arena/neural.py',[
('from .strategy_rules import STRATEGY_SPECS,encode_strategy,strategy_action_index','from .strategy_rules import STRATEGY_SPECS,encode_strategy,strategy_action_index\nfrom .hex_rules import HEX_SPECS,encode_hex,hex_action_index'),
('**STRATEGY_SPECS}', '**STRATEGY_SPECS, **HEX_SPECS}'),
('    if name in STRATEGY_SPECS:', "    if name=='hex':return np.asarray(encode_hex(obs),dtype=np.float32)\n    if name in STRATEGY_SPECS:"),
('    if game in STRATEGY_SPECS:', "    if game=='hex':return hex_action_index(action)\n    if game in STRATEGY_SPECS:")])
# All old layouts are strict prefixes; identifiers move after the new features.
p=ROOT/'logic_arena/migration.py';s=p.read_text(encoding='utf-8')
a=s.index("    if data.get('games')");b=s.index("    for key,length",a)
s=s[:a]+'''    layouts=[(list(LEGACY_GAMES),1906,1912,818),(list(LEGACY_GAMES)+['reversi','nim','lightsout'],2051,2060,925),(list(LEGACY_GAMES)+['reversi','nim','lightsout','draughts','breakthrough'],2483,2494,3617)]
    layout=next((layout for layout in layouts if layout[0]==data.get('games')),None)
    if layout is None:raise ValueError('Architecture historique invalide')
    old_games,old_features,old_input,old_output=layout;h=data.get('hidden')
    if type(h) is not int or not 1<=h<=256 or data.get('input')!=old_input or data.get('output')!=old_output:raise ValueError('Architecture historique invalide')
'''+s[b:];s=s.replace("version='4.0.0'","version='5.0.0'");p.write_text(s,encoding='utf-8')
edit('logic_arena/general.py',[
("data.get('games')==list(LEGACY_GAMES)+['reversi','nim','lightsout']", "data.get('games') in (list(LEGACY_GAMES)+['reversi','nim','lightsout'],list(LEGACY_GAMES)+['reversi','nim','lightsout','draughts','breakthrough'])"),
("!= ('garry-mlp-v3','4.0.0')", "!= ('garry-mlp-v3','5.0.0')")])
edit('logic_arena/planner.py',[("    elif game in ('draughts','breakthrough'):", "    elif game=='hex':\n        from .hex_planner import hex_values\n        values,info=hex_values(obs,legal,Budget(4000,200 if time_ms is None else time_ms))\n    elif game in ('draughts','breakthrough'):")])
edit('logic_arena/harness.py',[
('    "lightsout": {"row":"0..4","col":"0..4"},','    "lightsout": {"row":"0..4","col":"0..4"},\n    "hex": [{"row":"0..6","col":"0..6"},{"swap":True}],'),
('[2494,48,48,3617]', '[2595,48,48,3667]')])
edit('web/engine.js',[
("import {STRATEGY_NAMES", "import {HEX_SPECS,newHex,legalHex,stepHex,encodeHex,hexActionIndex} from './hex-games.js';\nimport {STRATEGY_NAMES"),
("...STRATEGY_NAMES}","...STRATEGY_NAMES,hex:'Hex 7 × 7'}"),('...STRATEGY_SPECS}', '...STRATEGY_SPECS,...HEX_SPECS}'),
(" if(STRATEGY_NAMES[name]){", " if(name==='hex'){const next=newHex();this.board=next.board;this.hexState=next.state;return;}\n if(STRATEGY_NAMES[name]){"),
("'draughts','breakthrough'].includes(this.name)", "'draughts','breakthrough','hex'].includes(this.name)"),
("moves:this.moves,...", "moves:this.moves,...(this.name==='hex'?{hex_state:clone(this.hexState)}:{}),..."),
("legal(){if(this.done)return [];", "legal(){if(this.done)return [];if(this.name==='hex')return legalHex(this.board,this.hexState);"),
(" if(STRATEGY_NAMES[this.name]){", " if(this.name==='hex'){const s=stepHex(b,this.player,a,this.hexState);Object.assign(this,{player:s.player,done:s.done,winner:s.winner,score:s.score,hexState:s.state});return s.reward;}\n if(STRATEGY_NAMES[this.name]){"),
("export function encode(o){", "export function encode(o){if(o.game==='hex')return Float32Array.from(encodeHex(o));"),
("export function actionIndex(game,a){", "export function actionIndex(game,a){if(game==='hex')return hexActionIndex(a);"),
("...Object.keys(STRATEGY_SPECS)]", "...Object.keys(STRATEGY_SPECS),...Object.keys(HEX_SPECS)]"),
("JSON.stringify(d.games)===JSON.stringify([...LEGACY_GAMES,'reversi','nim','lightsout'])", "[9,11].includes(d.games?.length)"),
("d.format==='garry-mlp-v3'&&d.version==='4.0.0')||d.name", "d.format==='garry-mlp-v3'&&d.version==='5.0.0')||d.name"),
("version:games.length===6?'2.0.0':'4.0.0'", "version:games.length===6?'2.0.0':'5.0.0'")])
p=ROOT/'web/migration.js';s=p.read_text(encoding='utf-8');a=s.index(' const h=d.hidden');b=s.index(' for(const [k,n]',a)
s=s[:a]+''' const layouts=[[LEGACY_GAMES,1906,1912,818],[[...LEGACY_GAMES,'reversi','nim','lightsout'],2051,2060,925],[[...LEGACY_GAMES,'reversi','nim','lightsout','draughts','breakthrough'],2483,2494,3617]];
 const layout=layouts.find(l=>JSON.stringify(l[0])===JSON.stringify(d.games));if(!layout)throw Error('Architecture historique invalide');
 const [oldGames,oldFeatures,oldInput,oldOutput]=layout,h=d.hidden;
 if(!Number.isInteger(h)||h<1||h>256||d.input!==oldInput||d.output!==oldOutput)throw Error('Architecture historique invalide');
'''+s[b:];s=s.replace("version:'4.0.0'","version:'5.0.0'");p.write_text(s,encoding='utf-8')
edit('web/planner.js',[
("import {strategyValues}", "import {hexValues} from './hex-planner.js';\nimport {strategyValues}"),
("CONNECT_LIMITS[9]:['draughts'", "CONNECT_LIMITS[9]:o.game==='hex'?4000:['draughts'"),
("['draughts','breakthrough'].includes(o.game)?200", "['draughts','breakthrough','hex'].includes(o.game)?200"),
("const solver={", "const solver={hex:(o,legal,logits,budget)=>hexValues(o,legal,budget),")])
edit('web/teachers.js',[
("import {strategyValues}", "import {hexValues} from './hex-planner.js';\nimport {strategyValues}"),
("export function teacher(o,legal){", "export function teacher(o,legal){\n if(o.game==='hex'){const start=performance.now(),budget={nodes:0,tick(){if(this.nodes++>=300||performance.now()-start>=30)throw Error('budget');}},result=hexValues(o,legal,budget,{maxDepth:2,beam:6});return selectQuality(result.action_values,10,Array(50).fill(0),'hex').selected.action;}")])
edit('logic_arena/diversity.py',[
("    if game in ('draughts','breakthrough'):return", "    if game=='hex':return digest([game,b,p,obs.get('hex_state')])\n    if game in ('draughts','breakthrough'):return"),
("    elif game in ('draughts','breakthrough'):", "    elif game=='hex':\n        from .hex_planner import hex_values\n        values,info=hex_values(obs,legal,Budget(nodes,10000),max_depth=2,beam=8)\n        info['category']='opening' if obs['moves']<8 else 'endgame' if sum(not v for row in obs['board'] for v in row)<=10 else 'middle'\n    elif game in ('draughts','breakthrough'):"),
("('sliding_puzzle','nim','draughts','breakthrough'):return", "('sliding_puzzle','nim','draughts','breakthrough','hex'):return")])
edit('examples/build_garry_repertoire.py',[("('reversi','nim','lightsout','draughts','breakthrough'):","('reversi','nim','lightsout','draughts','breakthrough','hex'):")])
edit('web/repertoire.js',[
("breakthrough:[8,8]}","breakthrough:[8,8],hex:[7,7]}"),
("'draughts_state'];", "'draughts_state','hex_state'];"),
("breakthrough:2}","breakthrough:2,hex:2}"),
("player:o.current_player,draughtsState", "player:o.current_player,hexState:o.hex_state,draughtsState"),
("  const env=Object.assign", "  if(o.game==='hex'){const s=o.hex_state,coord=p=>Array.isArray(p)&&p.length===2&&p.every(v=>Number.isInteger(v)&&v>=0&&v<7);if(!s||Object.keys(s).some(k=>!['colors','swap_available','winning_path'].includes(k))||!Array.isArray(s.colors)||s.colors.length!==2||![1,2].includes(s.colors[0])||s.colors[1]!==3-s.colors[0]||typeof s.swap_available!=='boolean'||!Array.isArray(s.winning_path)||s.winning_path.length>49||s.winning_path.some(p=>!coord(p)))throw Error('État Hex invalide');}\n  const env=Object.assign")])
p=ROOT/'web/agents.json';data=json.loads(p.read_text());data.update(version='5.0.0',previous_version='4.0.0');data['agents']['hex']={'codename':'garry','mode':'hex'}
for a in data['agents'].values():a['version']='5.0.0'
p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
edit('pyproject.toml', [('version = "4.0.0"','version = "5.0.0"'),('onze jeux','douze jeux')])
edit('logic_arena/__main__.py',[('onze jeux','douze jeux')])
print('Hex rules, swap ownership, search, learning and strict 4.0 migration installed.')
