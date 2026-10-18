"""Compact antisymmetric position head, distilled from deeper public search.

32 features: 24 open-line counts (direction, starting-row parity, 1..3
stones), four mirrored column occupancies, four playable/floating threats.
No bias: swapping the players negates the value exactly.
"""
import numpy as np

LINES = [(r,c,dr,dc,d) for r in range(6) for c in range(7)
         for d,(dr,dc) in enumerate(((0,1),(1,0),(1,1),(1,-1)))
         if r+3*dr<6 and 0<=c+3*dc<7]

def features(obs):
    b=obs['board']; p=obs['current_player']; x=np.zeros(32,dtype=np.float64)
    threats=[set(),set()]
    for r,c,dr,dc,d in LINES:
        cells=[(r+i*dr,c+i*dc) for i in range(4)]
        a=sum(b[y][z]==p for y,z in cells); e=sum(b[y][z]==3-p for y,z in cells)
        for count,other,sign,side in ((a,e,1,0),(e,a,-1,1)):
            if count and not other and count<4:
                x[(d*2+(r%2))*3+count-1]+=sign
                if count==3:threats[side].update((y,z) for y,z in cells if not b[y][z])
    for r in range(6):
        for c in range(7):
            if b[r][c]:x[24+min(c,6-c)]+=1 if b[r][c]==p else -1
    for side,sign in ((0,1),(1,-1)):
        for r,c in threats[side]:
            playable=r==5 or bool(b[r+1][c])
            x[28+(0 if playable else 2)+(r%2)]+=sign
    return x

def default_head():
    # Exact initialization of the former handcrafted evaluator.
    return {'id':'garry-position-v1','features':32,'game':'connect4',
            'weights':[2.,16.,120.]*8+[0.,0.,0.,7.]+[0.]*4,
            'samples':0,'revision':'initial','enabled':False}

def validate_head(head):
    if not isinstance(head,dict) or head.get('id')!='garry-position-v1' or head.get('features')!=32 or head.get('game')!='connect4':
        raise ValueError('Évaluateur Garry invalide')
    w=head.get('weights')
    if not isinstance(w,list) or len(w)!=32 or any(type(v) not in (int,float) or not np.isfinite(v) or abs(v)>10000 for v in w):
        raise ValueError('Poids de valeur invalides')
    if type(head.get('samples')) is not int or head['samples']<0 or type(head.get('enabled')) is not bool or not isinstance(head.get('revision'),str):
        raise ValueError('Métadonnées de valeur invalides')
    return dict(head,weights=list(w))
