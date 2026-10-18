"""One timed training process at a time, independent of the browser tab."""
from pathlib import Path
import json,os,subprocess,sys,threading,time,uuid
ROOT=Path(__file__).resolve().parents[1]
class ContinuousTraining:
 def __init__(self,directory=None):self.directory=Path(directory or ROOT/'training/continuous');self.lock=threading.RLock();self.processes={}
 def list(self):
  if not self.directory.exists():return []
  out=[]
  for p in self.directory.glob('*/status.json'):
   try:
    d=json.loads(p.read_text(encoding='utf-8'));d['id']=p.parent.name
    process=self.processes.get(p.parent.name)
    if d['state']=='running' and ((process is not None and process.poll() is not None) or time.time()-p.stat().st_mtime>60):d.update(state='error',error='Le processus d’apprentissage s’est arrêté ; le dernier modèle accepté est conservé.')
    out.append(d)
   except (OSError,json.JSONDecodeError):continue
  return sorted(out,key=lambda d:d.get('started_at',''),reverse=True)
 def get(self,identifier=None):
  all=self.list();return next((s for s in all if s['id']==identifier),None) if identifier else next(iter(all),None)
 def start(self,seconds=3600,profile='balanced'):
  if profile not in ('balanced','weakness'):raise ValueError('Programme inconnu')
  if type(seconds)is not int or not 1<=seconds<=3600:raise ValueError('Durée entre 1 et 3600 secondes')
  with self.lock:
   if any(s['state']=='running' and time.time()-(self.directory/s['id']/'status.json').stat().st_mtime<60 for s in self.list()):raise ValueError('Une session continue est déjà active')
   identifier=uuid.uuid4().hex;p=self.directory/identifier;p.mkdir(parents=True);atomic={'id':identifier,'state':'running','phase':'starting','duration_seconds':seconds,'profile':profile,'started_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'remaining_seconds':seconds};(p/'status.json').write_text(json.dumps(atomic),encoding='utf-8')
   with (p/'process.log').open('wb')as stream:self.processes[identifier]=subprocess.Popen([sys.executable,'-m','logic_arena.targeted' if profile=='weakness' else 'logic_arena.continuous','--output',str(p),'--seconds',str(seconds)],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)|getattr(subprocess,'CREATE_NEW_PROCESS_GROUP',0))
   return self.get(identifier)
 def stop(self,identifier):
  if not self.get(identifier):raise ValueError('Session inconnue')
  (self.directory/identifier/'stop.json').write_text('{}',encoding='utf-8');return self.get(identifier)
