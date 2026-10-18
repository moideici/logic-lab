from pathlib import Path
import json,shutil
ROOT=Path(r'C:\Users\gabor\code\playi')
HERE=Path(__file__).parent
def edit(path, replacements):
    p=ROOT/path;s=p.read_text(encoding='utf-8')
    for before,after in replacements:
        if before not in s:raise RuntimeError(f'Missing marker {path}: {before[:100]}')
        s=s.replace(before,after)
    p.write_text(s,encoding='utf-8')

# Freeze the last six-game version before expanding any dimensions.
snapshot=ROOT/'versions/3.2.0'
if not snapshot.exists():
    snapshot.mkdir()
    for name in ('web/models/garry.json','web/connect4-search.wasm','search/connect4-search.ts','logic_arena/general.py','logic_arena/search_memory.py','web/engine.js','web/search-memory.js','web/agents.json'):
        src=ROOT/name
        if src.exists():shutil.copy2(src,snapshot/src.name)
    (snapshot/'manifest.json').write_text(json.dumps({'name':'garry','version':'3.2.0','games':6,'architecture':[1912,48,48,818]},indent=2),encoding='utf-8')
for source,target in [('extra_rules.py','logic_arena/extra_rules.py'),('extra_planner.py','logic_arena/extra_planner.py'),('migration.py','logic_arena/migration.py'),('extra-games.js','web/extra-games.js'),('extra-planner.js','web/extra-planner.js'),('migration.js','web/migration.js')]:shutil.copy2(HERE/source,ROOT/target)

edit('logic_arena/games.py',[
('GAMES = {g.name: g for g in (TicTacToe, Game2048, Sudoku, Connect4, Minesweeper, SlidingPuzzle)}','''class ExtraGame(Game):
    def __init__(self, seed=0, options=None):
        super().__init__(seed, options)
        from .extra_rules import create_extra
        self.board=create_extra(self.name,seed)
        self.score=sum(map(sum,self.board)) if self.name=='nim' else 25-sum(map(sum,self.board)) if self.name=='lightsout' else 0
    def legal_actions(self):
        from .extra_rules import legal_extra
        return [] if self.done else legal_extra(self.name,self.board,self.current_player)
    def apply(self,action):
        from .extra_rules import step_extra
        self.current_player,self.done,self.winner,self.score,reward=step_extra(self.name,self.board,self.current_player,action)
        return reward

class Reversi(ExtraGame):
    name='reversi'
    players=2
class Nim(ExtraGame):
    name='nim'
    players=2
class LightsOut(ExtraGame):
    name='lightsout'

GAMES = {g.name: g for g in (TicTacToe, Game2048, Sudoku, Connect4, Minesweeper, SlidingPuzzle, Reversi, Nim, LightsOut)}''')])
edit('logic_arena/neural.py',[
('from .identity import agent_identity','from .identity import agent_identity\nfrom .extra_rules import EXTRA_SPECS, encode_extra, extra_action_index'),
('"sliding_puzzle": (81, 4)}','"sliding_puzzle": (81, 4), **EXTRA_SPECS}'),
('    name = obs["game"]','    name = obs["game"]\n    if name in EXTRA_SPECS:return np.asarray(encode_extra(obs),dtype=np.float32)'),
('def action_index(game, action):','def action_index(game, action):\n    if game in EXTRA_SPECS:return extra_action_index(game,action)')])
edit('logic_arena/planner.py',[
("    elif game=='2048':", "    elif game in ('reversi','nim','lightsout'):\n        from .extra_planner import extra_values\n        values,info=extra_values(obs,legal,Budget(100000,150 if time_ms is None else time_ms))\n    elif game=='2048':")])
edit('logic_arena/general.py',[
('from .search_memory import empty_memory,validate_memory','from .search_memory import empty_memory,validate_memory\nfrom .migration import LEGACY_GAMES,upgrade_legacy'),
("'format':'garry-mlp-v2'","'format':'garry-mlp-v3'"),
("        if (data.get('format'),data.get('version')) not in (('garry-mlp-v1','2.0.0'),('garry-mlp-v2','3.0.0'),('garry-mlp-v2','3.1.0'),('garry-mlp-v2','3.2.0'))", "        if (data.get('format'),data.get('version')) in (('garry-mlp-v1','2.0.0'),('garry-mlp-v2','3.0.0'),('garry-mlp-v2','3.1.0'),('garry-mlp-v2','3.2.0')):\n            data=upgrade_legacy(data,SPECS,default_head())\n        if (data.get('format'),data.get('version')) != ('garry-mlp-v3','4.0.0')"),
("        if set(models)!=set(GAMES):raise ValueError('Les six modèles sont nécessaires à la fusion')", "        games=LEGACY_GAMES if set(models)==set(LEGACY_GAMES) else GAMES\n        if set(models)!=set(games):raise ValueError('Tous les modèles sont nécessaires à la fusion')"),
("        for i,g in enumerate(GAMES):\n            m=models[g]", "        for i,g in enumerate(games):\n            m=models[g]")])

