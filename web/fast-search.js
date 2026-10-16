// Optimisations explicites : le réseau ordonne les choix, les règles vérifient
// les objectifs. Aucun professeur ni état caché n'entre dans ces fonctions.
import {actionIndex} from './engine.js';
import slidingTable from './models/sliding-distances.json' with {type:'json'};

const distances=Uint8Array.from(atob(slidingTable.data),c=>c.charCodeAt(0));
const FACT=[1,1,2,6,24,120,720,5040,40320,362880];
export function slidingDistance(board){const b=board.flat();let rank=0;for(let i=0;i<8;i++){let smaller=0;for(let j=i+1;j<9;j++)if(b[j]<b[i])smaller++;rank+=smaller*FACT[8-i];}return distances[rank];}
export function exactSliding(o,legal,logits){const distance=slidingDistance(o.board);let best=null,prior=-Infinity;const flat=o.board.flat(),zero=flat.indexOf(0),offset={up:-3,down:3,left:-1,right:1};for(const a of legal){const b=flat.slice(),at=zero+offset[a.direction];[b[zero],b[at]]=[b[at],0];if(slidingDistance([b])===distance-1&&logits[actionIndex(o.game,a)]>prior){best=a;prior=logits[actionIndex(o.game,a)];}}return {action:best||legal[0],info:{method:'exact_shortest_path',optimal:distance!==255,remaining_moves:distance,solution_found:distance!==255,nodes:legal.length}};}

const TTT_LINES=[[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]],tttMemo=new Map();
function won(b,p){return TTT_LINES.some(l=>l.every(i=>b[i]===p));}
function superior(a,b){if(!b||a.value!==b.value)return !b||a.value>b.value;return a.value===-1?a.plies>b.plies:a.plies<b.plies;}
function tttValue(b,p){if(won(b,3-p))return {value:-1,plies:0};const free=b.flatMap((v,i)=>v?[]:[i]);if(!free.length)return {value:0,plies:0};const key=b.join('')+p;if(tttMemo.has(key))return tttMemo.get(key);let best=null;for(const i of free){b[i]=p;const child=tttValue(b,3-p);b[i]=0;const v={value:-child.value,plies:child.plies+1};if(superior(v,best))best=v;}tttMemo.set(key,best);return best;}
export function exactTictactoe(o,legal,logits){const before=tttMemo.size,b=o.board.flat();let best=null,choice=legal[0],prior=-Infinity;for(const a of legal){const i=a.row*3+a.col;b[i]=o.current_player;const child=tttValue(b,3-o.current_player);b[i]=0;const v={value:-child.value,plies:child.plies+1},score=logits[i];if(superior(v,best)||(best&&v.value===best.value&&v.plies===best.plies&&score>prior)){best=v;choice=a;prior=score;}}return {action:choice,info:{method:'exact_minimax_distance',optimal:true,outcome:best.value,remaining_moves:best.plies,nodes:tttMemo.size-before,states_cached:tttMemo.size}};}

