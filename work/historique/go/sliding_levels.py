from .quality import select_quality
import random
def select_sliding_level(values,level,logits,rng=None):
 if level in (0,10):return select_quality(values,level,logits,'sliding_puzzle')
 if type(level)is not int or not 0<=level<=10:raise ValueError('Niveau du taquin invalide')
 rng=rng or random;ordered=sorted(values,key=lambda v:v['quality']);best=ordered[-1]['quality'];optimal=[v for v in ordered if v['quality']==best];others=[v for v in ordered if v['quality']!=best];probability=.5+level*.05
 pool=optimal if not others or rng.random()<probability else others;selected=pool[min(len(pool)-1,int(rng.random()*len(pool)))];return selected,{'level':level,'quality_rank':ordered.index(selected),'legal_count':len(ordered),'selected_is_best':selected['quality']==best,'selected_is_worst':selected['quality']==ordered[0]['quality'],'quality':selected['quality'],'level_semantics':'optimal_path_probability','optimal_move_probability':probability}
