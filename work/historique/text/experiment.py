"""Independent French inference comparison. Tests are evaluated only after selection."""
from pathlib import Path
import argparse,collections,hashlib,json,os,random,re,statistics,time
os.environ.setdefault('TOKENIZERS_PARALLELISM','false')
import numpy as np
import psutil,torch
from torch import nn
from safetensors.torch import save_file,load_file
from transformers import AutoTokenizer,AutoModelForSequenceClassification
ROOT=Path(__file__).resolve().parent
LABELS=['confirme','contredit','indetermine'];MODEL='almanach/camembert-base';REVISION='a75967561c78f2aa81cc41045378d3b4ee25af9e'
SEEDS=[17,42,91];MAX_LENGTH=512
def write(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8');os.replace(tmp,p)
def read(split):return [json.loads(s) for s in (ROOT/'data'/f'{split}.jsonl').read_text(encoding='utf-8').splitlines()]
def seed_all(seed):random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
def byte_encode(cases):
 seqs=[];segments=[]
 for c in cases:
  a=list(c['premise'].encode());b=list(c['hypothesis'].encode());ids=[1]+[x+4 for x in a]+[2]+[x+4 for x in b]+[2]
  if len(ids)>MAX_LENGTH:raise ValueError('Texte trop long : aucune troncature silencieuse')
  seqs.append(ids);segments.append([0]*(len(a)+2)+[1]*(len(b)+1))
 n=max(map(len,seqs));x=torch.zeros((len(cases),n),dtype=torch.long);s=torch.zeros_like(x)
 for i,(ids,seg) in enumerate(zip(seqs,segments)):x[i,:len(ids)]=torch.tensor(ids);s[i,:len(ids)]=torch.tensor(seg)
 return {'input_ids':x,'segments':s,'attention_mask':x.ne(0)}
class ByteTransformer(nn.Module):
 def __init__(self):
  super().__init__();self.embedding=nn.Embedding(260,96,padding_idx=0);self.position=nn.Embedding(MAX_LENGTH,96);self.segment=nn.Embedding(2,96)
  layer=nn.TransformerEncoderLayer(96,4,384,dropout=.1,activation='gelu',batch_first=True,norm_first=True)
  self.encoder=nn.TransformerEncoder(layer,2,enable_nested_tensor=False);self.norm=nn.LayerNorm(96);self.head=nn.Linear(96,3)
 def forward(self,input_ids,segments,attention_mask):
  x=self.embedding(input_ids)+self.position(torch.arange(input_ids.shape[1],device=input_ids.device))+self.segment(segments)
  x=self.encoder(x,src_key_padding_mask=~attention_mask.bool());mask=attention_mask.unsqueeze(-1);return self.head(self.norm((x*mask).sum(1)/mask.sum(1)))
def tensors(cases,kind,tokenizer=None):
 if kind=='scratch':return byte_encode(cases)
 d=tokenizer([c['premise'] for c in cases],[c['hypothesis'] for c in cases],padding=True,truncation=False,return_tensors='pt')
 if d['input_ids'].shape[1]>MAX_LENGTH:raise ValueError('Texte trop long')
 return dict(d)
def batch(data,ids,device):
 d={k:v[ids].to(device) for k,v in data.items()};n=int(d['attention_mask'].sum(1).max());return {k:v[:,:n] for k,v in d.items()}
def logits(model,d,kind):return model(**d) if kind=='scratch' else model(**d).logits
@torch.inference_mode()
def predict(model,data,kind,device,batch_size=32):
 model.eval();out=[]
 for at in range(0,len(data['input_ids']),batch_size):
  with torch.autocast(device_type='cuda',dtype=torch.float16,enabled=device=='cuda'):z=logits(model,batch(data,slice(at,at+batch_size),device),kind)
  out.extend(z.float().softmax(-1).cpu().tolist())
 return out
def metrics(cases,probs):
 pred=[max(range(3),key=lambda j:p[j]) for p in probs];conf=[[0]*3 for _ in range(3)];families=collections.defaultdict(list);categories=collections.defaultdict(list);errors=[]
 for c,p,z in zip(cases,pred,probs):
  ok=p==c['label'];conf[c['label']][p]+=1;families[c['family']].append(ok);categories[c['category']].append(ok)
  if not ok and len(errors)<20:errors.append({**c,'prediction':LABELS[p],'probabilities':z})
 return {'accuracy':sum(pred[i]==c['label'] for i,c in enumerate(cases))/len(cases),'family_exact':sum(all(v) for v in families.values())/len(families),'by_category':{k:sum(v)/len(v) for k,v in categories.items()},'confusion':conf,'cases':len(cases),'errors':errors}
def make_model(kind,device):
 return (ByteTransformer() if kind=='scratch' else AutoModelForSequenceClassification.from_pretrained(MODEL,revision=REVISION,cache_dir=ROOT/'cache',num_labels=3,id2label=dict(enumerate(LABELS)),label2id={v:k for k,v in enumerate(LABELS)},trust_remote_code=False,use_safetensors=True)).to(device)
def train_one(kind,seed,train,valid,data,validation,device,epochs):
 seed_all(seed);model=make_model(kind,device);folder=ROOT/'models'/kind/str(seed);folder.mkdir(parents=True,exist_ok=True);opt=torch.optim.AdamW(model.parameters(),lr=3e-4 if kind=='scratch' else 2e-5,weight_decay=.01);scaler=torch.amp.GradScaler('cuda',enabled=device=='cuda');y=torch.tensor([c['label'] for c in train],device=device);best=-1;history=[];began=time.perf_counter();size=64 if kind=='scratch' else 16;peak=0
 if device=='cuda':torch.cuda.reset_peak_memory_stats()
 for epoch in range(epochs):
  model.train();order=torch.randperm(len(train));loss_sum=0
  for at in range(0,len(order),size):
   ids=order[at:at+size];d=batch(data,ids,device);opt.zero_grad(set_to_none=True)
   with torch.autocast(device_type='cuda',dtype=torch.float16,enabled=device=='cuda'):z=logits(model,d,kind);loss=nn.functional.cross_entropy(z,y[ids.to(device)])
   scaler.scale(loss).backward();scaler.unscale_(opt);nn.utils.clip_grad_norm_(model.parameters(),1);scaler.step(opt);scaler.update();loss_sum+=float(loss.detach())*len(ids)
  score=metrics(valid,predict(model,validation,kind,device))['accuracy'];history.append({'epoch':epoch+1,'train_loss':loss_sum/len(train),'validation_accuracy':score});peak=max(peak,psutil.Process().memory_info().rss)
  if score>best:
   best=score;selected_epoch=epoch+1;save_file({k:v.detach().cpu().contiguous() for k,v in model.state_dict().items()},str(folder/'model.safetensors'))
   if kind=='pretrained':model.config.save_pretrained(folder)
  write(ROOT/'results/status.json',{'state':'training','approach':kind,'seed':seed,'epoch':epoch+1,'epochs':epochs,'validation_accuracy':score,'best_validation_accuracy':best,'elapsed_run_seconds':time.perf_counter()-began})
  print(json.dumps({'kind':kind,'seed':seed,**history[-1]}),flush=True)
 result={'approach':kind,'seed':seed,'selected_epoch':selected_epoch,'validation_accuracy':best,'epochs':epochs,'examples_presented':epochs*len(train),'parameters':sum(p.numel() for p in model.parameters()),'training_seconds':time.perf_counter()-began,'peak_process_rss_bytes':peak,'peak_cuda_bytes':torch.cuda.max_memory_allocated() if device=='cuda' else 0,'history':history}
 write(folder/'training.json',result);del model,opt,scaler
 if device=='cuda':torch.cuda.empty_cache()
 return result
def hypothesis_baseline(train,valid,tests,device):
 words=lambda c:re.findall(r'\w+',c['hypothesis'].lower());vocab={w:i for i,w in enumerate(sorted({w for c in train for w in words(c)}))}
 def encode(cs):
  x=torch.zeros((len(cs),len(vocab)),device=device)
  for i,c in enumerate(cs):
   for w in words(c):
    if w in vocab:x[i,vocab[w]]+=1
  return x
 seed_all(17);model=nn.Linear(len(vocab),3).to(device);opt=torch.optim.AdamW(model.parameters(),lr=.03,weight_decay=.01);x=encode(train);y=torch.tensor([c['label'] for c in train],device=device);vx=encode(valid);best=-1;state=None
 for _ in range(200):
  opt.zero_grad();loss=nn.functional.cross_entropy(model(x),y);loss.backward();opt.step()
  with torch.no_grad():score=float((model(vx).argmax(-1)==torch.tensor([c['label'] for c in valid],device=device)).float().mean())
  if score>best:best=score;state={k:v.detach().clone() for k,v in model.state_dict().items()}
 model.load_state_dict(state)
 with torch.no_grad():return {s:metrics(c,model(encode(c)).softmax(-1).cpu().tolist()) for s,c in tests.items()}
def run():
 torch.set_num_threads(4);device='cuda' if torch.cuda.is_available() else 'cpu';train=read('train');valid=read('validation');runs=[];tokenizer=None
 write(ROOT/'results/status.json',{'state':'preparing','device':device})
 for kind in ('scratch','pretrained'):
  if kind=='pretrained':tokenizer=AutoTokenizer.from_pretrained(MODEL,revision=REVISION,cache_dir=ROOT/'cache',trust_remote_code=False);tokenizer.save_pretrained(ROOT/'models/tokenizer')
  data=tensors(train,kind,tokenizer);validation=tensors(valid,kind,tokenizer)
  for seed in SEEDS:runs.append(train_one(kind,seed,train,valid,data,validation,device,30 if kind=='scratch' else 4))
 # All selections are frozen before any reserved test is loaded.
 write(ROOT/'results/selections.json',runs);tests={s:read(s) for s in ('test_iid','test_rephrasing','test_new_names','test_composition')};report={'version':'0.1.0','language':'fr','scope':'controlled synthetic inference, not general language understanding','model':MODEL,'model_revision':REVISION,'torch':torch.__version__,'device':torch.cuda.get_device_name(0) if device=='cuda' else 'CPU','seeds':SEEDS,'data_manifest':json.loads((ROOT/'data/manifest.json').read_text(encoding='utf-8')),'runs':runs,'baseline_hypothesis_only':hypothesis_baseline(train,valid,tests,device)}
 for run in runs:
  kind=run['approach'];model=(ByteTransformer() if kind=='scratch' else AutoModelForSequenceClassification.from_config(__import__('transformers').AutoConfig.from_pretrained(ROOT/'models'/kind/str(run['seed'])))).to(device);model.load_state_dict(load_file(str(ROOT/'models'/kind/str(run['seed'])/'model.safetensors')));run['tests']={}
  for split,cases in tests.items():run['tests'][split]=metrics(cases,predict(model,tensors(cases,kind,tokenizer),kind,device))
  sample=tensors(valid[:1],kind,tokenizer)
  for _ in range(5):predict(model,sample,kind,device)
  if device=='cuda':torch.cuda.synchronize()
  began=time.perf_counter()
  for _ in range(50):predict(model,sample,kind,device)
  if device=='cuda':torch.cuda.synchronize()
  run['single_example_latency_ms']=(time.perf_counter()-began)*20;del model
  if device=='cuda':torch.cuda.empty_cache()
 report['summary']={kind:{s:{'accuracy_mean':statistics.mean(r['tests'][s]['accuracy'] for r in runs if r['approach']==kind),'accuracy_std':statistics.pstdev(r['tests'][s]['accuracy'] for r in runs if r['approach']==kind),'family_exact_mean':statistics.mean(r['tests'][s]['family_exact'] for r in runs if r['approach']==kind)} for s in tests} for kind in ('scratch','pretrained')}
 write(ROOT/'results/report.json',report);write(ROOT/'results/status.json',{'state':'completed','summary':report['summary']});print(json.dumps(report['summary']),flush=True)
if __name__=='__main__':
 try:run()
 except Exception as e:write(ROOT/'results/status.json',{'state':'error','error':str(e)});raise
