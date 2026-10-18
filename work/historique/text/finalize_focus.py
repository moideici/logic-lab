from pathlib import Path
root=Path(r'C:\Users\gabor\code\text-comprehension')
p=root/'web/bilan.html';s=p.read_text(encoding='utf-8').replace('Mesures tous les 50 pas','Mesures périodiques').replace('La première mesure apparaîtra après 50 étapes.','La première mesure apparaîtra après une validation.');p.write_text(s,encoding='utf-8')
p=root/'web/bilan.js';s=p.read_text(encoding='utf-8').replace("$('run-detail').textContent=t.detail", "$('curve-state').textContent=t.duree_secondes?'Validation tous les 100 pas':'Validation tous les 50 pas';$('run-detail').textContent=t.detail");p.write_text(s,encoding='utf-8')
print('Measurement cadence matches the active training program')
