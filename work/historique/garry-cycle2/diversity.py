"""Public-state curriculum, family-separated trials and guarded soft imitation.

This module never reads hidden mines. Puzzle solutions are offline labels only;
they are not encoded into observations or shipped with training examples.
"""
from collections import Counter
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
import math
import random
import numpy as np
from .games import make_game, sudoku_candidates
from .neural import encode, action_index, SPECS, NeuralPolicy
from .general import GAMES, INPUT_OFFSETS, OUTPUT_OFFSETS, FEATURES
from .agents import Budget

SPLITS=('train','validation','test')
PROFILES=('random','center','edges','current_policy','legacy_policy','tactical','legacy_search','champion')

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def family_split(family):
    n=int(digest(family)[:12],16)%10
    return 'test' if n==0 else 'validation' if n==1 else 'train'

def transforms(board):
    b=[r[:] for r in board]
    for _ in range(4):
        yield b
        yield [r[::-1] for r in b]
        b=[list(r) for r in zip(*b[::-1])]

def canonical_key(obs):
    game=obs['game'];b=obs['board'];p=obs.get('current_player',1)
    if game in ('tictactoe','connect4'):
        b=[[0 if not v else 1 if v==p else 2 for v in row] for row in b]
    if game=='tictactoe':variants=list(transforms(b))
    elif game=='connect4':variants=[b,[r[::-1] for r in b]]
    elif game in ('2048','minesweeper'):variants=list(transforms(b))
    else:variants=[b]
    # Givens and undo availability change the Sudoku action space.
    return digest([game,min(variants),obs.get('givens'),bool(obs.get('history'))])

class HistoricalSplits:
    """Keep earlier held-out families out of replay and all old states out of new trials."""
    def __init__(self,cases=(),observations=(),encoded_rows=()):
        self.keys=set();self.families=set();self.held_keys=set();self.held_families=set()
        for case in cases:
            key=canonical_key(case['observation']);self.keys.add(key);self.families.add(case['family'])
            if case['split']!='train':self.held_keys.add(key);self.held_families.add(case['family'])
        self.keys.update(canonical_key(o) for o in observations)
        self.encoded={hashlib.sha256(np.asarray(row,dtype=np.float32).tobytes()).digest() for row in encoded_rows}

    def fresh(self,obs,family):
        if canonical_key(obs) in self.keys or family in self.families:return False
        if self.encoded:
            from .general import general_encode
            boards=[obs['board']]
            if obs['game']=='connect4':boards.append([r[::-1] for r in obs['board']])
            elif obs['game'] in ('tictactoe','2048','minesweeper'):boards=list(transforms(obs['board']))
            for board in boards:
                row=np.asarray(general_encode({**obs,'board':board}),dtype=np.float32)
                if hashlib.sha256(row.tobytes()).digest() in self.encoded:return False
        return True

    def replayable(self,case):
        return case['split']=='train' and canonical_key(case['observation']) not in self.held_keys and case['family'] not in self.held_families

def sudoku_family(board):
    def normalize(b):
        mapping={};out=[]
        for row in b:
            for v in row:
                if v and v not in mapping:mapping[v]=len(mapping)+1
                out.append(mapping.get(v,0))
        return out
    return digest(min(normalize(b) for b in transforms(board)))

def sudoku_solutions(board,limit=2,node_limit=100000,rng=None):
    b=[r[:] for r in board];answers=[];nodes=0
    def visit():
        nonlocal nodes
        nodes+=1
        if nodes>node_limit:raise RuntimeError('Sudoku oracle budget exhausted')
        cell=None
        for r in range(9):
            for c in range(9):
                if not b[r][c]:
                    vals=sudoku_candidates(b,r,c)
                    if not vals:return
                    if cell is None or len(vals)<len(cell[0]):cell=vals,r,c
        if cell is None:answers.append(deepcopy(b));return
        vals,r,c=cell
        if rng is not None:rng.shuffle(vals)
        for v in vals:
            b[r][c]=v
            try:visit()
            finally:b[r][c]=0
            if len(answers)>=limit:return
    # Reject invalid filled boards as well as invalid partial givens.
    for r in range(9):
        for c in range(9):
            v=b[r][c]
            if v:
                b[r][c]=0;valid=v in sudoku_candidates(b,r,c);b[r][c]=v
                if not valid:return [],0
    visit();return answers,nodes

