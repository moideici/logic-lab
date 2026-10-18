"""Pinned French corpora. Large files stay in Parquet and are read in batches."""
from pathlib import Path
import concurrent.futures,hashlib,json,os,time
from huggingface_hub import hf_hub_download,snapshot_download
import pyarrow.parquet as pq
ROOT=Path(__file__).resolve().parent
def atomic(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
 for i in range(12):
  try:os.replace(tmp,p);return
  except PermissionError:time.sleep(.02*(i+1))
def main():
 sources=json.loads((ROOT/'sources.json').read_text(encoding='utf-8-sig'));state={'etat':'preparation','phase':'telechargement','fichiers':0,'octets':0,'documents':0};atomic(ROOT/'results/corpus_status.json',state);manifest={'sources':sources,'wikipedia':[],'dialogues':[],'licences':{'wikipedia':'CC-BY-SA-3.0 / GFDL','oasst2':'Apache-2.0'}}
 tasks=[(repo,f) for repo in ('OpenAssistant/oasst2','wikimedia/wikipedia') for f in sources[repo]['files']]
 def download(task):
  repo,f=task;path=hf_hub_download(repo,f['name'],repo_type='dataset',revision=sources[repo]['revision'],cache_dir=ROOT/'corpus_cache');return repo,f,Path(path)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
  for repo,f,path in pool.map(download,tasks):
   rows=pq.ParquetFile(path).metadata.num_rows;item={'path':str(path),'file':f['name'],'bytes':path.stat().st_size,'rows':rows,'revision':sources[repo]['revision']};manifest['wikipedia' if repo.endswith('wikipedia') else 'dialogues'].append(item);state['fichiers']+=1;state['octets']+=path.stat().st_size
   if repo.endswith('wikipedia'):state['documents']+=rows
   atomic(ROOT/'corpus/manifest.json',manifest);atomic(ROOT/'results/corpus_status.json',state);print(json.dumps(state),flush=True)
 state.update(etat='pret',phase='corpus_disponible');atomic(ROOT/'results/corpus_status.json',state)
def download_chat():
 sources=json.loads((ROOT/'sources.json').read_text(encoding='utf-8-sig'));folder=snapshot_download('Qwen/Qwen3-0.6B',revision=sources['Qwen/Qwen3-0.6B']['revision'],allow_patterns=['*.safetensors','*.json','*.txt','*.jinja'],cache_dir=ROOT/'chat_cache',max_workers=2);atomic(ROOT/'models/chat_base.json',{'path':folder,'repo':'Qwen/Qwen3-0.6B','revision':sources['Qwen/Qwen3-0.6B']['revision'],'licence':'Apache-2.0'});print('Chat model downloaded',flush=True)
if __name__=='__main__':
 import sys
 try:download_chat() if '--model' in sys.argv else main()
 except Exception as e:atomic(ROOT/'results'/('chat_download_error.json' if '--model'in sys.argv else 'corpus_status.json'),{'etat':'erreur','erreur':str(e)});raise
