"""Public rules shared by the new games and their search adapters."""
EXTRA_SPECS={'reversi':(72,37),'nim':(48,45),'lightsout':(25,25)}
EXTRA_PLAYERS={'reversi':2,'nim':2,'lightsout':1}
DIRECTIONS=tuple((dr,dc) for dr in (-1,0,1) for dc in (-1,0,1) if dr or dc)
def seeded(seed):
    value=seed&0xffffffff
    while True:
        value=(1664525*value+1013904223)&0xffffffff
        yield value/4294967296
def flip_lights(board,row,col):
    for dr,dc in ((0,0),(1,0),(-1,0),(0,1),(0,-1)):
        r,c=row+dr,col+dc
        if 0<=r<5 and 0<=c<5:board[r][c]^=1
def create_extra(name,seed):
    random=seeded(seed)
    if name=='reversi':
        b=[[0]*6 for _ in range(6)];b[2][2]=b[3][3]=2;b[2][3]=b[3][2]=1;return b
    if name=='nim':return [[1]*n+[0]*(15-n) for n in (3+int(next(random)*4),5+int(next(random)*4),7+int(next(random)*4))]
    b=[[0]*5 for _ in range(5)]
    for i in range(25):
        if next(random)<.5:flip_lights(b,i//5,i%5)
    if not any(map(any,b)):flip_lights(b,2,2)
    return b
def reversi_flips(board,player,row,col):
    if board[row][col]:return []
    result=[]
    for dr,dc in DIRECTIONS:
        r,c=row+dr,col+dc;line=[]
        while 0<=r<6 and 0<=c<6 and board[r][c]==3-player:line.append((r,c));r+=dr;c+=dc
        if line and 0<=r<6 and 0<=c<6 and board[r][c]==player:result.extend(line)
    return result
def reversi_moves(board,player):return [{'row':r,'col':c} for r in range(6) for c in range(6) if reversi_flips(board,player,r,c)]
def legal_extra(name,board,player):
    if name=='nim':return [{'pile':p,'take':n} for p,row in enumerate(board) for n in range(1,sum(row)+1)]
    if name=='lightsout':return [{'row':r,'col':c} for r in range(5) for c in range(5)]
    moves=reversi_moves(board,player)
    return moves or ([{'pass':True}] if reversi_moves(board,3-player) else [])
def step_extra(name,board,player,action):
    """Mutate the supplied public board; return player, done, winner, score, reward."""
    if name=='nim':
        p=action['pile'];n=sum(board[p])-action['take'];board[p]=[1]*n+[0]*(15-n);left=sum(map(sum,board));done=left==0
        return (player if done else 3-player),done,player if done else None,left,1. if done else 0.
    if name=='lightsout':
        before=sum(map(sum,board));flip_lights(board,action['row'],action['col']);left=sum(map(sum,board));done=left==0
        return player,done,1 if done else None,25-left,(before-left)/25+(1. if done else 0.)
    actor=player
    if not action.get('pass'):
        r,c=action['row'],action['col'];flipped=reversi_flips(board,player,r,c);board[r][c]=player
        for r,c in flipped:board[r][c]=player
    player=3-player;done=not reversi_moves(board,1) and not reversi_moves(board,2)
    score=sum(v==1 for row in board for v in row)-sum(v==2 for row in board for v in row)
    winner=(1 if score>0 else 2 if score<0 else 0) if done else None
    return player,done,winner,score,(1. if winner==actor else -1. if winner else 0.) if done else 0.
def encode_extra(obs):
    name=obs['game'];board=obs['board'];x=[0.]*EXTRA_SPECS[name][0]
    if name=='nim':
        for p,row in enumerate(board):x[p*16+sum(row)]=1.
    elif name=='lightsout':x=[float(v) for row in board for v in row]
    else:
        for i,v in enumerate(v for row in board for v in row):
            if v:x[i*2+(0 if v==obs['current_player'] else 1)]=1.
    return x
def extra_action_index(name,a):
    if name=='nim':return a['pile']*15+a['take']-1
    if name=='reversi':return 36 if a.get('pass') else a['row']*6+a['col']
    return a['row']*5+a['col']
