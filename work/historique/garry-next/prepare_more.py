exec((__import__('pathlib').Path(__file__).parent/'prepare.py').read_text(encoding='utf-8'))
def staged(p):return (OUT/p).read_text(encoding='utf-8')
write('web/value.js',(Path(__file__).parent/'value.js').read_text(encoding='utf-8'))
s=staged('web/engine.js')
s=s.replace("if(d.format!=='garry-mlp-v1'||d.name!=='garry'||d.version!=='2.0.0'", "if(!((d.format==='garry-mlp-v1'&&d.version==='2.0.0')||(d.format==='garry-mlp-v2'&&d.version==='3.0.0'))||d.name!=='garry'")
s=s.replace('  this.input=d.input;', "  this.positionHead=validatePositionHead(d.position_head??(d.format==='garry-mlp-v1'?defaultPositionHead():null));\n  this.input=d.input;")
# Constructor has no name field in the original implementation.
s=s.replace("  this.input=GARRY_INPUT;", "  this.positionHead=validatePositionHead(data.position_head??(data.format==='garry-mlp-v1'?defaultPositionHead():null));\n  this.input=GARRY_INPUT;")
write('web/engine.js',s)

s=read('search/connect4-search.ts')
s=s.replace('const center =', 'const lineFeatures = new StaticArray<i32>(69);\nconst parity = new StaticArray<u64>(2);\nconst valueWeights = new StaticArray<f64>(32);\nlet learned=false;\nconst center =')
s=s.replace('((c+i*dc)*7+r+i*dr);lines[at++]=mask;', '((c+i*dc)*7+5-r-i*dr);lines[at]=mask;lineFeatures[at++]=(d*2+(r&1))*3;')
s=s.replace(' initialized=true;', ' for(let r=0;r<6;r++)for(let c=0;c<7;c++)parity[r&1]|=<u64>1<<(c*7+5-r);\n initialized=true;')
s=s.replace(' const enemy=position^mask;let score=0;', ''' const enemy=position^mask;let score=0;
 if(learned){
  let result:f64=0.;
  for(let i=0;i<69;i++){const line=lines[i],a=<i32>popcnt<u64>(position&line),b=<i32>popcnt<u64>(enemy&line),f=lineFeatures[i];if(!b&&a>0&&a<4)result+=valueWeights[f+a-1];if(!a&&b>0&&b<4)result-=valueWeights[f+b-1];}
  for(let c=0;c<7;c++){const col=<u64>63<<(c*7);result+=valueWeights[24+min(c,6-c)]*(<i32>popcnt<u64>(position&col)-<i32>popcnt<u64>(enemy&col));}
  const moves=(mask+BOTTOM)&BOARD,mine=winning(position,mask),theirs=winning(enemy,mask);
  for(let p=0;p<2;p++){
   result+=valueWeights[28+p]*(<i32>popcnt<u64>(mine&moves&parity[p])-<i32>popcnt<u64>(theirs&moves&parity[p]));
   result+=valueWeights[30+p]*(<i32>popcnt<u64>(mine&~moves&parity[p])-<i32>popcnt<u64>(theirs&~moves&parity[p]));
  }
  return <i32>Math.round(max(-20000.,min(20000.,result)));
 }''')
s+='\n'+(Path(__file__).parent/'wasm_append.ts').read_text(encoding='utf-8')
write('search/connect4-search.ts',s)

s=read('web/connect4-runtime.js')
s=s.replace('{timeMs=300,maxDepth=40}={}', '{timeMs=300,maxDepth=40,analyze=false,positionHead=null}={}')
s=s.replace(' const bits=[0n,0n,0n];', ''' runtime.enableValue(positionHead?.enabled?1:0);
 if(positionHead?.enabled)positionHead.weights.forEach((v,i)=>runtime.setValueWeight(i,v));
 const bits=[0n,0n,0n];''')
