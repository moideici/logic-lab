from pathlib import Path
root=Path(r'C:\Users\gabor\code\playi');stage=Path(__file__).parent
(root/'web/game-ui-policy.js').write_text((stage/'game-ui-policy.js').read_text(encoding='utf-8'),encoding='utf-8')
p=root/'web/index.html';t=p.read_text(encoding='utf-8')
t=t.replace('<div id="style-options">','<p id="level-note" class="fine-print"></p><div id="style-options">',1)
t=t.replace('Un peu meilleur.<br>À chaque exemple.','Des poids qui changent.<br>Des progrès à mesurer.')
p.write_text(t,encoding='utf-8')
p=root/'web/app.js';t=p.read_text(encoding='utf-8');needle="$('level-title').textContent=policy.levelTitle;"
addition="""
 const probabilityPuzzle=['sudoku','sliding_puzzle'].includes(game.name)&&$('planning').checked&&+$('level').value>0&&+$('level').value<10;
 $('level-note').textContent=probabilityPuzzle?`${50+5*+$('level').value} % de meilleurs coups évalués à chaque décision ; les autres coups créent la difficulté.`:'Le niveau classe les coups évalués. Des niveaux différents peuvent choisir des coups de même qualité.';
"""
if needle not in t:raise RuntimeError('Level label absent')
p.write_text(t.replace(needle,needle+addition),encoding='utf-8')
p=root/'README.md';t=p.read_text(encoding='utf-8');needle='Le navigateur affiche chaque transition, y compris au **2048**.'
t=t.replace(needle,needle+' Les quatorze jeux disposent d’un mode humain : 2048 utilise les flèches ou ses boutons de direction ; le démineur se joue au clic. Les réglages IA sont masqués quand vous résolvez seul, et les styles sans effet pour le moteur choisi ne sont pas proposés. Le lien **Input** ouvre le projet séparé de français sur http://127.0.0.1:8766/.')
needle='Les tests ne sélectionnent pas les poids.'
t=t.replace(needle,needle+' Une quarantaine persistante exclut aussi tous les états déjà produits par les sessions précédentes, quel que soit leur lot, afin de conserver les anciennes réserves. Chaque nouvelle session utilise une graine distincte et consignée.')
t+='\nLe [bilan de cohérence 0.6.0](docs/GARRY-0.6-COHERENCE.md) décrit les contrôles disponibles, les vérifications et la protection des évaluations entre sessions.\n'
p.write_text(t,encoding='utf-8');print('Documentation et explications des niveaux actualisées.')
