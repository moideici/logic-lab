import {connectStrong,CONNECT_LIMITS,CONNECT_TIMES} from './connect4.js';
export {CONNECT_LIMITS,CONNECT_TIMES};
let runtime=null;
export const connectReady=(async()=>{try{
 const url=new URL('./connect4-search.wasm',import.meta.url);
 const bytes=typeof process!=='undefined'&&process.versions?.node?(await import('node:fs/promises')).readFile(url):fetch(url).then(r=>{if(!r.ok)throw Error('Moteur indisponible');return r.arrayBuffer();});
 runtime=(await WebAssembly.instantiate(await bytes,{env:{now:()=>performance.now(),abort(){throw Error('Erreur du moteur Garry');}}})).instance.exports;
}catch{ /* Le solveur JavaScript reste disponible hors WebAssembly. */ }})();
export const connectRuntime=()=>runtime?'wasm':'javascript';
export function connectDecision(o,legal,logits,budget,{timeMs=300,maxDepth=40,analyze=false,positionHead=null}={}){
 if(!runtime){if(!analyze)return connectStrong(o,legal,logits,budget,{maxDepth});return fallbackAnalysis(o,legal,logits,budget,maxDepth);}
 runtime.enableValue(positionHead?.enabled?1:0);
 if(positionHead?.enabled)positionHead.weights.forEach((v,i)=>runtime.setValueWeight(i,v));
 const bits=[0n,0n,0n];o.board.forEach((row,r)=>row.forEach((p,c)=>{if(p)bits[p]|=1n<<BigInt(c*7+5-r);}));
 const order=legal.slice().sort((a,b)=>Number(logits?.[b.column]??-Math.abs(b.column-3))-Number(logits?.[a.column]??-Math.abs(a.column-3)));
 for(let c=0;c<7;c++)runtime.setPrior(c,-1);
 order.forEach((a,i)=>runtime.setPrior(a.column,7-i));
 // Les tests et benchmarks peuvent fournir une borne en nœuds explicite.
 const limit=Number.isInteger(budget.limit)?budget.limit:Math.max(0,CONNECT_LIMITS[9]);
 const column=runtime[analyze?'analyze':'decide'](bits[1],bits[2],o.current_player,limit,timeMs,maxDepth),nodes=runtime.getNodes(),depth=runtime.getDepth(),value=runtime.getValue();
 budget.nodes=nodes;
 if(!legal.some(a=>a.column===column))throw Error('Décision Garry illégale');
 const forcedWin=value>999957,forcedLoss=value< -999957;
 const tactical=forcedWin&&(value===999999||value===999997);
 const action_values=analyze?legal.map(action=>({action,quality:[runtime.getScore(action.column)]})):undefined;
 return {action:{column},action_values,info:{method:tactical?(value===999999?'tactical_win':'tactical_fork'):'bitboard_alpha_beta',runtime:'wasm',nodes,depth,value,learned_value:!!positionHead?.enabled,evaluation_scope:'bounded_adversarial_search',forced_win:forcedWin,forced_loss:forcedLoss,optimal:tactical,remaining_moves:tactical?1000000-value:undefined}};
}

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
