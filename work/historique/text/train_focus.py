"""Thirty-minute targeted session, with explicit deadlines and independent gates."""
from pathlib import Path
import argparse,collections,copy,gc,hashlib,json,math,os,random,time
from datetime import datetime,timezone
os.environ.setdefault('TOKENIZERS_PARALLELISM','false')
import torch
from peft import PeftModel
from transformers import AutoTokenizer
from train_language import model,packed,wikipedia,gpu
from focus_curriculum import build as build_curriculum
from chat import SYSTEM,SCHEMA,validate_response
from json_output import loads
from prepare_large import atomic
ROOT=Path(__file__).resolve().parent
def read(path):return [json.loads(s) for s in Path(path).read_text(encoding='utf-8').splitlines()]
def encode(c,tok):
 prompt=tok.apply_chat_template([{'role':'system','content':SYSTEM}]+c['messages'],tokenize=False,add_generation_prompt=True,enable_thinking=False);target=json.dumps(c['answer'],ensure_ascii=False,separators=(',',':'))+tok.eos_token;pre=tok(prompt,add_special_tokens=False).input_ids;post=tok(target,add_special_tokens=False,return_offsets_mapping=True);ids=post['input_ids'];offsets=post['offset_mapping']
 if len(pre)+len(ids)>640:return None
 start=target.index('"valeurs"');weights=[3. if end>start else .7 for begin,end in offsets];weights[-1]=4.
 return {'id':c['id'],'kind':c['kind'],'ids':pre+ids,'labels':[-100]*len(pre)+ids,'weights':[0.]*len(pre)+weights}
def loss_batch(net,items,tok,weighted=True):
 d=packed(items,tok);labels=d.pop('labels');active=(labels[:,1:]!=-100).any(dim=0).nonzero().flatten();positions=active;targets=labels[:,positions+1];logits=net(**d,logits_to_keep=positions,use_cache=False).logits
 ce=torch.nn.functional.cross_entropy(logits.float().reshape(-1,logits.shape[-1]),targets.reshape(-1),ignore_index=-100,reduction='none').reshape_as(targets)
 weights=torch.zeros_like(labels,dtype=torch.float32)
 for i,c in enumerate(items):weights[i,:len(c['ids'])]=torch.tensor(c.get('weights',[1.]*len(c['ids'])),device='cuda')
 w=weights[:,positions+1] if weighted else (targets!=-100).float();w=w*(targets!=-100);return (ce*w).sum()/w.sum(),int((targets!=-100).sum())
@torch.inference_mode()
def measure_loss(net,cases,tok):
 net.eval();total=0;count=0
 for at in range(0,len(cases),2):
  l,n=loss_batch(net,cases[at:at+2],tok);total+=float(l)*n;count+=n
 return total/count
@torch.inference_mode()
def evaluate(net,cases,tok,deadline=None):
 from lmformatenforcer.integrations.transformers import build_token_enforcer_tokenizer_data
 from decoding import generate_json
 net.eval();token_data=build_token_enforcer_tokenizer_data(tok);details=[];valid=correct=0
 for c in cases:
  answer=None;error=None;began=time.monotonic()
  if deadline and deadline-began<2:error='budget_session_epuise'
  else:
   prompt=tok.apply_chat_template([{'role':'system','content':SYSTEM}]+c['messages'],tokenize=False,add_generation_prompt=True,enable_thinking=False);inp=tok(prompt,return_tensors='pt').to('cuda');budget=min(16,max(1,deadline-began)) if deadline else 16
   try:
    raw,_=generate_json(net,tok,token_data,inp,SCHEMA,sample=False,max_tokens=320,max_seconds=budget);answer=validate_response(loads(raw));valid+=1;correct+=answer['valeurs']==c['answer']['valeurs']
   except ValueError as e:error=str(e)
  details.append({'id':c['id'],'kind':c['kind'],'expected':c['answer']['valeurs'],'answer':answer,'erreur':error,'secondes':round(time.monotonic()-began,2)})
 groups={}
 for kind in sorted({c['kind'] for c in cases}):
  rows=[d for d in details if d['kind']==kind];groups[kind]={'cas':len(rows),'json_valides':sum(d['answer']is not None for d in rows),'valeurs_exactes':sum(d['answer']is not None and d['answer']['valeurs']==d['expected'] for d in rows)}
 return {'cas':len(cases),'json_valides':valid,'valeurs_exactes':correct,'taux_json':valid/len(cases),'taux_valeurs':correct/len(cases),'groupes':groups,'details':details,'budget_tokens':320,'budget_secondes_par_cas':16}
