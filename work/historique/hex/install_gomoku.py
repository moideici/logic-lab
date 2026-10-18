exec((__import__('pathlib').Path(__file__).parent/'install_hex.py').read_text(encoding='utf-8').split('archive=')[0])
for f,target in [('gomoku_rules.py','logic_arena/gomoku_rules.py'),('gomoku_planner.py','logic_arena/gomoku_planner.py'),('gomoku-games.js','web/gomoku-games.js'),('gomoku-planner.js','web/gomoku-planner.js')]:shutil.copy2(HERE/f,ROOT/target)
edit('logic_arena/games.py',[("GAMES = {g.name:",'''class Gomoku(Game):
    name='gomoku'
    players=2
    def __init__(self,seed=0,options=None):
        super().__init__(seed,options)
        from .gomoku_rules import new_gomoku
        self.board,self.gomoku_state=new_gomoku()
    def observation(self):return {**super().observation(),'gomoku_state':deepcopy(self.gomoku_state)}
    def legal_actions(self):
        from .gomoku_rules import legal_gomoku
        return [] if self.done else legal_gomoku(self.board,self.gomoku_state)
    def apply(self,action):
        from .gomoku_rules import step_gomoku
        s=step_gomoku(self.board,self.current_player,action,self.gomoku_state)
        self.current_player=s['player'];self.done=s['done'];self.winner=s['winner'];self.score=s['score'];self.gomoku_state=s['state'];return s['reward']

GAMES = {g.name:'''),('Breakthrough, Hex)}','Breakthrough, Hex, Gomoku)}')])
edit('logic_arena/neural.py',[
('from .hex_rules import HEX_SPECS,encode_hex,hex_action_index','from .hex_rules import HEX_SPECS,encode_hex,hex_action_index\nfrom .gomoku_rules import GOMOKU_SPECS,encode_gomoku,gomoku_action_index'),('**HEX_SPECS}', '**HEX_SPECS, **GOMOKU_SPECS}'),
("    if name=='hex':", "    if name=='gomoku':return np.asarray(encode_gomoku(obs),dtype=np.float32)\n    if name=='hex':"),
("    if game=='hex':", "    if game=='gomoku':return gomoku_action_index(action)\n    if game=='hex':")])
edit('logic_arena/migration.py',[("'breakthrough'],2483,2494,3617)]", "'breakthrough'],2483,2494,3617),(list(LEGACY_GAMES)+['reversi','nim','lightsout','draughts','breakthrough','hex'],2583,2595,3667)]")])
edit('logic_arena/general.py',[("        if data.get('format')=='garry-mlp-v3' and data.get('version')=='4.0.0'", "        if data.get('format')=='garry-mlp-v3' and data.get('version')=='5.0.0' and data.get('games')==list(LEGACY_GAMES)+['reversi','nim','lightsout','draughts','breakthrough','hex']:\n            data=upgrade_legacy(data,SPECS,default_head())\n        if data.get('format')=='garry-mlp-v3' and data.get('version')=='4.0.0'")])
edit('logic_arena/planner.py',[("    elif game=='hex':", "    elif game=='gomoku':\n        from .gomoku_planner import gomoku_values\n        values,info=gomoku_values(obs,legal,Budget(20000,200 if time_ms is None else time_ms))\n    elif game=='hex':")])
edit('logic_arena/harness.py',[("    \"hex\":", "    \"gomoku\": [{\"row\":\"0..14\",\"col\":\"0..14\"},{\"choose\":\"black|white\"}],\n    \"hex\":"),('[2595,48,48,3667]','[3055,48,48,3894]')])
edit('web/engine.js',[
("import {HEX_SPECS", "import {GOMOKU_SPECS,newGomoku,legalGomoku,stepGomoku,encodeGomoku,gomokuActionIndex} from './gomoku-games.js';\nimport {HEX_SPECS"),
("hex:'Hex 7 × 7'}", "hex:'Hex 7 × 7',gomoku:'Gomoku · Swap2'}"),('...HEX_SPECS}', '...HEX_SPECS,...GOMOKU_SPECS}'),
(" if(name==='hex'){", " if(name==='gomoku'){const next=newGomoku();this.board=next.board;this.gomokuState=next.state;return;}\n if(name==='hex'){"),
("'breakthrough','hex'].includes(this.name)", "'breakthrough','hex','gomoku'].includes(this.name)"),
("moves:this.moves,...", "moves:this.moves,...(this.name==='gomoku'?{gomoku_state:clone(this.gomokuState)}:{}),..."),
("legal(){if(this.done)return [];", "legal(){if(this.done)return [];if(this.name==='gomoku')return legalGomoku(this.board,this.gomokuState);"),
(" if(this.name==='hex'){", " if(this.name==='gomoku'){const s=stepGomoku(b,this.player,a,this.gomokuState);Object.assign(this,{player:s.player,done:s.done,winner:s.winner,score:s.score,gomokuState:s.state});return s.reward;}\n if(this.name==='hex'){"),
("export function encode(o){", "export function encode(o){if(o.game==='gomoku')return Float32Array.from(encodeGomoku(o));"),
("export function actionIndex(game,a){", "export function actionIndex(game,a){if(game==='gomoku')return gomokuActionIndex(a);"),
("...Object.keys(HEX_SPECS)]", "...Object.keys(HEX_SPECS),...Object.keys(GOMOKU_SPECS)]"),
(" constructor(d){", " constructor(d){\n  if(d.format==='garry-mlp-v3'&&d.version==='5.0.0'&&d.games?.length===12)d=upgradeLegacy(d,SPECS,defaultPositionHead());")])
edit('web/migration.js',[("'breakthrough'],2483,2494,3617]]", "'breakthrough'],2483,2494,3617],[[...LEGACY_GAMES,'reversi','nim','lightsout','draughts','breakthrough','hex'],2583,2595,3667]]")])
edit('web/planner.js',[("import {hexValues}", "import {gomokuValues} from './gomoku-planner.js';\nimport {hexValues}"),("'breakthrough','hex'].includes(o.game)?200", "'breakthrough','hex','gomoku'].includes(o.game)?200"),("const solver={", "const solver={gomoku:(o,legal,logits,budget)=>gomokuValues(o,legal,budget),")])
edit('web/teachers.js',[("import {hexValues}", "import {gomokuValues} from './gomoku-planner.js';\nimport {hexValues}"),("export function teacher(o,legal){", "export function teacher(o,legal){\n if(o.game==='gomoku'){const began=performance.now(),budget={nodes:0,tick(){if(this.nodes++>=200||performance.now()-began>30)throw Error('budget');}},result=gomokuValues(o,legal,budget);return selectQuality(result.action_values,10,Array(227).fill(0),'gomoku').selected.action;}")])
edit('logic_arena/diversity.py',[("    if game=='hex':return", "    if game=='gomoku':return digest([game,b,p,obs.get('gomoku_state')])\n    if game=='hex':return"),("    elif game=='hex':", "    elif game=='gomoku':\n        from .gomoku_planner import gomoku_values\n        values,info=gomoku_values(obs,legal,Budget(nodes,200));info['category']='opening' if obs['gomoku_state']['phase']!='play' else 'middle'\n    elif game=='hex':"),("'breakthrough','hex'):return", "'breakthrough','hex','gomoku'):return")])
edit('examples/build_garry_repertoire.py',[("'breakthrough','hex'):","'breakthrough','hex','gomoku'):")])
edit('web/repertoire.js',[("hex:[7,7]}","hex:[7,7],gomoku:[15,15]}"),("'hex_state'];", "'hex_state','gomoku_state'];"),("hex:2}","hex:2,gomoku:2}"),("hexState:o.hex_state,draughtsState", "hexState:o.hex_state,gomokuState:o.gomoku_state,draughtsState"),
("  const env=Object.assign", "  if(o.game==='gomoku'){const s=o.gomoku_state;if(!s||Object.keys(s).some(k=>!['phase','colors','placed','winning_line'].includes(k))||!['opening_three','choose_or_extend','opening_two','choose_color','play'].includes(s.phase)||!Array.isArray(s.colors)||s.colors.length!==2||s.colors.some(v=>![0,1,2].includes(v))||!Number.isInteger(s.placed)||s.placed<0||s.placed>225||!Array.isArray(s.winning_line))throw Error('État Gomoku invalide');}\n  const env=Object.assign")])
p=ROOT/'web/agents.json';d=json.loads(p.read_text());d['agents']['gomoku']={'codename':'garry','version':'5.0.0','mode':'gomoku'};p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
edit('web/app.js',[("hex:'⬡'}","hex:'⬡',gomoku:'●·●'}"),("knownGames.length<12", "knownGames.length<13"),("function renderBoard(){", "function renderBoard(){if(game.name==='gomoku'){renderGomokuBoard();return;}"),("'breakthrough','hex'].includes(id)", "'breakthrough','hex','gomoku'].includes(id)"),("architecture:[2595,48,48,3667]","architecture:[3055,48,48,3894]"),("les douze jeux", "les treize jeux"),
("const labels=game.name==='hex'?", "const labels=game.name==='gomoku'?game.gomokuState.colors.map((c,i)=>c===1?'Noir':c===2?'Blanc':`Joueur ${i+1} · ouverture`):game.name==='hex'?"),
("if(game.name==='draughts'&&game.draughtsState.forced_piece)", "if(game.name==='gomoku')$('game-hint').textContent=gomokuHint();if(game.name==='draughts'&&game.draughtsState.forced_piece)")])
p=ROOT/'web/app.js';s=p.read_text(encoding='utf-8');marker='function renderHexBoard(){'
code='''function gomokuHint(){return {opening_three:'Swap2 : le premier joueur pose noir, blanc, puis noir.',choose_or_extend:'Le second joueur choisit sa couleur, ou pose encore blanc puis noir pour laisser le choix à son adversaire.',opening_two:'Posez maintenant la seconde pierre supplémentaire : noire.',choose_color:'Le premier joueur choisit sa couleur. Blanc jouera ensuite.',play:'Alignez exactement cinq pierres. Six pierres ou plus ne gagnent pas.'}[game.gomokuState.phase];}
function renderGomokuBoard(){const b=$('board'),s=game.gomokuState,active=humanTurn()&&!game.done,canPlace=s.phase!=='choose_color';b.className='board-gomoku';b.innerHTML='';const grid=document.createElement('div');grid.className='gomoku-grid';game.board.forEach((row,r)=>row.forEach((v,c)=>{const cell=document.createElement('button');cell.className='gomoku-cell'+(v?' stone-'+v:'');cell.disabled=!active||!!v||!canPlace;cell.setAttribute('aria-label',`Ligne ${r+1}, colonne ${c+1} : ${v===1?'noir':v===2?'blanc':'vide'}`);if(lastAction?.row===r&&lastAction?.col===c)cell.classList.add('last-stone');if(s.winning_line.some(p=>p[0]===r&&p[1]===c))cell.classList.add('winning-stone');cell.onclick=()=>humanAction({row:r,col:c});grid.append(cell);}));b.append(grid);if(['choose_or_extend','choose_color'].includes(s.phase)){const choices=document.createElement('div');choices.className='gomoku-choices';for(const [value,text]of [['black','Choisir noir'],['white','Choisir blanc']]){const button=document.createElement('button');button.textContent=text;button.disabled=!active;button.onclick=()=>humanAction({choose:value});choices.append(button);}b.append(choices);}$('game-result').hidden=!game.done;$('game-result').textContent=game.winner===0?'Match nul':$('mode').value==='human'&&game.winner===+$('human-player').value?'Vous avez aligné cinq pierres !':`Victoire du joueur ${game.winner}`;}
'''
s=s.replace(marker,code+marker);p.write_text(s,encoding='utf-8')
p=ROOT/'web/style.css';p.write_text(p.read_text(encoding='utf-8')+'''
#board.board-gomoku{width:min(100%,480px);display:block}.gomoku-grid{display:grid;grid-template-columns:repeat(15,1fr);padding:8px;background:#ddbf87;border:4px solid #a3814b;border-radius:7px}.gomoku-cell{position:relative;aspect-ratio:1;min-width:0;border:0;padding:0;background:linear-gradient(90deg,transparent 48%,#927549 49% 51%,transparent 52%),linear-gradient(transparent 48%,#927549 49% 51%,transparent 52%)}.gomoku-cell:disabled{opacity:1}.gomoku-cell.stone-1::before,.gomoku-cell.stone-2::before{content:'';position:absolute;inset:9%;border-radius:50%;box-shadow:0 1px 2px #0006}.gomoku-cell.stone-1::before{background:#253630}.gomoku-cell.stone-2::before{background:#fff7e7}.gomoku-cell.last-stone::after{content:'';position:absolute;inset:38%;border-radius:50%;background:#d47f42}.gomoku-cell.winning-stone{background:#d4cf77}.gomoku-choices{display:flex;justify-content:center;gap:10px;margin:15px 0}.gomoku-choices button{padding:10px;border-radius:8px;background:#e7eddc;font-size:12px}
''',encoding='utf-8')
edit('web/index.html',[(a,b) for a,b in [('douze jeux','treize jeux'),('12 jeux','13 jeux'),('12 ENVIRONNEMENTS','13 ENVIRONNEMENTS'),('Douze façons','Treize façons'),('2595','3055'),('2 595','3 055'),('3667','3894'),('3 667','3 894'),('306 675','339 878')]])
for file in ('pyproject.toml','logic_arena/__main__.py'):
    p=ROOT/file;s=p.read_text(encoding='utf-8').replace('douze jeux','treize jeux');p.write_text(s,encoding='utf-8')
print('Gomoku 15x15 with exact-five and full Swap2 opening integrated.')