edit('web/engine.js',[
("import {validateSearchMemory}","import {EXTRA_NAMES,EXTRA_SPECS,createExtra,legalExtra,stepExtra,encodeExtra,extraActionIndex} from './extra-games.js';\nimport {LEGACY_GAMES,upgradeLegacy} from './migration.js';\nimport {validateSearchMemory}"),
("sliding_puzzle:'Taquin'}","sliding_puzzle:'Taquin',...EXTRA_NAMES}"),
("sliding_puzzle:[81,4]}","sliding_puzzle:[81,4],...EXTRA_SPECS}"),
(" const shapes=", " if(EXTRA_NAMES[name]){this.board=createExtra(name,seed);this.score=name==='nim'?this.board.flat().reduce((s,v)=>s+v,0):name==='lightsout'?25-this.board.flat().reduce((s,v)=>s+v,0):0;return;}\n const shapes="),
("['tictactoe','connect4'].includes(this.name)","['tictactoe','connect4','reversi','nim'].includes(this.name)"),
("legal(){if(this.done)return [];", "legal(){if(this.done)return [];if(EXTRA_NAMES[this.name])return legalExtra(this.name,this.board,this.player);"),
(" if(this.multiplayer){", " if(EXTRA_NAMES[this.name]){const state=stepExtra(this.name,b,this.player,a);Object.assign(this,{player:state.player,done:state.done,winner:state.winner,score:state.score});return state.reward;}\n if(this.multiplayer){"),
("export function encode(o){", "export function encode(o){if(EXTRA_NAMES[o.game])return Float32Array.from(encodeExtra(o));"),
("export function actionIndex(game,a){", "export function actionIndex(game,a){if(EXTRA_NAMES[game])return extraActionIndex(game,a);"),
("export const GARRY_GAMES=['tictactoe','connect4','2048','sudoku','minesweeper','sliding_puzzle'];", "export const GARRY_GAMES=[...LEGACY_GAMES,...Object.keys(EXTRA_SPECS)];"),
("GARRY_INPUT=GARRY_FEATURES+6", "GARRY_INPUT=GARRY_FEATURES+GARRY_GAMES.length"),
(" constructor(d){\n  if(!((d.format==='garry-mlp-v1'&&d.version==='2.0.0')||(d.format==='garry-mlp-v2'&&['3.0.0','3.1.0','3.2.0'].includes(d.version)))", " constructor(d){\n  if((d.format==='garry-mlp-v1'&&d.version==='2.0.0')||(d.format==='garry-mlp-v2'&&['3.0.0','3.1.0','3.2.0'].includes(d.version)))d=upgradeLegacy(d,SPECS,defaultPositionHead());\n  if(!(d.format==='garry-mlp-v3'&&d.version==='4.0.0')"),
("export(){const d={format:'garry-mlp-v2',name:'garry'", "export(){const d={format:'garry-mlp-v3',name:'garry'"),
("  if(GARRY_GAMES.some(g=>!old[g]))throw Error('La fusion nécessite les six modèles');", "  const games=data.length===6?LEGACY_GAMES:GARRY_GAMES;\n  if(games.some(g=>!old[g])||data.length!==games.length)throw Error('La fusion nécessite tous les modèles');\n  const features=games.reduce((n,g)=>n+SPECS[g][0],0),input=features+games.length,output=games.reduce((n,g)=>n+SPECS[g][1],0);"),
("  if(GARRY_GAMES.some(g=>old[g].hidden", "  if(games.some(g=>old[g].hidden"),
("const w1=Array(GARRY_INPUT*hidden).fill(0),w2=Array(hidden*GARRY_OUTPUT).fill(0),b2=Array(GARRY_OUTPUT).fill(0)","const w1=Array(input*hidden).fill(0),w2=Array(hidden*output).fill(0),b2=Array(output).fill(0)"),
("  GARRY_GAMES.forEach((g,i)=>", "  games.forEach((g,i)=>"),
("w1[(GARRY_FEATURES+i)*hidden+k]", "w1[(features+i)*hidden+k]"),
("w2[j*GARRY_OUTPUT+b+k]", "w2[j*output+b+k]"),
("{format:'garry-mlp-v1',name:'garry',version:'2.0.0',games:GARRY_GAMES.slice(),input:GARRY_INPUT,output:GARRY_OUTPUT", "{format:games.length===6?'garry-mlp-v1':'garry-mlp-v3',name:'garry',version:games.length===6?'2.0.0':'4.0.0',position_head:defaultPositionHead(),games:games.slice(),input,output"),
("...GARRY_GAMES.map(g=>old[g].core.steps)", "...games.map(g=>old[g].core.steps)")])
edit('web/planner.js',[
("import {CONNECT_LIMITS", "import {extraValues} from './extra-planner.js';\nimport {CONNECT_LIMITS"),
("CONNECT_TIMES[9]:TIMES[9]", "CONNECT_TIMES[9]:o.game==='reversi'?150:TIMES[9]"),
("sudoku:sudokuValues}[o.game]", "sudoku:sudokuValues,...Object.fromEntries(['reversi','nim','lightsout'].map(g=>[g,(o,legal,logits,budget)=>extraValues(o,legal,budget)]))}[o.game]")])
edit('web/teachers.js',[
("import {Game", "import {extraValues} from './extra-planner.js';\nimport {selectQuality} from './quality.js';\nimport {Game"),
("export function teacher(o,legal){", "export function teacher(o,legal){\n if(['reversi','nim','lightsout'].includes(o.game)){const began=performance.now(),budget={nodes:0,tick(){if(this.nodes++>=2000||performance.now()-began>30)throw Error('budget');}},result=extraValues(o,legal,budget);return selectQuality(result.action_values,10,null,o.game).selected.action;}")])
edit('web/repertoire.js',[
("sliding_puzzle:[3,3]}","sliding_puzzle:[3,3],reversi:[6,6],nim:[3,15],lightsout:[5,5]}"),
("sliding_puzzle:8}","sliding_puzzle:8,reversi:2,nim:1,lightsout:1}"),
("board:o.board,done:false", "board:o.board,player:o.current_player,done:false")])
edit('logic_arena/harness.py',[
('    "sliding_puzzle": {"direction": "up|down|left|right"},','    "sliding_puzzle": {"direction": "up|down|left|right"},\n    "reversi": [{"row":"0..5","col":"0..5"},{"pass":True}],\n    "nim": {"pile":"0..2","take":"1..remaining"},\n    "lightsout": {"row":"0..4","col":"0..4"},'),
('"format":"garry-mlp-v2","architecture":[1912,48,48,818]','"format":"garry-mlp-v3","architecture":[2060,48,48,925]')])
p=ROOT/'web/agents.json';d=json.loads(p.read_text());d.update(version='4.0.0',previous_version='3.2.0')
for game in ('reversi','nim','lightsout'):d['agents'][game]={'codename':'garry','mode':game}
for a in d['agents'].values():a['version']='4.0.0'
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
edit('web/index.html',[(a,b) for a,b in [('six jeux','neuf jeux'),('6 jeux','9 jeux'),('3.2.0','4.0.0'),('1912','2060'),('1 912','2 060'),('818','925'),('134 290','146 637'),('utilisés par les six jeux','utilisés par les neuf jeux'),('et contraintes/probabilités publiques au démineur','contraintes/probabilités publiques au démineur, recherche au Reversi, calcul exact à Nim et résolution minimale à Lights Out')]])
print('Integrated nine games and model migration; 3.2.0 archived.')
