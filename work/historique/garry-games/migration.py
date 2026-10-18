"""Expand legacy six-game models without changing any old coefficient."""
import copy
LEGACY_GAMES=('tictactoe','connect4','2048','sudoku','minesweeper','sliding_puzzle')
def initial_weight(index):
    x=(index+0x9e3779b9)&0xffffffff;x^=x>>16;x=x*0x85ebca6b&0xffffffff;x^=x>>13;x=x*0xc2b2ae35&0xffffffff;x^=x>>16
    # Binary fractions, rounded once to IEEE float32 by both runtimes.
    import struct
    return struct.unpack('<f',struct.pack('<f',((x>>8)/16777216-.5)/16))[0]
def upgrade_legacy(data,specs,default_head):
    h=data.get('hidden')
    if type(h) is not int or not 1<=h<=256 or data.get('games')!=list(LEGACY_GAMES) or data.get('input')!=1912 or data.get('output')!=818:raise ValueError('Architecture historique invalide')
    for key,length in (('w1',1912*h),('w2',818*h),('b1',h),('b2',818)):
        if not isinstance(data.get(key),list) or len(data[key])!=length:raise ValueError('Poids historiques invalides')
    games=list(specs);features=sum(v[0] for v in specs.values());inputs=features+len(games);outputs=sum(v[1] for v in specs.values())
    d=copy.deepcopy(data);d.update(format='garry-mlp-v3',version='4.0.0',games=games,input=inputs,output=outputs)
    d['w1']=[initial_weight(i) for i in range(inputs*h)];d['w2']=[initial_weight(1000000+i) for i in range(outputs*h)];d['b2']=[0.]*outputs
    d['w1'][:1906*h]=data['w1'][:1906*h]
    for i in range(6):d['w1'][(features+i)*h:(features+i+1)*h]=data['w1'][(1906+i)*h:(1907+i)*h]
    for j in range(h):d['w2'][j*outputs:j*outputs+818]=data['w2'][j*818:(j+1)*818]
    d['b2'][:818]=data['b2'];d['game_steps']={g:data.get('game_steps',{}).get(g) if g in LEGACY_GAMES else 0 for g in games}
    if data['format']=='garry-mlp-v1':d['position_head']=copy.deepcopy(default_head)
    return d
