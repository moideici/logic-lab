"""One-thread, time-bounded weakness curriculum; test sets never select weights."""
import os
for _key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[_key]='1'
import argparse,copy,hashlib,json,random,time
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timezone
import numpy as np
from .continuous import atomic_json,file_hash,should_promote
from .continuous_history import historical_case_ids
from .general import GarryPolicy,GAMES,FEATURES,INPUT_OFFSETS,OUTPUT_OFFSETS
from .games import make_game
from .neural import SPECS,action_index
from .diversity import arrays,metrics,assess,canonical_key,family_split,SoftImitation
from .go_ai_policy import go_ai_actions

ROOT=Path(__file__).resolve().parents[1]
TARGETS=('go','hex','gomoku')

def strict_promotion(before,after,fresh_before,fresh_after):
    return should_promote(before,after,fresh_before,fresh_after) and after['soft_cross_entropy']<=before['soft_cross_entropy']+1e-6 and fresh_after['soft_cross_entropy']<=fresh_before['soft_cross_entropy']+1e-6

def sample_pool(cases,hard_ids,rng,limit=480,hard_fraction=.60):
    if any(c['split']!='train' for c in cases):raise ValueError('Le rejeu accepte uniquement le lot train')
    selected={};hard=[c for c in cases if c['id'] in hard_ids]
    for c in rng.sample(hard,min(len(hard),round(limit*hard_fraction))):selected[c['id']]=c
    categories=defaultdict(list)
    for c in cases:
        if c['id'] not in selected:categories[c['category']].append(c)
    for group in categories.values():rng.shuffle(group)
    names=list(categories);rng.shuffle(names)
    while len(selected)<min(round(limit*.9),len(cases)) and any(categories.values()):
        for category in names:
            if categories[category]:
                c=categories[category].pop();selected[c['id']]=c
                if len(selected)>=round(limit*.9):break
    rest=[c for c in cases if c['id'] not in selected]
    for c in rng.sample(rest,min(len(rest),limit-len(selected))):selected[c['id']]=c
    return list(selected.values())

def current_errors(model,cases,game):
    if not cases:return set()
    _,x,_,mask,_=arrays(cases,game);ni,no=SPECS[game];a=INPUT_OFFSETS[game];b=OUTPUT_OFFSETS[game]
    rows=np.r_[np.arange(a,a+ni),FEATURES+GAMES.index(game)]
    h=np.tanh(np.tanh(x@model.w1[rows]+model.b1)@model.core['w']+model.core['b'])
    choices=np.where(mask,h@model.w2[:,b:b+no]+model.b2[b:b+no],-1e9).argmax(1)
    return {c['id'] for i,c in enumerate(cases) if int(choices[i]) not in c.get('sound',c['optimal'])}

def assert_retention(candidate,champion,game):
    ni,no=SPECS[game];a=INPUT_OFFSETS[game];b=OUTPUT_OFFSETS[game]
    rows=set(range(a,a+ni))|{FEATURES+GAMES.index(game)};keep=[i for i in range(candidate.w1.shape[0]) if i not in rows]
    np.testing.assert_array_equal(candidate.w1[keep],champion.w1[keep]);np.testing.assert_array_equal(candidate.b1,champion.b1)
    for name in ('w2','b2'):
        x=getattr(candidate,name);y=getattr(champion,name)
        np.testing.assert_array_equal(x[...,:b],y[...,:b]);np.testing.assert_array_equal(x[...,b+no:],y[...,b+no:])
    for key in ('w','b'):np.testing.assert_array_equal(candidate.core[key],champion.core[key])
    for other in GAMES:
        if other!=game:assert candidate.game_steps[other]==champion.game_steps[other]

