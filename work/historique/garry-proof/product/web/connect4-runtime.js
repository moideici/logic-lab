import {connectStrong,CONNECT_LIMITS,CONNECT_TIMES} from './connect4.js';
import {lookupSearchMemory,memoryDecision} from './search-memory.js';
export {CONNECT_LIMITS,CONNECT_TIMES};
let runtime=null;
export const connectReady=(async()=>{try{
 const url=new URL('./connect4-search.wasm',import.meta.url);
 const bytes=typeof process!=='undefined'&&process.versions?.node?(await import('node:fs/promises')).readFile(url):fetch(url).then(r=>{if(!r.ok)throw Error('Moteur indisponible');return r.arrayBuffer();});
 runtime=(await WebAssembly.instantiate(await bytes,{env:{now:()=>performance.now(),abort(){throw Error('Erreur du moteur Garry');}}})).instance.exports;
}catch{ /* Le solveur JavaScript reste disponible hors WebAssembly. */ }})();
export const connectRuntime=()=>runtime?'wasm':'javascript';
export function connectDecision(o,legal,logits,budget,{timeMs=300,maxDepth=40,analyze=false,positionHead=null,searchMemory=null}={}){
 if(!analyze){const entry=lookupSearchMemory(o,legal,searchMemory);if(entry)return memoryDecision(entry,42-o.board.flat().filter(Boolean).length);}
 if(!runtime){if(!analyze)return connectStrong(o,legal,logits,budget,{maxDepth});return fallbackAnalysis(o,legal,logits,budget,maxDepth);}
 runtime.enableValue(positionHead?.enabled?1:0);
 if(positionHead?.enabled)positionHead.weights.forEach((v,i)=>runtime.setValueWeight(i,v));
 const bits=[0n,0n,0n];o.board.forEach((row,r)=>row.forEach((p,c)=>{if(p)bits[p]|=1n<<BigInt(c*7+5-r);}));
 const order=legal.slice().sort((a,b)=>Number(logits?.[b.column]??-Math.abs(b.column-3))-Number(logits?.[a.column]??-Math.abs(a.column-3)));
 for(let c=0;c<7;c++)runtime.setPrior(c,-1);
 order.forEach((a,i)=>runtime.setPrior(a.column,7-i));
 // Les tests et benchmarks peuvent fournir une borne en nœuds explicite.
 const limit=Number.isInteger(budget.limit)?budget.limit:Math.max(0,CONNECT_LIMITS[9]);
 const column=runtime[analyze?'analyze':'decideVerified'](bits[1],bits[2],o.current_player,limit,timeMs,maxDepth),nodes=runtime.getNodes(),depth=runtime.getDepth(),value=runtime.getValue();
 budget.nodes=nodes;
 if(!legal.some(a=>a.column===column))throw Error('Décision Garry illégale');
 const forcedWin=value>999957,forcedLoss=value< -999957;
 const certificate=analyze?0:runtime.getProofState(),tactical=!certificate&&forcedWin&&(value===999999||value===999997);
 const remaining=42-o.board.flat().filter(Boolean).length,proof=forcedWin?'win':forcedLoss?'loss':certificate===3?'draw':certificate===1?'non_loss':depth>=remaining?'draw':null;
 const exactOutcome=certificate>=2||forcedWin||forcedLoss||depth>=remaining,certifiedNonLoss=(certificate>=1&&certificate<=3)||forcedWin||proof==='draw';
 const trace=certificate>0&&certificate<4?runtime.traceProof:runtime.trace;
 const principal_variation=Array.from({length:trace(bits[1],bits[2],o.current_player,column,certificate?remaining:Math.max(depth,1))},(_,i)=>runtime.getPrincipal(i));
 const action_values=analyze?legal.map(action=>({action,quality:[runtime.getScore(action.column)]})):undefined;
 return {action:{column},action_values,info:{method:certificate?'exact_wdl_search':tactical?(value===999999?'tactical_win':'tactical_fork'):'bitboard_alpha_beta',runtime:'wasm',nodes,depth,value,principal_variation,proof,search_complete:!!proof&&proof!=='non_loss',outcome_proven:exactOutcome,certified_non_loss:certifiedNonLoss,certificate_nodes:analyze?0:runtime.getProofNodes(),solved_horizon:exactOutcome?remaining:null,mate_distance_known:!certificate&&(forcedWin||forcedLoss),learned_value:!!positionHead?.enabled,evaluation_scope:exactOutcome?'exact_game_outcome':certifiedNonLoss?'certified_non_loss':'bounded_adversarial_search',forced_win:forcedWin,forced_loss:forcedLoss,optimal:!certificate&&(tactical||forcedWin||depth>=remaining),outcome_optimal:exactOutcome,remaining_moves:tactical?1000000-value:undefined}};
}

function fallbackAnalysis(o,legal,logits,budget,maxDepth){
 const values=legal.map(action=>{const board=o.board.map(r=>r.slice()),r=board.map(row=>row[action.column]).lastIndexOf(0);board[r][action.column]=o.current_player;
  let won=false;for(const [dr,dc] of [[0,1],[1,0],[1,1],[1,-1]]){let n=1;for(const sign of [-1,1]){let y=r+sign*dr,c=action.column+sign*dc;while(y>=0&&y<6&&c>=0&&c<7&&board[y][c]===o.current_player){n++;y+=sign*dr;c+=sign*dc;}}if(n>=4)won=true;}
  if(won)return {action,quality:[999999]};const childLegal=board[0].flatMap((v,column)=>v?[]:[{column}]);if(!childLegal.length)return {action,quality:[0]};
  const local={nodes:0,limit:Math.max(1,Math.floor((budget.limit??10000)/legal.length))},began=performance.now();local.tick=function(){if(this.nodes++>=this.limit||performance.now()-began>30)throw Error('budget');};
  const d=connectStrong({...o,board,current_player:3-o.current_player},childLegal,Array(7).fill(0),local,{maxDepth});budget.nodes+=local.nodes;
  const v=d.info.value??(d.info.forced_win?999990:d.info.forced_loss?-999990:0);return {action,quality:[-v]};
 });
 const best=values.slice().sort((a,b)=>b.quality[0]-a.quality[0])[0];return {action:best.action,action_values:values,info:{method:best.quality[0]===999999?'tactical_win':'javascript_root_analysis',remaining_moves:best.quality[0]===999999?1:undefined,runtime:'javascript',optimal:best.quality[0]===999999,nodes:budget.nodes,evaluation_scope:'bounded_adversarial_search'}};
}
export function positionRuntimeValue(o,head){if(!runtime)throw Error('WASM indisponible');runtime.enableValue(head.enabled?1:0);head.weights.forEach((v,i)=>runtime.setValueWeight(i,v));const bits=[0n,0n,0n];o.board.forEach((row,r)=>row.forEach((p,c)=>{if(p)bits[p]|=1n<<BigInt(c*7+5-r);}));return runtime.evaluateBoard(bits[1],bits[2],o.current_player);}
