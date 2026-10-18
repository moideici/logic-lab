from pathlib import Path
ROOT=Path(r'C:\Users\gabor\code\playi');OUT=Path(__file__).parent/'deep'
def edit(p,fn):
    f=OUT/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(fn((ROOT/p).read_text(encoding='utf-8')),encoding='utf-8',newline='\n')
s=(ROOT/'search/connect4-search.ts').read_text(encoding='utf-8').replace('1 << 18','1 << 20').replace('>>46','>>44')
# A horizon fork is a three-ply proof, not a heuristic. Forced responses are
# already extended by visit(), so this preserves the adversarial assumption.
s=s.replace(' if(depth<=0&&!forced)return evaluate(position,mask);', ''' if(depth<=0&&!forced){
  for(let c=0;c<7;c++){
   const move=nonLosing&(<u64>63<<(c*7));if(!move)continue;
   const nextMask=mask|move,nextMoves=(nextMask+BOTTOM)&BOARD,threats=nextMoves&winning(position|move,nextMask);
   if(threats&&(threats&(threats-1)))return WIN-ply-3;
  }
  return evaluate(position,mask);
 }''')
s+='''
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
'''
f=OUT/'search/connect4-search.ts';f.parent.mkdir(parents=True,exist_ok=True);f.write_text(s,encoding='utf-8',newline='\n')
edit('web/connect4-runtime.js',lambda s:s.replace(' const action_values=analyze?', ''' const remaining=42-o.board.flat().filter(Boolean).length,proof=forcedWin?'win':forcedLoss?'loss':depth>=remaining?'draw':null;
 const principal_variation=Array.from({length:runtime.trace(bits[1],bits[2],o.current_player,column,Math.max(depth,1))},(_,i)=>runtime.getPrincipal(i));
 const action_values=analyze?''').replace("runtime:'wasm',nodes,depth,value,", "runtime:'wasm',nodes,depth,value,principal_variation,proof,search_complete:!!proof,").replace('optimal:tactical,remaining_moves:', 'optimal:tactical||forcedWin||depth>=remaining,remaining_moves:'))
edit('logic_arena/connect4_wasm.py',lambda s:s.replace("    info = {'method':", "    remaining=42-sum(bool(v) for r in obs['board'] for v in r)\n    proof='win' if value>999957 else 'loss' if value< -999957 else 'draw' if depth>=remaining else None\n    count=runtime['trace'](store,bits[1],bits[2],obs['current_player'],column,max(depth,1))\n    principal=[runtime['getPrincipal'](store,i) for i in range(count)]\n    info = {'method':").replace("'runtime': 'wasm', 'value':value,", "'runtime': 'wasm', 'principal_variation':principal,'proof':proof,'search_complete':proof is not None,'value':value,").replace("'optimal': tactical}","'optimal': tactical or value>999957 or depth>=remaining}"))
