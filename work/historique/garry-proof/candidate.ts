// Source du moteur local Garry ; aucune donnée cachée ou service distant.
@external("env", "now") declare function now(): f64;
const WIN: i32 = 1000000;
const SIZE: i32 = 1 << 20;
const BOARD: u64 = 0xFDFBF7EFDFBF;
const BOTTOM: u64 = 0x40810204081;
const keys = new StaticArray<u64>(SIZE);
const values = new StaticArray<i32>(SIZE);
const depths = new StaticArray<u8>(SIZE);
const flags = new StaticArray<u8>(SIZE);
const bestCols = new StaticArray<i8>(SIZE);
const moveStack = new StaticArray<u64>(43 * 7);
const rankStack = new StaticArray<i32>(43 * 7);
const columnStack = new StaticArray<i32>(43 * 7);
const lines = new StaticArray<u64>(69);
const lineFeatures = new StaticArray<i32>(69);
const parity = new StaticArray<u64>(2);
const valueWeights = new StaticArray<f64>(32);
let learned=false;
const center = new StaticArray<i32>(7);
const priors = new StaticArray<i32>(7);
let initialized = false;
let nodeLimit: i32 = 0, deadline: f64 = 0, expired = false;
let nodes: i32 = 0, reached: i32 = 0, finalValue: i32 = 0;

