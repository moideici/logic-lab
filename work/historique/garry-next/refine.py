from pathlib import Path
ROOT=Path(r'C:\Users\gabor\code\playi');OUT=Path(__file__).parent/'fixes'
def edit(p,fn):
    f=OUT/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(fn((ROOT/p).read_text(encoding='utf-8')),encoding='utf-8',newline='\n')
edit('web/connect4-runtime.js',lambda s:s.replace("method:'javascript_root_analysis',runtime:'javascript',optimal:false", "method:best.quality[0]===999999?'tactical_win':'javascript_root_analysis',remaining_moves:best.quality[0]===999999?1:undefined,runtime:'javascript',optimal:best.quality[0]===999999"))
edit('web/connect4.js',lambda s:s.replace("{depth:reached,forced_win:","{value:Number.isFinite(bestValue)?bestValue:score,depth:reached,forced_win:"))
edit('logic_arena/connect4.py',lambda s:s.replace('depth=depth_reached, forced_win=', 'value=best_value if math.isfinite(best_value) else evaluate(),depth=depth_reached, forced_win='))
edit('web/planner.js',lambda s:s.replace(' const selectedInfo={...selected};', ''' const selectedInfo={...selected};
 if(o.game==='connect4'){const v=selected.quality[0];selectedInfo.value=v;selectedInfo.forced_win=v>999957;selectedInfo.forced_loss=v< -999957;selectedInfo.remaining_moves=Math.abs(v)>999957?1000000-Math.abs(v):undefined;}
''').replace('optimal:best&&!!result.info.optimal', "optimal:best&&(!!result.info.optimal||(o.game==='connect4'&&[999999,999997].includes(selected.quality[0])))"))
edit('logic_arena/planner.py',lambda s:s.replace("    extra={k:v for k,v in selected.items() if k not in ('action','quality')}", "    extra={k:v for k,v in selected.items() if k not in ('action','quality')}\n    if game=='connect4':\n        v=selected['quality'][0];extra.update(value=v,forced_win=v>999957,forced_loss=v< -999957,remaining_moves=1000000-abs(v) if abs(v)>999957 else None)\n        info['optimal']=v in (999999,999997) or info.get('optimal',False)"))
# Pure Python fallback preserves all legal actions and never needs hidden state.
edit('logic_arena/connect4_wasm.py',lambda s:s.replace("        action, info = fallback(obs, legal, budget, logits, weights, max_depth)", "        if analyze:return _fallback_analysis(obs,legal,budget,logits,weights,max_depth)\n        action, info = fallback(obs, legal, budget, logits, weights, max_depth)")+'''

def _fallback_analysis(obs,legal,budget,logits,weights,max_depth):
    from .connect4 import search, _won
    from .agents import Budget
    values=[]
    for a in legal:
        board=[row[:] for row in obs['board']];c=a['column'];r=max(r for r in range(6) if not board[r][c]);board[r][c]=obs['current_player']
        mine=sum(1<<(c*7+5-r) for r in range(6) for c in range(7) if board[r][c]==obs['current_player'])
        if _won(mine):value=999999
        else:
            children=[{'column':c} for c in range(7) if not board[0][c]]
            if not children:value=0
            else:
                child={**obs,'board':board,'current_player':3-obs['current_player']}
                local=Budget(max(1,(budget.limit-budget.nodes)//len(legal)),max(.1,(budget.deadline-time.monotonic())*1000/len(legal)))
                _,info=search(child,children,local,None,weights,max_depth);budget.nodes+=local.nodes
                value=-(1000000-info['remaining_moves'] if info.get('optimal') and info.get('remaining_moves') else info.get('value',0))
        values.append({'action':a,'quality':[value]})
    best=max(values,key=lambda v:(v['quality'],float(logits[v['action']['column']]) if logits is not None else 0))
    return best['action'],{'runtime':'python','method':'python_root_analysis','nodes':budget.nodes,'optimal':best['quality']==[999999],'action_values':values,'evaluation_scope':'bounded_adversarial_search'}
''')