s=s.replace('const column=runtime.decide(', 'const column=runtime[analyze?\'analyze\':\'decide\'](')
s=s.replace(" return {action:{column},info:", " const action_values=analyze?legal.map(action=>({action,quality:[runtime.getScore(action.column)]})):undefined;\n return {action:{column},action_values,info:")
s=s.replace("runtime:'wasm',nodes,depth,forced_win:", "runtime:'wasm',nodes,depth,value,learned_value:!!positionHead?.enabled,evaluation_scope:'bounded_adversarial_search',forced_win:")
# Fallback evaluates each public child with the existing BigInt search. Kept
# bounded per action, tactical terminal actions dominate all estimates.
s=s.replace(" if(!runtime)return connectStrong(o,legal,logits,budget,{maxDepth});", " if(!runtime){if(!analyze)return connectStrong(o,legal,logits,budget,{maxDepth});return fallbackAnalysis(o,legal,logits,budget,maxDepth);}")
s+='''
function fallbackAnalysis(o,legal,logits,budget,maxDepth){
 const values=legal.map(action=>{const board=o.board.map(r=>r.slice()),r=board.map(row=>row[action.column]).lastIndexOf(0);board[r][action.column]=o.current_player;
  let won=false;for(const [dr,dc] of [[0,1],[1,0],[1,1],[1,-1]]){let n=1;for(const sign of [-1,1]){let y=r+sign*dr,c=action.column+sign*dc;while(y>=0&&y<6&&c>=0&&c<7&&board[y][c]===o.current_player){n++;y+=sign*dr;c+=sign*dc;}}if(n>=4)won=true;}
  if(won)return {action,quality:[999999]};const childLegal=board[0].flatMap((v,column)=>v?[]:[{column}]);if(!childLegal.length)return {action,quality:[0]};
  const local={nodes:0,limit:Math.max(1,Math.floor((budget.limit??10000)/legal.length))},began=performance.now();local.tick=function(){if(this.nodes++>=this.limit||performance.now()-began>30)throw Error('budget');};
  const d=connectStrong({...o,board,current_player:3-o.current_player},childLegal,Array(7).fill(0),local,{maxDepth});budget.nodes+=local.nodes;
  const v=d.info.value??(d.info.forced_win?999990:d.info.forced_loss?-999990:0);return {action,quality:[-v]};
 });
 const best=values.slice().sort((a,b)=>b.quality[0]-a.quality[0])[0];return {action:best.action,action_values:values,info:{method:'javascript_root_analysis',runtime:'javascript',optimal:false,nodes:budget.nodes,evaluation_scope:'bounded_adversarial_search'}};
}
export function positionRuntimeValue(o,head){if(!runtime)throw Error('WASM indisponible');runtime.enableValue(head.enabled?1:0);head.weights.forEach((v,i)=>runtime.setValueWeight(i,v));const bits=[0n,0n,0n];o.board.forEach((row,r)=>row.forEach((p,c)=>{if(p)bits[p]|=1n<<BigInt(c*7+5-r);}));return runtime.evaluateBoard(bits[1],bits[2],o.current_player);}
'''
write('web/connect4-runtime.js',s)
s=read('logic_arena/connect4_wasm.py')
s=s.replace('weights=None, max_depth=40)', 'weights=None, max_depth=40, analyze=False, position_head=None)')
s=s.replace('    bits = [0, 0, 0]', '''    runtime['enableValue'](store, int(bool(position_head and position_head.get('enabled'))))
    if position_head and position_head.get('enabled'):
        for i,value in enumerate(position_head['weights']):runtime['setValueWeight'](store,i,float(value))
    bits = [0, 0, 0]''')
