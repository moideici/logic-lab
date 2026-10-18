from pathlib import Path
import shutil,os,subprocess
R=Path(r'C:\Users\gabor\code\text-comprehension');S=Path(__file__).parent
for f in ('prepare_large.py','sources.json'):shutil.copyfile(S/f,R/f)
python=Path(r'C:\Users\gabor\code\logic-lab\work\text-env\Scripts\python.exe');env=dict(os.environ,PYTHONUTF8='1',TOKENIZERS_PARALLELISM='false')
for name,args in [('corpus',['prepare_large.py']),('chat-download',['prepare_large.py','--model'])]:
 with (R/'results'/f'{name}.log').open('wb')as out,(R/'results'/f'{name}-error.log').open('wb')as err:p=subprocess.Popen([str(python),'-u',*args],cwd=R,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.CREATE_NEW_PROCESS_GROUP);print(name,p.pid)
