from pathlib import Path
import re
ROOT=Path(r'C:\Users\gabor\code\playi')
OUT=Path(__file__).parent/'stage'
def read(p):return (ROOT/p).read_text(encoding='utf-8')
def write(p,s):
    target=OUT/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(s,encoding='utf-8',newline='\n')

# The previous ten budgets remain available to legacy integrations. Difficulty
# no longer changes the analysis effort; it selects a quality quantile.
s=read('web/engine.js')
s="import {selectQuality} from './quality.js';\n"+s
start=s.index(' choose(o,legal,level=10,style=')
end=s.index('\n train(',start)
s=s[:start]+''' choose(o,legal,level=10,style='balanced',random=Math.random,preparedLogits=null){
  if(!Number.isInteger(level)||level<0||level>10||!STYLES.includes(style))throw Error('Niveau ou style invalide');
  if(!legal.length||o.done)throw Error('Partie terminée');
  const start=performance.now(),z=preparedLogits??this.forward(o).z;
  const scores=legal.map(a=>z[actionIndex(this.game,a)]),values=legal.map((action,i)=>({action,quality:[scores[i]]}));
  const {selected,info}=selectQuality(values,level,z,this.game),max=Math.max(...scores),p=scores.map(v=>Math.exp(Math.max(-50,v-max))),sum=p.reduce((a,b)=>a+b,0),at=legal.indexOf(selected.action);
  return {action:selected.action,info:{agent:'neural',identity:agentIdentity(this.game),...info,style,confidence:p[at]/sum,optimal:false,evaluation_scope:'policy_scores',time_ms:performance.now()-start,training_steps:this.steps,parameters:this.w1.length+this.w2.length+this.b1.length+this.b2.length}};
 }
'''+s[end:]
# New policy+position architecture, backwards-readable 2.0 model migration.
s=s.replace("if(data.format!=='garry-mlp-v1'||data.name!=='garry'||data.version!=='2.0.0'", "if(!((data.format==='garry-mlp-v1'&&data.version==='2.0.0')||(data.format==='garry-mlp-v2'&&data.version==='3.0.0'))||data.name!=='garry'")
# Locate exact constructor and export below after inspection if formatting differs.
s=s.replace("this.name='garry';", "this.name='garry';this.positionHead=validatePositionHead(data.position_head??(data.format==='garry-mlp-v1'?defaultPositionHead():null));")
s=s.replace("format:'garry-mlp-v1',name:'garry',version:'2.0.0',games:GARRY_GAMES.slice(),input:this.input", "format:'garry-mlp-v2',name:'garry',version:'3.0.0',position_head:structuredClone(this.positionHead),games:GARRY_GAMES.slice(),input:this.input")
s="import {defaultPositionHead,validatePositionHead,positionFeatures} from './value.js';\n"+s
s=s.replace(' get core(){return this.model.core;}', ' get positionHead(){return this.model.positionHead;}\n get core(){return this.model.core;}')
write('web/engine.js',s)

s=read('logic_arena/neural.py');a=s.index('        temperature = TEMPERATURES[level-1]');b=s.index('\n    def fit(',a)
s=s[:a]+'''        from .quality import select_quality
        # Styles may order exact ties, never turn a better evaluation into a
        # worse one at the endpoints.
        values = [{'action':a,'quality':[float(values[action_index(self.game,a)])]} for a in legal]
        selected,_ = select_quality(values,level,self.logits(obs) if logits is None else logits,self.game)
        return selected['action']
'''+s[b:]
write('logic_arena/neural.py',s)
s=read('logic_arena/agents.py').replace('not 1 <= level <= 10','not 0 <= level <= 10').replace('entre 1 et 10','entre 0 et 10')
s=s.replace('self.time_ms = TIME_LIMITS[level-1] if time_ms is None else time_ms','self.time_ms = TIME_LIMITS[-1] if time_ms is None else time_ms')
a=s.index('        budget = Budget(NODE_LIMITS[self.level-1]');b=s.index('\n    def line_game',a)
s=s[:a]+'''        from .planner import plan
        from .neural import SPECS
        import numpy as np
        class Neutral:
            position_head=None
            def logits(self,obs):return np.zeros(SPECS[obs['game']][1])
        started=time.monotonic()
        action,info=plan(observation,legal_actions,Neutral(),self.level,legal_actions[0],self.time_ms)
        return Decision(action,{**info,'agent':'reference','identity':agent_identity(observation['game']),'style':self.style,'time_ms':round((time.monotonic()-started)*1000,3)})
'''+s[b:]
# Retain the public constraint solver as an analysis adapter, expose all legal
# moves including proved bombs so level zero can deliberately choose one.
s=s.replace('        r, c = min(sorted(available), key=value)', '''        self._mine_values=[]
        for a in actions:
            p=(a['row'],a['col'])
            risk=0. if p in safe else 1. if p in bombs else max([count/len(cells) for cells,count in constraints if p in cells and cells] or [base])
            area=sum((x,y) in hidden for x in range(max(0,p[0]-1),min(n,p[0]+2)) for y in range(max(0,p[1]-1),min(n,p[1]+2)))
            if len(hidden)==n*n:risk=0. # protected opening rule
            self._mine_values.append({'action':a,'quality':[-risk,area],'risk':risk})
        r, c = min(sorted(available), key=value)''')