def choose_eval(cases,counts):
 result=[]
 for kind,count in counts.items():result.extend([c for c in cases if c['kind']==kind][:count])
 return result
def run(seconds=1800,seed=172211,preflight=False):
 torch.set_num_threads(4);torch.manual_seed(seed);random.seed(seed)
 if not torch.cuda.is_available():raise RuntimeError('GPU CUDA absent')
 if not 60<=seconds<=1800:raise ValueError('Durée de 60 à 1800 secondes')
 root=ROOT/'chat_data/focus30'
 if not (root/'manifest.json').exists():build_curriculum(root)
 train_raw=read(root/'train.jsonl');valid_raw=read(root/'validation.jsonl');replay_raw=read(ROOT/'chat_data/train.jsonl');old_valid_raw=read(ROOT/'chat_data/validation.jsonl');base=json.loads((ROOT/'models/chat_base.json').read_text(encoding='utf-8'));tok=AutoTokenizer.from_pretrained(base['path'],local_files_only=True);tok.pad_token=tok.eos_token
 encoded=[v for c in train_raw if (v:=encode(c,tok)) is not None];valid=[v for c in valid_raw if (v:=encode(c,tok)) is not None];replay=[v for c in replay_raw if (v:=encode(c,tok)) is not None];retention=[v for c in old_valid_raw if (v:=encode(c,tok)) is not None][:80];natural=[v for v in replay if v['kind']=='dialogue']+[v for v in encoded if v['kind']=='dialogue']*8;valid_loss_cases=[c for k in ('calcul','structure','contexte') for c in [v for v in valid if v['kind']==k][:24]]
 start=time.monotonic();deadline=start+seconds;training_deadline=start+seconds*(.74 if not preflight else .9);job='focus-'+datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S');folder=ROOT/'models/chat'/job;folder.mkdir(parents=True);state={'etat':'en_cours','phase':'preparation','session':job,'pid':os.getpid(),'duree_secondes':seconds,'objectif_etapes':0,'etapes':0,'objectif_gpu':80,'exemples_vus':0,'tokens_vus':0,'historique':[],'exemples_disponibles':len(encoded)+len(replay),'documents_prepares':0,'fin_prevue':datetime.fromtimestamp(time.time()+seconds,timezone.utc).isoformat(),'detail':'Programme ciblé : champs numériques, calculs exacts, fin de JSON, contexte et conservation du français'}
 def emit(**kw):
  state.update(kw);elapsed=time.monotonic()-start;state.update(ecoule_secondes=round(elapsed),restant_secondes=max(0,round(deadline-time.monotonic())),date=datetime.now().astimezone().isoformat(),gpu=gpu());atomic(folder/'status.json',state)
  if not preflight:atomic(ROOT/'results/language_status.json',state)
 snapshot={'duration_seconds':seconds,'seed':seed,'base':base,'curriculum':json.loads((root/'manifest.json').read_text(encoding='utf-8')),'legacy_dataset_hashes':{s:hashlib.sha256((ROOT/'chat_data'/f'{s}.jsonl').read_bytes()).hexdigest() for s in ('train','validation','test')},'programme':['Reference sur validation et conservation','Maths/JSON prioritaires puis mélange contexte/français','Sélection sur validation uniquement','Tests finaux nouveaux après sélection'],'selection':'JSON complete non-regression, exact values non-regression per group, French retention loss within 10%; tests excluded'};atomic(folder/'input-manifest.json',snapshot);emit()
 net=model(tok);active_path=ROOT/'models/chat/active.json';active=json.loads(active_path.read_text(encoding='utf-8')) if active_path.exists() else None
 if active:net=PeftModel.from_pretrained(net,active['path'],is_trainable=False)
 if preflight:
  warm=ROOT/'models/chat/cycle-0.2.0/best';del net;gc.collect();torch.cuda.empty_cache();net=PeftModel.from_pretrained(model(tok),warm,is_trainable=True);net.enable_input_require_grads();net.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False});net.train();loss,n=loss_batch(net,encoded[:2],tok);loss.backward();assert torch.isfinite(loss);assert all(torch.isfinite(p.grad).all() for p in net.parameters() if p.grad is not None);print(json.dumps({'ok':True,'loss':float(loss.detach()),'supervised_tokens':n,'folder':str(folder)}));return
 emit(phase='reference',detail='Mesure de référence sur nouvelles épreuves réservées et conservation des acquis')
 evaluation_cases=choose_eval(valid_raw,{'calcul':8,'structure':8,'contexte':8})+choose_eval(old_valid_raw,{'extraction':2,'contexte':2});before_loss=measure_loss(net,valid_loss_cases,tok);before_retention=measure_loss(net,retention,tok);baseline=evaluate(net,evaluation_cases,tok,deadline=min(deadline,start+300));before={'perte_validation':before_loss,'perte_francais':before_retention,'generation':baseline};atomic(folder/'before.json',before);atomic(ROOT/'results/focus_reference.json',before);emit(reference_perte=before_loss,reference_valeurs=baseline['taux_valeurs'],reference_json=baseline['taux_json'])
 del net;gc.collect();torch.cuda.empty_cache();warm=Path(active['path']) if active else ROOT/'models/chat/cycle-0.2.0/best';net=PeftModel.from_pretrained(model(tok),warm,is_trainable=True);net.enable_input_require_grads();net.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False});net.config.use_cache=False;optimizer=torch.optim.AdamW([p for p in net.parameters() if p.requires_grad],lr=4e-5,weight_decay=.01)
 wiki,wiki_valid,docs=wikipedia(tok);state['documents_prepares']=docs;by_kind={k:[c for c in encoded if c['kind']==k] for k in ('calcul','structure','contexte')};warm_loss=measure_loss(net,valid_loss_cases,tok);best=float('inf');snapshots=[];step=0;micro=2;history=[];elapsed_training=0;emit(phase='apprentissage',detail='Entraînement ciblé en cours · priorité aux valeurs chiffrées et aux objets JSON terminés')
 while time.monotonic()<training_deadline:
  if (folder/'stop.json').exists():break
  compute_start=time.monotonic();net.train();optimizer.zero_grad(set_to_none=True);total=0.;tokens=0;examples=0;fraction=(time.monotonic()-start)/seconds
  weights=[.55,.20,.15,.075,.025] if fraction<.3 else [.40,.20,.20,.15,.05] if fraction<.55 else [.35,.20,.20,.20,.05]
  try:
   for _ in range(4//micro):
    category=random.choices(['calcul','structure','contexte','replay','wiki'],weights=weights,k=1)[0];pool=(natural if random.random()<.65 else replay) if category=='replay' else wiki if category=='wiki' else by_kind[category];items=random.sample(pool,micro);loss,n=loss_batch(net,items,tok);(loss/(4//micro)).backward();total+=float(loss.detach())/(4//micro);tokens+=n;examples+=len(items)
   torch.nn.utils.clip_grad_norm_(net.parameters(),1);optimizer.step();torch.cuda.synchronize()
  except torch.cuda.OutOfMemoryError:
   optimizer.zero_grad(set_to_none=True);torch.cuda.empty_cache()
   if micro==1:raise
   micro=1;emit(detail='Ajustement automatique des lots pour conserver la mémoire GPU');continue
  step+=1;state['exemples_vus']+=examples;state['tokens_vus']+=tokens;compute=time.monotonic()-compute_start;time.sleep(min(compute*.25,max(0,training_deadline-time.monotonic())))
  if step%10==0:emit(etapes=step,perte=total,detail=f"Session 30 min · {state['exemples_vus']} exemples traités · chiffres, JSON, contexte et français")
  if step%100==0 or training_deadline-time.monotonic()<8:
   score=measure_loss(net,valid_loss_cases,tok);ret=measure_loss(net,retention,tok);point={'etape':step,'perte_apprentissage':total,'perte_validation':score,'perte_francais':ret};history.append(point);state['historique']=history
   if ret<=before_retention*1.10:
    path=folder/f'checkpoint-{step}';net.save_pretrained(path,safe_serialization=True);snapshots.append({'path':str(path),'step':step,'loss':score,'retention':ret});best=min(best,score)
   emit(meilleure_perte=best if math.isfinite(best) else None,meilleure_etape=min(snapshots,key=lambda c:c['loss'])['step'] if snapshots else 0)
 if not snapshots:
  path=folder/'checkpoint-final';net.save_pretrained(path,safe_serialization=True);score=measure_loss(net,valid_loss_cases,tok);ret=measure_loss(net,retention,tok);snapshots.append({'path':str(path),'step':step,'loss':score,'retention':ret})
 emit(phase='evaluation',etapes=step,detail='Contrôle de la complétude JSON, des nombres et du contexte avant activation');del net,optimizer;gc.collect();torch.cuda.empty_cache();report={'version':'0.2.0','session':job,'avant':before,'apres':None,'active':False,'exemples_vus':state['exemples_vus'],'tokens_vus':state['tokens_vus'],'historique':history,'duree_cible':seconds,'budget_generation':{'tokens':320,'secondes_par_cas':16},'candidats':[]};selected=None
 for checkpoint in sorted(snapshots,key=lambda c:c['loss'])[:2]:
  if deadline-time.monotonic()<50:break
  net=PeftModel.from_pretrained(model(tok),checkpoint['path'],is_trainable=False);after=evaluate(net,evaluation_cases,tok,deadline=deadline-100);groups_ok=all(after['groupes'][k]['valeurs_exactes']>=v['valeurs_exactes'] for k,v in baseline['groupes'].items());accept=after['json_valides']==len(evaluation_cases) and after['taux_valeurs']>=baseline['taux_valeurs'] and groups_ok and checkpoint['retention']<=before_retention*1.1
  report['candidats'].append({'checkpoint':checkpoint,'generation':after,'retenu':accept});report['apres']={'perte_validation':checkpoint['loss'],'generation':after}
  if accept:selected=checkpoint;break
  del net;gc.collect();torch.cuda.empty_cache()
 if report['apres']is None:report['apres']={'perte_validation':best if math.isfinite(best) else before_loss,'generation':{'cas':0,'taux_json':0,'taux_valeurs':0,'details':[]}}
 # Newly reserved tests are read only after all selection decisions are frozen.
 if selected:
  report['active']=True;report['etape_selectionnee']=selected['step'];test_cases=choose_eval(read(root/'test.jsonl'),{'calcul':12,'structure':12,'contexte':12});report['tests']=evaluate(net,test_cases,tok,deadline=deadline)
  atomic(ROOT/'models/chat/active.json',{'path':selected['path'],'version':'0.2.0','session':job,'selection':'independent_validation_complete_json_and_per_category_non_regression','step':selected['step']})
 else:report['non_activation']='Aucun candidat ne satisfait tous les critères avant la fin du budget ; modèle précédent conservé.'
 report['duree_reelle_secondes']=round(time.monotonic()-start,2);atomic(folder/'report.json',report);atomic(ROOT/'results/language_report.json',report);emit(etat='termine',phase='termine',adaptation_active=report['active'],bilan=report,detail='Session ciblée terminée : modèle validé et activé' if selected else 'Session ciblée terminée : modèle précédent conservé')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--seconds',type=int,default=1800);p.add_argument('--preflight',action='store_true');a=p.parse_args()
 try:run(a.seconds,preflight=a.preflight)
 except Exception as e:
  import traceback;traceback.print_exc()
  if not a.preflight:atomic(ROOT/'results/language_status.json',{'etat':'erreur','erreur':str(e),'detail':'La session ciblée s’est arrêtée ; le modèle précédent reste conservé.'})
  raise
