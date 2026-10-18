from pathlib import Path
import json
R=Path(r'C:\Users\gabor\code\playi');O=Path(r'C:\Users\gabor\code\logic-lab\outputs')
p=R/'logic_arena/puzzle_levels.py';t=p.read_text(encoding='utf-8').replace('    value=seed&0xffffffff','    value=seed&0xffffffff\n    value=((value^(value>>16))*0x7feb352d)&0xffffffff\n    value=((value^(value>>15))*0x846ca68b)&0xffffffff\n    value^=value>>16');p.write_text(t,encoding='utf-8')
p=R/'web/puzzle-levels.js';t=p.read_text(encoding='utf-8').replace('let state=seed>>>0;return()=>','let state=seed>>>0;state=Math.imul(state^(state>>>16),0x7feb352d)>>>0;state=Math.imul(state^(state>>>15),0x846ca68b)>>>0;state=(state^(state>>>16))>>>0;return()=>');p.write_text(t,encoding='utf-8')
p=R/'tests/expansion.test.mjs';t=p.read_text(encoding='utf-8');t+='''
test('successive new-game seeds produce varied puzzles',()=>{
 for(const [name,options]of [['sudoku',{difficulty:'medium'}],['sliding_puzzle',{size:3,difficulty:'hard'}]]){const boards=new Set(Array.from({length:16},(_,i)=>JSON.stringify(new Game(name,42+i,options).board)));assert(boards.size>=8);}
});
''';p.write_text(t,encoding='utf-8')
p=R/'README.md';p.write_text(p.read_text(encoding='utf-8').replace('47 tests JavaScript','48 tests JavaScript'),encoding='utf-8')
p=O/'Garry-5-jeux-reels-et-difficultes.md';p.write_text(p.read_text(encoding='utf-8').replace('47 tests JavaScript','48 tests JavaScript').replace('133 tests','134 tests'),encoding='utf-8')
p=O/'garry-5-mesures.json';d=json.loads(p.read_text(encoding='utf-8'));d['tests']['javascript']=48;p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
print('New-game seed diversity fixed')
