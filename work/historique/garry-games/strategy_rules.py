"""International draughts (FMJD Annex 1) and Breakthrough public rules.

A draughts capture leg is one protocol action. The same player must finish the
maximum capture; victims stay on the board as blockers until the turn ends.
https://www.fmjd.org/downloads/FMJD_Annexes_2024_8-sig.pdf
https://superdupergames.org/rules/break.pdf
"""
from copy import deepcopy
STRATEGY_SPECS={'draughts':(304,2500),'breakthrough':(128,192)}
DIAGONALS=((-1,-1),(-1,1),(1,-1),(1,1))
def owner(piece):return (piece-1)%2+1 if piece else 0
def position_key(board,player):return str(player)+':'+''.join(str(v) for row in board for v in row)
def new_state(board=None,player=1):
    return {'forced_piece':None,'pending_captures':[],'quiet_plies':0,'endgame_16':None,'endgame_5':None,'repetitions':{position_key(board,player):1} if board else {}}
def create_strategy(name):
    n=10 if name=='draughts' else 8
    board=[[0]*n for _ in range(n)]
    for r in range(n):
        for c in range(n):
            if name=='draughts' and (r+c)%2!=1:continue
            if r<(4 if name=='draughts' else 2):board[r][c]=2
            elif r>=n-(4 if name=='draughts' else 2):board[r][c]=1
    return board,new_state(board)
def capture_legs(board,player,r,c,pending):
    piece=board[r][c];king=piece>2;out=[]
    for dr,dc in DIAGONALS:
        y,x=r+dr,c+dc
        if king:
            while 0<=y<10 and 0<=x<10 and not board[y][x]:y+=dr;x+=dc
        if not (0<=y<10 and 0<=x<10) or owner(board[y][x])!=3-player or (y,x) in pending:continue
        victim=(y,x);y+=dr;x+=dc
        while 0<=y<10 and 0<=x<10 and not board[y][x]:
            out.append((y,x,victim))
            if not king:break
            y+=dr;x+=dc
    return out
def maximal_first_legs(board,player,origins,pending):
    # Only the best remaining length is needed, not an exponential path list.
    memo={}
    def length(r,c,captured):
        key=(r,c,tuple(sorted(captured)))
        if key in memo:return memo[key]
        best=0
        for y,x,victim in capture_legs(board,player,r,c,captured):
            piece=board[r][c];board[r][c]=0;board[y][x]=piece
            try:n=1+length(y,x,captured|{victim})
            finally:board[r][c]=piece;board[y][x]=0
            best=max(best,n)
        memo[key]=best;return best
    best=0;out=[]
    for r,c in origins:
        # A different starting square leaves a different empty square behind.
        memo.clear()
        for y,x,victim in capture_legs(board,player,r,c,pending):
            piece=board[r][c];board[r][c]=0;board[y][x]=piece
            try:n=1+length(y,x,pending|{victim})
            finally:board[r][c]=piece;board[y][x]=0
            action={'from':[r,c],'to':[y,x]}
            if n>best:best=n;out=[action]
            elif n==best:out.append(action)
    return out
def legal_strategy(name,board,player,state=None):
    state=state or new_state();n=len(board)
    if name=='breakthrough':
        out=[];dr=-1 if player==1 else 1
        for r in range(8):
            for c in range(8):
                if board[r][c]!=player:continue
                for dc in (-1,0,1):
                    y,x=r+dr,c+dc
                    if 0<=y<8 and 0<=x<8 and (not board[y][x] or dc and board[y][x]==3-player):out.append({'from':[r,c],'to':[y,x]})
        return out
    pending=set(map(tuple,state['pending_captures']));forced=state['forced_piece']
    origins=[tuple(forced)] if forced is not None else [(r,c) for r in range(10) for c in range(10) if owner(board[r][c])==player]
    captures=maximal_first_legs(board,player,origins,pending)
    if captures or forced is not None:return captures
    out=[]
    for r,c in origins:
        for dr,dc in DIAGONALS:
            if board[r][c]<=2 and dr!=(-1 if player==1 else 1):continue
            y,x=r+dr,c+dc
            while 0<=y<10 and 0<=x<10 and not board[y][x]:
                out.append({'from':[r,c],'to':[y,x]})
                if board[r][c]<=2:break
                y+=dr;x+=dc
    return out
