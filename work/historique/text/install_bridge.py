from pathlib import Path
import shutil
root=Path(r'C:\Users\gabor\code\text-comprehension');source=Path(__file__).parent
for name,target in (('bridge.py','bridge.py'),('test_bridge.py','tests/test_bridge.py'),('test_decoding.py','tests/test_decoding.py'),('BRIDGE.md','BRIDGE.md')):
    shutil.copyfile(source/name,root/target)
p=root/'README.md';s=p.read_text(encoding='utf-8')
s=s.replace('Pendant l’apprentissage, la conversation utilise le CPU pour laisser la mémoire graphique au cycle.', 'La conversation reste sur le GPU pendant l’apprentissage ; les deux processus partagent sa mémoire et leur débit peut diminuer pendant les calculs simultanés.')
if '[passerelle' not in s:
    s+='\n## Direction : passerelle de langage\n\nLe [contrat provisoire de passerelle](BRIDGE.md) prépare la conversion français → requête JSON structurée → modèle de raisonnement → résultat JSON → français. Aucun second modèle n’est connecté. La validation du contrat est distincte de l’apprentissage de cette traduction.\n\n`python train_focus.py --seconds 1800` lance le programme ciblé de trente minutes. Il mesure une référence, travaille les nombres, les champs JSON et le contexte en conservant du français, puis sélectionne uniquement sur la validation avant des tests réservés. Son manifeste est figé dans le dossier de session ; le bilan affiche le temps et les exemples réellement traités.\n'
p.write_text(s,encoding='utf-8')
p=root/'web/bilan.js';s=p.read_text(encoding='utf-8')
s=s.replace("Math.ceil((t.restant_secondes||0)/60)","Math.ceil(Math.max(0,t.etat==='termine'?0:(Date.parse(t.fin_prevue)-Date.now())/1000)/60)")
s=s.replace("Math.min(t.duree_secondes,t.ecoule_secondes||0)","Math.min(t.duree_secondes,Math.max(0,t.duree_secondes-(Date.parse(t.fin_prevue)-Date.now())/1000))")
p.write_text(s,encoding='utf-8')
print('Provisional bridge contract installed, no external backend connected')
