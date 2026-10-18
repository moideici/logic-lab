// Source du moteur local Garry ; aucune donnée cachée ou service distant.
@external("env", "now") declare function now(): f64;
const WIN: i32 = 1000000;
const SIZE: i32 = 1 << 18;
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
function evaluate(position:u64,mask:u64):i32{
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
 if(depth<=0&&!forced)return evaluate(position,mask);
 depth=max(depth,1);
 beta=min(beta,WIN-ply-3);
 if(alpha>=beta)return beta;
 const key=position+mask,index=<i32>((key*<u64>0x9e3779b97f4a7c15)>>46),originalAlpha=alpha,originalBeta=beta;
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
  const move=moveStack[offset+i],child=-visit(position^mask,mask|move,depth-1,-beta,-alpha,ply+1);
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
 initialize();nodes=0;reached=0;finalValue=0;expired=false;nodeLimit=max(0,limit);deadline=now()+max(0.,timeMs);
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
  let candidate=best,value=-WIN;
  for(let i=-1;i<7;i++){
   const c=i<0?best:center[i];if(i>=0&&c==best)continue;
   const move=allowed&(<u64>63<<(c*7));if(!move)continue;
   const child=-visit(position^mask,mask|move,depth-1,-WIN,-value,1);
   if(expired)break;
   if(child>value){value=child;candidate=c;}
  }
  if(expired)break;
  best=candidate;finalValue=value;reached=depth;
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
