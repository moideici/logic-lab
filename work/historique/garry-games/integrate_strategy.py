exec((__import__('pathlib').Path(__file__).parent/'integrate.py').read_text(encoding='utf-8').split('# Freeze the last')[0])
import shutil
for source,target in [('strategy_rules.py','logic_arena/strategy_rules.py'),('strategy_planner.py','logic_arena/strategy_planner.py'),('strategy-games.js','web/strategy-games.js'),('strategy-planner.js','web/strategy-planner.js')]:shutil.copy2(HERE/source,ROOT/target)
shutil.copy2(ROOT/'web/models/garry.json',ROOT/'training/new-games-4.0.0/nine-game-bootstrap.json')
edit('logic_arena/games.py',[("GAMES = {g.name:",'''class StrategyGame(Game):
    players=2
    def __init__(self,seed=0,options=None):
        super().__init__(seed,options)
        from .strategy_rules import create_strategy
        self.board,self.draughts_state=create_strategy(self.name)
    def observation(self):
        obs=super().observation()
        if self.name=='draughts':obs['draughts_state']=deepcopy(self.draughts_state)
        return obs
    def legal_actions(self):
        from .strategy_rules import legal_strategy
        return [] if self.done else legal_strategy(self.name,self.board,self.current_player,self.draughts_state)
    def apply(self,action):
        from .strategy_rules import step_strategy
        result=step_strategy(self.name,self.board,self.current_player,action,self.draughts_state)
        self.current_player=result['player'];self.done=result['done'];self.winner=result['winner'];self.score=result['score'];self.draughts_state=result['state']
        return result['reward']
class Draughts(StrategyGame):
    name='draughts'
class Breakthrough(StrategyGame):
    name='breakthrough'

GAMES = {g.name:'''),('Reversi, Nim, LightsOut)}','Reversi, Nim, LightsOut, Draughts, Breakthrough)}')])
edit('logic_arena/neural.py',[
('from .extra_rules import EXTRA_SPECS, encode_extra, extra_action_index','from .extra_rules import EXTRA_SPECS, encode_extra, extra_action_index\nfrom .strategy_rules import STRATEGY_SPECS,encode_strategy,strategy_action_index'),
('**EXTRA_SPECS}', '**EXTRA_SPECS, **STRATEGY_SPECS}'),
('    if name in EXTRA_SPECS:return', '    if name in STRATEGY_SPECS:return np.asarray(encode_strategy(obs),dtype=np.float32)\n    if name in EXTRA_SPECS:return'),
('    if game in EXTRA_SPECS:return', '    if game in STRATEGY_SPECS:return strategy_action_index(game,action)\n    if game in EXTRA_SPECS:return')])
# Migrate the intermediate nine-game development model as well as real old exports.
edit('logic_arena/migration.py',[
("def upgrade_legacy(data,specs,default_head):", "def upgrade_legacy(data,specs,default_head):\n    if data.get('games')==list(LEGACY_GAMES)+['reversi','nim','lightsout']:\n        old_features,old_input,old_output=2051,2060,925\n    else:old_features,old_input,old_output=1906,1912,818\n    old_games=data.get('games',[])"),
("data.get('games')!=list(LEGACY_GAMES) or data.get('input')!=1912 or data.get('output')!=818", "old_games not in (list(LEGACY_GAMES),list(LEGACY_GAMES)+['reversi','nim','lightsout']) or data.get('input')!=old_input or data.get('output')!=old_output"),
("('w1',1912*h),('w2',818*h),('b1',h),('b2',818)", "('w1',old_input*h),('w2',old_output*h),('b1',h),('b2',old_output)"),
("[:1906*h]", "[:old_features*h]"),
("for i in range(6):d['w1'][(features+i)*h:(features+i+1)*h]=data['w1'][(1906+i)*h:(1907+i)*h]", "for i in range(len(old_games)):d['w1'][(features+i)*h:(features+i+1)*h]=data['w1'][(old_features+i)*h:(old_features+i+1)*h]"),
("j*outputs+818]=data['w2'][j*818:(j+1)*818]", "j*outputs+old_output]=data['w2'][j*old_output:(j+1)*old_output]"),
("d['b2'][:818]=data['b2']", "d['b2'][:old_output]=data['b2']"),
("if g in LEGACY_GAMES else 0", "if g in old_games else 0")])
edit('logic_arena/general.py',[("        if (data.get('format'),data.get('version')) in", "        if data.get('format')=='garry-mlp-v3' and data.get('version')=='4.0.0' and data.get('games')==list(LEGACY_GAMES)+['reversi','nim','lightsout']:\n            data=upgrade_legacy(data,SPECS,default_head())\n        if (data.get('format'),data.get('version')) in")])
edit('logic_arena/planner.py',[("    elif game in ('reversi','nim','lightsout'):", "    elif game in ('draughts','breakthrough'):\n        from .strategy_planner import strategy_values\n        values,info=strategy_values(obs,legal,Budget(30000,200 if time_ms is None else time_ms))\n    elif game in ('reversi','nim','lightsout'):")])
edit('web/engine.js',[
("import {EXTRA_NAMES", "import {STRATEGY_NAMES,STRATEGY_SPECS,createStrategy,legalStrategy,stepStrategy,encodeStrategy,strategyActionIndex} from './strategy-games.js';\nimport {EXTRA_NAMES"),
("...EXTRA_NAMES}", "...EXTRA_NAMES,...STRATEGY_NAMES}"),('...EXTRA_SPECS}', '...EXTRA_SPECS,...STRATEGY_SPECS}'),
(" if(EXTRA_NAMES[name]){", " if(STRATEGY_NAMES[name]){const created=createStrategy(name);this.board=created.board;this.draughtsState=created.state;return;}\n if(EXTRA_NAMES[name]){"),
("['tictactoe','connect4','reversi','nim'].includes(this.name)","['tictactoe','connect4','reversi','nim','draughts','breakthrough'].includes(this.name)"),
("moves:this.moves,...", "moves:this.moves,...(this.name==='draughts'?{draughts_state:clone(this.draughtsState)}:{}),..."),
("legal(){if(this.done)return [];", "legal(){if(this.done)return [];if(STRATEGY_NAMES[this.name])return legalStrategy(this.name,this.board,this.player,this.draughtsState);"),
(" if(EXTRA_NAMES[this.name]){", " if(STRATEGY_NAMES[this.name]){const s=stepStrategy(this.name,b,this.player,a,this.draughtsState);Object.assign(this,{player:s.player,done:s.done,winner:s.winner,score:s.score,draughtsState:s.state});return s.reward;}\n if(EXTRA_NAMES[this.name]){"),
("export function encode(o){", "export function encode(o){if(STRATEGY_NAMES[o.game])return Float32Array.from(encodeStrategy(o));"),
("export function actionIndex(game,a){", "export function actionIndex(game,a){if(STRATEGY_NAMES[game])return strategyActionIndex(game,a);"),
("...Object.keys(EXTRA_SPECS)]", "...Object.keys(EXTRA_SPECS),...Object.keys(STRATEGY_SPECS)]"),
(" constructor(d){\n  if(", " constructor(d){\n  if(d.format==='garry-mlp-v3'&&d.version==='4.0.0'&&JSON.stringify(d.games)===JSON.stringify([...LEGACY_GAMES,'reversi','nim','lightsout']))d=upgradeLegacy(d,SPECS,defaultPositionHead());\n  if(")])
p=ROOT/'web/migration.js';p.write_text('''export const LEGACY_GAMES=['tictactoe','connect4','2048','sudoku','minesweeper','sliding_puzzle'];
export function initialWeight(index){let x=(index+0x9e3779b9)>>>0;x^=x>>>16;x=Math.imul(x,0x85ebca6b);x^=x>>>13;x=Math.imul(x,0xc2b2ae35);x^=x>>>16;return Math.fround(((x>>>8)/16777216-.5)/16);}
export function upgradeLegacy(d,specs,defaultHead){
 const h=d.hidden,nine=JSON.stringify(d.games)===JSON.stringify([...LEGACY_GAMES,'reversi','nim','lightsout']),oldFeatures=nine?2051:1906,oldInput=nine?2060:1912,oldOutput=nine?925:818;
 if(!Number.isInteger(h)||h<1||h>256||(!nine&&JSON.stringify(d.games)!==JSON.stringify(LEGACY_GAMES))||d.input!==oldInput||d.output!==oldOutput)throw Error('Architecture historique invalide');
 for(const [k,n]of[['w1',oldInput*h],['w2',oldOutput*h],['b1',h],['b2',oldOutput]])if(!Array.isArray(d[k])||d[k].length!==n)throw Error('Poids historiques invalides');
 const games=[...LEGACY_GAMES,...Object.keys(specs).filter(g=>!LEGACY_GAMES.includes(g))],features=Object.values(specs).reduce((n,s)=>n+s[0],0),input=features+games.length,output=Object.values(specs).reduce((n,s)=>n+s[1],0);
 const out={...d,format:'garry-mlp-v3',version:'4.0.0',games,input,output,w1:Array.from({length:input*h},(_,i)=>initialWeight(i)),w2:Array.from({length:output*h},(_,i)=>initialWeight(1000000+i)),b2:Array(output).fill(0),game_steps:Object.fromEntries(games.map(g=>[g,d.games.includes(g)?d.game_steps?.[g]:0]))};
 for(let i=0;i<oldFeatures*h;i++)out.w1[i]=d.w1[i];
 for(let g=0;g<d.games.length;g++)for(let j=0;j<h;j++)out.w1[(features+g)*h+j]=d.w1[(oldFeatures+g)*h+j];
 for(let j=0;j<h;j++)for(let k=0;k<oldOutput;k++)out.w2[j*output+k]=d.w2[j*oldOutput+k];
 for(let k=0;k<oldOutput;k++)out.b2[k]=d.b2[k];if(d.format==='garry-mlp-v1')out.position_head=structuredClone(defaultHead);return out;
}
''',encoding='utf-8')
edit('web/planner.js',[
("import {extraValues}", "import {strategyValues} from './strategy-planner.js';\nimport {extraValues}"),
("o.game==='reversi'?150:TIMES[9]", "['draughts','breakthrough'].includes(o.game)?200:o.game==='reversi'?150:TIMES[9]"),
("const solver={", "const solver={...Object.fromEntries(['draughts','breakthrough'].map(g=>[g,(o,legal,logits,budget)=>strategyValues(o,legal,budget)])),")])
edit('web/teachers.js',[
("import {extraValues}", "import {strategyValues} from './strategy-planner.js';\nimport {extraValues}"),
(" if(['reversi','nim','lightsout'].includes(o.game))", " if(['draughts','breakthrough'].includes(o.game)){const began=performance.now(),budget={nodes:0,tick(){if(this.nodes++>=2000||performance.now()-began>30)throw Error('budget');}},result=strategyValues(o,legal,budget,{maxDepth:3});return selectQuality(result.action_values,10,Array(3617).fill(0),o.game).selected.action;}\n if(['reversi','nim','lightsout'].includes(o.game))")])
edit('logic_arena/diversity.py',[
("    game=obs['game'];b=obs['board'];p=obs.get('current_player',1)", "    game=obs['game'];b=obs['board'];p=obs.get('current_player',1)\n    if game in ('draughts','breakthrough'):return digest([game,b,p,obs.get('draughts_state')])"),
("    elif game in ('reversi','nim','lightsout'):", "    elif game in ('draughts','breakthrough'):\n        from .strategy_planner import strategy_values\n        values,info=strategy_values(obs,legal,Budget(nodes,10000),max_depth=3)\n        info['category']='rafle' if obs.get('draughts_state',{}).get('forced_piece') else 'endgame' if sum(bool(v) for row in obs['board'] for v in row)<=8 else 'opening' if obs['moves']<16 else 'middle'\n    elif game in ('reversi','nim','lightsout'):"),
("('sliding_puzzle','nim'):return", "('sliding_puzzle','nim','draughts','breakthrough'):return")])
edit('examples/build_garry_repertoire.py',[("elif game in ('reversi','nim','lightsout'):", "elif game in ('reversi','nim','lightsout','draughts','breakthrough'):")])
edit('web/repertoire.js',[
("lightsout:[5,5]}","lightsout:[5,5],draughts:[10,10],breakthrough:[8,8]}"),
("'mine_count'];", "'mine_count','draughts_state'];"),
("lightsout:1}","lightsout:1,draughts:4,breakthrough:2}"),
("player:o.current_player,done:false", "player:o.current_player,draughtsState:o.draughts_state,done:false")])
edit('logic_arena/harness.py',[
('    "lightsout": {"row":"0..4","col":"0..4"},','    "lightsout": {"row":"0..4","col":"0..4"},\n    "draughts": {"from":["row 0..9","col 0..9"],"to":["row 0..9","col 0..9"]},\n    "breakthrough": {"from":["row 0..7","col 0..7"],"to":["row 0..7","col 0..7"]},'),
('[2060,48,48,925]', '[2494,48,48,3617]')])
p=ROOT/'web/agents.json';d=json.loads(p.read_text());
for game in ('draughts','breakthrough'):d['agents'][game]={'codename':'garry','mode':game,'version':'4.0.0'}
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
edit('web/index.html',[(a,b) for a,b in [('neuf jeux','onze jeux'),('9 jeux','11 jeux'),('2060','2494'),('2 060','2 494'),('925','3617'),('146 637','299 377'),('résolution minimale à Lights Out','résolution minimale à Lights Out, rafles et recherche aux dames internationales et courses de pions à Percée')]])
for file in ('tests/test_garry.py','tests/garry.test.mjs','tests/levels.test.mjs','tests/test_certified.py','tests/new-games.test.mjs'):
    p=ROOT/file;s=p.read_text(encoding='utf-8');s=s.replace('(2060,925)','(2494,3617)').replace('m.input,2060','m.input,2494').replace('m.output,925','m.output,3617').replace('encodeGeneral(o).length,2060','encodeGeneral(o).length,2494').replace('2051*48,2057*48','2483*48,2489*48').replace('2051:2057','2483:2489');p.write_text(s,encoding='utf-8')
edit('tests/test_diversity.py',[("self.assertEqual(len(first),27)","self.assertEqual(len(first),33)")])
print('Eleven-game architecture installed; intermediate nine-game weights retained for migration.')
