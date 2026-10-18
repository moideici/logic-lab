"""One bounded French adaptation cycle, with validation gates and GPU telemetry."""
from pathlib import Path
import collections,copy,gc,hashlib,json,math,os,random,shutil,subprocess,time
os.environ.setdefault('TOKENIZERS_PARALLELISM','false')
import numpy as np,torch
from transformers import AutoModelForCausalLM,AutoTokenizer
from peft import LoraConfig,get_peft_model
import pyarrow.parquet as pq
from chat import SYSTEM,SCHEMA,validate_response
from json_output import loads
from prepare_large import atomic
ROOT=Path(__file__).resolve().parent
def gpu():
 try:
  result=subprocess.run(['nvidia-smi','--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=3,creationflags=subprocess.CREATE_NO_WINDOW);v=[int(x.strip()) for x in result.stdout.splitlines()[0].split(',')];return dict(zip(('utilisation','memoire_mo','memoire_totale_mo','temperature'),v))
 except Exception:return {}
def read(split):return [json.loads(s) for s in (ROOT/'chat_data'/f'{split}.jsonl').read_text(encoding='utf-8').splitlines()]
def model(tokenizer):
 base=json.loads((ROOT/'models/chat_base.json').read_text(encoding='utf-8'));return AutoModelForCausalLM.from_pretrained(base['path'],local_files_only=True,use_safetensors=True,trust_remote_code=False,torch_dtype=torch.bfloat16,attn_implementation='sdpa').to('cuda')
def encode(c,tokenizer):
 messages=[{'role':'system','content':SYSTEM}]+c['messages'];prompt=tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False);target=json.dumps(c['answer'],ensure_ascii=False,separators=(',',':'))+tokenizer.eos_token;pre=tokenizer(prompt,add_special_tokens=False).input_ids;post=tokenizer(target,add_special_tokens=False).input_ids
 if len(pre)+len(post)>512:return None
 return {'ids':pre+post,'labels':[-100]*len(pre)+post,'kind':c['kind'],'id':c['id']}
def packed(items,tokenizer):
 n=max(len(c['ids']) for c in items);ids=torch.full((len(items),n),tokenizer.pad_token_id or tokenizer.eos_token_id,dtype=torch.long,device='cuda');labels=torch.full_like(ids,-100);mask=torch.zeros_like(ids)
 for i,c in enumerate(items):ids[i,:len(c['ids'])]=torch.tensor(c['ids'],device='cuda');labels[i,:len(c['labels'])]=torch.tensor(c['labels'],device='cuda');mask[i,:len(c['ids'])]=1
 return {'input_ids':ids,'labels':labels,'attention_mask':mask}
@torch.inference_mode()
def loss_on(net,cases,tokenizer):
 net.eval();total=0;count=0
 for at in range(0,len(cases),2):
  d=packed(cases[at:at+2],tokenizer);n=int((d['labels']!=-100).sum());total+=float(net(**d).loss)*n;count+=n
 return total/count
@torch.inference_mode()
def generation_metrics(net,cases,tokenizer,limit=12):
 from lmformatenforcer import JsonSchemaParser
 from lmformatenforcer.integrations.transformers import build_token_enforcer_tokenizer_data,build_transformers_prefix_allowed_tokens_fn
 net.eval();token_data=build_token_enforcer_tokenizer_data(tokenizer);selected=[]
 for kind in ('extraction','calcul','contexte'):selected.extend([c for c in cases if c['kind']==kind][:limit//3])
 valid=correct=0;details=[]
 for c in selected:
  prompt=tokenizer.apply_chat_template([{'role':'system','content':SYSTEM}]+c['messages'],tokenize=False,add_generation_prompt=True,enable_thinking=False);inputs=tokenizer(prompt,return_tensors='pt').to('cuda');prefix=build_transformers_prefix_allowed_tokens_fn(token_data,JsonSchemaParser(SCHEMA));ids=net.generate(**inputs,max_new_tokens=256,do_sample=False,prefix_allowed_tokens_fn=prefix,pad_token_id=tokenizer.eos_token_id);raw=tokenizer.decode(ids[0,inputs['input_ids'].shape[1]:],skip_special_tokens=True);answer=None
  try:answer=validate_response(loads(raw));valid+=1;correct+=answer['valeurs']==c['answer']['valeurs']
  except ValueError:pass
  details.append({'id':c['id'],'kind':c['kind'],'expected':c['answer']['valeurs'],'answer':answer})
 return {'cas':len(selected),'json_valides':valid,'valeurs_exactes':correct,'taux_json':valid/len(selected),'taux_valeurs':correct/len(selected),'details':details}
def wikipedia(tokenizer):
 source=json.loads((ROOT/'corpus/manifest.json').read_text(encoding='utf-8'));train=[];valid=[];documents=0;seen=set()
 for f in source['wikipedia']:
  taken=0
  for batch in pq.ParquetFile(f['path']).iter_batches(batch_size=64,columns=['id','text']):
   for row in batch.to_pylist():
    text=row['text'].strip()
    if len(text)<300:continue
    key=hashlib.sha256(text.encode()).hexdigest()
    if key in seen:continue
    seen.add(key);ids=tokenizer(text[:6000],add_special_tokens=False,truncation=True,max_length=512).input_ids
    if len(ids)<64:continue
    case={'id':'wiki:'+str(row['id']),'ids':ids,'labels':ids[:],'kind':'wikipedia'};(valid if int(key[:8],16)%10==0 else train).append(case);documents+=1;taken+=1
    if taken>=300:break
   if taken>=300:break
 return train,valid,documents
def run(steps=400):
 if not torch.cuda.is_available():raise RuntimeError('Un GPU CUDA est nécessaire pour ce cycle')
 torch.set_num_threads(4);random.seed(171026);torch.manual_seed(171026);folder=ROOT/'models/chat/cycle-0.2.0';folder.mkdir(parents=True,exist_ok=True);status={'etat':'en_cours','phase':'preparation','etapes':0,'objectif_etapes':steps,'objectif_gpu':80,'exemples_vus':0,'tokens_vus':0,'historique':[],'detail':'Préparation des dialogues, du JSON et des textes français'}
 def emit(**kw):status.update(kw);status.update(gpu=gpu(),date=time.strftime('%Y-%m-%dT%H:%M:%S'));atomic(ROOT/'results/language_status.json',status)
 emit();base=json.loads((ROOT/'models/chat_base.json').read_text(encoding='utf-8'));tokenizer=AutoTokenizer.from_pretrained(base['path'],local_files_only=True,trust_remote_code=False);tokenizer.pad_token=tokenizer.eos_token;train_raw=read('train');valid_raw=read('validation');train=[v for c in train_raw if (v:=encode(c,tokenizer)) is not None];valid=[v for c in valid_raw if (v:=encode(c,tokenizer)) is not None];wiki,wiki_valid,docs=wikipedia(tokenizer);emit(phase='reference',documents_prepares=docs,exemples_disponibles=len(train),exemples_ignores=len(train_raw)-len(train),detail='Mesure du modèle avant adaptation, sur la validation réservée')
 net=model(tokenizer);before=loss_on(net,valid,tokenizer);before_wiki=loss_on(net,wiki_valid[:64],tokenizer);baseline=generation_metrics(net,valid_raw,tokenizer);atomic(folder/'before.json',{'perte_validation':before,'perte_textes':before_wiki,'generation':baseline})
 config=LoraConfig(r=8,lora_alpha=16,lora_dropout=.05,target_modules=['q_proj','k_proj','v_proj','o_proj'],task_type='CAUSAL_LM');net=get_peft_model(net,config);net.enable_input_require_grads();net.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False});net.config.use_cache=False;optimizer=torch.optim.AdamW([p for p in net.parameters() if p.requires_grad],lr=1e-4,weight_decay=.01);best=before;best_step=0;began=time.monotonic();micro=2;accumulation=4;history=[];emit(phase='apprentissage',reference_perte=before,reference_valeurs=baseline['taux_valeurs'],parametres_appris=sum(p.numel() for p in net.parameters() if p.requires_grad),detail='Apprentissage français : dialogues, contexte, valeurs JSON et textes encyclopédiques')
 for step in range(1,steps+1):
  if (ROOT/'results/language-stop.json').exists():break
  net.train();optimizer.zero_grad(set_to_none=True);loss_total=0;torch.cuda.synchronize();compute_began=time.monotonic()
  for _ in range(accumulation):
   pool=wiki if random.random()<.2 else train;items=random.sample(pool,micro);batch=packed(items,tokenizer);loss=net(**batch).loss;loss_total+=float(loss.detach())/accumulation;(loss/accumulation).backward();status['exemples_vus']+=len(items);status['tokens_vus']+=int((batch['labels']!=-100).sum())
  torch.nn.utils.clip_grad_norm_(net.parameters(),1);optimizer.step();torch.cuda.synchronize();compute=time.monotonic()-compute_began
  # Approximate 80% duty cycle, with extra backoff if measured total use is high.
  measured=status.get('gpu',{}).get('utilisation',80);pause=compute*.25+(compute*.15 if measured>90 else 0);time.sleep(pause)
  if step%10==0:emit(etapes=step,perte=loss_total,secondes=round(time.monotonic()-began),detail=f"{status['exemples_vus']:,} exemples vus · charge GPU cible 80 %".replace(',',' '))
  if step%50==0 or step==steps:
   score=loss_on(net,valid,tokenizer);wiki_score=loss_on(net,wiki_valid[:64],tokenizer);point={'etape':step,'perte_apprentissage':loss_total,'perte_validation':score,'perte_textes':wiki_score};history.append(point);status['historique']=history
   if score<best and wiki_score<=before_wiki*1.15:best=score;best_step=step;net.save_pretrained(folder/'best',safe_serialization=True)
   emit(meilleure_perte=best,meilleure_etape=best_step);atomic(folder/'history.json',history)
 emit(phase='evaluation',detail='Vérification des valeurs JSON et du contexte avant activation');del net,optimizer;gc.collect();torch.cuda.empty_cache()
 from peft import PeftModel
 candidate=PeftModel.from_pretrained(model(tokenizer),folder/'best',is_trainable=False) if best_step else None;after=generation_metrics(candidate,valid_raw,tokenizer) if candidate is not None else baseline;accepted=best_step>0 and after['taux_valeurs']>=baseline['taux_valeurs'] and after['taux_json']>=baseline['taux_json'];report={'version':'0.2.0','avant':{'perte_validation':before,'generation':baseline},'apres':{'perte_validation':best,'generation':after},'active':accepted,'etape_selectionnee':best_step,'documents_prepares':docs,'exemples_vus':status['exemples_vus'],'tokens_vus':status['tokens_vus'],'objectif_gpu':80,'historique':history,'note':'Sélection sur validation ; évaluation finale des tests après la sélection. Les textes disponibles ne sont pas tous déjà appris.'}
 if candidate is not None:report['tests']=generation_metrics(candidate,read('test'),tokenizer,limit=24)
 if accepted:atomic(ROOT/'models/chat/active.json',{'path':str(folder/'best'),'version':'0.2.0','selection':'validation_loss_and_structured_values_non_regression','step':best_step})
 atomic(ROOT/'results/language_report.json',report);emit(etat='termine',phase='termine',adaptation_active=accepted,bilan=report,detail='Cycle terminé : adaptation française validée et activée' if accepted else 'Cycle terminé : base conservée, adaptation non retenue')
if __name__=='__main__':
 try:run()
 except Exception as e:
  import traceback;traceback.print_exc();atomic(ROOT/'results/language_status.json',{'etat':'erreur','erreur':str(e),'detail':'Entraînement interrompu ; le dernier modèle validé reste disponible.'});raise
