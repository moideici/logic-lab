from pathlib import Path
import shutil
R=Path(r'C:\Users\gabor\code\playi');S=Path(__file__).parent
p=R/'logic_arena/diversity.py';t=p.read_text(encoding='utf-8').replace("if game=='go':return digest([game,b,p,obs.get('go_state')])","if game=='go':return digest([game,min(transforms(b)),p,obs['go_state']['komi'],obs['go_state']['phase'],obs['go_state']['passes'],obs['go_state']['dead']])");p.write_text(t,encoding='utf-8')
shutil.copyfile(S/'train_go_cycle.py',R/'examples/train_go_cycle.py')