export function connectSearch(o,legal,logits,budget){
 const b=o.board.flat(),heights=Array.from({length:7},(_,c)=>{for(let r=5;r>=0;r--)if(!b[r*7+c])return r;return -1;}),root=o.current_player;
 const center=[3,2,4,1,5,0,6],lines=[];for(let r=0;r<6;r++)for(let c=0;c<7;c++)for(const [dr,dc] of [[0,1],[1,0],[1,1],[1,-1]]){const cells=Array.from({length:4},(_,i)=>(r+i*dr)*7+c+i*dc);if(r+3*dr<6&&c+3*dc>=0&&c+3*dc<7)lines.push(cells);}
 function win(r,c,p){for(const [dr,dc] of [[0,1],[1,0],[1,1],[1,-1]]){let n=1;for(const s of [-1,1]){let x=r+s*dr,y=c+s*dc;while(x>=0&&x<6&&y>=0&&y<7&&b[x*7+y]===p){n++;x+=s*dr;y+=s*dc;}}if(n>=4)return true;}return false;}
 const play=(c,p)=>{const r=heights[c]--;b[r*7+c]=p;return r;},undo=(r,c)=>{b[r*7+c]=0;heights[c]++;};
 const available=()=>center.filter(c=>heights[c]>=0);
 function immediate(p){return available().filter(c=>{const r=play(c,p),yes=win(r,c,p);undo(r,c);return yes;});}
 const wins=immediate(root);if(wins.length)return {action:{column:wins.sort((a,b)=>logits[b]-logits[a])[0]},info:{method:'tactical_win',optimal:true,remaining_moves:1,nodes:budget.nodes}};
 const threats=immediate(3-root),safe=threats.length===1?[threats[0]]:available();
 if(threats.length===1)return {action:{column:threats[0]},info:{method:'forced_block',optimal:false,nodes:budget.nodes}};
 function evaluate(){let score=0;for(const l of lines){let a=0,d=0;for(const i of l){a+=b[i]===root;d+=b[i]===3-root;}if(!d)score+=[0,2,16,120,100000][a];if(!a)score-=[0,2,18,140,100000][d];}for(let r=0;r<6;r++){if(b[r*7+3]===root)score+=7;else if(b[r*7+3]===3-root)score-=7;}return score;}
 const cache=new Map();
 function search(depth,p,alpha,beta,ply){budget.tick();const moves=available();if(!moves.length)return 0;if(!depth)return evaluate();const originalA=alpha,originalB=beta,key=b.join('')+p+':'+depth,cached=cache.get(key);if(cached){if(cached.flag==='exact')return cached.value;if(cached.flag==='lower')alpha=Math.max(alpha,cached.value);else beta=Math.min(beta,cached.value);if(alpha>=beta)return cached.value;}
  const max=p===root;let value=max?-Infinity:Infinity;
  for(const c of moves){const r=play(c,p);let v;try{v=win(r,c,p)?(max?1000000-ply:-1000000+ply):search(depth-1,3-p,alpha,beta,ply+1);}finally{undo(r,c);}value=max?Math.max(value,v):Math.min(value,v);if(max)alpha=Math.max(alpha,value);else beta=Math.min(beta,value);if(alpha>=beta)break;}
  cache.set(key,{value,flag:value<=originalA?'upper':value>=originalB?'lower':'exact'});return value;
 }
 const order=safe.sort((a,b)=>logits[b]-logits[a]);let best=order[0],depthReached=0,bestValue=-Infinity;
 for(let depth=1;depth<=10;depth++){
  let candidate=best,value=-Infinity;try{for(const c of order){const r=play(c,root);let v;try{v=search(depth-1,3-root,-Infinity,Infinity,1);}finally{undo(r,c);}if(v>value){value=v;candidate=c;}}best=candidate;bestValue=value;depthReached=depth;if(value>900000)break;}catch(error){if(error.message!=='budget')throw error;break;}
 }
 return {action:{column:best},info:{method:'neural_alpha_beta',optimal:false,depth:depthReached,forced_win:bestValue>900000,nodes:budget.nodes}};
}