def new_sudoku(seed,clues=34):
    if not 24<=clues<=60:raise ValueError('clues must be 24..60')
    rng=random.Random(seed)
    for attempt in range(8):
        try:answers,_=sudoku_solutions([[0]*9 for _ in range(9)],1,50000,rng)
        except RuntimeError:continue
        if answers:break
    else:raise RuntimeError('Cannot generate solved grid')
    solution=answers[0];puzzle=deepcopy(solution);cells=list(range(81));rng.shuffle(cells)
    for i in cells:
        if sum(bool(v) for row in puzzle for v in row)<=clues:break
        r,c=divmod(i,9);v=puzzle[r][c];puzzle[r][c]=0
        try:answers,_=sudoku_solutions(puzzle,2,12000)
        except RuntimeError:answers=[]
        if len(answers)!=1:puzzle[r][c]=v
    env=make_game('sudoku',seed);env.board=deepcopy(puzzle);env.givens=deepcopy(puzzle);env.history=[]
    return env,solution

def c4_tactics(obs):
    from .connect4 import _won
    b=obs['board'];p=obs['current_player'];bits=[0,0,0];heights=[]
    for c in range(7):
        heights.append(sum(bool(b[r][c]) for r in range(6)))
        for r in range(6):
            if b[r][c]:bits[b[r][c]]|=1<<(c*7+5-r)
    columns=[c for c in range(7) if heights[c]<6]
    def wins(who):return [c for c in columns if heights[c]<6 and _won(bits[who]|(1<<(c*7+heights[c])))]
    immediate=wins(p);enemy=wins(3-p);safe=[];forks=[]
    for c in columns:
        bit=1<<(c*7+heights[c]);bits[p]|=bit;heights[c]+=1
        if not wins(3-p):
            safe.append(c)
            if len(wins(p))>=2:forks.append(c)
        heights[c]-=1;bits[p]^=bit
    phase='opening' if obs['moves']<10 else 'endgame' if obs['moves']>=28 else 'middle'
    category='finish' if immediate else 'resist_loss' if not safe else 'block' if enemy else 'fork' if forks else 'support_trap' if len(safe)<len(columns) else phase
    return {'category':category,'phase':phase,'immediate':immediate,'enemy':enemy,'safe':safe,'forks':forks}

def soft_targets(game,legal,values,temperature=48.):
    """Several sound moves can receive mass; known tactical losses cannot."""
    no=SPECS[game][1];target=np.zeros(no,dtype=np.float64)
    qualities=[tuple(v['quality']) for v in values];best=max(qualities)
    if game=='connect4':
        q=np.array([v[0] for v in qualities],dtype=np.float64)
        if best[0]>999957 or best[0]<-999957:weights=(q==best[0]).astype(float)
        else:
            weights=np.exp(np.clip((q-q.max())/temperature,-50,0));weights[q<-999957]=0
    else:weights=np.array([float(q==best) for q in qualities])
    for v,w in zip(values,weights):target[action_index(game,v['action'])]=w
    if not target.sum():raise ValueError('Empty target')
    return target/target.sum()

def assess(obs,legal,model,nodes=50000):
    from .planner import _ttt_value,sliding_distance
    game=obs['game'];view=model.for_game(game);logits=view.logits(obs);values=[];info={}
    if game=='connect4':
        from .connect4_wasm import search
        _,info=search(obs,legal,Budget(nodes,10000),logits=logits,position_head=model.position_head,max_depth=10,analyze=True)
        values=info.pop('action_values');info.update(c4_tactics(obs))
    elif game=='tictactoe':
        b=tuple(v for row in obs['board'] for v in row);p=obs['current_player']
        for a in legal:
            i=action_index(game,a);v,n=_ttt_value(b[:i]+(p,)+b[i+1:],3-p);v=-v;n+=1
            values.append({'action':a,'quality':[v,n if v==-1 else -n]})
        outcomes=[v['quality'][0] for v in values];info={'category':'win' if max(outcomes)==1 else 'draw' if max(outcomes)==0 else 'resist_loss','exact':True}
    elif game=='sliding_puzzle':
        b=obs['board'];r,c=next((r,c) for r in range(3) for c in range(3) if b[r][c]==0)
        for a in legal:
            dr,dc={'up':(-1,0),'down':(1,0),'left':(0,-1),'right':(0,1)}[a['direction']];child=deepcopy(b);child[r][c],child[r+dr][c+dc]=child[r+dr][c+dc],0
            values.append({'action':a,'quality':[-sliding_distance(child)]})
        d=sliding_distance(b);info={'category':'short' if d<=10 else 'medium' if d<=20 else 'long','distance':d,'exact':True}
    elif game=='2048':
        from .tiles import search
        _,info=search(obs,legal,logits,Budget(50000,10000),max_depth=1)
        values=info.pop('action_values');spaces=sum(v==0 for row in obs['board'] for v in row);largest=max(map(max,obs['board']))
        info.update(category='goal' if largest>=1024 else 'cramped' if spaces<=3 else 'middle' if largest>=64 else 'opening',exact=False)
    elif game=='minesweeper':
        from .agents import ReferenceAgent
        agent=ReferenceAgent(10);agent.mines(obs,legal,Budget(20000,10000),legal[0]);values=agent._mine_values
        risk=min(-v['quality'][0] for v in values);info={'category':'protected_opening' if obs['moves']==0 else 'safe_frontier' if risk==0 else 'uncertain','exact':False}
    elif game=='sudoku':
        answers,_=sudoku_solutions(obs['board'],2,100000)
        if not answers:values=[{'action':a,'quality':[1 if a.get('undo') else -1]} for a in legal]
        elif len(answers)==1:
            solved=answers[0];values=[{'action':a,'quality':[-1 if a.get('undo') else int(a['value']==solved[a['row']][a['col']])]} for a in legal]
        else:raise ValueError('Ambiguous puzzle cannot supply proved targets')
        zeros=sum(v==0 for row in obs['board'] for v in row);info={'category':'repair' if not answers else 'finish' if zeros<=12 else 'deduction','exact':True}
    else:raise ValueError('Unknown game')
    target=soft_targets(game,legal,values);best=max(tuple(v['quality']) for v in values)
    optimal=[action_index(game,v['action']) for v in values if tuple(v['quality'])==best]
    sound=[action_index(game,v['action']) for v in values if (v['quality'][0]>=best[0]-24 and v['quality'][0]>-999957)] if game=='connect4' and -999957<best[0]<999957 else optimal
    choice=max(legal,key=lambda a:float(logits[action_index(game,a)]));chosen=next(v for v in values if v['action']==choice)
    return target,{**info,'values':values,'optimal':optimal,'sound':sound,'baseline_error':action_index(game,choice) not in sound}

