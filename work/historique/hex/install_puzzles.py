from pathlib import Path
import shutil
R=Path(r'C:\Users\gabor\code\playi');S=Path(__file__).parent
for name in ('puzzle_levels.py','large_sliding.py'):shutil.copyfile(S/name,R/'logic_arena'/name)
for name in ('puzzle-levels.js','large-sliding.js'):shutil.copyfile(S/name,R/'web'/name)
def edit(file,old,new):
 p=R/file;t=p.read_text(encoding='utf-8');assert old in t,(file,old[:100]);p.write_text(t.replace(old,new,1),encoding='utf-8')
edit('logic_arena/games.py','        digits = list(range(1, 10))', '''        if 'difficulty' in self.options:
            from .puzzle_levels import sudoku_level
            self.board,self.difficulty_info=sudoku_level(seed,self.options['difficulty'])
            self.givens=deepcopy(self.board);self.history=[]
            return
        digits = list(range(1, 10))''')
edit('logic_arena/games.py','"history": [list(cell) for cell in self.history]}','"history": [list(cell) for cell in self.history], **({"difficulty_info":deepcopy(self.difficulty_info)} if hasattr(self,"difficulty_info") else {})}')
edit('logic_arena/games.py','        scramble = self.options.get("scramble", 30)', '''        if 'size' in self.options or 'difficulty' in self.options:
            if 'scramble' in self.options:raise ValueError('Choisir difficulté ou scramble, pas les deux')
            from .puzzle_levels import sliding_level
            self.board,self.difficulty_info=sliding_level(seed,self.options.get('size',3),self.options.get('difficulty','medium'))
            return
        scramble = self.options.get("scramble", 30)''')
edit('logic_arena/games.py','    def distance(self):\n        return sum(abs(r-(v-1)//3)+abs(c-(v-1)%3) for r, row in enumerate(self.board) for c, v in enumerate(row) if v)', '''    def observation(self):
        return {**super().observation(),**({'difficulty_info':deepcopy(self.difficulty_info)} if hasattr(self,'difficulty_info') else {})}

    def distance(self):
        from .puzzle_levels import manhattan
        return manhattan([v for row in self.board for v in row],len(self.board))''')
p=R/'logic_arena/games.py';t=p.read_text();start=t.index('class SlidingPuzzle');end=t.index('class ExtraGame',start);part=t[start:end].replace('range(3)','range(len(self.board))').replace('r+dr < 3 and 0 <= c+dc < 3','r+dr < len(self.board) and 0 <= c+dc < len(self.board)');p.write_text(t[:start]+part+t[end:],encoding='utf-8')
edit('logic_arena/games.py','allowed = {"scramble"} if name == "sliding_puzzle" else set()', 'allowed = {"scramble","size","difficulty"} if name == "sliding_puzzle" else {"difficulty"} if name == "sudoku" else set()')
edit('logic_arena/neural.py','    for i, value in enumerate(v for row in obs["board"] for v in row):', '''    if name=='sliding_puzzle' and len(obs['board'])>3:
        from .puzzle_levels import manhattan
        n=len(obs['board']);flat=[v for row in obs['board'] for v in row];z=flat.index(0)
        for i,v in enumerate(flat):
            if v:x[i*3:i*3+3]=(v/(n*n-1),((v-1)//n-i//n)/(n-1),((v-1)%n-i%n)/(n-1))
        x[75:]=(n==4,n==5,(z//n)/(n-1),(z%n)/(n-1),manhattan(flat,n)/(n**3),sum(v!=((i+1)%(n*n)) for i,v in enumerate(flat))/(n*n))
        return x
    for i, value in enumerate(v for row in obs["board"] for v in row):''')
edit('logic_arena/planner.py','    b=tuple(v for row in board for v in row)', '''    if len(board)>3:
        from .puzzle_levels import manhattan
        return manhattan([v for row in board for v in row],len(board))
    b=tuple(v for row in board for v in row)''')
