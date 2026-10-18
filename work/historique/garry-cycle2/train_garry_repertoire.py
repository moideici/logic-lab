"""Teach multiple good moves; validate once per game and preserve other modes."""
import argparse,json,math,sys,time
from collections import Counter
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from logic_arena.diversity import SoftImitation,arrays,metrics,augment
from logic_arena.general import GarryPolicy,GAMES,INPUT_OFFSETS,OUTPUT_OFFSETS,FEATURES
from logic_arena.neural import SPECS
from examples.train_garry_curriculum import atomic_json
from examples.train_garry_guarded import protected_weights_equal

def copy_mode(source,target,game):
    ni,no=SPECS[game];a=INPUT_OFFSETS[game];b=OUTPUT_OFFSETS[game];tag=FEATURES+GAMES.index(game)
    target.w1[a:a+ni]=source.w1[a:a+ni];target.w1[tag]=source.w1[tag];target.w2[:,b:b+no]=source.w2[:,b:b+no];target.b2[b:b+no]=source.b2[b:b+no]
    target.steps+=source.game_steps[game]-target.game_steps[game];target.game_steps[game]=source.game_steps[game]

def allowed(before,after):
    critical={'finish','block','fork','support_trap','repair','safe_frontier','draw','win','resist_loss','cramped','goal'}
    return after['sound_choice_rate']>=before['sound_choice_rate'] and after['soft_cross_entropy']<=before['soft_cross_entropy'] and all(after['categories'].get(k,{}).get('sound_choice_rate',0)>=v['sound_choice_rate'] for k,v in before['categories'].items() if k in critical and v['samples']>=8)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--dataset',type=Path,required=True);ap.add_argument('--source',default='web/models/garry.json');ap.add_argument('--output',type=Path,required=True);ap.add_argument('--epochs',type=int,default=100);ap.add_argument('--lr',type=float,default=.0003);ap.add_argument('--retention-dataset',type=Path,action='append',default=[]);args=ap.parse_args()
    if args.epochs<1 or not math.isfinite(args.lr) or args.lr<=0:ap.error('Invalid training settings')
    args.output.mkdir(parents=True,exist_ok=True);started=time.monotonic();data=json.loads(args.dataset.read_text());cases=data['cases'];base=GarryPolicy.load(args.source);active=GarryPolicy.from_dict(base.export());base.save(args.output/'before.json');rng=np.random.default_rng(16035999);history={};selection={}
    train=[c for c in cases if c['split']=='train'];val=[c for c in cases if c['split']=='validation'];test=[c for c in cases if c['split']=='test']
    retention={c['id']:c for p in args.retention_dataset for c in json.loads(p.read_text())['cases'] if c['split']=='validation'};retention=list(retention.values())
    for game in GAMES:
        model=GarryPolicy.from_dict(base.export());training=[a for c in train if c['observation']['game']==game for a in augment(c)]
        _,x,target,mask,importance=arrays(training,game);trainer=SoftImitation(model,game,args.lr);best=metrics(model,val,game);before_val=dict(best);best_score=(-best['soft_cross_entropy'],best['sound_choice_rate']);best_epoch=0;best_data=model.export();trace=[];stale=0
        retention_before=metrics(base,retention,game) if retention else None
        for epoch in range(1,args.epochs+1):
            trainer.lr=args.lr*(.25+.75*.5*(1+math.cos(math.pi*epoch/args.epochs)));order=rng.permutation(len(x));loss=0.
            for begin in range(0,len(x),64):
                at=order[begin:begin+64];loss+=trainer.batch(x[at],target[at],mask[at],importance[at])*len(at)
            metric=metrics(model,val,game);score=(-metric['soft_cross_entropy'],metric['sound_choice_rate'])
            # Choose checkpoints on validation only, preserving critical skills
            # there as well as on the final, unopened test split.
            retained=metrics(model,retention,game) if retention else None
            if allowed(before_val,metric) and (retained is None or allowed(retention_before,retained)) and score>best_score:best_score=score;best=dict(metric);best_epoch=epoch;best_data=model.export();stale=0
            else:stale+=1
            trace.append({'epoch':epoch,'loss':loss/len(x),'validation':metric,'retention_validation':retained})
            if epoch%10==0:print(json.dumps({'game':game,'epoch':epoch,'best_epoch':best_epoch,'validation':best}),flush=True)
            atomic_json(args.output/'status.json',{'state':'training','game':game,'epoch':epoch,'best_epoch':best_epoch,'seconds':time.monotonic()-started})
            if stale>=40:break
        candidate=GarryPolicy.from_dict(best_data)
        if not protected_weights_equal(base,candidate,game) or candidate.position_head!=base.position_head:raise RuntimeError('Protected weights changed')
        # The test split is opened once, after checkpoint selection has finished.
        before_test=metrics(base,test,game);after_test=metrics(candidate,test,game);accept=allowed(before_test,after_test) and best_epoch>0
        selection[game]={'best_epoch':best_epoch,'unique_training':sum(c['observation']['game']==game for c in train),'augmented_training':len(training),'before_validation':before_val,'after_validation':best,'before_test':before_test,'after_test':after_test,'retention_before_validation':retention_before,'retention_after_validation':metrics(candidate,retention,game) if retention else None,'accepted':accept,'protected_other_modes':True}
        if accept:copy_mode(candidate,active,game)
        history[game]=trace;atomic_json(args.output/f'{game}-training.json',trace);atomic_json(args.output/'selection.json',selection);active.save(args.output/'candidate.json')
        print(json.dumps({'selected_game':game,**selection[game]}),flush=True)
    report={'state':'completed','software_version':'3.1.0','architecture_changed':False,'source':str(args.source),'selection':selection,'dataset_summary':data['summary'],'policy_core_unchanged':True,'position_head_unchanged':active.position_head==base.position_head,'active_model_replaced':False,'seconds':time.monotonic()-started}
    atomic_json(args.output/'report.json',report);atomic_json(args.output/'status.json',report);active.save(args.output/'candidate.json')
    print(json.dumps({'accepted_games':[g for g,s in selection.items() if s['accepted']],'seconds':report['seconds']}),flush=True)
if __name__=='__main__':main()
