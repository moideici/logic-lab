from pathlib import Path
root=Path(r'C:\Users\gabor\code\playi');stage=Path(__file__).parent
for source,target in [('targeted.py','logic_arena/targeted.py'),('test_targeted.py','tests/test_targeted.py')]:(root/target).write_text((stage/source).read_text(encoding='utf-8'),encoding='utf-8')
def edit(name,old,new):
 p=root/name;t=p.read_text(encoding='utf-8')
 if old not in t:raise RuntimeError(f'Absent {name}: {old[:70]}')
 p.write_text(t.replace(old,new),encoding='utf-8')
edit('logic_arena/continuous_history.py','def historical_case_ids(directory,current):','def historical_case_ids(directory,current,progress=None):')
edit('logic_arena/continuous_history.py',"for folder in sorted(directory.iterdir()):", "for folder in sorted(directory.iterdir()):\n        if progress:progress()")
edit('logic_arena/continuous_history.py','for number,line in enumerate(stream,1):','for number,line in enumerate(stream,1):\n                    if progress and number%256==0:progress()')
edit('logic_arena/continuous_service.py','def start(self,seconds=3600):','def start(self,seconds=3600,profile=\'balanced\'):\n  if profile not in (\'balanced\',\'weakness\'):raise ValueError(\'Programme inconnu\')')
edit('logic_arena/continuous_service.py',"'duration_seconds':seconds,'started_at'", "'duration_seconds':seconds,'profile':profile,'started_at'")
edit('logic_arena/continuous_service.py',"[sys.executable,'-m','logic_arena.continuous'", "[sys.executable,'-m','logic_arena.targeted' if profile=='weakness' else 'logic_arena.continuous'")
edit('logic_arena/server.py',"set(data)<={'seconds'}:result=CONTINUOUS.start(data.get('seconds',3600))", "set(data)<={'seconds','profile'}:result=CONTINUOUS.start(data.get('seconds',3600),data.get('profile','balanced'))")
print('Programme ciblé indépendant installé, version et dimensions inchangées.')
