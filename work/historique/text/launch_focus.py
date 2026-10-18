from pathlib import Path
import os,sys,json,subprocess,shutil
from datetime import datetime
root=Path(r'C:\Users\gabor\code\text-comprehension')
result=root/'results'
archive=result/('before-focus-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
archive.mkdir()
for name in ('language_status.json','language_report.json'):
    if (result/name).exists():shutil.copyfile(result/name,archive/name)
env=os.environ.copy();env.update(PYTHONUTF8='1',TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS='4')
with (result/'focus-training.log').open('w',encoding='utf-8') as out,(result/'focus-training-error.log').open('w',encoding='utf-8') as err:
    p=subprocess.Popen([sys.executable,'-u','train_focus.py','--seconds','1800'],cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.CREATE_NEW_PROCESS_GROUP)
print(json.dumps({'pid':p.pid,'launched':datetime.now().astimezone().isoformat(),'seconds':1800,'archive':str(archive)}))
