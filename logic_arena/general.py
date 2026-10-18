"""Garry : un MLP conditionné par le jeu, un encodeur et une sortie globaux."""
import json
import copy
from .identity import AGENT_VERSION
from .value import default_head, validate_head, features
from .search_memory import empty_memory,validate_memory
from .migration import LEGACY_GAMES,upgrade_legacy
from pathlib import Path
import numpy as np

from .neural import NeuralPolicy, SPECS, encode, action_index

GAMES = tuple(SPECS)
INPUT_OFFSETS = {game: sum(SPECS[g][0] for g in GAMES[:i]) for i,game in enumerate(GAMES)}
OUTPUT_OFFSETS = {game: sum(SPECS[g][1] for g in GAMES[:i]) for i,game in enumerate(GAMES)}
FEATURES = sum(s[0] for s in SPECS.values())
INPUT = FEATURES + len(GAMES)
OUTPUT = sum(s[1] for s in SPECS.values())


def general_encode(obs):
    game = obs['game']
    x = np.zeros(INPUT, dtype=np.float32)
    start = INPUT_OFFSETS[game]
    x[start:start+SPECS[game][0]] = encode(obs)
    x[FEATURES+GAMES.index(game)] = 1
    return x


class GarryPolicy(NeuralPolicy):
    def __init__(self, hidden=48, seed=0):
        self.game, self.hidden, self.steps = 'general', hidden, 0
        self.rng = np.random.default_rng(seed)
        self.w1 = (self.rng.standard_normal((INPUT,hidden))*np.sqrt(2/(INPUT+hidden))).astype(np.float32)
        self.b1 = np.zeros(hidden, dtype=np.float32)
        self.w2 = (self.rng.standard_normal((hidden,OUTPUT))*np.sqrt(2/(hidden+OUTPUT))).astype(np.float32)
        self.b2 = np.zeros(OUTPUT, dtype=np.float32)
        self.core = {'w': np.eye(hidden,dtype=np.float32), 'b': np.zeros(hidden,dtype=np.float32), 'steps':0}
        self.game_steps = {g:0 for g in GAMES}
        self._adam = None
        self.position_head = default_head()
        self.search_memory = empty_memory()

    def logits(self, obs):
        e = np.tanh(general_encode(obs)@self.w1+self.b1)
        return np.tanh(e@self.core['w']+self.core['b'])@self.w2+self.b2

    def position_value(self, obs):
        if obs['game']!=self.position_head['game']:return None
        return float(features(obs)@np.asarray(self.position_head['weights']))

    def for_game(self, game):
        if game not in SPECS:raise ValueError('Jeu inconnu')
        return GarryView(self,game)

    def choose(self,obs,legal,level=10,style='balanced',*,logits=None,rng=None):
        if logits is not None and len(logits)==OUTPUT:
            start=OUTPUT_OFFSETS[obs['game']]
            logits=logits[start:start+SPECS[obs['game']][1]]
        return self.for_game(obs['game']).choose(obs,legal,level,style,logits=logits,rng=rng)

    def fit(self,x,targets,masks,epochs=20,batch_size=64,lr=.003):
        samples=np.asarray(x,dtype=np.float32)
        losses=super().fit(samples,targets,masks,epochs,batch_size,lr)
        for i,game in enumerate(GAMES):
            self.game_steps[game]+=int(np.count_nonzero(samples[:,FEATURES+i]))*epochs
        return losses

    def export(self):
        return {'format':'garry-mlp-v3','name':'garry','version':AGENT_VERSION,'position_head':copy.deepcopy(self.position_head),'search_memory':copy.deepcopy(self.search_memory),'games':list(GAMES),
                'input':INPUT,'output':OUTPUT,'hidden':self.hidden,'steps':self.steps,'game_steps':dict(self.game_steps),
                'w1':self.w1.ravel().tolist(),'b1':self.b1.tolist(),'w2':self.w2.ravel().tolist(),'b2':self.b2.tolist(),
                'core':{'id':'garry-core-v1','w':self.core['w'].ravel().tolist(),'b':self.core['b'].tolist(),'steps':self.core['steps']}}

    @classmethod
    def from_dict(cls,data):
        if data.get('format')=='garry-mlp-v3' and data.get('version')=='5.0.0' and data.get('games')==list(LEGACY_GAMES)+['reversi','nim','lightsout','draughts','breakthrough','hex','gomoku']:
            data=upgrade_legacy(data,SPECS,default_head())
        if data.get('format')=='garry-mlp-v3' and data.get('version')=='5.0.0' and data.get('games')==list(LEGACY_GAMES)+['reversi','nim','lightsout','draughts','breakthrough','hex']:
            data=upgrade_legacy(data,SPECS,default_head())
        if data.get('format')=='garry-mlp-v3' and data.get('version')=='4.0.0' and data.get('games') in (list(LEGACY_GAMES)+['reversi','nim','lightsout'],list(LEGACY_GAMES)+['reversi','nim','lightsout','draughts','breakthrough']):
            data=upgrade_legacy(data,SPECS,default_head())
        if (data.get('format'),data.get('version')) in (('garry-mlp-v1','2.0.0'),('garry-mlp-v2','3.0.0'),('garry-mlp-v2','3.1.0'),('garry-mlp-v2','3.2.0')):
            data=upgrade_legacy(data,SPECS,default_head())
        if data.get('format')!='garry-mlp-v3' or data.get('version') not in (AGENT_VERSION,'6.0.0') or data.get('name')!='garry' or data.get('games')!=list(GAMES) or data.get('input')!=INPUT or data.get('output')!=OUTPUT:
            raise ValueError('Architecture Garry invalide')
        hidden=data.get('hidden')
        if type(hidden) is not int or not 1<=hidden<=256:raise ValueError('Taille cachée invalide')
        model=cls(hidden)
        model.position_head=validate_head(data.get('position_head',default_head() if data.get('format')=='garry-mlp-v1' else None))
        model.search_memory=validate_memory(data.get('search_memory',empty_memory()))
        for key,shape in (('w1',(INPUT,hidden)),('b1',(hidden,)),('w2',(hidden,OUTPUT)),('b2',(OUTPUT,))):
            arr=np.asarray(data.get(key),dtype=np.float32)
            if arr.size!=int(np.prod(shape)) or not np.isfinite(arr).all():raise ValueError('Poids Garry invalides')
            setattr(model,key,arr.reshape(shape))
        core=data.get('core',{})
        if core.get('id')!='garry-core-v1':raise ValueError('Module Garry invalide')
        for key,shape in (('w',(hidden,hidden)),('b',(hidden,))):
            arr=np.asarray(core.get(key),dtype=np.float32)
            if arr.size!=int(np.prod(shape)) or not np.isfinite(arr).all():raise ValueError('Module Garry invalide')
            model.core[key]=arr.reshape(shape)
        for value in (data.get('steps'),core.get('steps'),*(data.get('game_steps',{}).get(g) for g in GAMES)):
            if type(value) is not int or value<0:raise ValueError('Compteur Garry invalide')
        model.steps=data['steps'];model.game_steps=dict(data['game_steps']);model.core['steps']=core['steps']
        return model

    @classmethod
    def fuse(cls,models):
        games=LEGACY_GAMES if set(models)==set(LEGACY_GAMES) else GAMES
        if set(models)!=set(games):raise ValueError('Tous les modèles sont nécessaires à la fusion')
        first=models[GAMES[0]]
        if any(m.hidden!=first.hidden for m in models.values()):raise ValueError('Dimensions incompatibles')
        common=max(models.values(),key=lambda m:m.core['steps']).core
        if any(not np.array_equal(m.core['w'],common['w']) or not np.array_equal(m.core['b'],common['b']) for m in models.values()):
            raise ValueError('Les six modèles doivent partager les mêmes poids centraux avant la fusion')
        out=cls(first.hidden);out.w1.fill(0);out.b1.fill(0)
        out.core={'w':common['w'].copy(),'b':common['b'].copy(),'steps':common['steps']}
        for i,g in enumerate(games):
            m=models[g];start=INPUT_OFFSETS[g];target=OUTPUT_OFFSETS[g]
            out.w1[start:start+SPECS[g][0]]=m.w1
            out.w1[FEATURES+i]=m.b1
            out.w2[:,target:target+SPECS[g][1]]=m.w2
            out.b2[target:target+SPECS[g][1]]=m.b2
            out.game_steps[g]=m.steps
        out.steps=sum(out.game_steps.values())
        return out