def example(env,model,family,source,nodes=50000):
    obs=env.observation();legal=env.legal_actions();target,info=assess(obs,legal,model,nodes)
    return {'id':canonical_key(obs),'family':str(family),'split':family_split(family),'source':source,'observation':obs,'legal':legal,'target':target.tolist(),**info}

class SoftImitation:
    """Local gradients only: shared core and other games remain exact."""
    def __init__(self,model,game,lr=.0003):
        self.model=model;self.game=game;self.lr=lr;ni,no=SPECS[game];a=INPUT_OFFSETS[game];b=OUTPUT_OFFSETS[game]
        self.rows=np.r_[np.arange(a,a+ni),FEATURES+GAMES.index(game)];self.cols=np.arange(b,b+no)
        self.w1=model.w1[self.rows].copy();self.w2=model.w2[:,self.cols].copy();self.b2=model.b2[self.cols].copy()
        self.m=[np.zeros_like(v) for v in (self.w1,self.w2,self.b2)];self.v=[v.copy() for v in self.m];self.t=0

    def batch(self,x,target,mask,importance=None):
        x=np.asarray(x,dtype=np.float32);target=np.asarray(target,dtype=np.float32);mask=np.asarray(mask,dtype=bool)
        if x.shape[1]!=len(self.rows) or target.shape!=mask.shape or target.shape[1]!=len(self.cols) or len(x)!=len(target):raise ValueError('Invalid batch shapes')
        if not np.isfinite(x).all() or not np.isfinite(target).all() or np.any(target<0) or np.any(target[~mask]!=0) or not np.allclose(target.sum(1),1,atol=1e-5) or not mask.any(1).all():raise ValueError('Invalid probability target')
        e=np.tanh(x@self.w1+self.model.b1);h=np.tanh(e@self.model.core['w']+self.model.core['b'])
        z=np.where(mask,h@self.w2+self.b2,-1e9);z-=z.max(1,keepdims=True);p=np.exp(z);p/=p.sum(1,keepdims=True)
        weight=np.ones(len(x),dtype=np.float32) if importance is None else np.asarray(importance,dtype=np.float32)
        if weight.shape!=(len(x),) or not np.isfinite(weight).all() or np.any(weight<=0):raise ValueError('Invalid importance')
        loss=float(np.sum(-target*np.log(np.maximum(p,1e-12))*weight[:,None])/weight.sum())
        dz=(p-target)*weight[:,None]/weight.sum();dh=(dz@self.w2.T)*(1-h*h);de=(dh@self.model.core['w'].T)*(1-e*e)
        grads=(x.T@de,h.T@dz,dz.sum(0));self.t+=1
        for at,(param,grad) in enumerate(zip((self.w1,self.w2,self.b2),grads)):
            grad=np.clip(grad,-5,5);self.m[at]*=.9;self.m[at]+=.1*grad;self.v[at]*=.999;self.v[at]+=.001*grad*grad
            param-=self.lr*(self.m[at]/(1-.9**self.t))/(np.sqrt(self.v[at]/(1-.999**self.t))+1e-8)
        self.model.w1[self.rows]=self.w1;self.model.w2[:,self.cols]=self.w2;self.model.b2[self.cols]=self.b2
        self.model.steps+=len(x);self.model.game_steps[self.game]+=len(x)
        return loss

