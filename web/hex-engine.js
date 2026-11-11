// Hex 7x7 avec r√®gle de la tarte : distance de connexion avec ponts et bords virtuels, alpha-b√™ta √† table de transposition.
// Aucun entra√Ænement : coefficients de PARAMS r√©gl√©s par duels (bench/hex-duel.mjs).
import {HEX_DIRS} from './hex-games.js';
const N=7,NN=49,INF=1e9,WIN=100000;
export const PARAMS={beam:[8,6,5,4,4,3,3,3],maxDepth:12,endgame:11,dist:100,center:2,bridge:true,tempo:30,swapRule:false,firstMove:[1,0]};
// RËgle d'Èchange par connaissance (dÈsactivÈe : aucun gain mesurÈ contre la dÈcision par recherche). Ouverture forte (‡ Èchanger) : toute pierre intÈrieure, sauf prËs des coins aigus (0,0) et (6,6) ; les pierres de bord sont faibles.
const strongOpening=i=>{const r=Math.floor(i/N),c=i%N;return Math.min(r,c,N-1-r,N-1-c)>=1&&!((r===1&&c===1)||(r===N-2&&c===N-2));};
const idx=(r,c)=>r*N+c,inside=(r,c)=>r>=0&&r<N&&c>=0&&c<N;
const NEIGH=[],BRIDGES=[];
for(let r=0;r<N;r++)for(let c=0;c<N;c++){
 NEIGH.push(HEX_DIRS.map(([dr,dc])=>[r+dr,c+dc]).filter(([y,x])=>inside(y,x)).map(([y,x])=>idx(y,x)));
 BRIDGES.push([[-2,1,-1,0,-1,1],[-1,2,-1,1,0,1],[1,1,0,1,1,0],[2,-1,1,0,1,-1],[1,-2,1,-1,0,-1],[-1,-1,0,-1,-1,0]]
  .filter(([dr,dc])=>inside(r+dr,c+dc)).map(([dr,dc,a,b,e,f])=>[idx(r+dr,c+dc),idx(r+a,c+b),idx(r+e,c+f)]));}
// Paires de cases de bord qu'une pierre de la deuxi√®me rang√©e relie virtuellement au bord.
const EDGE_START=[null,[],[]],EDGE_END=[null,[],[]];
for(let r=0;r<N;r++)for(let c=0;c<N;c++){const i=idx(r,c);
 EDGE_START[1][i]=r===1?[idx(0,c),idx(0,c+1<N?c+1:c)]:null;
 EDGE_END[1][i]=r===N-2?[idx(N-1,c),idx(N-1,c-1>=0?c-1:c)]:null;
 EDGE_START[2][i]=c===1?[idx(r,0),idx(r+1<N?r+1:r,0)]:null;
 EDGE_END[2][i]=c===N-2?[idx(r,N-1),idx(r-1>=0?r-1:r,N-1)]:null;}
const side=(color,i)=>color===1?Math.floor(i/N):i%N;
// Dijkstra complet depuis un bord (rev : depuis le bord opposÈ), ponts et bords virtuels compris : co˚t en pierres ‡ poser.
function dijk(b,color,rev){
 const o=3-color,dist=new Int16Array(NN).fill(1000),done=new Uint8Array(NN),src=rev?N-1:0,edge=rev?EDGE_END[color]:EDGE_START[color],bridges=PARAMS.bridge;
 for(let i=0;i<NN;i++){
  if(b[i]===o)continue;
  if(side(color,i)===src)dist[i]=b[i]===color?0:1;
  else if(bridges&&b[i]===color){const e=edge[i];if(e&&b[e[0]]===0&&b[e[1]]===0)dist[i]=0;}}
 for(;;){
  let k=-1,best=1000;for(let i=0;i<NN;i++)if(!done[i]&&dist[i]<best){best=dist[i];k=i;}
  if(k<0)return dist;done[k]=1;
  for(const n of NEIGH[k]){if(b[n]===o)continue;const v=best+(b[n]===color?0:1);if(v<dist[n])dist[n]=v;}
  if(bridges&&b[k]===color)for(const [t,x,y] of BRIDGES[k]){if(b[t]===o||b[x]||b[y])continue;const v=best+(b[t]===color?0:1);if(v<dist[t])dist[t]=v;}
 }
}
// Distance de connexion et, case par case, la longueur du meilleur chemin qui la traverse.
function analyse(b,color){
 const dS=dijk(b,color,false),dE=dijk(b,color,true),thr=new Int16Array(NN);let d=1000;
 for(let i=0;i<NN;i++){const v=dS[i]>=1000||dE[i]>=1000?1000:dS[i]+dE[i]-(b[i]?0:1);thr[i]=v;if(v<d)d=v;}
 return {thr,d};
}
function distance(b,color){// un seul Dijkstra : distance minimale jusqu'au bord opposÈ
 const dist=dijk(b,color,false),edge=EDGE_END[color];let d=1000;
 for(let i=0;i<NN;i++){if(dist[i]>=d)continue;
  if(side(color,i)===N-1)d=dist[i];
  else if(PARAMS.bridge&&b[i]===color&&edge[i]&&b[edge[i][0]]===0&&b[edge[i][1]]===0)d=dist[i];}
 return d;}
