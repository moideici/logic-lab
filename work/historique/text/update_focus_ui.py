from pathlib import Path
root=Path(r'C:\Users\gabor\code\text-comprehension')
p=root/'serve.py';s=p.read_text(encoding='utf-8')
s=s.replace('import argparse,json,threading','import argparse,json,threading,re')
s=s.replace("   reference=ROOT/'models/chat/cycle-0.2.0/before.json'", "   training=state('language_status.json');session=training.get('session','')\n   reference=ROOT/'models/chat'/session/'before.json' if re.fullmatch(r'focus-\\d{8}-\\d{6}',session) else ROOT/'models/chat/cycle-0.2.0/before.json'")
s=s.replace("'entrainement':state('language_status.json')", "'entrainement':training")
p.write_text(s,encoding='utf-8')
p=root/'web/bilan.js';s=p.read_text(encoding='utf-8')
old="$ ('steps')" # exact existing fragment below
old="$('steps').textContent=num(t.etapes||0)+' / '+num(t.objectif_etapes||400);$('steps-bar').max=t.objectif_etapes||400;$('steps-bar').value=t.etapes||0;"
new="if(t.duree_secondes){$('steps').textContent=num(t.etapes||0)+' étapes · '+Math.ceil((t.restant_secondes||0)/60)+' min restantes';$('steps-bar').max=t.duree_secondes;$('steps-bar').value=Math.min(t.duree_secondes,t.ecoule_secondes||0);}else{$('steps').textContent=num(t.etapes||0)+' / '+num(t.objectif_etapes||400);$('steps-bar').max=t.objectif_etapes||400;$('steps-bar').value=t.etapes||0;}"
assert old in s;s=s.replace(old,new);p.write_text(s,encoding='utf-8')
print('Timed progress and session-specific baseline installed')
