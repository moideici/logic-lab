"""Expand legacy six-game models without changing any old coefficient."""
import copy
LEGACY_GAMES=('tictactoe','connect4','2048','sudoku','minesweeper','sliding_puzzle')
def initial_weight(index):
    x=(index+0x9e3779b9)&0xffffffff;x^=x>>16;x=x*0x85ebca6b&0xffffffff;x^=x>>13;x=x*0xc2b2ae35&0xffffffff;x^=x>>16
    # Binary fractions, rounded once to IEEE float32 by both runtimes.
    import struct
    return struct.unpack('<f',struct.pack('<f',((x>>8)/16777216-.5)/16))[0]
def upgrade_legacy(data,specs,default_head):
    layouts=[(list(LEGACY_GAMES),1906,1912,818),(list(LEGACY_GAMES)+['reversi','nim','lightsout'],2051,2060,925),(list(LEGACY_GAMES)+['reversi','nim','lightsout','draughts','breakthrough'],2483,2494,3617),(list(LEGACY_GAMES)+['reversi','nim','lightsout','draughts','breakthrough','hex'],2583,2595,3667)]
    layout=next((layout for layout in layouts if layout[0]==data.get('games')),None)
    if layout is None:raise ValueError('Architecture historique invalide')
    old_games,old_features,old_input,old_output=layout;h=data.get('hidden')
    if type(h) is not int or not 1<=h<=256 or data.get('input')!=old_input or data.get('output')!=old_output:raise ValueError('Architecture historique invalide')
    for key,length in (('w1',old_input*h),('w2',old_output*h),('b1',h),('b2',old_output)):
        if not isinstance(data.get(key),list) or len(data[key])!=length:raise ValueError('Poids historiques invalides')
    games=list(specs);features=sum(v[0] for v in specs.values());inputs=features+len(games);outputs=sum(v[1] for v in specs.values())
    d=copy.deepcopy(data);d.update(format='garry-mlp-v3',version='5.0.0',games=games,input=inputs,output=outputs)
    d['w1']=[initial_weight(i) for i in range(inputs*h)];d['w2']=[initial_weight(1000000+i) for i in range(outputs*h)];d['b2']=[0.]*outputs
    d['w1'][:old_features*h]=data['w1'][:old_features*h]
    for i in range(len(old_games)):d['w1'][(features+i)*h:(features+i+1)*h]=data['w1'][(old_features+i)*h:(old_features+i+1)*h]
    for j in range(h):d['w2'][j*outputs:j*outputs+old_output]=data['w2'][j*old_output:(j+1)*old_output]
    d['b2'][:old_output]=data['b2'];d['game_steps']={g:data.get('game_steps',{}).get(g) if g in old_games else 0 for g in games}
    if data['format']=='garry-mlp-v1':d['position_head']=copy.deepcopy(default_head)
    return d
