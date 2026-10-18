// Bitboards 7×7 : six rangées jouables et une sentinelle par colonne.
export const CONNECT_LIMITS=[64,256,1024,4096,20000,100000,500000,2000000,10000000,30000000];
export const CONNECT_TIMES=[1,2,4,8,16,30,60,100,180,300];
const CENTER=[3,2,4,1,5,0,6],WIN=1000000;
const BITS=Array.from({length:49},(_,i)=>1n<<BigInt(i));
const BOTTOM=CENTER.reduce((m,c)=>m|BITS[c*7],0n);
const BOARD=CENTER.reduce((m,c)=>m|(63n<<BigInt(c*7)),0n);
const ODD=CENTER.reduce((m,c)=>m|(21n<<BigInt(c*7)),0n);
const SHIFTS=[7n,6n,8n];
const LINES=[],CELL_LINES=Array.from({length:49},()=>[]);
for(let r=0;r<6;r++)for(let c=0;c<7;c++)for(const [dr,dc] of [[0,1],[1,0],[1,1],[1,-1]]){
 if(r+3*dr<6&&c+3*dc>=0&&c+3*dc<7){const line=Array.from({length:4},(_,i)=>(c+i*dc)*7+r+i*dr),index=LINES.length;LINES.push(line);for(const at of line)CELL_LINES[at].push(index);}
}
export function winningPositions(p,mask){
 let out=(p<<1n)&(p<<2n)&(p<<3n);
 for(const s of SHIFTS){let pair=(p<<s)&(p<<(2n*s));out|=pair&(p<<(3n*s));out|=pair&(p>>s);pair=(p>>s)&(p>>(2n*s));out|=pair&(p<<s);out|=pair&(p>>(3n*s));}
 return out&BOARD&~mask;
}
const multiple=bits=>Boolean(bits&(bits-1n));
const count=bits=>{let n=0;while(bits){bits&=bits-1n;n++;}return n;};
export function connectStrong(o,legal,logits,budget,{maxDepth=24}={}){
 const root=o.current_player,bits=[0n,0n,0n],heights=Array(7).fill(0),cells=Array(49).fill(0);
 for(let c=0;c<7;c++)for(let r=0;r<6;r++){const p=o.board[5-r][c],at=c*7+r;if(p){bits[p]|=BITS[at];heights[c]=r+1;cells[at]=p;}}
 let mask=bits[1]|bits[2],occupied=heights.reduce((a,b)=>a+b,0),score=0;
 const own=new Uint8Array(LINES.length),opp=new Uint8Array(LINES.length),A=[0,2,16,120,WIN],D=[0,2,18,140,WIN];
 const lineScore=k=>(opp[k]?0:A[own[k]])-(own[k]?0:D[opp[k]]);
 LINES.forEach((line,k)=>{for(const at of line){own[k]+=cells[at]===root;opp[k]+=cells[at]===3-root;}score+=lineScore(k);});
 for(let r=0;r<6;r++)score+=cells[21+r]===root?7:cells[21+r]===3-root?-7:0;
 function play(c,p){const at=c*7+heights[c]++,bit=BITS[at],counts=p===root?own:opp;for(const k of CELL_LINES[at]){score-=lineScore(k);counts[k]++;score+=lineScore(k);}if(c===3)score+=p===root?7:-7;bits[p]|=bit;mask|=bit;occupied++;return at;}
 function undo(c,p,at){const counts=p===root?own:opp;for(const k of CELL_LINES[at]){score-=lineScore(k);counts[k]--;score+=lineScore(k);}if(c===3)score-=p===root?7:-7;bits[p]^=BITS[at];mask^=BITS[at];heights[c]--;occupied--;}
 const possible=()=>((mask+BOTTOM)&BOARD);
 function safeMoves(p,possibleMask){const enemy=winningPositions(bits[3-p],mask),forced=possibleMask&enemy;if(multiple(forced))return 0n;return (forced||possibleMask)&~(enemy>>1n);}
 const columns=m=>CENTER.filter(c=>heights[c]<6&&Boolean(m&BITS[c*7+heights[c]]));
 const preference=c=>Number(logits?.[c]??-Math.abs(c-3));
 const choose=cols=>cols.slice().sort((a,b)=>preference(b)-preference(a))[0];
 const result=(c,method,info={})=>({action:{column:c},info:{method,optimal:false,nodes:budget.nodes,...info}});
 const moves=possible(),wins=moves&winningPositions(bits[root],mask);
 if(wins)return result(choose(columns(wins)),'tactical_win',{optimal:true,remaining_moves:1,forced_win:true});
 const safe=safeMoves(root,moves),choices=columns(safe||moves),forks=[];
 for(const c of columns(safe)){const at=play(c,root);try{if(multiple(possible()&winningPositions(bits[root],mask)))forks.push(c);}finally{undo(c,root,at);}}
 if(forks.length)return result(choose(forks),'tactical_fork',{optimal:true,remaining_moves:3,forced_win:true});
 if(safe&&choices.length===1)return result(choices[0],'only_safe_move');
 const cache=new Map(),preferred=new Map();let hits=0;
 function visit(depth,p,alpha,beta,ply){
  budget.tick();const moves=possible();if(!moves)return 0;
  if(moves&winningPositions(bits[p],mask))return WIN-ply-1;
  const safe=safeMoves(p,moves);if(!safe)return -WIN+ply+2;
  const forced=Boolean(moves&winningPositions(bits[3-p],mask));
  if(!depth&&!forced){const ownThreats=winningPositions(bits[root],mask),enemyThreats=winningPositions(bits[3-root],mask),favored=root===1?ODD:BOARD^ODD;
   const value=score+100*count(ownThreats)-110*count(enemyThreats)+80*count(ownThreats&favored)-90*count(enemyThreats&(BOARD^favored));
   return p===root?value:-value;
  }
  depth=Math.max(depth,1);
  const position=(bits[p]<<49n)|mask,originalAlpha=alpha,originalBeta=beta,cached=cache.get(position);
  if(cached&&cached.depth>=depth){hits++;if(cached.flag===0)return cached.value;if(cached.flag===1)alpha=Math.max(alpha,cached.value);else beta=Math.min(beta,cached.value);if(alpha>=beta)return cached.value;}
  const ordered=columns(safe),prior=preferred.get(position);
  if(ordered.length>1){const rank=new Map();for(const c of ordered){const at=play(c,p);try{rank.set(c,count(winningPositions(bits[p],mask)));}finally{undo(c,p,at);}}ordered.sort((a,b)=>rank.get(b)-rank.get(a));}
  if(ordered.includes(prior)){ordered.splice(ordered.indexOf(prior),1);ordered.unshift(prior);}
  let value=-Infinity,best=ordered[0];
  for(const c of ordered){const at=play(c,p);let child;try{child=-visit(depth-1,3-p,-beta,-alpha,ply+1);}finally{undo(c,p,at);}if(child>value){value=child;best=c;}alpha=Math.max(alpha,value);if(alpha>=beta)break;}
  preferred.set(position,best);cache.set(position,{depth,value,flag:value<=originalAlpha?2:value>=originalBeta?1:0});return value;
 }
 const order=choices.sort((a,b)=>preference(b)-preference(a));let best=order[0],bestValue=-Infinity,reached=0;
 const remaining=42-occupied;
 for(let depth=1;depth<=Math.min(maxDepth,remaining);depth++){
  let value=-Infinity,candidate=best;
  try{
   for(const c of [best,...order.filter(c=>c!==best)]){const at=play(c,root);let v;try{v=-visit(depth-1,3-root,-Infinity,-value,1);}finally{undo(c,root,at);}if(v>value){value=v;candidate=c;}}
   best=candidate;bestValue=value;reached=depth;
   if(Math.abs(value)>WIN-43||depth===remaining)break;
  }catch(error){if(error.message!=='budget')throw error;break;}
 }
 const proven=reached===remaining;
 return result(best,'bitboard_alpha_beta',{depth:reached,forced_win:bestValue>WIN-43,forced_loss:bestValue< -WIN+43,optimal:proven,remaining_moves:proven&&Math.abs(bestValue)>WIN-43?WIN-Math.abs(bestValue):undefined,cache_hits:hits});
}
