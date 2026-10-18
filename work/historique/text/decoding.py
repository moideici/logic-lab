"""Shared bounded JSON decoding with real token and first-token timings."""
import copy,json,time
import torch
from transformers import StoppingCriteria,StoppingCriteriaList
from lmformatenforcer import JsonSchemaParser
from lmformatenforcer.characterlevelparser import CharacterLevelParserConfig
from lmformatenforcer.integrations.transformers import build_transformers_prefix_allowed_tokens_fn
class CompleteObject(StoppingCriteria):
 def __init__(self,tokenizer,prompt_length):self.tokenizer=tokenizer;self.prompt_length=prompt_length;self.first=None
 def __call__(self,input_ids,scores,**kwargs):
  if self.first is None:self.first=time.perf_counter()
  text=self.tokenizer.decode(input_ids[0,self.prompt_length:],skip_special_tokens=True).strip()
  if not text.endswith('}'):return False
  try:obj=json.loads(text);return isinstance(obj,dict)
  except (ValueError,TypeError):return False
def generate_json(net,tokenizer,token_data,inputs,schema,*,sample=False,max_tokens=320,max_seconds=35):
 bounded=copy.deepcopy(schema);bounded['properties']['texte']['maxLength']=480
 parser=JsonSchemaParser(bounded,config=CharacterLevelParserConfig(max_consecutive_whitespaces=2));prefix=build_transformers_prefix_allowed_tokens_fn(token_data,parser);stop=CompleteObject(tokenizer,inputs['input_ids'].shape[1]);began=time.perf_counter()
 options={'do_sample':sample,'repetition_penalty':1.12}
 if sample:options.update(temperature=.7,top_p=.8,top_k=20)
 with torch.inference_mode():ids=net.generate(**inputs,max_new_tokens=max_tokens,max_time=max_seconds,prefix_allowed_tokens_fn=prefix,pad_token_id=tokenizer.eos_token_id,use_cache=True,stopping_criteria=StoppingCriteriaList([stop]),**options)
 elapsed=time.perf_counter()-began;tokens=ids[0,inputs['input_ids'].shape[1]:];raw=tokenizer.decode(tokens,skip_special_tokens=True).strip();first=(stop.first or time.perf_counter())-began;decode=elapsed-first
 return raw,{'tokens':len(tokens),'generation_ms':round(elapsed*1000),'premier_token_ms':round(first*1000),'tokens_par_seconde':round(len(tokens)/max(elapsed,.00001),1),'decodage_tokens_par_seconde':round(max(0,len(tokens)-1)/max(decode,.00001),1)}