function initialize(): void {
 if (initialized) return;
 const order = [3,2,4,1,5,0,6];
 for(let i=0;i<7;i++)center[i]=order[i];
 let at=0;
 for(let r=0;r<6;r++)for(let c=0;c<7;c++)for(let d=0;d<4;d++){
  const dr=d==0?0:1,dc=d==0?1:d==1?0:d==2?1:-1;
  if(r+3*dr<6&&c+3*dc>=0&&c+3*dc<7){let mask:u64=0;for(let i=0;i<4;i++)mask|=<u64>1<<((c+i*dc)*7+5-r-i*dr);lines[at]=mask;lineFeatures[at++]=(d*2+(r&1))*3;}
 }
 for(let r=0;r<6;r++)for(let c=0;c<7;c++)parity[r&1]|=<u64>1<<(c*7+5-r);
 initialized=true;
}
function winning(p:u64,mask:u64):u64{
 let out=(p<<1)&(p<<2)&(p<<3);
 for(let i=0;i<3;i++){const s=i==0?7:i==1?6:8;let pair=(p<<s)&(p<<(2*s));out|=pair&(p<<(3*s));out|=pair&(p>>s);pair=(p>>s)&(p>>(2*s));out|=pair&(p<<s);out|=pair&(p>>(3*s));}
 return out&BOARD&~mask;
}
function safe(position:u64,mask:u64,moves:u64):u64{
 const enemy=winning(position^mask,mask),forced=moves&enemy;
 if(forced&&(forced&(forced-1)))return 0;
 return (forced?forced:moves)&~(enemy>>1);
}
const EVAL_SIZE:i32=1<<18;
const evalKeys=new StaticArray<u64>(EVAL_SIZE);
const evalValues=new StaticArray<i32>(EVAL_SIZE);
const evalTags=new StaticArray<u32>(EVAL_SIZE);
let evalEpoch:u32=1;
function invalidateEval():void{evalEpoch++;if(!evalEpoch){memory.fill(changetype<usize>(evalTags),0,EVAL_SIZE*4);evalEpoch=1;}}
function evaluate(position:u64,mask:u64):i32{
 const key=position+mask,index=<i32>((key*<u64>0x9e3779b97f4a7c15)>>46);
 if(evalTags[index]==evalEpoch&&evalKeys[index]==key)return evalValues[index];
 const score=rawEvaluate(position,mask);evalKeys[index]=key;evalValues[index]=score;evalTags[index]=evalEpoch;return score;
}
function rawEvaluate(position:u64,mask:u64):i32{
 const enemy=position^mask;let score=0;
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
 }
 for(let i=0;i<69;i++){
  const line=lines[i],a=<i32>popcnt<u64>(position&line),b=<i32>popcnt<u64>(enemy&line);
  if(!b)score+=a==3?120:a==2?16:a==1?2:0;
  if(!a)score-=b==3?120:b==2?16:b==1?2:0;
 }
 const middle:u64=<u64>63<<21;
 return score+7*(<i32>popcnt<u64>(position&middle)-<i32>popcnt<u64>(enemy&middle));
}
function visit(position:u64,mask:u64,depth:i32,alpha:i32,beta:i32,ply:i32):i32{
 if(expired)return 0;
 if(nodes>=nodeLimit){expired=true;return 0;}
 nodes++;
 if((nodes&1023)==0&&now()>=deadline){expired=true;return 0;}
 const moves=(mask+BOTTOM)&BOARD;
 if(!moves)return 0;
 if(moves&winning(position,mask))return WIN-ply-1;
 const nonLosing=safe(position,mask,moves);
 if(!nonLosing)return -WIN+ply+2;
 const forced=bool(moves&winning(position^mask,mask));
 if(depth<=0&&!forced){
  for(let c=0;c<7;c++){
   const move=nonLosing&(<u64>63<<(c*7));if(!move)continue;
   const nextMask=mask|move,nextMoves=(nextMask+BOTTOM)&BOARD,threats=nextMoves&winning(position|move,nextMask);
   if(threats&&(threats&(threats-1)))return WIN-ply-3;
  }
  return evaluate(position,mask);
 }
 depth=max(depth,1);
 beta=min(beta,WIN-ply-3);
 if(alpha>=beta)return beta;
 const key=position+mask,index=<i32>((key*<u64>0x9e3779b97f4a7c15)>>44),originalAlpha=alpha,originalBeta=beta;
 let prior:i32=-1;
 if(depths[index]&&keys[index]==key){
  prior=bestCols[index];
  if(<i32>depths[index]>=depth){const value=values[index],flag=flags[index];if(flag==1)return value;if(flag==2)alpha=max(alpha,value);else beta=min(beta,value);if(alpha>=beta)return value;}
 }
 const offset=ply*7;let count=0;
 for(let i=0;i<7;i++){
  const c=center[i],move=nonLosing&(<u64>63<<(c*7));if(!move)continue;
  const rank=(c==prior?1000:0)+16*<i32>popcnt<u64>(winning(position|move,mask|move))+7-i;
  let j=count;
  while(j>0&&rankStack[offset+j-1]<rank){moveStack[offset+j]=moveStack[offset+j-1];rankStack[offset+j]=rankStack[offset+j-1];columnStack[offset+j]=columnStack[offset+j-1];j--;}
  moveStack[offset+j]=move;rankStack[offset+j]=rank;columnStack[offset+j]=c;count++;
 }
 let value=-WIN,best=columnStack[offset];
 for(let i=0;i<count;i++){
  const move=moveStack[offset+i];
  let child=i==0?-visit(position^mask,mask|move,depth-1,-beta,-alpha,ply+1):-visit(position^mask,mask|move,depth-1,-alpha-1,-alpha,ply+1);
  if(!expired&&i>0&&child>alpha&&child<beta)child=-visit(position^mask,mask|move,depth-1,-beta,-alpha,ply+1);
  if(expired)return 0;
  if(child>value){value=child;best=columnStack[offset+i];}
  alpha=max(alpha,value);if(alpha>=beta)break;
 }
 if(!depths[index]||keys[index]!=key||depth>=<i32>depths[index]){
  keys[index]=key;values[index]=value;depths[index]=<u8>depth;bestCols[index]=<i8>best;flags[index]=<u8>(value<=originalAlpha?3:value>=originalBeta?2:1);
 }
 return value;
}
export function setPrior(column:i32,rank:i32):void{if(column>=0&&column<7)priors[column]=rank;}
export function decide(first:u64,second:u64,player:i32,limit:i32,timeMs:f64,maxDepth:i32):i32{
 initialize();invalidateEval();nodes=0;reached=0;finalValue=0;expired=false;nodeLimit=max(0,limit);deadline=now()+max(0.,timeMs);
 // Les bornes de la table dépendent du nombre de coups depuis cette racine.
 memory.fill(changetype<usize>(depths),0,SIZE);
 const position=player==1?first:second,mask=first|second,moves=(mask+BOTTOM)&BOARD,wins=moves&winning(position,mask);
 const candidates=wins?wins:safe(position,mask,moves),allowed=candidates?candidates:moves;
 let best:i32=-1,rank:i32=i32.MIN_VALUE;
 for(let i=0;i<7;i++){const c=center[i];if(allowed&(<u64>63<<(c*7))&&priors[c]>rank){rank=priors[c];best=c;}}
 if(best<0)return -1;
 if(wins){finalValue=WIN-1;return best;}
 let fork:i32=-1,forkRank:i32=i32.MIN_VALUE;
 for(let i=0;i<7;i++){const c=center[i],move=candidates&(<u64>63<<(c*7));if(move){const nextMask=mask|move,nextMoves=(nextMask+BOTTOM)&BOARD,nextWins=nextMoves&winning(position|move,nextMask);if(nextWins&&(nextWins&(nextWins-1))&&priors[c]>forkRank){fork=c;forkRank=priors[c];}}}
 if(fork>=0){finalValue=WIN-3;return fork;}
 if((allowed&(allowed-1))==0)return best;
 const remaining=42-<i32>popcnt<u64>(mask);
 for(let depth=1;depth<=min(maxDepth,remaining);depth++){
  let low=depth>1?max(-WIN,finalValue-64):-WIN,high=depth>1?min(WIN,finalValue+64):WIN;
  let value=rootVisit(position,mask,allowed,depth,low,high,best);
  if(!expired&&(value<=low||value>=high))value=rootVisit(position,mask,allowed,depth,-WIN,WIN,best);
  if(expired)break;
  best=rootBest;finalValue=value;reached=depth;
  if(abs(value)>WIN-43||now()>=deadline)break;
 }
 return best;
}
export function getNodes():i32{return nodes;}
export function getDepth():i32{return reached;}
export function getValue():i32{return finalValue;}
export function winningMask(position:u64,mask:u64):u64{return winning(position,mask);}