write('logic_arena/agents.py',s)

s=read('logic_arena/general.py');s=s.replace('import json','import json\nimport copy\nfrom .value import default_head, validate_head, features')
s=s.replace("        self._adam = None","        self._adam = None\n        self.position_head = default_head()")
s=s.replace("'format':'garry-mlp-v1','name':'garry','version':'2.0.0'","'format':'garry-mlp-v2','name':'garry','version':'3.0.0','position_head':copy.deepcopy(self.position_head)")
s=s.replace("data.get('format')!='garry-mlp-v1' or data.get('name')!='garry' or data.get('version')!='2.0.0'", "(data.get('format'),data.get('version')) not in (('garry-mlp-v1','2.0.0'),('garry-mlp-v2','3.0.0')) or data.get('name')!='garry'")
s=s.replace('        model=cls(hidden)',"        model=cls(hidden)\n        model.position_head=validate_head(data.get('position_head',default_head() if data.get('format')=='garry-mlp-v1' else None))")
s=s.replace('    def for_game(self, game):', '''    def position_value(self, obs):
        if obs['game']!=self.position_head['game']:return None
        return float(features(obs)@np.asarray(self.position_head['weights']))

    def for_game(self, game):''')
s=s.replace('    @property\n    def hidden(self):', '    @property\n    def position_head(self):return self.model.position_head\n    @property\n    def hidden(self):')
write('logic_arena/general.py',s)