function connected(b,color){
 const seen=new Uint8Array(NN),stack=[];
 for(let i=0;i<NN;i++)if(side(color,i)===0&&b[i]===color){seen[i]=1;stack.push(i);}
 while(stack.length){const k=stack.pop();if(side(color,k)===N-1)return true;for(const n of NEIGH[k])if(!seen[n]&&b[n]===color){seen[n]=1;stack.push(n);}}
 return false;
}
function evaluate(b,color){// du point de vue de `color` au trait
 const dm=distance(b,color),dop=distance(b,3-color);
 let center=0;for(let i=0;i<NN;i++)if(b[i]){const r=Math.floor(i/N),c=i%N;center+=(b[i]===color?1:-1)*(6-Math.abs(r-3)-Math.abs(c-3));}
 return PARAMS.dist*(dop-dm)+PARAMS.center*center+PARAMS.tempo;
}
function ordered(b,color){// cases candidates : celles qui servent mon meilleur chemin ou coupent celui de l'adversaire
 const me=analyse(b,color),op=analyse(b,3-color),out=[];
 for(let i=0;i<NN;i++)if(!b[i]){const r=Math.floor(i/N),c=i%N;out.push([i,0,-(me.thr[i]+op.thr[i])*10-Math.abs(r-3)-Math.abs(c-3)]);}
 return out;
}
function search(b,color,depth,alpha,beta,ply,budget,tt,empties){
 budget.tick();
 const key=b.join('')+color,hit=tt.get(key);let ttMove=-1;
 if(hit){ttMove=hit.m;if(hit.d>=depth){if(hit.f===0)return hit.v;if(hit.f===1&&hit.v>alpha)alpha=hit.v;else if(hit.f===2&&hit.v<beta)beta=hit.v;if(alpha>=beta)return hit.v;}}
 if(depth<=0||empties===0)return evaluate(b,color);
 const orig=alpha,cand=ordered(b,color);
 cand.sort((x,y)=>y[2]-x[2]);
 let moves=cand.map(m=>m[0]);
 if(empties>PARAMS.endgame){const lim=PARAMS.beam[Math.min(ply,PARAMS.beam.length-1)];moves=moves.slice(0,lim);}
 if(ttMove>=0){const i=moves.indexOf(ttMove);if(i>0){moves.splice(i,1);moves.unshift(ttMove);}else if(i<0)moves.unshift(ttMove);}
 let best=-INF,bestMove=-1;
 for(const i of moves){
  b[i]=color;let v;
  try{v=connected(b,color)?WIN-ply:-search(b,3-color,depth-1,-beta,-alpha,ply+1,budget,tt,empties-1);}finally{b[i]=0;}
  if(v>best){best=v;bestMove=i;}if(v>alpha)alpha=v;if(alpha>=beta)break;}
 tt.set(key,{d:depth,v:best,f:best<=orig?2:best>=beta?1:0,m:bestMove});
 return best;
}
export function hexValues(o,legal,budget){
 const b=Int8Array.from(o.board.flat()),s=o.hex_state,me=s.colors[o.current_player-1],tt=new Map();
 const moves=legal.filter(a=>!a.swap),swap=legal.find(a=>a.swap);
 const empties=b.reduce((n,v)=>n+(v?0:1),0),results=new Map();let depthDone=0;
 // victoire imm√©diate
 for(const a of moves){const i=idx(a.row,a.col);b[i]=me;const win=connected(b,me);b[i]=0;if(win)results.set(i,WIN);}
 if(!results.size){
  let order=ordered(b,me).sort((x,y)=>y[2]-x[2]).map(m=>m[0]);
  const keep=empties>PARAMS.endgame?order.slice(0,Math.max(PARAMS.beam[0],10)):order;
  const limit=Math.min(PARAMS.maxDepth,empties);
  let seeded=false;
  for(let depth=1;depth<=limit;depth++){
   const cur=new Map();let alpha=-INF;
   try{
    for(const i of order.filter(i=>keep.includes(i))){
     b[i]=me;let v;
     try{v=connected(b,me)?WIN:-search(b,3-me,depth-1,-INF,-alpha,1,budget,tt,empties-1);}finally{b[i]=0;}
     cur.set(i,v);if(v>alpha)alpha=v;}
   }catch(e){if(e.message!=='budget')throw e;break;}
   for(const [i,v] of cur)results.set(i,v);depthDone=depth;seeded=true;
   order=[...cur.entries()].sort((x,y)=>y[1]-x[1]).map(e=>e[0]).concat(order.filter(i=>!cur.has(i)));
   const top=Math.max(...cur.values());if(top>=WIN-60||(top<=-WIN+60&&depth>=2))break;
  }
  if(!seeded){const e=ordered(b,me).sort((x,y)=>y[2]-x[2])[0];results.set(e[0],evaluate(b,me));}
 }
 if(empties===NN){const first=idx(...PARAMS.firstMove);results.set(first,1e4);}
 const floor=Math.min(...results.values())-1e4,heur=new Map(ordered(b,me).map(m=>[m[0],m[2]]));
 const values=legal.map(a=>{
  if(a.swap){// √©change : je prends la pierre pos√©e, donc la valeur du meilleur coup non √©chang√© devient la mienne invers√©e
   const best=Math.max(...results.values());return {action:a,quality:[-best]};}
  const i=idx(a.row,a.col);return {action:a,quality:[results.has(i)?results.get(i):floor+(heur.get(i)??0)/100]};});
 return {action_values:values,info:{method:'hex_bridge_distance_alpha_beta',depth:depthDone,nodes:budget.nodes,analysis_exact:false,optimal:false,immediate_win:[...results.values()].includes(WIN),evaluation_scope:'bounded_connection_search'}};
}
