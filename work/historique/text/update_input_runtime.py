from pathlib import Path
import shutil
R=Path(r'C:\Users\gabor\code\text-comprehension');S=Path(__file__).parent
for f in ('chat.py','telemetry.py'):shutil.copyfile(S/f,R/f)
p=R/'serve.py';t=p.read_text(encoding='utf-8').replace("self.send({'chat_pret':", "from telemetry import gpu_live\n   self.send({'gpu':gpu_live(),'chat_pret':");p.write_text(t,encoding='utf-8')
p=R/'web/bilan.js';t=p.read_text(encoding='utf-8').replace("const g=t.gpu||{}", "const g=v.gpu||t.gpu||{}");p.write_text(t,encoding='utf-8')
p=R/'.gitignore';t=p.read_text(encoding='utf-8')+'\nchat_cache/\ncorpus_cache/\n';p.write_text(t,encoding='utf-8')
p=R/'requirements.txt';t=p.read_text(encoding='utf-8')+'\npeft==0.17.1\npyarrow==21.0.0\nlm-format-enforcer==0.11.3\n';p.write_text(t,encoding='utf-8')
