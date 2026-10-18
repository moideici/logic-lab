import subprocess,time,threading
_cache={};_at=0;_lock=threading.Lock()
def gpu_live():
 global _at,_cache
 with _lock:
  if time.monotonic()-_at<2:return _cache
  try:
   r=subprocess.run(['nvidia-smi','--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=3,creationflags=subprocess.CREATE_NO_WINDOW);v=[int(x.strip()) for x in r.stdout.splitlines()[0].split(',')];_cache=dict(zip(('utilisation','memoire_mo','memoire_totale_mo','temperature'),v));_at=time.monotonic()
  except Exception:_cache={}
  return _cache