s=read('web/fast-search.js')
s=s.replace('function tttValue(b,p)', 'export function tttValue(b,p)')
# Add per-action assessments to the existing exact solvers.
a=s.index('export function exactSliding(');b=s.index('\n\nconst TTT_LINES',a)
s=s[:a]+'''export function exactSliding(o,legal,logits){const distance=slidingDistance(o.board),flat=o.board.flat(),zero=flat.indexOf(0),offset={up:-3,down:3,left:-1,right:1};const action_values=legal.map(action=>{const b=flat.slice(),at=zero+offset[action.direction];[b[zero],b[at]]=[b[at],0];const d=slidingDistance([b]);return {action,quality:[d===255?-1000:-d],remaining_moves:d+1};});const best=action_values.slice().sort((a,b)=>b.quality[0]-a.quality[0]||logits[actionIndex(o.game,b.action)]-logits[actionIndex(o.game,a.action)])[0];return {action:best.action,action_values,info:{method:'exact_shortest_path',analysis_exact:distance!==255,optimal:distance!==255,remaining_moves:distance,solution_found:distance!==255,nodes:legal.length}};}
'''+s[b:]
a=s.index('export function exactTictactoe(');b=s.index('\n\nexport function connectSearch',a)
s=s[:a]+'''export function exactTictactoe(o,legal,logits){const before=tttMemo.size,b=o.board.flat(),action_values=legal.map(action=>{const i=action.row*3+action.col;b[i]=o.current_player;const child=tttValue(b,3-o.current_player);b[i]=0;const outcome=-child.value,plies=child.plies+1;return {action,quality:[outcome,outcome===-1?plies:-plies],outcome,remaining_moves:plies};});const best=action_values.slice().sort((a,b)=>b.quality[0]-a.quality[0]||b.quality[1]-a.quality[1]||logits[actionIndex(o.game,b.action)]-logits[actionIndex(o.game,a.action)])[0];return {action:best.action,action_values,info:{method:'exact_minimax_distance',optimal:true,analysis_exact:true,outcome:best.outcome,remaining_moves:best.remaining_moves,nodes:tttMemo.size-before,states_cached:tttMemo.size}};}
'''+s[b:]
# Keep a complete, comparable root vector, commit only a completed iteration.
s=s.replace('let best=ordered[0],bestValue=-Infinity,depthReached=0;', 'let best=ordered[0],bestValue=-Infinity,depthReached=0,rootValues=[];')
s=s.replace("if(isWin(child))return {action:a,info:{method:'expectimax_goal',optimal:true,remaining_moves:1,nodes:budget.nodes}};const v=heuristic(child)+g*.05;", "const v=isWin(child)?1e9:heuristic(child)+g*.05;rootValues.push({action:a,quality:[v]});")
s=s.replace("let candidate=best,value=-Infinity;try{for(const a of ordered){const [child,g]=move(initial,a.direction),score=chance(child,depth)+g*.05;", "let candidate=best,value=-Infinity,next=[];try{for(const a of ordered){const [child,g]=move(initial,a.direction),score=isWin(child)?1e9:chance(child,depth)+g*.05;next.push({action:a,quality:[score]});")
s=s.replace('best=candidate;depthReached=depth;}catch(error)', 'best=candidate;rootValues=next;depthReached=depth;}catch(error)')
s=s.replace("return {action:best,info:{method:'neural_expectimax_tables',optimal:false", "return {action:best,action_values:rootValues,info:{method:bestValue===1e9?'expectimax_goal':'neural_expectimax_tables',remaining_moves:bestValue===1e9?1:undefined,optimal:bestValue===1e9")
# Protected opening is equal risk for all choices, prefer maximum public area.
s=s.replace("return {action:{row:3,col:3},info:{method:'protected_opening'", "return {action:{row:3,col:3},action_values:legal.map(action=>({action,quality:[0,nearby(action.row*8+action.col).length],risk:0})),info:{method:'protected_opening'")
s=s.replace(' const risk=risks.get(best)??base;\n return', ''' const action_values=legal.map(action=>{const i=action.row*8+action.col,risk=risks.get(i)??base,neighbors=nearby(i).filter(j=>b[j]===-1),flood=neighbors.reduce((p,j)=>p*(1-(risks.get(j)??base)),1)*(neighbors.length+1);return {action,quality:[-risk,flood],risk,certain_safe:risk===0};});
 const risk=risks.get(best)??base;
 return''')
s=s.replace('return {action:{row:Math.floor(best/8),col:best%8},info:', 'return {action:{row:Math.floor(best/8),col:best%8},action_values,info:')
write('web/fast-search.js',s)

s=read('logic_arena/tiles.py')
s=s.replace('best, best_value, depth_reached = ordered[0], -float("inf"), 0','best, best_value, depth_reached = ordered[0], -float("inf"), 0\n    root_values=[]')
s=s.replace('''        if won(child):
            return action, {"method": "expectimax_goal", "optimal": True, "remaining_moves": 1, "nodes": budget.nodes}
        value = heuristic(child, tables) + gain*.05''','''        value = 1e9 if won(child) else heuristic(child, tables) + gain*.05
        root_values.append({'action':action,'quality':[value]})''')
s=s.replace('        candidate, value = best, -float("inf")','        candidate, value = best, -float("inf")\n        next_values=[]')
s=s.replace('                score = chance(child, depth) + gain*.05',"                score = 1e9 if won(child) else chance(child, depth) + gain*.05\n                next_values.append({'action':action,'quality':[score]})")
s=s.replace('            best, depth_reached = candidate, depth','            best, depth_reached = candidate, depth\n            root_values=next_values')
s=s.replace('return best, {"method": "neural_expectimax_tables", "optimal": False, "depth": depth_reached, "nodes": budget.nodes}', 'return best, {"method": "expectimax_goal" if best_value==1e9 else "neural_expectimax_tables", "optimal":best_value==1e9,"remaining_moves":1 if best_value==1e9 else None,"depth": depth_reached, "nodes": budget.nodes,"action_values":root_values}')
write('logic_arena/tiles.py',s)

for source,target in [('quality.js','web/quality.js'),('quality.py','logic_arena/quality.py'),('value.py','logic_arena/value.py')]:write(target,(Path(__file__).parent/source).read_text(encoding='utf-8'))
