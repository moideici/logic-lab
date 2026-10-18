"""Exact immediate wins/blocks with bounded reply analysis and Swap2 choices."""
from .gomoku_rules import exact_five,gomoku_color,DIRS
def potential(b,r,c,color):
    score=0
    for dr,dc in DIRS:
        length=1;opened=0
        for sign in (-1,1):
            y,x=r+sign*dr,c+sign*dc
            while 0<=y<15 and 0<=x<15 and b[y][x]==color:length+=1;y+=sign*dr;x+=sign*dc
            opened+=int(0<=y<15 and 0<=x<15 and b[y][x]==0)
        if length==5:score+=100000
        elif length<5:score+=(0,1,8,80,1000)[length]*(opened+int(opened==2))
    return score
def static_color(b,color):return sum(potential(b,r,c,color) for r,row in enumerate(b) for c,v in enumerate(row) if v==color)
def winning_moves(b,color):
    out=[]
    for r in range(15):
        for c in range(15):
            if b[r][c]:continue
            b[r][c]=color
            try:won=bool(exact_five(b,r,c,color))
            finally:b[r][c]=0
            if won:out.append((r,c))
    return out
def gomoku_values(o,legal,budget):
    b=o['board'];s=o['gomoku_state'];phase=s['phase'];color=gomoku_color(o['current_player'],s);values=[]
    if phase!='play':
        balance=static_color(b,1)-static_color(b,2)
        for a in legal:
            if 'choose' in a:q=balance if a['choose']=='black' else -balance
            else:
                r,c=a['row'],a['col'];b[r][c]=color
                try:q=-abs(static_color(b,1)-static_color(b,2))
                finally:b[r][c]=0
                q-=abs(r-7)+abs(c-7)
            values.append({'action':a,'quality':[q]})
        return values,{'method':'gomoku_swap2_balance','analysis_exact':False,'optimal':False,'depth':1,'nodes':0}
    wins=winning_moves(b,color);threats=winning_moves(b,3-color);proven=bool(wins)
    for a in legal:
        r,c=a['row'],a['col'];q=1000000 if (r,c) in wins else -999999 if threats and any(t!=(r,c) for t in threats) else potential(b,r,c,color)+potential(b,r,c,3-color)*.9-(abs(r-7)+abs(c-7))*.01
        values.append({'action':a,'quality':[q]})
    reached=0
    if not wins:
        updated=[]
        try:
            for v in values:
                budget.tick();a=v['action'];r,c=a['row'],a['col']
                if abs(v['quality'][0])>900000:updated.append(v);continue
                b[r][c]=color
                try:
                    forks=winning_moves(b,color)
                    if len(forks)>=2:q=999997
                    else:
                        replies=sorted(((potential(b,y,x,3-color)+potential(b,y,x,color)*.9,y,x) for y in range(15) for x in range(15) if not b[y][x]),reverse=True)
                        q=v['quality'][0]-(replies[0][0] if replies else 0)*.5
                finally:b[r][c]=0
                updated.append({'action':a,'quality':[q]})
            values=updated;reached=2
        except Exception as error:
            from .agents import Exhausted
            if not isinstance(error,Exhausted):raise
    return values,{'method':'gomoku_threats_and_replies','analysis_exact':False,'optimal':proven,'immediate_win':proven,'depth':reached,'nodes':budget.nodes,'evaluation_scope':'bounded_threat_analysis'}
