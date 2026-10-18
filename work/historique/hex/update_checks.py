from pathlib import Path
R=Path(r'C:\Users\gabor\code\playi')
for p in (R/'tests').iterdir():
 if p.suffix not in ('.py','.mjs'):continue
 t=p.read_text(encoding='utf-8').replace('2494','3055').replace('3617','3894').replace('2483','3042').replace('2489','3048')
 # Only assertions of active version change; historical model paths stay fixed.
 t=t.replace("version,'4.0.0'","version,'5.0.0'").replace("['version'],'4.0.0'","['version'],'5.0.0'")
 if p.name=='test_strategy.py':t=t.replace("len(catalog()['games']),11","len(catalog()['games']),13")
 if p.name=='test_diversity.py':t=t.replace('len(first),33','len(first),39')
 p.write_text(t,encoding='utf-8')
p=R/'logic_arena/agents.py';t=p.read_text(encoding='utf-8').replace("return max(values,key=lambda v:v['quality'])['action'],info","return max(values,key=lambda v:v['quality'])['action']");p.write_text(t,encoding='utf-8')
p=R/'web/teachers.js';t=p.read_text(encoding='utf-8');t="import {largeSliding} from './large-sliding.js';\n"+t;t=t.replace("export function teacher(o,legal){","export function teacher(o,legal){\n if(o.game==='sliding_puzzle'&&o.board.length>3){const began=performance.now(),budget={nodes:0,tick(){if(this.nodes++>=3000||performance.now()-began>30)throw Error('budget');}},result=largeSliding(o,legal,budget);return selectQuality(result.action_values,10,Array(4).fill(0),o.game).selected.action;}");p.write_text(t,encoding='utf-8')
p=R/'web/puzzle-ui.js';t=p.read_text(encoding='utf-8');t="import {slidingDistance} from './fast-search.js';\n"+t;a=t.index('const bound=lastDecision?.solution_found?');b=t.index('\n if(sudoku)',a);t=t[:a]+'''const bound=n===3?slidingDistance(game.board):game.distance();$('move-counter').textContent=`${game.moves} coups · ${n===3?'':'au moins '}${bound} restants`;}
'''+t[b:];p.write_text(t,encoding='utf-8')
print('Checks and puzzle details updated')