// A complete root vector is necessary to play deliberately badly as well as
// well. Descendants always assume a strongest responding opponent.
const rootScores = new StaticArray<i32>(7);
const nextScores = new StaticArray<i32>(7);
export function getScore(column:i32):i32{return rootScores[column];}
export function setValueWeight(index:i32,value:f64):void{if(index>=0&&index<32){valueWeights[index]=value;invalidateEval();}}
export function enableValue(enabled:i32):void{learned=enabled!=0;invalidateEval();}
export function evaluateBoard(first:u64,second:u64,player:i32):i32{initialize();return evaluate(player==1?first:second,first|second);}
export function analyze(first:u64,second:u64,player:i32,limit:i32,timeMs:f64,maxDepth:i32):i32{
 initialize();invalidateEval();nodes=0;reached=0;finalValue=0;expired=false;nodeLimit=max(0,limit);deadline=now()+max(0.,timeMs);
 memory.fill(changetype<usize>(depths),0,SIZE);
 const position=player==1?first:second,mask=first|second,moves=(mask+BOTTOM)&BOARD,wins=moves&winning(position,mask);
 let best:i32=-1,bestValue:i32=-WIN;
 for(let c=0;c<7;c++){
  const move=moves&(<u64>63<<(c*7));let value=i32.MIN_VALUE;
  if(move){const nextMask=mask|move,enemy=position^mask,enemyMoves=(nextMask+BOTTOM)&BOARD;
   if(move&wins)value=WIN-1;
   else if(enemyMoves&winning(enemy,nextMask))value=-WIN+2;
   else if(!enemyMoves)value=0;
   else if(!safe(enemy,nextMask,enemyMoves))value=WIN-3;
   else value=-evaluate(enemy,nextMask);
  }
  rootScores[c]=value;
  if(move&&(best<0||value>bestValue||(value==bestValue&&priors[c]>priors[best]))){best=c;bestValue=value;}
 }
 if(best<0)return -1;
 const remaining=42-<i32>popcnt<u64>(mask);
 for(let depth=1;depth<=min(maxDepth,remaining);depth++){
  for(let i=0;i<7;i++)nextScores[i]=rootScores[i];
  let unresolved=false;
  for(let i=-1;i<7;i++){
   const c=i<0?best:center[i];if(i>=0&&c==best)continue;
   const move=moves&(<u64>63<<(c*7));if(!move||abs(rootScores[c])>WIN-43)continue;
   unresolved=true;
   // Full windows provide comparable values, not alpha-beta upper bounds.
   const prior=rootScores[c],low=max(-WIN,prior-64),high=min(WIN,prior+64);
   let value=-visit(position^mask,mask|move,depth-1,-high,-low,1);
   if(!expired&&(value<=low||value>=high))value=-visit(position^mask,mask|move,depth-1,-WIN,WIN,1);
   nextScores[c]=value;
   if(expired)break;
  }
  if(expired)break;
  bestValue=-WIN;
  for(let c=0;c<7;c++){rootScores[c]=nextScores[c];if(rootScores[c]>bestValue||(rootScores[c]==bestValue&&priors[c]>priors[best])){bestValue=rootScores[c];best=c;}}
  reached=depth;
  if(!unresolved||now()>=deadline)break;
 }
 finalValue=rootScores[best];return best;
}

