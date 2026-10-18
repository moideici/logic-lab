// Même file de recherche pour deux jeux : le réseau ordonne les branches,
// les adaptateurs ne fournissent que transitions publiques et objectif.
import {CONNECT_LIMITS,CONNECT_TIMES} from './connect4-runtime.js';
import {candidates,actionIndex,clone} from './engine.js';
import {exactSliding,exactTictactoe,connectSearch,tileSearch,mineSearch} from './fast-search.js';
const paths=new Map();
export const LIMITS=[16,50,150,500,1500,4000,10000,25000,50000,100000];
export const TIMES=[.5,1,2,3,5,8,12,16,22,30];
class Heap{
 constructor(){this.a=[];}
 push(v){let i=this.a.length;this.a.push(v);while(i){const p=(i-1)>>1;if(this.a[p].priority<=v.priority)break;this.a[i]=this.a[p];i=p;}this.a[i]=v;}
 pop(){const out=this.a[0],last=this.a.pop();if(this.a.length){let i=0;while(i*2+1<this.a.length){let c=i*2+1;if(c+1<this.a.length&&this.a[c+1].priority<this.a[c].priority)c++;if(this.a[c].priority>=last.priority)break;this.a[i]=this.a[c];i=c;}this.a[i]=last;}return out;}
}
const key=o=>o.game+JSON.stringify(o.board)+(o.givens?JSON.stringify(o.givens):'');
function adapter(o){
 if(o.game==='sliding_puzzle')return {
  distance:b=>b.flat().reduce((s,v,i)=>s+(v?Math.abs(Math.floor(i/3)-Math.floor((v-1)/3))+Math.abs(i%3-(v-1)%3):0),0),
  expand:b=>{const i=b.flat().indexOf(0),r=Math.floor(i/3),c=i%3,out=[];for(const [d,dr,dc] of [['up',-1,0],['down',1,0],['left',0,-1],['right',0,1]])if(r+dr>=0&&r+dr<3&&c+dc>=0&&c+dc<3){const child=clone(b);child[r][c]=child[r+dr][c+dc];child[r+dr][c+dc]=0;out.push([{direction:d},child]);}return out;}
 };
 return {
  distance:b=>b.flat().filter(v=>!v).length,
  expand:b=>{let cell=null;for(let r=0;r<9;r++)for(let c=0;c<9;c++)if(!b[r][c]){const v=candidates(b,r,c);if(!cell||v.length<cell[0].length)cell=[v,r,c];}if(!cell)return [];const [vals,r,c]=cell;return vals.map(value=>{const child=clone(b);child[r][c]=value;return [{row:r,col:c,value},child];});}
 };
}
export function planDecision(o,legal,model,level,decision,preparedLogits=null){
 if(o.done)return decision;
 const began=performance.now();
 if(o.game!=='sudoku'){
  const logits=preparedLogits??model.forward(o).z,budget={nodes:0,depth:level>=8?2:1,criticalDepth:level>=9?3:level>=8?2:1,tick(){if(this.nodes++>=LIMITS[level-1]||performance.now()-began>=TIMES[level-1])throw Error('budget');}};
  const solver={tictactoe:exactTictactoe,sliding_puzzle:exactSliding,connect4:connectSearch,'2048':tileSearch,minesweeper:mineSearch}[o.game];
  if(!solver)return decision;
  if(o.game==='connect4'){budget.limit=CONNECT_LIMITS[level-1];budget.tick=function(){if(this.nodes++>=this.limit||performance.now()-began>=CONNECT_TIMES[level-1])throw Error('budget');};}
  const result=solver(o,legal,logits,budget,o.game==='connect4'?{timeMs:CONNECT_TIMES[level-1]}:{});
  return {action:result.action,info:{...decision.info,agent:'neural+planner',policy_confidence:decision.info.confidence,confidence:null,objective:'win_then_fewest_moves',optimal_scope:'remaining_from_current_state',...result.info,time_ms:decision.info.time_ms+performance.now()-began}};
 }
 const started=performance.now(),cached=paths.get(key(o)),cache=cached?.action;
 if(cache&&legal.some(a=>JSON.stringify(a)===JSON.stringify(cache)))return {action:cache,info:{...decision.info,agent:'neural+planner',method:'shared_search_cached',optimal_scope:'remaining_from_current_state',optimal:true,remaining_moves:cached.remaining,solution_found:true,policy_confidence:decision.info.confidence,confidence:null,time_ms:decision.info.time_ms+performance.now()-started,nodes:0}};
 const a=adapter(o),initial={board:clone(o.board),cost:0,path:[],priority:a.distance(o.board)},queue=new Heap(),seen=new Map([[JSON.stringify(o.board),0]]);
 queue.push(initial);let nodes=0,best=decision.action,bestH=a.distance(o.board),solved=null;
 while(queue.a.length&&nodes<LIMITS[level-1]&&performance.now()-started<TIMES[level-1]){
  const item=queue.pop();nodes++;const h=a.distance(item.board);
  if(item.path.length&&h<bestH){bestH=h;best=item.path[0].action;}
  if(!h){solved=item;best=item.path[0]?.action||best;break;}
  const children=a.expand(item.board);let logits=null;
  if(children.length>1)logits=item.cost===0&&preparedLogits?preparedLogits:model.forward({...o,board:item.board}).z;
  const order=children.sort((x,y)=>logits?logits[actionIndex(o.game,y[0])]-logits[actionIndex(o.game,x[0])]:0);
  for(let i=0;i<order.length;i++){
   const [action,board]=order[i],k=JSON.stringify(board),cost=item.cost+1;
   if(cost>=(seen.get(k)??Infinity))continue;
   seen.set(k,cost);
   const path=[...item.path,{board:item.board,action}];
   // Sudoku : descente vers une solution ; taquin : coût + Manhattan.
   const priority=o.game==='sudoku'?a.distance(board)+i*.001:cost+a.distance(board)+i*.001;
   queue.push({board,cost,path,priority});
  }
 }
 if(solved){solved.path.forEach((p,i)=>paths.set(key({...o,board:p.board}),{action:p.action,remaining:solved.path.length-i}));if(paths.size>5000)paths.clear();}
 if(!solved&&!queue.a.length&&legal.some(a=>a.undo))best={undo:true};
 return {action:best,info:{...decision.info,agent:'neural+planner',method:'shared_best_first',policy_confidence:decision.info.confidence,confidence:null,time_ms:decision.info.time_ms+performance.now()-started,nodes,node_limit:LIMITS[level-1],budget_ms:TIMES[level-1],solution_found:!!solved,optimal_scope:'remaining_from_current_state',optimal:!!solved,remaining_moves:solved?.path.length??null,objective:'win_then_fewest_moves'}};
}
