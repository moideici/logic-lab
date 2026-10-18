"""Create a unique-solution bank and grade it with a fixed, reproducible solver."""
from pathlib import Path
import sys,json,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from logic_arena.diversity import new_sudoku,sudoku_solutions
from logic_arena.games import sudoku_candidates
ROOT=Path(__file__).resolve().parents[1]
UNITS=[[(r,c) for c in range(9)] for r in range(9)]+[[(r,c) for r in range(9)] for c in range(9)]+[[(r,c) for r in range(br,br+3) for c in range(bc,bc+3)] for br in (0,3,6) for bc in (0,3,6)]
def grade(board):
    b=[row[:] for row in board];stats={'singles':0,'hidden_singles':0,'guesses':0,'max_depth':0}
    def solve(depth=0):
        stats['max_depth']=max(stats['max_depth'],depth)
        while True:
            empty={(r,c):sudoku_candidates(b,r,c) for r in range(9) for c in range(9) if not b[r][c]}
            if not empty:return True
            if any(not v for v in empty.values()):return False
            single=next(((r,c,v[0]) for (r,c),v in empty.items() if len(v)==1),None)
            if single:r,c,v=single;b[r][c]=v;stats['singles']+=1;continue
            hidden=None
            for unit in UNITS:
                for v in range(1,10):
                    cells=[(r,c) for r,c in unit if v in empty.get((r,c),[])]
                    if len(cells)==1:hidden=(*cells[0],v);break
                if hidden:break
            if hidden:r,c,v=hidden;b[r][c]=v;stats['hidden_singles']+=1;continue
            break
        r,c=min(empty,key=lambda cell:len(empty[cell]));snapshot=[row[:] for row in b]
        for v in empty[r,c]:
            stats['guesses']+=1;b[r][c]=v
            if solve(depth+1):return True
            b[:]=[row[:] for row in snapshot]
        return False
    if not solve():raise ValueError('Unsolvable puzzle')
    stats['score']=stats['guesses']*10000+stats['max_depth']*500+stats['hidden_singles']*5+stats['singles'];return stats
def main():
    candidates=[];seen=set();started=time.monotonic()
    # A fixed valid candidate supplements generated grids; uniqueness is checked.
    raw='100007090030020008009600500005300900010080002600004000300000010040000007007000300'
    boards=[[[int(raw[r*9+c]) for c in range(9)] for r in range(9)]]
    for i in range(44):
        env,_=new_sudoku(1719000+i,(24,26,28,32,36,42)[i%6]);boards.append(env.board)
        if i%10==0:print('sudoku generated',i,flush=True)
    for board in boards:
        key=''.join(str(v) for row in board for v in row)
        if key in seen:continue
        solutions,_=sudoku_solutions(board,2,200000)
        if len(solutions)!=1:continue
        seen.add(key);stats=grade(board);candidates.append({'puzzle':key,'clues':sum(bool(v) for row in board for v in row),'grade':stats,'unique':True})
    singles=sorted([c for c in candidates if not c['grade']['guesses']],key=lambda c:(c['grade']['hidden_singles'],81-c['clues']))
    branching=sorted([c for c in candidates if c['grade']['guesses']],key=lambda c:c['grade']['score'])
    assert len(singles)>=8 and len(branching)>=2,(len(singles),len(branching))
    levels={'easy':singles[:max(4,len(singles)//3)],'medium':singles[max(4,len(singles)//3):],'hard':branching[:-1],'expert':branching[-1:]}
    # Expert always selects the strongest catalog entry by this fixed solver.
    assert levels['expert'][0]['grade']['score']==max(c['grade']['score'] for c in candidates)
    data={'format':'garry-sudoku-levels-v1','grading':'naked and hidden singles, then deterministic MRV search; solver-specific, not universal human difficulty','expert_scope':'maximum score in this verified catalog','levels':levels,'verified_count':len(candidates)}
    (ROOT/'web/models/sudoku-levels.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf-8');print(json.dumps({'grids':len(candidates),'levels':{k:len(v) for k,v in levels.items()},'expert':levels['expert'][0]['grade'],'seconds':time.monotonic()-started}),flush=True)
if __name__=='__main__':main()
