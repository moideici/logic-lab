from pathlib import Path
R=Path(r'C:\Users\gabor\code\text-comprehension')
p=R/'serve.py';t=p.read_text(encoding='utf-8').replace("from telemetry import gpu_live\n   self.send({'gpu':", "from telemetry import gpu_live\n   reference=ROOT/'models/chat/cycle-0.2.0/before.json'\n   baseline=loads(reference.read_text(encoding='utf-8')) if reference.exists() else {}\n   self.send({'reference':baseline,'gpu':");p.write_text(t,encoding='utf-8')
p=R/'web/bilan.js';t=p.read_text(encoding='utf-8').replace('before=b.avant||{}','before=b.avant||v.reference||{}').replace("+' unités de texte apprises'","+' unités de texte traitées'");p.write_text(t,encoding='utf-8')
p=R/'web/input.js';t=p.read_text(encoding='utf-8').replace('${result.messages_utilises} messages de contexte','${result.messages_utilises} message${result.messages_utilises>1?\'s\':\'\'} de contexte');p.write_text(t,encoding='utf-8')
print('Baseline measurements visible during the running cycle')