def restore_training_position(case,seed):
    if case['split']!='train':raise ValueError('Un départ ciblé doit provenir du lot train')
    o=case['observation'];game=o['game'];options={'size':len(o['board']),'komi':o['go_state']['komi']} if game=='go' else None
    env=make_game(game,seed,options);env.board=copy.deepcopy(o['board']);env.current_player=o['current_player'];env.moves=o['moves'];env.score=o.get('score',0)
    setattr(env,game+'_state',copy.deepcopy(o[game+'_state']))
    return env

def case_category(obs,info):
    game=obs['game'];b=obs['board'];n=len(b)
    if game=='go' and obs['go_state']['phase']=='play':
        from .go_rules import group
        seen=set()
        for r,row in enumerate(b):
            for c,value in enumerate(row):
                if value and (r,c) not in seen:
                    stones,liberties=group(b,r,c);seen.update(stones)
                    if len(liberties)==1:return 'atari'
        if sum(v==0 for row in b for v in row)<n*n*.22:return 'endgame'
    if game=='gomoku' and any(abs(v['quality'][0])>900000 for v in info['values']):return 'win_or_urgent_defense'
    return info['category']

def load_replay(directory,rng,emit):
    """Only earlier quarantined sessions can supply replay/validation, never tests."""
    replay={g:[] for g in TARGETS};validation={g:[] for g in TARGETS};counts=Counter();sources=[]
    for folder in sorted(directory.iterdir()):
        if not (folder/'cases.jsonl').is_file() or not (folder/'status.json').is_file():continue
        status=json.loads((folder/'status.json').read_text(encoding='utf-8'))
        if status.get('state') not in ('completed','stopped') or status.get('assessment_valid') is False or not status.get('history_quarantined_cases'):continue
        sources.append(folder.name)
        with (folder/'cases.jsonl').open(encoding='utf-8') as stream:
            for number,line in enumerate(stream,1):
                c=json.loads(line);split=c['split'];game=c['observation']['game']
                if split not in ('train','validation') or game not in TARGETS:continue
                key=(game,split);counts[key]+=1;pool=(replay if split=='train' else validation)[game];limit=1800 if split=='train' else 120
                if len(pool)<limit:pool.append(c)
                else:
                    at=rng.randrange(counts[key])
                    if at<limit:pool[at]=c
                if number%128==0:emit(phase='starting')
    return replay,validation,sources

