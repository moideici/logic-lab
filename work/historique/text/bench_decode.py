import sys,time,json,torch
from pathlib import Path
R=Path(r'C:\Users\gabor\code\text-comprehension');sys.path.insert(0,str(R))
import chat
from lmformatenforcer import JsonSchemaParser
from lmformatenforcer.integrations.transformers import build_transformers_prefix_allowed_tokens_fn
torch.set_num_threads(4);began=time.perf_counter();m=chat.model();load=time.perf_counter()-began;tok=m['tokenizer'];history=[];rows=[]
for text in ['bonjour ! tu fonctionne','hey ! ça va ??','Quelle est ta phrase préférée ?']:
 history.append({'role':'user','content':text});prompt=tok.apply_chat_template([{'role':'system','content':chat.SYSTEM}]+history,tokenize=False,add_generation_prompt=True,enable_thinking=False);inp=tok(prompt,return_tensors='pt').to(m['device']);fn=build_transformers_prefix_allowed_tokens_fn(m['tokens'],JsonSchemaParser(chat.SCHEMA));count=0;seconds=0.
 def prefix(batch,ids):
  global count,seconds
  t=time.perf_counter();v=fn(batch,ids);seconds+=time.perf_counter()-t;count+=1;return v
 torch.cuda.synchronize();start=time.perf_counter()
 with torch.inference_mode():ids=m['net'].generate(**inp,max_new_tokens=256,do_sample=False,prefix_allowed_tokens_fn=prefix,pad_token_id=tok.eos_token_id,use_cache=True)
 torch.cuda.synchronize();elapsed=time.perf_counter()-start;output=ids[0,inp['input_ids'].shape[1]:];raw=tok.decode(output,skip_special_tokens=True);history.append({'role':'assistant','content':raw});rows.append({'prompt':text,'device':m['device'],'tokens':len(output),'seconds':elapsed,'tokens_per_second':len(output)/elapsed,'prefix_seconds':seconds,'raw_tail':repr(raw[-100:]),'answer':raw});print(json.dumps(rows[-1],ensure_ascii=False),flush=True)
Path('outputs/input-decodage-avant.json').write_text(json.dumps({'load_seconds':load,'cases':rows},ensure_ascii=False,indent=2),encoding='utf-8')
