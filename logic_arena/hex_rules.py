"""Hex 7x7 with the pie rule: the second actor can swap ownership once."""
from collections import deque
SIZE=7
HEX_SPECS={'hex':(100,50)}
NEIGHBORS=((-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0))
def new_hex():return [[0]*SIZE for _ in range(SIZE)],{'colors':[1,2],'swap_available':False,'winning_path':[]}
def connection_path(board,color):
    n=len(board);starts=[(0,c) for c in range(n)] if color==1 else [(r,0) for r in range(n)]
    parent={s:None for s in starts if board[s[0]][s[1]]==color};queue=deque(parent)
    while queue:
        r,c=queue.popleft()
        if (r if color==1 else c)==n-1:
            path=[];at=(r,c)
            while at is not None:path.append(list(at));at=parent[at]
            return path[::-1]
        for dr,dc in NEIGHBORS:
            y,x=r+dr,c+dc
            if 0<=y<n and 0<=x<n and board[y][x]==color and (y,x) not in parent:parent[y,x]=(r,c);queue.append((y,x))
    return []
def legal_hex(board,state):
    out=[{'row':r,'col':c} for r in range(SIZE) for c in range(SIZE) if not board[r][c]]
    if state['swap_available']:out.append({'swap':True})
    return out
def step_hex(board,player,action,state):
    if action.get('swap'):
        state['colors'].reverse();state['swap_available']=False
        return {'player':3-player,'done':False,'winner':None,'score':0,'reward':0.,'state':state}
    color=state['colors'][player-1];board[action['row']][action['col']]=color
    path=connection_path(board,color);state['winning_path']=path
    state['swap_available']=sum(bool(v) for row in board for v in row)==1 and player==1
    return {'player':player if path else 3-player,'done':bool(path),'winner':player if path else None,'score':1 if path else 0,'reward':1. if path else 0.,'state':state}
def encode_hex(obs):
    own=obs['hex_state']['colors'][obs['current_player']-1];x=[0.]*100
    for i,v in enumerate(v for row in obs['board'] for v in row):
        if v:x[2*i+(v!=own)]=1
    x[98]=int(obs['hex_state']['swap_available']);x[99]=int(own==1);return x
def hex_action_index(action):return 49 if action.get('swap') else action['row']*SIZE+action['col']