def material(board):return sum((1 if owner(v)==1 else -1)*(3 if v>2 else 1) for row in board for v in row if v)
def draw_limits(board,state):
    pieces={p:[(r,c,v) for r,row in enumerate(board) for c,v in enumerate(row) if owner(v)==p] for p in (1,2)}
    for p in (1,2):
        lone=pieces[p];other=pieces[3-p]
        if len(lone)!=1 or lone[0][2]<=2 or not any(v>2 for _,_,v in other):continue
        if len(other)==3 and state['endgame_16'] is None:state['endgame_16']=0
        if (1<=len(other)<=2 or len(other)==3 and lone[0][0]+lone[0][1]==9) and state['endgame_5'] is None:state['endgame_5']=0
def step_strategy(name,board,player,action,state=None):
    state=state if state is not None else new_state();r,c=action['from'];y,x=action['to'];piece=board[r][c]
    if name=='breakthrough':
        board[r][c]=0;board[y][x]=piece
        won=y==(0 if player==1 else 7) or not any(3-player in row for row in board)
        next_player=player if won else 3-player
        if not won and not legal_strategy(name,board,next_player):won=True;next_player=player
        return {'player':next_player,'done':won,'winner':player if won else None,'score':material(board),'reward':1. if won else 0.,'state':state}
    # Locate the single jumped piece. Legal actions already enforce the maximum.
    dr=1 if y>r else -1;dc=1 if x>c else -1;victims=[];rr,cc=r+dr,c+dc
    while (rr,cc)!=(y,x):
        if board[rr][cc]:victims.append([rr,cc])
        rr+=dr;cc+=dc
    board[r][c]=0;board[y][x]=piece
    if victims:
        state['pending_captures']+=victims;state['forced_piece']=[y,x]
        if capture_legs(board,player,y,x,set(map(tuple,state['pending_captures']))):
            return {'player':player,'done':False,'winner':None,'score':material(board),'reward':0.,'state':state}
    captured=bool(state['pending_captures'])
    for rr,cc in state['pending_captures']:board[rr][cc]=0
    state['pending_captures']=[];state['forced_piece']=None
    if piece<=2 and y==(0 if player==1 else 9):board[y][x]=player+2
    state['quiet_plies']=0 if piece<=2 or captured else state['quiet_plies']+1
    for key in ('endgame_16','endgame_5'):
        if state[key] is not None:state[key]+=1
    draw_limits(board,state)
    next_player=3-player;won=not legal_strategy(name,board,next_player,state)
    key=position_key(board,next_player);state['repetitions'][key]=state['repetitions'].get(key,0)+1
    drawn=not won and (state['repetitions'][key]>=3 or state['quiet_plies']>=50 or state['endgame_16'] is not None and state['endgame_16']>=32 or state['endgame_5'] is not None and state['endgame_5']>=10)
    return {'player':player if won else next_player,'done':won or drawn,'winner':player if won else 0 if drawn else None,'score':material(board),'reward':1. if won else 0.,'state':state}
def encode_strategy(obs):
    name=obs['game'];p=obs['current_player'];x=[0.]*STRATEGY_SPECS[name][0]
    if name=='breakthrough':
        for i,v in enumerate(v for row in obs['board'] for v in row):
            if v:x[i*2+(v!=p)]=1
        return x
    for r in range(10):
        for c in range(10):
            v=obs['board'][r][c]
            if v:x[(r*5+c//2)*4+(0 if owner(v)==p else 2)+(v>2)]=1
    state=obs.get('draughts_state') or new_state();forced=state['forced_piece']
    if forced is not None:x[200+forced[0]*5+forced[1]//2]=1
    for r,c in state['pending_captures']:x[250+r*5+c//2]=1
    x[300:]=[state['quiet_plies']/50,(state['endgame_16'] or 0)/32,(state['endgame_5'] or 0)/10,state['repetitions'].get(position_key(obs['board'],p),0)/3]
    return x
def strategy_action_index(name,action):
    r,c=action['from'];y,x=action['to']
    return (r*5+c//2)*50+y*5+x//2 if name=='draughts' else (r*8+c)*3+x-c+1