class GarryView:
    """Vue d'actions ; toutes les matrices appartiennent au même GarryPolicy."""
    def __init__(self,model,game):self.model,self.game=model,game
    @property
    def position_head(self):return self.model.position_head
    @property
    def search_memory(self):return self.model.search_memory
    @property
    def hidden(self):return self.model.hidden
    @property
    def core(self):return self.model.core
    @property
    def steps(self):return self.model.game_steps[self.game]
    @property
    def rng(self):return self.model.rng
    def logits(self,obs):
        if obs['game']!=self.game:raise ValueError('Jeu incompatible')
        start=OUTPUT_OFFSETS[self.game]
        return self.model.logits(obs)[start:start+SPECS[self.game][1]]
    choose=NeuralPolicy.choose
    def fit(self,x,targets,masks,epochs=20,batch_size=64,lr=.003):
        x=np.asarray(x,dtype=np.float32);n=len(x);ni,no=SPECS[self.game]
        expanded=np.zeros((n,INPUT),dtype=np.float32);start=INPUT_OFFSETS[self.game]
        expanded[:,start:start+ni]=x;expanded[:,FEATURES+GAMES.index(self.game)]=1
        legal=np.zeros((n,OUTPUT),dtype=bool);offset=OUTPUT_OFFSETS[self.game]
        legal[:,offset:offset+no]=masks
        losses=self.model.fit(expanded,np.asarray(targets)+offset,legal,epochs,batch_size,lr)
        return losses
    def export(self):return self.model.export()
    def save(self,path):self.model.save(path)