let rootBest:i32=-1;
function rootVisit(position:u64,mask:u64,allowed:u64,depth:i32,alpha:i32,beta:i32,preferred:i32):i32{
 let value=-WIN;rootBest=preferred;
 for(let i=-1;i<7;i++){
  const c=i<0?preferred:center[i];if(i>=0&&c==preferred)continue;
  const move=allowed&(<u64>63<<(c*7));if(!move)continue;
  let child=i<0?-visit(position^mask,mask|move,depth-1,-beta,-alpha,1):-visit(position^mask,mask|move,depth-1,-alpha-1,-alpha,1);
  if(!expired&&i>=0&&child>alpha&&child<beta)child=-visit(position^mask,mask|move,depth-1,-beta,-alpha,1);
  if(expired)return 0;
  if(child>value){value=child;rootBest=c;}
  alpha=max(alpha,value);if(alpha>=beta)break;
 }
 return value;
}

const principal = new StaticArray<i32>(42);
function aligned(p:u64):bool{for(let s=0;s<4;s++){const shift=s==0?1:s==1?7:s==2?6:8;const pairs=p&(p>>shift);if(pairs&(pairs>>(2*shift)))return true;}return false;}
export function trace(first:u64,second:u64,player:i32,column:i32,limit:i32):i32{
 let position=player==1?first:second,mask=first|second,count=0;
 for(let ply=0;ply<min(42,limit);ply++){
  const moves=(mask+BOTTOM)&BOARD,move=column>=0&&column<7?moves&(<u64>63<<(column*7)):0;
  if(!move)break;principal[count++]=column;
  const placed=position|move;mask|=move;if(aligned(placed))break;position=placed^mask;
  const next=(mask+BOTTOM)&BOARD;if(!next)break;
  const wins=next&winning(position,mask);
  if(wins){for(let i=0;i<7;i++)if(wins&(<u64>63<<(center[i]*7))){column=center[i];break;}continue;}
  const key=position+mask,index=<i32>((key*<u64>0x9e3779b97f4a7c15)>>44);
  if(depths[index]&&keys[index]==key){column=bestCols[index];continue;}
  const choices=safe(position,mask,next);
  if(choices&&(choices&(choices-1))==0){for(let i=0;i<7;i++)if(choices&(<u64>63<<(center[i]*7))){column=center[i];break;}continue;}
  break;
 }
 return count;
}
export function getPrincipal(index:i32):i32{return principal[index];}

