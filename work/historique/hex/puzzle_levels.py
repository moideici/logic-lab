"""Reproducible Sudoku bank and solvable sliding-puzzle difficulty profiles."""
import json,base64
from pathlib import Path
from functools import lru_cache
ROOT=Path(__file__).resolve().parents[1]/'web/models'
LEVELS=('easy','medium','hard','expert')
def random_values(seed):
    value=seed&0xffffffff
    while True:value=(1664525*value+1013904223)&0xffffffff;yield value/4294967296
@lru_cache(None)
def sudoku_bank():return json.loads((ROOT/'sudoku-levels.json').read_text())
def sudoku_level(seed,difficulty):
    if difficulty not in LEVELS:raise ValueError('Difficulté Sudoku inconnue')
    items=sudoku_bank()['levels'][difficulty];entry=items[int(next(random_values(seed))*len(items))];raw=entry['puzzle'];return [[int(raw[r*9+c]) for c in range(9)] for r in range(9)],{'difficulty':difficulty,'grading_scope':'maximum_catalog' if difficulty=='expert' else 'fixed_solver','score':entry['grade']['score'],'guesses':entry['grade']['guesses'],'unique':True}
def manhattan(flat,n):return sum(abs(i//n-(v-1)//n)+abs(i%n-(v-1)%n) for i,v in enumerate(flat) if v)
@lru_cache(None)
def distance_buckets():
    table=base64.b64decode(json.loads((ROOT/'sliding-distances.json').read_text())['data']);buckets={level:[] for level in LEVELS}
    for i,d in enumerate(table):
        if 1<=d<=8:buckets['easy'].append(i)
        elif 9<=d<=16:buckets['medium'].append(i)
        elif 17<=d<=24:buckets['hard'].append(i)
        elif d==31:buckets['expert'].append(i)
    return table,buckets
def unrank(rank):
    import math
    available=list(range(9));out=[]
    for i in range(9):f=math.factorial(8-i);index,rank=divmod(rank,f);out.append(available.pop(index))
    return out
def sliding_level(seed,size,difficulty):
    if type(size) is not int or size not in (3,4,5):raise ValueError('Le taquin accepte les tailles 3, 4 ou 5')
    if difficulty not in LEVELS:raise ValueError('Difficulté du taquin inconnue')
    random=random_values(seed)
    if size==3:
        table,buckets=distance_buckets();ranks=buckets[difficulty];rank=ranks[int(next(random)*len(ranks))];flat=unrank(rank);distance=table[rank]
        return [flat[r:r+3] for r in (0,3,6)],{'size':3,'difficulty':difficulty,'exact_distance':distance,'lower_bound':distance,'maximum_distance':31,'scope':'exact_shortest_distance'}
    params={4:{'easy':(8,4),'medium':(28,14),'hard':(120,28),'expert':(800,44)},5:{'easy':(12,8),'medium':(50,24),'hard':(240,50),'expert':(1500,85)}};minimum,target=params[size][difficulty];flat=list(range(1,size*size))+[0];zero=len(flat)-1;previous=None;best=None;best_h=-1;directions=((-1,0),(1,0),(0,-1),(0,1))
    for step in range(minimum+8000):
        r,c=divmod(zero,size);choices=[i for i,(dr,dc) in enumerate(directions) if 0<=r+dr<size and 0<=c+dc<size and i!=(None if previous is None else previous^1)]
        at=choices[int(next(random)*len(choices))];dr,dc=directions[at];other=(r+dr)*size+c+dc;flat[zero],flat[other]=flat[other],0;zero=other;previous=at
        if step+1>=minimum:
            h=manhattan(flat,size)
            if h>best_h:best_h=h;best=flat[:];used=step+1
            if h>=target:break
    return [best[r*size:(r+1)*size] for r in range(size)],{'size':size,'difficulty':difficulty,'exact_distance':None,'lower_bound':best_h,'maximum_distance':None,'scramble_steps':used,'scope':'solvable_scramble_and_manhattan_bound'}
