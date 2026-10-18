
// A complete root vector is necessary to play deliberately badly as well as
// well. Descendants always assume a strongest responding opponent.
const rootScores = new StaticArray<i32>(7);
const nextScores = new StaticArray<i32>(7);
export function getScore(column:i32):i32{return rootScores[column];}
export function setValueWeight(index:i32,value:f64):void{if(index>=0&&index<32)valueWeights[index]=value;}
export function enableValue(enabled:i32):void{learned=enabled!=0;}
export function evaluateBoard(first:u64,second:u64,player:i32):i32{initialize();return evaluate(player==1?first:second,first|second);}
export function analyze(first:u64,second:u64,player:i32,limit:i32,timeMs:f64,maxDepth:i32):i32{
 initialize();nodes=0;reached=0;finalValue=0;expired=false;nodeLimit=max(0,limit);deadline=now()+max(0.,timeMs);
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
   nextScores[c]=-visit(position^mask,mask|move,depth-1,-WIN,WIN,1);
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