def arrays(cases,game):
    selected=[c for c in cases if c['observation']['game']==game];no=SPECS[game][1]
    x=np.asarray([np.r_[encode(c['observation']),1] for c in selected],dtype=np.float32);targets=np.asarray([c['target'] for c in selected],dtype=np.float32)
    masks=np.zeros((len(selected),no),dtype=bool)
    for i,c in enumerate(selected):masks[i,[action_index(game,a) for a in c['legal']]]=True
    counts=Counter(c['category'] for c in selected)
    weights=np.asarray([math.sqrt(len(selected)/counts[c['category']])*(1.5 if c['baseline_error'] else 1) for c in selected],dtype=np.float32)
    return selected,x,targets,masks,weights

def augment(case):
    """Equivalent orientations stay inside their original training family."""
    game=case['observation']['game']
    yield case
    if game=='sliding_puzzle':return # mirroring changes this game's goal
    for turns,mirror in ([(r,m) for r in range(4) for m in (False,True) if r or m] if game in ('tictactoe','minesweeper','2048') else [(0,True)]):
        c=deepcopy(case);o=c['observation'];n=len(o['board']);width=len(o['board'][0])
        def board_transform(b):
            for _ in range(turns):b=[list(row) for row in zip(*b[::-1])]
            return [row[::-1] for row in b] if mirror else b
        o['board']=board_transform(o['board'])
        if 'givens' in o:o['givens']=board_transform(o['givens'])
        def coord(r,col):
            for _ in range(turns):r,col=col,n-1-r
            return r,width-1-col if mirror else col
        def action(a):
            if a.get('undo'):return dict(a)
            if game=='connect4':return {'column':6-a['column']}
            if 'direction' in a:
                d=a['direction']
                for _ in range(turns):d={'up':'right','right':'down','down':'left','left':'up'}[d]
                if mirror:d={'left':'right','right':'left','up':'up','down':'down'}[d]
                return {'direction':d}
            r,col=coord(a['row'],a['col']);return {**a,'row':r,'col':col}
        if 'history' in o:o['history']=[list(coord(r,col)) for r,col in o['history']]
        c['legal']=[action(a) for a in case['legal']];c['target']=[0.]*len(case['target']);c['optimal']=[]
        c['sound']=[]
        for old,new in zip(case['legal'],c['legal']):
            i=action_index(game,old);j=action_index(game,new);c['target'][j]=case['target'][i]
            if i in case['optimal']:c['optimal'].append(j)
            if i in case.get('sound',case['optimal']):c['sound'].append(j)
        c['values']=[{**v,'action':action(v['action'])} for v in case['values']]
        yield c

def metrics(model,cases,game):
    selected,x,target,mask,_=arrays(cases,game);start=OUTPUT_OFFSETS[game];ni,no=SPECS[game];rows=np.r_[np.arange(INPUT_OFFSETS[game],INPUT_OFFSETS[game]+ni),FEATURES+GAMES.index(game)]
    e=np.tanh(x@model.w1[rows]+model.b1);h=np.tanh(e@model.core['w']+model.core['b']);z=np.where(mask,h@model.w2[:,start:start+no]+model.b2[start:start+no],-1e9);z-=z.max(1,keepdims=True);p=np.exp(z);p/=p.sum(1,keepdims=True);choice=p.argmax(1)
    by_category={}
    for category in sorted({c['category'] for c in selected}):
        at=[i for i,c in enumerate(selected) if c['category']==category];by_category[category]={'samples':len(at),'optimal_choice_rate':sum(int(choice[i]) in selected[i]['optimal'] for i in at)/len(at),'sound_choice_rate':sum(int(choice[i]) in selected[i].get('sound',selected[i]['optimal']) for i in at)/len(at)}
    return {'samples':len(selected),'soft_cross_entropy':float(np.mean(np.sum(-target*np.log(np.maximum(p,1e-12)),axis=1))),'optimal_choice_rate':sum(int(choice[i]) in c['optimal'] for i,c in enumerate(selected))/len(selected),'sound_choice_rate':sum(int(choice[i]) in c.get('sound',c['optimal']) for i,c in enumerate(selected))/len(selected),'acceptable_target_mass':float(np.mean([p[i,np.asarray(c['target'])>0].sum() for i,c in enumerate(selected)])),'categories':by_category}