// Exact win/draw/loss search. No heuristic value is allowed into this table.
const PROOF_SIZE:i32=1<<22;
const proofKeys=new StaticArray<u64>(PROOF_SIZE);
const proofBounds=new StaticArray<u8>(PROOF_SIZE);
const proofCols=new StaticArray<i8>(PROOF_SIZE);
const proofMoves=new StaticArray<u64>(43*7);
const proofRanks=new StaticArray<i32>(43*7);
const proofOrder=new StaticArray<i32>(43*7);
let proofNodes:i32=0,proofLimit:i32=0,proofDeadline:f64=0,proofExpired:bool=false;
let proofState:i32=0,proofColumn:i32=-1,proofRootBest:i32=-1;
function reflected(key:u64):u64{let result:u64=0;for(let c=0;c<7;c++){result=(result<<7)|(key&127);key>>=7;}return result;}
function proofVisit(position:u64,mask:u64,alpha:i32,beta:i32,ply:i32):i32{
 if(proofExpired)return 0;
 if(proofNodes>=proofLimit){proofExpired=true;return 0;}
 proofNodes++;
 if((proofNodes&4095)==0&&now()>=proofDeadline){proofExpired=true;return 0;}
 const moves=(mask+BOTTOM)&BOARD;
 if(!moves)return 0;
 if(moves&winning(position,mask))return 1;
 const choices=safe(position,mask,moves);
 if(!choices)return -1;
 if(popcnt<u64>(mask)>=40)return 0;
 const raw=position+mask,mirror=reflected(raw),flip=mirror<raw,key=flip?mirror:raw;
 const index=<i32>((key*<u64>0x9e3779b97f4a7c15)>>42),a0=alpha,b0=beta;
 let previous:i32=-1;
 if(proofBounds[index]&&proofKeys[index]==key){
  const flag=proofBounds[index];previous=flip?6-proofCols[index]:proofCols[index];
  if(flag<=3)return <i32>flag-2;
  if(flag==4)beta=min(beta,0);else alpha=max(alpha,0);
  if(alpha>=beta)return alpha;
 }
 let count=0;const offset=ply*7;
 for(let i=0;i<7;i++){
  const c=center[i],move=choices&(<u64>63<<(c*7));if(!move)continue;
  const rank=(c==previous?10000:0)+16*<i32>popcnt<u64>(winning(position|move,mask|move))+7-i;
  let at=count;
  while(at>0&&proofRanks[offset+at-1]<rank){proofMoves[offset+at]=proofMoves[offset+at-1];proofOrder[offset+at]=proofOrder[offset+at-1];proofRanks[offset+at]=proofRanks[offset+at-1];at--;}
  proofMoves[offset+at]=move;proofOrder[offset+at]=c;proofRanks[offset+at]=rank;count++;
 }
 let result=-1,best=proofOrder[offset];
 for(let i=0;i<count;i++){
  const value=-proofVisit(position^mask,mask|proofMoves[offset+i],-beta,-alpha,ply+1);
  if(proofExpired)return 0;
  if(value>result){result=value;best=proofOrder[offset+i];}
  alpha=max(alpha,value);if(alpha>=beta)break;
 }
 proofKeys[index]=key;proofCols[index]=<i8>(flip?6-best:best);
 proofBounds[index]=<u8>(result==-1?1:result==1?3:result<=a0?4:result>=b0?5:2);
 return result;
}
function proofRoot(position:u64,mask:u64,choices:u64,alpha:i32,beta:i32,preferred:i32):i32{
 let result=-1;proofRootBest=preferred;
 for(let i=-1;i<7;i++){
  const c=i<0?preferred:center[i];if(i>=0&&c==preferred)continue;
  const move=choices&(<u64>63<<(c*7));if(!move)continue;
  const value=-proofVisit(position^mask,mask|move,-beta,-alpha,1);
  if(proofExpired)return 0;
  if(value>result){result=value;proofRootBest=c;}
  alpha=max(alpha,value);if(alpha>=beta)break;
 }
 return result;
}
// state: 0 unknown; 1 certified non-loss; 2 win; 3 draw; 4 unavoidable loss.
export function certify(first:u64,second:u64,player:i32,limit:i32,timeMs:f64):i32{
 initialize();proofNodes=0;proofLimit=max(0,limit);proofDeadline=now()+max(0.,timeMs);proofExpired=false;proofState=0;proofColumn=-1;
 memory.fill(changetype<usize>(proofBounds),0,PROOF_SIZE);
 const position=player==1?first:second,mask=first|second,moves=(mask+BOTTOM)&BOARD;
 if(!moves){proofState=3;return -1;}
 const wins=moves&winning(position,mask),choices=wins?wins:safe(position,mask,moves);
 let best:i32=-1,rank=i32.MIN_VALUE;
 for(let i=0;i<7;i++){const c=center[i];if((choices?choices:moves)&(<u64>63<<(c*7))&&priors[c]>rank){best=c;rank=priors[c];}}
 if(wins){proofState=2;proofColumn=best;return best;}
 if(!choices){proofState=4;proofColumn=best;return best;}
 const lower=proofRoot(position,mask,choices,-1,0,best);
 if(proofExpired)return best;
 if(lower<0){proofState=4;proofColumn=proofRootBest;return proofColumn;}
 proofState=1;proofColumn=proofRootBest;
 const upper=proofRoot(position,mask,choices,0,1,proofColumn);
 if(!proofExpired){proofState=upper>0?2:3;proofColumn=proofRootBest;}
 return proofColumn;
}
export function getProofState():i32{return proofState;}
export function getProofNodes():i32{return proofNodes;}

