from pathlib import Path
import shutil,json,hashlib
R=Path(r'C:\Users\gabor\code\playi');S=Path(__file__).parent
snapshot=R/'versions/5.0.0';assert not snapshot.exists();snapshot.mkdir()
files={'garry.json':'web/models/garry.json','agents.json':'web/agents.json','engine.js':'web/engine.js','general.py':'logic_arena/general.py','planner.py':'logic_arena/planner.py','planner.js':'web/planner.js','migration.py':'logic_arena/migration.py','migration.js':'web/migration.js','connect4-search.wasm':'web/connect4-search.wasm'}
manifest={'version':'5.0.0','architecture':[3055,48,48,3894],'files':{}}
for name,source in files.items():shutil.copyfile(R/source,snapshot/name);manifest['files'][name]=hashlib.sha256((snapshot/name).read_bytes()).hexdigest()
(snapshot/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
for name in ('go_rules.py','go_planner.py'):shutil.copyfile(S/name,R/'logic_arena'/name)
for name in ('go-games.js','go-planner.js'):shutil.copyfile(S/name,R/'web'/name)
def edit(file,old,new):
 p=R/file;t=p.read_text(encoding='utf-8');assert old in t,(file,old[:100]);p.write_text(t.replace(old,new,1),encoding='utf-8')
edit('logic_arena/games.py','GAMES = {g.name:', '''class Go(Game):
    name='go';players=2
    def __init__(self,seed=0,options=None):
        super().__init__(seed,options)
        from .go_rules import new_go
        self.board,self.go_state=new_go(self.options.get('size',19),self.options.get('komi',7.5))
    def observation(self):return {**super().observation(),'go_state':deepcopy(self.go_state)}
    def legal_actions(self):
        from .go_rules import legal_go
        return [] if self.done else legal_go(self.board,self.current_player,self.go_state)
    def apply(self,action):
        from .go_rules import step_go
        s=step_go(self.board,self.current_player,action,self.go_state)
        self.current_player=s['player'];self.done=s['done'];self.winner=s['winner'];self.score=s['score'];self.go_state=s['state'];return s['reward']

GAMES = {g.name:''')
edit('logic_arena/games.py','Breakthrough, Hex, Gomoku)}','Breakthrough, Hex, Gomoku, Go)}')
edit('logic_arena/games.py','else {"difficulty"} if name == "sudoku" else set()','else {"difficulty"} if name == "sudoku" else {"size","komi"} if name == "go" else set()')
edit('logic_arena/neural.py','from .gomoku_rules import','from .go_rules import GO_SPECS,encode_go,go_action_index\nfrom .gomoku_rules import')
edit('logic_arena/neural.py','**HEX_SPECS, **GOMOKU_SPECS}','**HEX_SPECS, **GOMOKU_SPECS, **GO_SPECS}')
edit('logic_arena/neural.py',"    if name=='gomoku':", "    if name=='go':return np.asarray(encode_go(obs),dtype=np.float32)\n    if name=='gomoku':")
edit('logic_arena/neural.py',"    if game=='gomoku':", "    if game=='go':return go_action_index(action)\n    if game=='gomoku':")
edit('logic_arena/planner.py',"    elif game=='gomoku':", "    elif game=='go':\n        from .go_planner import go_values\n        values,info=go_values(obs,legal,Budget(1000,250 if time_ms is None else time_ms))\n    elif game=='gomoku':")
edit('logic_arena/harness.py','    "gomoku":', '    "go": [{"row":"0..size-1","col":"0..size-1"},{"pass":True},{"dead":["row","col"]},{"accept":True},{"resume":True},{"resign":True}],\n    "gomoku":')
edit('logic_arena/harness.py','[3055,48,48,3894]','[4872,48,48,4259]')
# Add the exact previous thirteen-game layout to lossless import migration.
edit('logic_arena/migration.py',"2583,2595,3667)]", "2583,2595,3667),(list(LEGACY_GAMES)+['reversi','nim','lightsout','draughts','breakthrough','hex','gomoku'],3042,3055,3894)]")
edit('logic_arena/migration.py',"version='5.0.0'", "version='6.0.0'")
edit('logic_arena/general.py',"        if data.get('format')=='garry-mlp-v3' and data.get('version')=='5.0.0'", "        if data.get('format')=='garry-mlp-v3' and data.get('version')=='5.0.0' and data.get('games')==list(LEGACY_GAMES)+['reversi','nim','lightsout','draughts','breakthrough','hex','gomoku']:\n            data=upgrade_legacy(data,SPECS,default_head())\n        if data.get('format')=='garry-mlp-v3' and data.get('version')=='5.0.0'")
edit('logic_arena/general.py',"!= ('garry-mlp-v3','5.0.0')", "!= ('garry-mlp-v3','6.0.0')")
edit('web/engine.js',"import {GOMOKU_SPECS", "import {GO_SPECS,newGo,legalGo,stepGo,encodeGo,goActionIndex} from './go-games.js';\nimport {GOMOKU_SPECS")
edit('web/engine.js',"gomoku:'Gomoku · Swap2'}", "gomoku:'Gomoku · Swap2',go:'Go'}")
edit('web/engine.js','...HEX_SPECS,...GOMOKU_SPECS}', '...HEX_SPECS,...GOMOKU_SPECS,...GO_SPECS}')
edit('web/engine.js',"name==='sudoku'?['difficulty']:[]", "name==='sudoku'?['difficulty']:name==='go'?['size','komi']:[]")
edit('web/engine.js'," if(name==='gomoku'){", " if(name==='go'){const next=newGo(options.size??19,options.komi??7.5);this.board=next.board;this.goState=next.state;return;}\n if(name==='gomoku'){")
p=R/'web/engine.js';t=p.read_text(encoding='utf-8').replace("'hex','gomoku'].includes(this.name)","'hex','gomoku','go'].includes(this.name)");p.write_text(t,encoding='utf-8')
edit('web/engine.js',"...(this.name==='gomoku'?", "...(this.name==='go'?{go_state:clone(this.goState)}:{}),...(this.name==='gomoku'?")
edit('web/engine.js',"if(this.name==='gomoku')return legalGomoku", "if(this.name==='go')return legalGo(this.board,this.player,this.goState);if(this.name==='gomoku')return legalGomoku")
edit('web/engine.js'," if(this.name==='gomoku'){const s=", " if(this.name==='go'){const s=stepGo(b,this.player,a,this.goState);Object.assign(this,{player:s.player,done:s.done,winner:s.winner,score:s.score,goState:s.state});return s.reward;}\n if(this.name==='gomoku'){const s=")
edit('web/engine.js',"export function encode(o){", "export function encode(o){if(o.game==='go')return Float32Array.from(encodeGo(o));")
edit('web/engine.js',"export function actionIndex(game,a){", "export function actionIndex(game,a){if(game==='go')return goActionIndex(a);")
edit('web/engine.js',"...Object.keys(GOMOKU_SPECS)];", "...Object.keys(GOMOKU_SPECS),...Object.keys(GO_SPECS)];")
edit('web/migration.js',"2583,2595,3667]]", "2583,2595,3667],[[...LEGACY_GAMES,'reversi','nim','lightsout','draughts','breakthrough','hex','gomoku'],3042,3055,3894]]")
edit('web/migration.js',"version:'5.0.0'", "version:'6.0.0'")
edit('web/engine.js',"d.games?.length===12", "[12,13].includes(d.games?.length)")
edit('web/engine.js',"if(!(d.format==='garry-mlp-v3'&&d.version==='5.0.0')", "if(!(d.format==='garry-mlp-v3'&&d.version==='6.0.0')")
edit('web/engine.js',"version:games.length===6?'2.0.0':'5.0.0'", "version:games.length===6?'2.0.0':'6.0.0'")
edit('web/planner.js',"import {gomokuValues}", "import {goValues} from './go-planner.js';\nimport {gomokuValues}")
edit('web/planner.js',"const solver={gomoku:", "const solver={go:(o,legal,logits,budget)=>goValues(o,legal,budget),gomoku:")
edit('web/planner.js',"o.game==='connect4'?CONNECT_TIMES[9]:", "o.game==='connect4'?CONNECT_TIMES[9]:o.game==='go'?250:")
edit('web/teachers.js',"import {gomokuValues}", "import {goValues} from './go-planner.js';\nimport {gomokuValues}")
edit('web/teachers.js',"export function teacher(o,legal){", "export function teacher(o,legal){\n if(o.game==='go'){const began=performance.now(),budget={nodes:0,tick(){if(this.nodes++>=2||performance.now()-began>=100)throw Error('budget');}},result=goValues(o,legal,budget,{beam:2});return selectQuality(result.action_values,10,Array(365).fill(0),'go').selected.action;}")
edit('logic_arena/diversity.py',"    if game=='gomoku':", "    if game=='go':return digest([game,b,p,obs.get('go_state')])\n    if game=='gomoku':")
edit('logic_arena/diversity.py',"    elif game=='gomoku':", "    elif game=='go':\n        from .go_planner import go_values\n        values,info=go_values(obs,legal,Budget(nodes,300),beam=8);info['category']='scoring' if obs['go_state']['phase']=='scoring' else 'opening' if obs['moves']<12 else 'middle'\n    elif game=='gomoku':")
edit('logic_arena/diversity.py',"'breakthrough','hex','gomoku'):return", "'breakthrough','hex','gomoku','go'):return")
edit('examples/build_garry_repertoire.py',"'breakthrough','hex','gomoku'):", "'breakthrough','hex','gomoku','go'):")
# Defaults to 9x9 for browser training; play defaults remain 19x19.
p=R/'web/trainer.js';t=p.read_text(encoding='utf-8').replace("k==='sliding_puzzle'?{scramble:10}:{}","k==='sliding_puzzle'?{scramble:10}:k==='go'?{size:9}:{}").replace("name==='sliding_puzzle'?{scramble:10}:{}","name==='sliding_puzzle'?{scramble:10}:name==='go'?{size:9}:{}").replace("model.game==='sliding_puzzle'?{scramble:8+episode%12}:{}","model.game==='sliding_puzzle'?{scramble:8+episode%12}:model.game==='go'?{size:9}:{}");p.write_text(t,encoding='utf-8')
p=R/'web/agents.json';d=json.loads(p.read_text(encoding='utf-8'));d['version']='6.0.0';d['previous_version']='5.0.0';d['agents']['go']={'codename':'garry','version':'6.0.0','mode':'go'}
for v in d['agents'].values():v['version']='6.0.0'
p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
p=R/'pyproject.toml';p.write_text(p.read_text(encoding='utf-8').replace('version = "5.0.0"','version = "6.0.0"').replace('treize jeux','quatorze jeux'),encoding='utf-8')
print('Go integrated; model migration pending')