s=s.replace("runtime['decide'](store,", "runtime['analyze' if analyze else 'decide'](store,")
s=s.replace("'runtime': 'wasm', 'nodes':", "'runtime': 'wasm', 'value':value,'learned_value':bool(position_head and position_head.get('enabled')),'evaluation_scope':'bounded_adversarial_search','nodes':")
s=s.replace('    return action, info', "    if analyze:info['action_values']=[{'action':a,'quality':[runtime['getScore'](store,a['column'])]} for a in legal]\n    return action, info")
write('logic_arena/connect4_wasm.py',s)

# Shared ranking entry point; all levels use the strongest configured budget.
write('web/planner.js','''import {CONNECT_LIMITS,CONNECT_TIMES} from './connect4-runtime.js';
import {exactSliding,exactTictactoe,connectSearch,tileSearch,mineSearch} from './fast-search.js';
import {selectQuality,sudokuValues} from './quality.js';
export const LIMITS=[16,50,150,500,1500,4000,10000,25000,50000,100000];
export const TIMES=[.5,1,2,3,5,8,12,16,22,30];
export function planDecision(o,legal,model,level,decision,preparedLogits=null){
 if(o.done)return decision;
 const began=performance.now(),logits=preparedLogits??model.forward(o).z;
 const budget={nodes:0,limit:o.game==='connect4'?CONNECT_LIMITS[9]:LIMITS[9],depth:2,criticalDepth:3,tick(){if(this.nodes++>=this.limit||performance.now()-began>=(o.game==='connect4'?CONNECT_TIMES[9]:TIMES[9]))throw Error('budget');}};
 const solver={tictactoe:exactTictactoe,sliding_puzzle:exactSliding,connect4:connectSearch,'2048':tileSearch,minesweeper:mineSearch,sudoku:sudokuValues}[o.game];
 if(!solver)return decision;
 const result=solver(o,legal,logits,budget,{timeMs:CONNECT_TIMES[9],analyze:true,positionHead:model.positionHead});
 const {selected,info}=selectQuality(result.action_values,level,logits,o.game),best=info.selected_is_best;
 const selectedInfo={...selected};delete selectedInfo.action;delete selectedInfo.quality;
 return {action:selected.action,info:{...decision.info,...result.info,...selectedInfo,...info,agent:'neural+planner',optimal:best&&!!result.info.optimal,confidence:null,policy_confidence:decision.info.confidence,evaluation_scope:result.info.analysis_exact?'exact_legal_move_values':result.info.evaluation_scope??'bounded_public_analysis',objective:'win_then_fewest_moves',time_ms:performance.now()-began+decision.info.time_ms}};
}
''')