edit('logic_arena/planner.py',"    elif game=='sliding_puzzle':", "    elif game=='sliding_puzzle' and len(obs['board'])>3:\n        from .large_sliding import large_sliding_values\n        values,info=large_sliding_values(obs,legal,Budget(30000,200 if time_ms is None else time_ms))\n    elif game=='sliding_puzzle':")
edit('web/engine.js',"import {GOMOKU_SPECS", "import {sudokuLevel,slidingLevel,manhattan} from './puzzle-levels.js';\nimport {GOMOKU_SPECS")
edit('web/engine.js',"if(Object.keys(options).some(k=>name!=='sliding_puzzle'||k!=='scramble'))", "if(Object.keys(options).some(k=>!(name==='sliding_puzzle'?['scramble','size','difficulty']:name==='sudoku'?['difficulty']:[]).includes(k)))")
edit('web/engine.js'," const shapes={", " if(name==='sudoku'&&'difficulty'in options){const next=sudokuLevel(seed,options.difficulty);this.board=next.board;this.difficultyInfo=next.info;this.givens=clone(this.board);return;}\n if(name==='sliding_puzzle'&&('size'in options||'difficulty'in options)){if('scramble'in options)throw Error('Choisir difficulté ou scramble, pas les deux');const next=slidingLevel(seed,options.size??3,options.difficulty??'medium');this.board=next.board;this.difficultyInfo=next.info;return;}\n const shapes={")
edit('web/engine.js',"obs(){return {game:this.name,", "obs(){return {...(this.difficultyInfo?{difficulty_info:clone(this.difficultyInfo)}:{}),game:this.name,")
edit('web/engine.js',"const i=b.flat().indexOf(0),r=Math.floor(i/3),c=i%3;return DIRS.filter(d=>d==='up'?r>0:d==='down'?r<2:d==='left'?c>0:c<2)", "const n=b.length,i=b.flat().indexOf(0),r=Math.floor(i/n),c=i%n;return DIRS.filter(d=>d==='up'?r>0:d==='down'?r<n-1:d==='left'?c>0:c<n-1)")
edit('web/engine.js',"distance(){return this.board.flat().reduce((s,v,i)=>s+(v?Math.abs(Math.floor(i/3)-Math.floor((v-1)/3))+Math.abs(i%3-(v-1)%3):0),0);}","distance(){return manhattan(this.board.flat(),this.board.length);}")
edit('web/engine.js',"swap(d){const i=this.board.flat().indexOf(0),r=Math.floor(i/3),c=i%3,", "swap(d){const n=this.board.length,i=this.board.flat().indexOf(0),r=Math.floor(i/n),c=i%n,")
edit('web/engine.js',"const x=new Float32Array(SPECS[o.game][0]);o.board.flat().forEach", "const x=new Float32Array(SPECS[o.game][0]);if(o.game==='sliding_puzzle'&&o.board.length>3){const n=o.board.length,f=o.board.flat(),z=f.indexOf(0);f.forEach((v,i)=>{if(v)x.set([v/(n*n-1),(Math.floor((v-1)/n)-Math.floor(i/n))/(n-1),((v-1)%n-i%n)/(n-1)],i*3);});x.set([Number(n===4),Number(n===5),Math.floor(z/n)/(n-1),(z%n)/(n-1),manhattan(f,n)/(n**3),f.filter((v,i)=>v!==(i+1)%(n*n)).length/(n*n)],75);return x;}o.board.flat().forEach")
# Style uses the actual board size as well.
p=R/'web/engine.js';t=p.read_text();start=t.index("if(o.game==='sliding_puzzle'){const i=");end=t.index('return 0;}',start);part=t[start:end].replace('const i=','const n=o.board.length,i=').replace('/3','/n').replace('%3','%n');p.write_text(t[:start]+part+t[end:],encoding='utf-8')
edit('web/fast-search.js',"import slidingTable", "import {largeSliding} from './large-sliding.js';\nimport {manhattan} from './puzzle-levels.js';\nimport slidingTable")
edit('web/fast-search.js',"export function slidingDistance(board){const b=", "export function slidingDistance(board){if(board.length>3)return manhattan(board.flat(),board.length);const b=")
edit('web/fast-search.js',"export function exactSliding(o,legal,logits){", "export function exactSliding(o,legal,logits,budget){if(o.board.length>3)return largeSliding(o,legal,budget);")
edit('web/planner.js',"['draughts','breakthrough','hex','gomoku'].includes(o.game)?200", "(['draughts','breakthrough','hex','gomoku'].includes(o.game)||o.game==='sliding_puzzle'&&o.board.length>3)?200")
edit('web/repertoire.js',"sliding_puzzle:[3,3]", "sliding_puzzle:[o?.board?.length,o?.board?.length]")
edit('web/repertoire.js',"'gomoku_state'];", "'gomoku_state','difficulty_info'];")
edit('web/repertoire.js',"sliding_puzzle:8", "sliding_puzzle:o.board.length**2-1")
edit('web/repertoire.js',"new Set(cells).size!==9", "(![3,4,5].includes(o.board.length)||new Set(cells).size!==o.board.length**2)")
print('Puzzle engines installed')
