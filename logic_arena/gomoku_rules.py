"""RIF Gomoku: exact five on 15x15, with the Swap2 opening."""
GOMOKU_SPECS={'gomoku':(459,227)}
PHASES=('opening_three','choose_or_extend','opening_two','choose_color','play')
DIRS=((0,1),(1,0),(1,1),(1,-1))
def new_gomoku():return [[0]*15 for _ in range(15)],{'phase':'opening_three','colors':[0,0],'placed':0,'winning_line':[]}
def gomoku_color(player,state):return state['colors'][player-1] if state['phase']=='play' else 1 if state['placed']%2==0 else 2
def exact_five(board,r,c,color):
    for dr,dc in DIRS:
        line=[[r,c]]
        for sign in (-1,1):
            y,x=r+sign*dr,c+sign*dc
            while 0<=y<15 and 0<=x<15 and board[y][x]==color:line.append([y,x]);y+=sign*dr;x+=sign*dc
        if len(line)==5:return sorted(line)
    return []
def legal_gomoku(board,state):
    out=[] if state['phase']=='choose_color' else [{'row':r,'col':c} for r in range(15) for c in range(15) if not board[r][c]]
    if state['phase'] in ('choose_or_extend','choose_color'):out += [{'choose':'black'},{'choose':'white'}]
    return out
def step_gomoku(board,player,a,state):
    phase=state['phase']
    if 'choose' in a:
        color=1 if a['choose']=='black' else 2;state['colors'][player-1]=color;state['colors'][2-player]=3-color;state['phase']='play'
        return {'player':state['colors'].index(2)+1,'done':False,'winner':None,'score':0,'reward':0.,'state':state}
    color=gomoku_color(player,state);r,c=a['row'],a['col'];board[r][c]=color;state['placed']+=1
    if phase=='opening_three':
        if state['placed']==3:state['phase']='choose_or_extend';player=2
    elif phase=='choose_or_extend':state['phase']='opening_two'
    elif phase=='opening_two':state['phase']='choose_color';player=1
    else:
        line=exact_five(board,r,c,color);state['winning_line']=line
        done=bool(line) or state['placed']==225
        return {'player':player if line else 3-player,'done':done,'winner':player if line else 0 if done else None,'score':1 if line else 0,'reward':1. if line else 0.,'state':state}
    return {'player':player,'done':False,'winner':None,'score':0,'reward':0.,'state':state}
def encode_gomoku(o):
    s=o['gomoku_state'];own=s['colors'][o['current_player']-1] or 1;x=[0.]*459
    for i,v in enumerate(v for row in o['board'] for v in row):
        if v:x[2*i+(v!=own)]=1
    x[450+PHASES.index(s['phase'])]=1;next_color=gomoku_color(o['current_player'],s);x[455+next_color-1]=1
    if s['colors'][o['current_player']-1]:x[457+s['colors'][o['current_player']-1]-1]=1
    return x
def gomoku_action_index(a):return 225+(a['choose']=='white') if 'choose' in a else a['row']*15+a['col']
