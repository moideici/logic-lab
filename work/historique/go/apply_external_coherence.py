from pathlib import Path
root=Path(r'C:\Users\gabor\code\playi');stage=Path(__file__).parent
def edit(name,old,new):
 p=root/name;t=p.read_text(encoding='utf-8')
 if old not in t:raise RuntimeError(f'Absent {name}: {old[:100]}')
 p.write_text(t.replace(old,new),encoding='utf-8')
(root/'web/external-ui.js').write_text((stage/'external-ui-coherent.js').read_text(encoding='utf-8'),encoding='utf-8')
edit('web/index.html','<p>Garry utilise les flèches du clavier sur <a id="external-site-link"','<p id="external-description">Garry joue avec les commandes du site.</p><p><a id="external-site-link"')
edit('web/index.html','<label for="external-game">Jeu réel</label>','<label for="external-game">Jeu à lancer</label>')
edit('web/index.html','<div class="external-stat"><small>ACCORD AVEC L’ANALYSE APPROFONDIE</small>','<div id="external-probes"><div class="external-stat"><small>ACCORD AVEC L’ANALYSE APPROFONDIE</small>')
edit('web/index.html','Les parties ont des tirages différents.</p><a id="external-record"','Les parties ont des tirages différents.</p></div><a id="external-record" hidden')
edit('logic_arena/external.py',"steps=config.get('max_steps',650 if game=='go' else 10000)","steps=config.get('max_steps',1000 if game=='go' else 10000)")
edit('logic_arena/external.py',"result['id']=identifier;process=self.processes.get(identifier)","result['id']=identifier;process=self.processes.get(identifier)\n        if result['state'] in ACTIVE and process is None and (p/'status.json').is_file() and time.time()-(p/'status.json').stat().st_mtime>180:\n            result.update(state='error',error='Cette partie ne publie plus de coups depuis trois minutes. Relancez une nouvelle partie.')")
edit('web/index.html','cache de solution au sudoku','recherche des solutions sur le plateau public au sudoku')
edit('web/index.html','au sudoku, une solution planifiée exige une saisie par case vide.','au sudoku, les erreurs de l’IA coûtent une des trois vies et la troisième termine la partie.')
edit('web/index.html','Les niveaux 0 à 9 sélectionnent des rangs plus faibles parmi les coups évalués.','Les niveaux intermédiaires des puzzles varient la fréquence des meilleurs coups ; les autres jeux utilisent un rang parmi les coups évalués.')
print('Jeux réels : commandes et mesures adaptées au jeu, anciens processus détectés.')
