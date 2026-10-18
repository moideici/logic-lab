
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