def run(output,seconds=1800):
    if type(seconds)is not int or not 1<=seconds<=3600:raise ValueError('Durée entre 1 et 3600 secondes')
    output=Path(output);output.mkdir(parents=True,exist_ok=True);start=time.monotonic();deadline=start+seconds
    path=ROOT/'web/models/garry.json';champion=GarryPolicy.load(path);champion.save(output/'initial.json');expected=file_hash(path)
    seed=int(hashlib.sha256(output.name.encode()).hexdigest()[:8],16)^301800;rng=random.Random(seed);last_write=0.
    state={'state':'running','phase':'starting','profile':'weakness','programme':'diversity_10pct_targeted_75pct_consolidation_15pct','started_at':datetime.now(timezone.utc).isoformat(),'ends_at':datetime.fromtimestamp(time.time()+seconds,timezone.utc).isoformat(),'duration_seconds':seconds,'elapsed_seconds':0,'remaining_seconds':seconds,'pid':os.getpid(),'rng_seed':seed,'cpu_threads':1,'device':'cpu','cycles':0,'promotions':0,'moves_total':0,'fresh_samples':0,'game':'go','observation':None,'action':None,'model_sha256':expected,'assessment':'bounded_teacher_agreement_not_certified_playing_strength','preserved_games':[g for g in GAMES if g not in TARGETS]}
    def emit(force=False,**changes):
        nonlocal last_write
        state.update(changes);now=time.monotonic()
        if force or now-last_write>=.4:
            state.update(elapsed_seconds=round(now-start,2),remaining_seconds=max(0,round(deadline-now,2)),updated_at=datetime.now(timezone.utc).isoformat());atomic_json(output/'status.json',state);last_write=now
    def stopped():return time.monotonic()>=deadline or (output/'stop.json').exists()
    try:
        emit(True);prior,sources=historical_case_ids(output.parent,output,progress=lambda:emit(phase='starting'))
        replay,old_validation,replay_sources=load_replay(output.parent,rng,emit);all_cases=[]
        for source in ('training/go-6.0.0/cases.json','training/competitive-5.0.0/cases.json'):all_cases.extend(json.loads((ROOT/source).read_text(encoding='utf-8'))['cases'])
        history=prior|{canonical_key(c['observation']) for c in all_cases};training={g:[c for c in all_cases if c['split']=='train' and c['observation']['game']==g]+replay[g] for g in TARGETS}
        validation={g:[c for c in all_cases if c['split']=='validation' and c['observation']['game']==g]+old_validation[g] for g in TARGETS};tests=[c for c in all_cases if c['split']=='test'];fresh_valid={g:[] for g in TARGETS};fresh_test=[];seed_pool={g:list(training[g]) for g in TARGETS}
        baseline={g:metrics(champion,validation[g],g) for g in TARGETS};state.update(history_quarantined_cases=len(prior),historical_case_sources=sources,replay_sources=replay_sources,replay_train_counts={g:len(training[g]) for g in TARGETS},validation_counts={g:len(validation[g]) for g in TARGETS},baseline_validation={g:v['optimal_choice_rate'] for g,v in baseline.items()});rates=dict(state['baseline_validation']);episode=0
        while not stopped():
            progress=(time.monotonic()-start)/seconds;stage='diversity' if progress<.10 else 'targeted' if progress<.85 else 'consolidation';weakest=min(TARGETS,key=lambda g:rates[g]);schedule=(*TARGETS,weakest,*TARGETS);game=schedule[state['cycles']%len(schedule)];new=[];new_valid=[]
            emit(True,programme_stage=stage,game=game,phase='playing')
            for match in range(3):
                if stopped():break
                family=f'targeted:{output.name}:{episode}';episode+=1;split=family_split(family);derived=False;size=(9,13,19)[(state['cycles']//3+match)%3]
                candidates=seed_pool[game]
                if split=='train' and stage!='diversity' and candidates and rng.random()<.5:
                    parent=rng.choice(candidates);env=restore_training_position(parent,episode);family=f"derived-train:{parent['family']}";derived=True
                else:env=make_game(game,episode,{'size':size} if game=='go' else None)
                max_plies=(166 if len(env.board)==9 else 200 if len(env.board)==13 else 240) if game=='go' else 100
                for ply in range(max_plies):
                    if stopped() or env.done:break
                    obs=env.observation();legal=env.legal_actions();key=canonical_key(obs);info=None
                    if ply%4==0 and key not in history:
                        target,info=assess(obs,legal,champion,nodes=0);info['category']=case_category(obs,info);case={'id':key,'family':family,'split':split,'source':'training_position_continuation' if derived else 'targeted_diverse_self_play','observation':obs,'legal':legal,'target':target.tolist(),**info};history.add(key)
                        with (output/'cases.jsonl').open('a',encoding='utf-8')as stream:stream.write(json.dumps(case,separators=(',',':'))+'\n')
                        (new if split=='train' else new_valid if split=='validation' else fresh_test).append(case);state['fresh_samples']+=1
                    choices=go_ai_actions(obs,legal) if game=='go' else [a for a in legal if not a.get('resign')]
                    coin=rng.random();epsilon=.35 if stage=='diversity' else .10 if stage=='consolidation' else .20
                    if game=='go' and env.go_state['phase']=='scoring':action=choices[0]
                    elif coin<epsilon:action=rng.choice(choices)
                    elif coin<epsilon+.30:action=champion.for_game(game).choose(obs,choices,10)
                    else:
                        if info is None:_,info=assess(obs,legal,champion,nodes=0)
                        action=max((v for v in info['values'] if v['action'] in choices),key=lambda v:tuple(v['quality']))['action']
                    env.step(action);state['moves_total']+=1;emit(phase='playing',game=game,observation=env.observation(),action=action,episode=episode)
            training[game].extend(new);fresh_valid[game].extend(new_valid);state['cycles']+=1
            if stopped():break
            recent=fresh_valid[game][-120:]
            if len(recent)<24:emit(True,phase='collecting_validation');continue
            before=metrics(champion,validation[game],game);fb=metrics(champion,recent,game);candidates=rng.sample(training[game],min(1200,len(training[game])));hard=current_errors(champion,candidates,game);pool=sample_pool(candidates,hard,rng,hard_fraction=.35 if stage=='consolidation' else .60)
            seed_pool[game]=[c for c in pool if c['id'] in hard] or pool
            candidate=copy.deepcopy(champion);lr=.0001 if stage=='consolidation' else (.00012,.00024,.0004)[state['cycles']%3];teacher=SoftImitation(candidate,game,lr=lr);_,x,y,mask,weight=arrays(pool,game);weight*=np.asarray([1.5 if c['id'] in hard else 1 for c in pool],np.float32)
            emit(True,phase='fitting',hard_pool_candidates=len(hard),training_pool=len(pool),hard_training_samples=sum(c['id'] in hard for c in pool),learning_rate=lr,training_categories=dict(Counter(c['category'] for c in pool)))
            for epoch in range(6 if stage=='consolidation' else 10):
                if stopped():break
                order=rng.sample(range(len(x)),len(x))
                for at in range(0,len(order),32):
                    if stopped():break
                    ids=order[at:at+32];teacher.batch(x[ids],y[ids],mask[ids],weight[ids])
            if stopped():break
            emit(True,phase='validating');after=metrics(candidate,validation[game],game);fa=metrics(candidate,recent,game);accepted=strict_promotion(before,after,fb,fa)
            assert_retention(candidate,champion,game)
            if accepted:
                if file_hash(path)!=expected:raise RuntimeError('Modèle changé ailleurs : aucun écrasement')
                candidate.save(path);champion=candidate;expected=file_hash(path);state['promotions']+=1;champion.save(output/'latest-accepted.json');state['model_sha256']=expected
            rates[game]=(after if accepted else before)['optimal_choice_rate']
            evaluation={'game':game,'accepted':accepted,'fixed_validation_before':before['optimal_choice_rate'],'fixed_validation_after':after['optimal_choice_rate'],'fresh_validation_before':fb['optimal_choice_rate'],'fresh_validation_after':fa['optimal_choice_rate'],'fixed_loss_before':before['soft_cross_entropy'],'fixed_loss_after':after['soft_cross_entropy'],'fresh_loss_before':fb['soft_cross_entropy'],'fresh_loss_after':fa['soft_cross_entropy'],'hard_samples':sum(c['id'] in hard for c in pool),'pool':len(pool),'stage':stage,'other_game_coefficients_unchanged':True}
            state['last_evaluation']=evaluation
            with (output/'evaluations.jsonl').open('a',encoding='utf-8')as stream:stream.write(json.dumps(evaluation)+'\n')
            emit(True,phase='checkpoint')
        emit(True,phase='final_evaluation');initial=GarryPolicy.load(output/'initial.json');report={'profile':'weakness','before':{},'after':{},'fresh_tests':len(fresh_test),'preserved_games':state['preserved_games'],'test_usage':'reported_only_after_selection_ends'}
        for game in TARGETS:report['before'][game]=metrics(initial,tests+fresh_test,game);report['after'][game]=metrics(champion,tests+fresh_test,game)
        atomic_json(output/'report.json',report);emit(True,state='stopped' if (output/'stop.json').exists() else 'completed',phase='finished',finished_at=datetime.now(timezone.utc).isoformat())
    except Exception as error:emit(True,state='error',phase='failed',error=str(error));raise
    return state

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--seconds',type=int,default=1800);args=parser.parse_args();run(args.output,args.seconds)
