// Gomoku RIF (cinq exact) : tables de motifs, alpha-bêta et suites de quatres (VCF).
// Aucun entraînement : tout est écrit à la main ; les coefficients de PARAMS sont réglés par duels (bench/gomoku-duel.mjs).
import {gomokuColor} from './gomoku-games.js';
import {gomokuValues as openingValues} from './gomoku-planner.js';
const W=25,PAD=5,DIRS=[1,W,W+1,W-1],MATE=1000000;
export const PARAMS={breadth:[20,12,9,8,6,6,5,5,4,4,4,4],maxDepth:14,vcfDepth:14,own2:.35,opp1:.95,opp2:.3,
 w:{five:1e6,open4:2e5,four43:1e5,three33:3e4,four:8e3,three:2500,pot:1}};
// Classes d'un motif sur une ligne (case centrale supposée posée) : 0 rien, 1 trois fermé, 2 trois ouvert, 3 quatre, 4 quatre ouvert, 5 cinq exact.
function runThrough(seg){let a=5,b=5;while(a>0&&seg[a-1]===1)a--;while(b<10&&seg[b+1]===1)b++;return b-a+1;}
function winCount(seg){let n=0;for(let e=0;e<11;e++)if(seg[e]===0){seg[e]=1;if(runThrough(seg)===5)n++;seg[e]=0;}return n;}
function classify(seg){
 seg[5]=1;let cls=0;
 if(runThrough(seg)===5)cls=5;
 else{const w=winCount(seg);
  if(w>=2)cls=4;else if(w===1)cls=3;
  else{let best=0;for(let e=0;e<11&&best<2;e++)if(seg[e]===0){seg[e]=1;const w2=winCount(seg);seg[e]=0;if(w2>=2)best=2;else if(w2===1)best=1;}cls=best;}}
 let pot=0;
 for(let lo=1;lo<=5;lo++){let mine=0,bad=false;for(let i=lo;i<lo+5;i++){if(seg[i]===2)bad=true;else if(seg[i]===1)mine++;}if(!bad)pot+=[0,1,3,12,40,0][mine];}
 return cls*256+Math.min(pot,255);
}
const table=new Int16Array(59049).fill(-1);
const MAP=[[0,1,2,2],[0,2,1,2]];// case vue par la couleur 1 / 2 : 0 vide, 1 à moi, 2 adversaire ou mur
export class Engine{
 constructor(board){
  this.b=new Int8Array(W*W).fill(3);this.near=new Uint8Array(W*W);this.cells=[];this.stones=0;
  for(let r=0;r<15;r++)for(let c=0;c<15;c++){const p=(r+PAD)*W+c+PAD;this.b[p]=0;this.cells.push(p);}
  this.pat=[null,[0,1,2,3].map(()=>new Uint16Array(W*W)),[0,1,2,3].map(()=>new Uint16Array(W*W))];
  this.zob=[null,new Float64Array(W*W),new Float64Array(W*W)];
  let s=123456789;const rnd=()=>{s^=s<<13;s^=s>>>17;s^=s<<5;return s>>>0;};
  for(const p of this.cells){this.zob[1][p]=(rnd()&16777215)*65536+(rnd()&65535);this.zob[2][p]=(rnd()&16777215)*65536+(rnd()&65535);}
  this.hash=0;
  for(const p of this.cells)for(let c=1;c<=2;c++)for(let d=0;d<4;d++)this.pat[c][d][p]=this.look(c,p,d);
  if(board)for(let r=0;r<15;r++)for(let c=0;c<15;c++)if(board[r][c])this.put((r+PAD)*W+c+PAD,board[r][c]);
 }
 look(c,p,d){const step=DIRS[d],m=MAP[c-1],b=this.b;let idx=0;
  for(let k=-5;k<=-1;k++)idx=idx*3+m[b[p+k*step]];
  for(let k=1;k<=5;k++)idx=idx*3+m[b[p+k*step]];
  let v=table[idx];
  if(v<0){let x=idx;const seg=Array(11).fill(0);for(let i=10;i>=0;i--){if(i===5)continue;seg[i]=x%3;x=Math.floor(x/3);}v=table[idx]=classify(seg);}
  return v;}
 refresh(p){for(let d=0;d<4;d++){const step=DIRS[d];for(let k=-5;k<=5;k++){const e=p+k*step;if(this.b[e]===0){this.pat[1][d][e]=this.look(1,e,d);this.pat[2][d][e]=this.look(2,e,d);}}}}
 bump(p,delta){for(let dr=-2;dr<=2;dr++)for(let dc=-2;dc<=2;dc++){const e=p+dr*W+dc;if(this.b[e]!==3)this.near[e]+=delta;}}
 put(p,c){this.b[p]=c;this.hash+=this.zob[c][p];this.stones++;this.bump(p,1);this.refresh(p);}
 take(p){const c=this.b[p];this.b[p]=0;this.hash-=this.zob[c][p];this.stones--;this.bump(p,-1);this.refresh(p);}
 score(c,p){const P=this.pat[c];let n5=0,n4o=0,n4=0,n3o=0,n3=0,pot=0;
  for(let d=0;d<4;d++){const v=P[d][p],cl=v>>8;pot+=v&255;if(cl===5)n5++;else if(cl===4)n4o++;else if(cl===3)n4++;else if(cl===2)n3o++;else if(cl===1)n3++;}
  const w=PARAMS.w;
  if(n5)return w.five;
  if(n4o||n4>=2)return w.open4;
  if(n4&&n3o)return w.four43;
  if(n3o>=2)return w.three33;
  return (n4?w.four:0)+n3o*w.three+n3*(w.three/8)+pot*w.pot;}
 hasFive(c,p){const P=this.pat[c];return (P[0][p]>>8)===5||(P[1][p]>>8)===5||(P[2][p]>>8)===5||(P[3][p]>>8)===5;}
 // Cases gagnantes de c créées par la pierre posée en p (le long des quatre lignes de p).
 winsAround(c,p){const out=[];for(let d=0;d<4;d++){const step=DIRS[d],P=this.pat[c][d];for(let k=-4;k<=4;k++){const e=p+k*step;if(k&&this.b[e]===0&&(P[e]>>8)===5&&!out.includes(e))out.push(e);}}return out;}
 toCell(p){return {row:Math.floor(p/W)-PAD,col:p%W-PAD};}
}
// Suite de quatres : renvoie la première case d'une victoire forcée de c, ou -1.
function vcf(E,c,depth,budget){
 budget.tick();const o=3-c,fours=[];
 for(const p of E.cells){if(E.b[p]||!E.near[p])continue;
  if(E.hasFive(c,p))return p;
  const P=E.pat[c];if((P[0][p]>>8)>=3||(P[1][p]>>8)>=3||(P[2][p]>>8)>=3||(P[3][p]>>8)>=3)fours.push(p);}
 if(depth<=0||!fours.length)return -1;
 for(const p of E.cells)if(!E.b[p]&&E.near[p]&&E.hasFive(o,p))return -1;
 for(const p of fours){
  E.put(p,c);const w=E.winsAround(c,p);let win=false;
  if(w.length>=2)win=true;
  else if(w.length===1){const q=w[0];if(!E.hasFive(o,q)){E.put(q,o);win=vcf(E,c,depth-1,budget)>=0;E.take(q);}}
  E.take(p);if(win)return p;}
 return -1;
}
function scan(E,c){// coups candidats triés, cases gagnantes de c et de l'adversaire
 const o=3-c,mv=[],oppFives=[];let myFive=-1,t1=0,t2=0,u1=0,u2=0;const five=PARAMS.w.five;
 for(const p of E.cells){if(E.b[p]||!E.near[p])continue;
  const s1=E.score(c,p),s2=E.score(o,p);
  if(s1>=five&&myFive<0)myFive=p;
  if(s2>=five)oppFives.push(p);
  mv.push([p,s1+PARAMS.opp1*s2,s1]);
  if(s1>t1){t2=t1;t1=s1;}else if(s1>t2)t2=s1;
  if(s2>u1){u2=u1;u1=s2;}else if(s2>u2)u2=s2;}
 mv.sort((a,b)=>b[1]-a[1]);
 return {mv,myFive,oppFives,eval:t1+PARAMS.own2*t2-PARAMS.opp1*u1-PARAMS.opp2*u2};
}
function negamax(E,c,depth,alpha,beta,ply,budget,tt){
 budget.tick();
 const o=3-c,key=E.hash*2+(c-1),orig=alpha;
 const hit=tt.get(key);let ttMove=-1;
 if(hit){ttMove=hit.m;if(hit.d>=depth){if(hit.f===0)return hit.v;if(hit.f===1&&hit.v>alpha)alpha=hit.v;else if(hit.f===2&&hit.v<beta)beta=hit.v;if(alpha>=beta)return hit.v;}}
 const sc=scan(E,c);
 if(sc.myFive>=0)return MATE-ply;
 if(!sc.mv.length)return 0;
 if(sc.oppFives.length>=2)return -(MATE-ply-1);
 let moves;
 if(sc.oppFives.length===1)moves=[sc.oppFives[0]];
 else{
  const top=sc.mv[0];
  if(top[2]>=PARAMS.w.open4){E.put(top[0],c);const w=E.winsAround(c,top[0]);E.take(top[0]);if(w.length>=2)return MATE-ply-2;}
  if(depth<=0){const w=vcf(E,c,PARAMS.vcfDepth,budget);return w>=0?MATE-ply-2:Math.round(sc.eval);}
  const lim=PARAMS.breadth[Math.min(ply,PARAMS.breadth.length-1)];
  moves=sc.mv.slice(0,lim).map(m=>m[0]);
 }
 if(ttMove>=0){const i=moves.indexOf(ttMove);if(i>0){moves.splice(i,1);moves.unshift(ttMove);}}
 const nextDepth=sc.oppFives.length===1&&ply<30?depth:depth-1;
 let best=-MATE*2,bestMove=-1;
 for(const p of moves){
  E.put(p,c);let v;
  try{v=-negamax(E,o,nextDepth,-beta,-alpha,ply+1,budget,tt);}finally{E.take(p);}
  if(v>best){best=v;bestMove=p;}
  if(v>alpha)alpha=v;if(alpha>=beta)break;}
 tt.set(key,{d:depth,v:best,f:best<=orig?2:best>=beta?1:0,m:bestMove});
 return best;
}
export function playValues(board,me,budget,maxDepth=PARAMS.maxDepth){
 const E=new Engine(board),o=3-me,tt=new Map();
 const sc=scan(E,me);let info={depth:0,forced:false};
 const heur=new Map(sc.mv.map(m=>[m[0],m[1]]));
 const result=new Map();
 const winNow=sc.myFive;
 if(winNow>=0){result.set(winNow,MATE);return {E,result,heur,info:{...info,win:'five'}};}
 let order;
 if(sc.oppFives.length>=1)order=[sc.oppFives[0]];
 else{
  let w=-1;try{w=vcf(E,me,PARAMS.vcfDepth,budget);}catch(e){if(e.message!=='budget')throw e;}
  if(w>=0){result.set(w,MATE-2);info.win='vcf';return {E,result,heur,info};}
  order=sc.mv.slice(0,PARAMS.breadth[0]).map(m=>m[0]);
 }
 for(let depth=1;depth<=maxDepth;depth++){
  const cur=new Map();let alpha=-MATE*2;
  try{
   for(const p of order){
    E.put(p,me);let v;
    try{v=-negamax(E,o,depth-1,-MATE*2,-alpha,1,budget,tt);}finally{E.take(p);}
    cur.set(p,v);if(v>alpha)alpha=v;}
  }catch(e){if(e.message!=='budget')throw e;break;}
  for(const [p,v] of cur)result.set(p,v);
  info.depth=depth;
  order=[...cur.entries()].sort((a,b)=>b[1]-a[1]).map(e=>e[0]);
  if(order.length===1||result.get(order[0])>=MATE-50||result.get(order[0])<=-MATE+50&&depth>=2)break;
 }
 if(!result.size)for(const p of order.slice(0,1))result.set(p,heur.get(p)??0);
 return {E,result,heur,info};
}
export function gomokuValues(o,legal,budget){
 const s=o.gomoku_state;
 if(s.phase!=='play')return openingValues(o,legal,budget);
 const me=gomokuColor(o.current_player,s),{E,result,heur,info}=playValues(o.board,me,budget);
 // Les coups non explorés restent sous tous les coups analysés, même perdants, classés entre eux par l'heuristique.
 const floor=Math.min(...result.values())-1e5;
 const values=legal.map(action=>{const p=(action.row+PAD)*W+action.col+PAD;
  return {action,quality:[result.has(p)?result.get(p):floor+Math.max(-9e4,Math.min(9e4,(heur.get(p)??0)/10))]};});
 return {action_values:values,info:{method:'gomoku_pattern_alpha_beta_vcf',depth:info.depth,nodes:budget.nodes,analysis_exact:false,optimal:!!info.win,immediate_win:info.win==='five',evaluation_scope:'bounded_pattern_search'}};
}
