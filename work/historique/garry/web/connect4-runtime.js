import {connectStrong,CONNECT_LIMITS,CONNECT_TIMES} from './connect4.js';
export {CONNECT_LIMITS,CONNECT_TIMES};
let runtime=null;
export const connectReady=(async()=>{try{
 const url=new URL('./connect4-search.wasm',import.meta.url);
 const bytes=typeof process!=='undefined'&&process.versions?.node?(await import('node:fs/promises')).readFile(url):fetch(url).then(r=>{if(!r.ok)throw Error('Moteur indisponible');return r.arrayBuffer();});
 runtime=(await WebAssembly.instantiate(await bytes,{env:{now:()=>performance.now(),abort(){throw Error('Erreur du moteur BASTION');}}})).instance.exports;
}catch{ /* Le solveur JavaScript reste disponible hors WebAssembly. */ }})();
export const connectRuntime=()=>runtime?'wasm':'javascript';
export function connectDecision(o,legal,logits,budget,{timeMs=300,maxDepth=40}={}){
 if(!runtime)return connectStrong(o,legal,logits,budget,{maxDepth});
 const bits=[0n,0n,0n];o.board.forEach((row,r)=>row.forEach((p,c)=>{if(p)bits[p]|=1n<<BigInt(c*7+5-r);}));
 const order=legal.slice().sort((a,b)=>Number(logits?.[b.column]??-Math.abs(b.column-3))-Number(logits?.[a.column]??-Math.abs(a.column-3)));
 for(let c=0;c<7;c++)runtime.setPrior(c,-1);
 order.forEach((a,i)=>runtime.setPrior(a.column,7-i));
 // Les tests et benchmarks peuvent fournir une borne en nœuds explicite.
 const limit=Number.isInteger(budget.limit)?budget.limit:Math.max(0,CONNECT_LIMITS[9]);
 const column=runtime.decide(bits[1],bits[2],o.current_player,limit,timeMs,maxDepth),nodes=runtime.getNodes(),depth=runtime.getDepth(),value=runtime.getValue();
 budget.nodes=nodes;
 if(!legal.some(a=>a.column===column))throw Error('Décision BASTION illégale');
 const forcedWin=value>999957,forcedLoss=value< -999957;
 const tactical=forcedWin&&(value===999999||value===999997)&&depth===0;
 return {action:{column},info:{method:tactical?(value===999999?'tactical_win':'tactical_fork'):'bitboard_alpha_beta',runtime:'wasm',nodes,depth,forced_win:forcedWin,forced_loss:forcedLoss,optimal:tactical,remaining_moves:tactical?1000000-value:undefined}};
}