let rowTables=null;
export function tables2048(){if(rowTables)return rowTables;const left=new Uint16Array(65536),right=new Uint16Array(65536),gain=new Uint32Array(65536),value=new Float64Array(65536);const reverse=n=>((n&15)<<12)|((n&240)<<4)|((n>>>4)&240)|(n>>>12);
 for(let row=0;row<65536;row++){const v=[row&15,(row>>>4)&15,(row>>>8)&15,row>>>12],nz=v.filter(Boolean),out=[];let score=0;for(let i=0;i<nz.length;i++){if(i+1<nz.length&&nz[i]===nz[i+1]){const rank=Math.min(15,nz[i]+1);out.push(rank);score+=2**rank;i++;}else out.push(nz[i]);}left[row]=out.reduce((s,v,i)=>s|(v<<(4*i)),0);gain[row]=score;let down=0,up=0,merges=0,sum=0;for(let i=0;i<4;i++){sum+=v[i]**3.5;if(i<3){const d=v[i]**4-v[i+1]**4;if(d>0)down+=d;else up-=d;}}for(let i=1;i<nz.length;i++)if(nz[i]===nz[i-1])merges++;value[row]=270*(4-nz.length)+700*merges-47*Math.min(up,down)-11*sum;}
 for(let row=0;row<65536;row++)right[row]=reverse(left[reverse(row)]);
 return rowTables={left,right,gain,value};
}
export function spawnExpectation(rows){
 const value=tables2048().value;
 const cols=Array.from({length:4},(_,c)=>rows.reduce((s,row,r)=>s|(((row>>>(c*4))&15)<<(r*4)),0));
 const base=rows.concat(cols).reduce((s,row)=>s+value[row],0);
 let adjustment=0,count=0;
 for(let r=0;r<4;r++)for(let c=0;c<4;c++){
  const row=rows[r],col=cols[c],shift=c*4;
  if((row>>>shift)&15)continue;
  const old=value[row]+value[col];
  adjustment+=.9*(value[row|(1<<shift)]+value[col|(1<<(r*4))]-old)+.1*(value[row|(2<<shift)]+value[col|(2<<(r*4))]-old);
  count++;
 }
 return count?base+adjustment/count:base;
}
export function tileSearch(o,legal,logits,budget){
 const {left,right,gain,value}=tables2048(),initial=o.board.map(row=>row.reduce((s,v,c)=>s|((v?Math.log2(v):0)<<(c*4)),0));
 function columns(rows){return Array.from({length:4},(_,c)=>rows.reduce((s,row,r)=>s|(((row>>>(c*4))&15)<<(r*4)),0));}
 function move(rows,d){const vertical=d==='up'||d==='down',source=vertical?columns(rows):rows,table=d==='up'||d==='left'?left:right,merged=source.map(row=>table[row]),score=source.reduce((s,row)=>s+gain[row],0);return [vertical?columns(merged):merged,score];}
 const equal=(a,b)=>a.every((v,i)=>v===b[i]);
 const heuristic=rows=>rows.concat(columns(rows)).reduce((s,row)=>s+value[row],0);
 const isWin=rows=>rows.some(row=>[0,4,8,12].some(shift=>((row>>>shift)&15)>=11));
 const cache=new Map(),chanceCache=new Map();
 function maxSearch(rows,depth){budget.tick();if(!depth)return heuristic(rows);const key=rows.join(',')+':'+depth,hit=cache.get(key);if(hit!==undefined)return hit;let best=-1e9;for(const d of ['up','down','left','right']){const [child,g]=move(rows,d);if(!equal(rows,child))best=Math.max(best,isWin(child)?1e9:chance(child,depth)+g*.05);}cache.set(key,best);return best;}
 function chance(rows,depth){budget.tick();const key=rows.join(',')+':'+depth;if(chanceCache.has(key))return chanceCache.get(key);if(!depth)return heuristic(rows);if(depth===1){const value=spawnExpectation(rows);chanceCache.set(key,value);return value;}const empty=[];for(let r=0;r<4;r++)for(let c=0;c<4;c++)if(!((rows[r]>>>(c*4))&15))empty.push([r,c]);if(!empty.length)return maxSearch(rows,depth-1);let score=0;for(const [r,c] of empty)for(const [rank,p] of [[1,.9],[2,.1]]){const child=rows.slice();child[r]|=rank<<(c*4);score+=p*maxSearch(child,depth-1)/empty.length;}chanceCache.set(key,score);return score;}
 const ordered=legal.slice().sort((a,b)=>logits[actionIndex(o.game,b)]-logits[actionIndex(o.game,a)]);let best=ordered[0],bestValue=-Infinity,depthReached=0;
 for(const a of ordered){const [child,g]=move(initial,a.direction);if(isWin(child))return {action:a,info:{method:'expectimax_goal',optimal:true,remaining_moves:1,nodes:budget.nodes}};const v=heuristic(child)+g*.05;if(v>bestValue+1e-7){bestValue=v;best=a;}}
 const spaces=initial.reduce((n,row)=>n+[0,4,8,12].filter(s=>!((row>>>s)&15)).length,0),depthLimit=spaces<=4?(budget.criticalDepth??budget.depth??2):(budget.depth??2);
 for(let depth=1;depth<=depthLimit;depth++){let candidate=best,value=-Infinity;try{for(const a of ordered){const [child,g]=move(initial,a.direction),score=chance(child,depth)+g*.05;if(score>value+1e-7){value=score;candidate=a;}}best=candidate;depthReached=depth;}catch(error){if(error.message!=='budget')throw error;break;}}
 return {action:best,info:{method:'neural_expectimax_tables',optimal:false,depth:depthReached,nodes:budget.nodes}};
}

