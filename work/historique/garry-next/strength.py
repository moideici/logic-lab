from pathlib import Path
ROOT=Path(r'C:\Users\gabor\code\playi');OUT=Path(__file__).parent/'strength'
def edit(p,fn):
    f=OUT/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(fn((ROOT/p).read_text(encoding='utf-8')),encoding='utf-8',newline='\n')
# Winning immediately must dominate a move which might win after a tile spawn.
edit('web/fast-search.js',lambda s:s.replace('const v=isWin(child)?1e9:', 'const v=isWin(child)?1e12:').replace(',score=isWin(child)?1e9:', ',score=isWin(child)?1e12:').replace('bestValue===1e9','bestValue===1e12'))
edit('logic_arena/tiles.py',lambda s:s.replace('value = 1e9 if won(child)', 'value = 1e12 if won(child)').replace('score = 1e9 if won(child)', 'score = 1e12 if won(child)').replace('best_value==1e9','best_value==1e12'))

# Level 10 spends its budget exclusively on finding the strongest move. Full
# root ranking is only used when deliberately selecting weaker moves.
edit('web/planner.js',lambda s:s.replace('analyze:true,positionHead:', 'analyze:level!==10,maxDepth:20,positionHead:').replace(' const {selected,info}=selectQuality(result.action_values,level,logits,o.game),best=info.selected_is_best;', ''' if(o.game==='connect4'&&level===10)return {action:result.action,info:{...decision.info,...result.info,level,agent:'neural+planner',confidence:null,selected_is_best:true,selected_is_worst:false,level_semantics:'strongest_completed_search',target_depth:20,depth_target_reached:result.info.depth>=20,quality:[result.info.value??0],time_ms:performance.now()-began+decision.info.time_ms}};
 const {selected,info}=selectQuality(result.action_values,level,logits,o.game),best=info.selected_is_best;'''))
edit('logic_arena/planner.py',lambda s:s.replace('analyze=True,position_head=', 'analyze=level!=10,max_depth=20,position_head=').replace("        values=info.pop('action_values')\n    elif game=='2048':", "        if level==10:return _,{'agent':'neural+planner',**info,'level':level,'selected_is_best':True,'selected_is_worst':False,'level_semantics':'strongest_completed_search','target_depth':20,'depth_target_reached':info.get('depth',0)>=20,'quality':[info.get('value',0)]}\n        values=info.pop('action_values')\n    elif game=='2048':"))
edit('logic_arena/connect4_wasm.py',lambda s:s.replace('10000000,30000000)', '10000000,200000000)').replace('180,300)', '180,2000)'))
edit('web/connect4.js',lambda s:s.replace('10000000,30000000]', '10000000,200000000]').replace('180,300]', '180,2000]'))
edit('web/app.js',lambda s:s.replace("$('game-hint').textContent='Réseau seul", "$('game-hint').textContent='Réseau seul").replace("if(!$('planning').checked)$('game-hint')", "if(game.name==='connect4'&&lastDecision?.depth!==undefined)$('game-hint').textContent=lastDecision.forced_win?'Victoire forcée trouvée dans la recherche.':`Recherche : ${lastDecision.depth} demi-coups analysés · cible ${lastDecision.target_depth??20}.` ;if(!$('planning').checked)$('game-hint')"))

s=(ROOT/'search/connect4-search.ts').read_text(encoding='utf-8')
s=s.replace('''  const move=moveStack[offset+i],child=-visit(position^mask,mask|move,depth-1,-beta,-alpha,ply+1);
  if(expired)return 0;''','''  const move=moveStack[offset+i];
  let child=i==0?-visit(position^mask,mask|move,depth-1,-beta,-alpha,ply+1):-visit(position^mask,mask|move,depth-1,-alpha-1,-alpha,ply+1);
  if(!expired&&i>0&&child>alpha&&child<beta)child=-visit(position^mask,mask|move,depth-1,-beta,-alpha,ply+1);
  if(expired)return 0;''')
a=s.index('  let candidate=best,value=-WIN;',s.index('export function decide'));b=s.index('\n  if(abs(value)>WIN-43',a)
s=s[:a]+'''  let low=depth>1?max(-WIN,finalValue-64):-WIN,high=depth>1?min(WIN,finalValue+64):WIN;
  let value=rootVisit(position,mask,allowed,depth,low,high,best);
  if(!expired&&(value<=low||value>=high))value=rootVisit(position,mask,allowed,depth,-WIN,WIN,best);
  if(expired)break;
  best=rootBest;finalValue=value;reached=depth;'''+s[b:]
s+='''
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
'''
f=OUT/'search/connect4-search.ts';f.parent.mkdir(parents=True,exist_ok=True);f.write_text(s,encoding='utf-8',newline='\n')

edit('examples/benchmark_garry_value.mjs',lambda s:s.replace('analyze:true,positionHead:head','analyze:false,positionHead:head'))