export function decideVerified(first:u64,second:u64,player:i32,limit:i32,timeMs:f64,maxDepth:i32):i32{
 proofState=0;proofNodes=0;
 const started=now(),mask=first|second,remaining=42-<i32>popcnt<u64>(mask);
 // Early opening trees need the full heuristic search budget. From eight
 // stones onward, reserve a quarter for an independent exact outcome probe.
 if(remaining<=34&&limit>0&&timeMs>0){
  const certified=certify(first,second,player,max(1,limit/4),timeMs*.25);
  if(proofState==2||proofState==3){
   nodes=proofNodes;reached=0;finalValue=proofState==2?WIN-remaining:0;return certified;
  }
  const state=proofState,used=proofNodes;
  const fallback=decide(first,second,player,max(0,limit-used),max(0.,timeMs-(now()-started)),maxDepth);
  nodes+=used;proofState=state;
  if(state==1&&finalValue<=WIN-43){finalValue=0;reached=0;return certified;}
  if(state==4)finalValue=-WIN+remaining;
  return fallback;
 }
 return decide(first,second,player,limit,timeMs,maxDepth);
}
export function traceProof(first:u64,second:u64,player:i32,column:i32,limit:i32):i32{
 let position=player==1?first:second,mask=first|second,count=0;
 for(let ply=0;ply<min(42,limit);ply++){
  const moves=(mask+BOTTOM)&BOARD,move=column>=0&&column<7?moves&(<u64>63<<(column*7)):0;
  if(!move)break;principal[count++]=column;
  const placed=position|move;mask|=move;if(aligned(placed))break;position=placed^mask;
  const next=(mask+BOTTOM)&BOARD;if(!next)break;
  const wins=next&winning(position,mask);
  if(wins){for(let i=0;i<7;i++)if(wins&(<u64>63<<(center[i]*7))){column=center[i];break;}continue;}
  const raw=position+mask,mirror=reflected(raw),flip=mirror<raw,key=flip?mirror:raw,index=<i32>((key*<u64>0x9e3779b97f4a7c15)>>42);
  if(proofBounds[index]&&proofKeys[index]==key){column=flip?6-proofCols[index]:proofCols[index];continue;}
  const choices=safe(position,mask,next);
  if(choices&&(choices&(choices-1))==0){for(let i=0;i<7;i++)if(choices&(<u64>63<<(center[i]*7))){column=center[i];break;}continue;}
  break;
 }
 return count;
}