function choose(n,k){if(k<0||k>n)return 0;k=Math.min(k,n-k);let out=1;for(let i=1;i<=k;i++)out=out*(n-k+i)/i;return out;}
function convolution(a,b,limit){const out=Array(limit+1).fill(0);for(let i=0;i<a.length;i++)for(let j=0;j<b.length&&i+j<=limit;j++)out[i+j]+=a[i]*b[j];return out;}
const nearby=i=>{const r=Math.floor(i/8),c=i%8,out=[];for(let x=Math.max(0,r-1);x<Math.min(8,r+2);x++)for(let y=Math.max(0,c-1);y<Math.min(8,c+2);y++)if(x!==r||y!==c)out.push(x*8+y);return out;};
export function mineSearch(o,legal,logits,budget){
 const b=o.board.flat(),hidden=b.flatMap((v,i)=>v===-1?[i]:[]),safe=new Set(),bombs=new Set();
 if(hidden.length===64)return {action:{row:3,col:3},info:{method:'protected_opening',certain_safe:true,risk:0,optimal:false,nodes:0}};
 let constraints=[];b.forEach((v,i)=>{if(v>=0){const cells=nearby(i).filter(j=>b[j]===-1);if(cells.length)constraints.push({cells,count:v});}});
 let complete=false,risks=new Map(),steps=0;
 try{while(steps++<30){budget.tick();const unique=new Map(),old=safe.size+bombs.size;for(const {cells,count} of constraints){const n=count-cells.filter(i=>bombs.has(i)).length,remaining=cells.filter(i=>!safe.has(i)&&!bombs.has(i));if(!remaining.length)continue;if(n===0)remaining.forEach(i=>safe.add(i));else if(n===remaining.length)remaining.forEach(i=>bombs.add(i));else if(n>0&&n<remaining.length)unique.set(remaining.join(','),{cells:remaining,count:n});}constraints=[...unique.values()];const remaining=hidden.filter(i=>!safe.has(i)&&!bombs.has(i)),mines=o.mine_count-bombs.size;if(mines===0)remaining.forEach(i=>safe.add(i));else if(mines===remaining.length)remaining.forEach(i=>bombs.add(i));if(safe.size+bombs.size!==old)continue;let derived=0;const current=constraints.slice();for(const a of current)for(const c of current){budget.tick();if(a.cells.length<c.cells.length&&a.cells.every(i=>c.cells.includes(i))){const cells=c.cells.filter(i=>!a.cells.includes(i)),count=c.count-a.count,k=cells.join(',');if(count>=0&&count<=cells.length&&!unique.has(k)&&unique.size<200){unique.set(k,{cells,count});derived++;}}}if(!derived){complete=true;break;}constraints=[...unique.values()];}}
 catch(error){if(error.message!=='budget')throw error;}
 const remaining=hidden.filter(i=>!bombs.has(i)),mineCount=o.mine_count-bombs.size,base=mineCount/Math.max(1,remaining.length-safe.size);
 for(const i of hidden)risks.set(i,safe.has(i)?0:bombs.has(i)?1:base);
 for(const {cells,count} of constraints)for(const i of cells)if(!safe.has(i)&&!bombs.has(i))risks.set(i,Math.max(risks.get(i)||0,count/cells.length));
 let exact=false;
 if(!safe.size&&complete){
  try{
   const frontier=[...new Set(constraints.flatMap(c=>c.cells))],groups=[],pending=new Set(frontier);
   while(pending.size){const group=new Set([pending.values().next().value]);let change=true;while(change){change=false;for(const c of constraints)if(c.cells.some(i=>group.has(i)))for(const i of c.cells)if(!group.has(i)){group.add(i);change=true;}}for(const i of group)pending.delete(i);groups.push([...group]);}
   const components=[];
   for(let vars of groups){if(vars.length>24)throw Error('approximate');const local=constraints.filter(c=>c.cells.some(i=>vars.includes(i)));vars=vars.sort((a,b)=>local.filter(c=>c.cells.includes(b)).length-local.filter(c=>c.cells.includes(a)).length);const indices=vars.map(v=>local.flatMap((c,i)=>c.cells.includes(v)?[i]:[])),sums=local.map(()=>0),left=local.map(c=>c.cells.length),assignment=vars.map(()=>0),ways=Array(mineCount+1).fill(0),mineWays=vars.map(()=>Array(mineCount+1).fill(0));
    function enumerate(at,n){budget.tick();if(n>mineCount)return;if(at===vars.length){ways[n]++;assignment.forEach((v,i)=>{if(v)mineWays[i][n]++;});return;}for(const v of [0,1]){let valid=true;for(const k of indices[at]){left[k]--;sums[k]+=v;if(sums[k]>local[k].count||sums[k]+left[k]<local[k].count)valid=false;}assignment[at]=v;if(valid)enumerate(at+1,n+v);for(const k of indices[at]){left[k]++;sums[k]-=v;}}}
    enumerate(0,0);components.push({vars,ways,mineWays});
   }
   const outside=remaining.filter(i=>!frontier.includes(i)&&!safe.has(i)),all=components.reduce((a,c)=>convolution(a,c.ways,mineCount),[1]),denom=all.reduce((s,v,k)=>s+v*choose(outside.length,mineCount-k),0);
   if(denom){for(let at=0;at<components.length;at++){const component=components[at],other=components.filter((_,i)=>i!==at).reduce((a,c)=>convolution(a,c.ways,mineCount),[1]);component.vars.forEach((v,i)=>{let numerator=0;for(let k=0;k<component.mineWays[i].length;k++)for(let j=0;j<other.length;j++)numerator+=component.mineWays[i][k]*other[j]*choose(outside.length,mineCount-k-j);risks.set(v,numerator/denom);});}const outsideRisk=all.reduce((s,v,k)=>s+v*choose(outside.length-1,mineCount-k-1),0)/denom;outside.forEach(i=>risks.set(i,outsideRisk));exact=true;}
  }catch(error){if(!['budget','approximate'].includes(error.message))throw error;}
 }
 const available=remaining.length?remaining:hidden;
 let best=available[0],bestRisk=Infinity,bestFlood=-Infinity,bestPrior=-Infinity;
 for(const i of available){
  const risk=risks.get(i)??base,neighbors=nearby(i).filter(j=>b[j]===-1);
  const flood=neighbors.reduce((p,j)=>p*(1-(risks.get(j)??base)),1)*(neighbors.length+1);
  // Comparaison lexicographique : une grande ouverture ou un score neuronal
  // ne peut jamais remplacer une case prouvée sûre par un pari.
  if(risk<bestRisk||(risk===bestRisk&&(flood>bestFlood||(flood===bestFlood&&logits[i]>bestPrior)))){
   best=i;bestRisk=risk;bestFlood=flood;bestPrior=logits[i];
  }
 }
 const risk=risks.get(best)??base;
 return {action:{row:Math.floor(best/8),col:best%8},info:{method:exact?'constraint_marginals':'public_constraints_flood',optimal:false,risk,certain_safe:risk===0,probabilities_exact:exact,nodes:budget.nodes}};
}
