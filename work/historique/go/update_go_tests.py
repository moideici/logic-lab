from pathlib import Path
import shutil
R=Path(r'C:\Users\gabor\code\playi');S=Path(__file__).parent
for p in (R/'tests').iterdir():
 if p.suffix not in ('.py','.mjs'):continue
 t=p.read_text(encoding='utf-8').replace('3055','4872').replace('3894','4259').replace('3042','4858').replace('3048','4864');t=t.replace("version,'5.0.0'","version,'6.0.0'").replace("['version'],'5.0.0'","['version'],'6.0.0'")
 if p.name=='test_strategy.py':t=t.replace("len(catalog()['games']),13","len(catalog()['games']),14")
 if p.name=='test_diversity.py':t=t.replace('len(first),39','len(first),42')
 p.write_text(t,encoding='utf-8')
for name in ('test_go.py','go.test.mjs'):shutil.copyfile(S/name,R/'tests'/name)
print('Go tests installed')