# Preserve exact-distance helpers, replace the old single-best-action planner.
s=read('logic_arena/planner.py');a=s.index('def plan(');s=s[:a]+'''def plan(obs, legal, model, level, fallback, time_ms=None, logits=None):
    from .quality import select_quality, sudoku_values
    from .agents import Budget, ReferenceAgent
    from .neural import SPECS
    game=obs['game'];logits=model.logits(obs) if logits is None else logits
    budget_ms=TIMES[-1] if time_ms is None else time_ms
    budget=Budget(LIMITS[-1],budget_ms);info={}
    if game=='tictactoe':
        board=tuple(v for row in obs['board'] for v in row);values=[]
        for a in legal:
            i=a['row']*3+a['col'];v,n=_ttt_value(board[:i]+(obs['current_player'],)+board[i+1:],3-obs['current_player']);v=-v;n+=1
            values.append({'action':a,'quality':[v,n if v==-1 else -n],'outcome':v,'remaining_moves':n})
        info={'method':'exact_minimax_distance','optimal':True,'analysis_exact':True}
    elif game=='sliding_puzzle':
        r,c=next((r,c) for r in range(3) for c in range(3) if not obs['board'][r][c]);values=[]
        for a in legal:
            dr,dc={'up':(-1,0),'down':(1,0),'left':(0,-1),'right':(0,1)}[a['direction']];b=[row[:] for row in obs['board']];b[r][c],b[r+dr][c+dc]=b[r+dr][c+dc],0;d=sliding_distance(b)
            values.append({'action':a,'quality':[-d if d!=255 else -1000],'remaining_moves':d+1})
        info={'method':'exact_shortest_path','optimal':sliding_distance(obs['board'])!=255,'analysis_exact':True,'solution_found':True}
    elif game=='connect4':
        from .connect4_wasm import search,CONNECT_LIMITS,CONNECT_TIMES
        _,info=search(obs,legal,Budget(CONNECT_LIMITS[-1],CONNECT_TIMES[-1] if time_ms is None else time_ms),logits=logits,analyze=True,position_head=getattr(model,'position_head',None))
        values=info.pop('action_values')
    elif game=='2048':
        from .tiles import search
        _,info=search(obs,legal,logits,budget,max_depth=2,critical_depth=3);values=info.pop('action_values')
    elif game=='sudoku':values,info=sudoku_values(obs,legal,logits,budget)
    elif game=='minesweeper':
        agent=ReferenceAgent(10,time_ms=budget_ms);agent.mines(obs,legal,budget,fallback);values=agent._mine_values
        info={'method':'public_constraints_ranking','optimal':False,'nodes':budget.nodes}
    else:return fallback,{}
    selected,ranking=select_quality(values,level,logits,game)
    extra={k:v for k,v in selected.items() if k not in ('action','quality')}
    return selected['action'],{'agent':'neural+planner',**info,**extra,**ranking,'optimal':ranking['selected_is_best'] and info.get('optimal',False),
                              'evaluation_scope':'exact_legal_move_values' if info.get('analysis_exact') else info.get('evaluation_scope','bounded_public_analysis'),'objective':'win_then_fewest_moves'}
'''
write('logic_arena/planner.py',s)

# User-facing version changes follow the added position-evaluation branch.
for p in ('web/agents.json','pyproject.toml','web/index.html'):
    s=read(p).replace('2.0.0','3.0.0')
    if p.endswith('index.html'):s=s.replace('10 NIVEAUX','11 NIVEAUX').replace('min="1" max="10" value="10"','min="0" max="10" step="1" value="10"').replace('<span>Exploration</span><span>Déterministe</span>','<span>0 · Pire coup</span><span>10 · Meilleur coup</span>')
    write(p,s)
s=read('web/app.js').replace("format:'garry-mlp-v1'","format:'garry-mlp-v2'")
s=s.replace("levels:TEMPS.map((temperature,i)=>({level:i+1,temperature,planning_nodes:LIMITS[i],planning_time_ms:TIMES[i]}))", "levels:Array.from({length:11},(_,level)=>({level,quality_quantile:level/10,planning_nodes:LIMITS[9],planning_time_ms:TIMES[9]}))")
s=s.replace("? 'Réseau seul : exploration", "? 'Réseau seul : classement")
s=s.replace("'Réseau seul : exploration et entraînement, sans garantie de chemin minimal.'", "'Réseau seul : niveau fondé sur ses scores appris. Activez la planification pour analyser les suites.'")
s=s.replace("$('level').oninput=()=>{$('level-label').innerHTML=`${$('level').value}<span> / 10</span>`;};", "$('level').oninput=()=>{$('level-label').innerHTML=`${$('level').value}<span> / 10</span>`;};")
write('web/app.js',s)
s=read('logic_arena/harness.py').replace('"format":"garry-mlp-v1"','"format":"garry-mlp-v2"')
a=s.index('"levels": [{"level": i+1');b=s.index('\n            "operations"',a)
s=s[:a]+'''"levels": [{"level":i,"quality_quantile":i/10,"reference_nodes":NODE_LIMITS[-1],"reference_time_ms":TIME_LIMITS[-1],"planning_nodes":LIMITS[-1],"planning_time_ms":TIMES[-1]} for i in range(11)],'''+s[b:]
write('logic_arena/harness.py',s)
