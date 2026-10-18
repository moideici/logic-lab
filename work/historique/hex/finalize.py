from pathlib import Path
import shutil,json,hashlib
R=Path(r'C:\Users\gabor\code\playi');S=Path(__file__).parent;O=S.parents[1]/'outputs'
shutil.copyfile(S/'score-array.js',R/'web/score-array.js')
p=R/'tools/real-games/external-2048.mjs';t=p.read_text(encoding='utf-8').replace("import {tileSearch}","import {scoreArraySearch} from '../../web/score-array.js';\nimport {tileSearch}");t=t.replace('const result=tileSearch(observation,legal,z,budget)',"const result=(Math.max(...observation.board.flat())>=16384?scoreArraySearch:tileSearch)(observation,legal,z,budget)");p.write_text(t,encoding='utf-8')
p=R/'tests/expansion.test.mjs';t=p.read_text(encoding='utf-8');t+='''
test('external score search preserves tiles beyond 32768 without packed overflow',()=>{
 const e=new Game('2048');e.board=[[32768,32768,2,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]];const before=e.obs(),d=decideScore(model,before,e.legal());assert.equal(d.info.method,'array_score_expectimax');assert(d.values.every(v=>Number.isFinite(v.quality[0])));assert.deepEqual(e.obs(),before);
});
test('Expert Sudoku is completed without undo at level ten',()=>{
 const e=new Game('sudoku',171,{difficulty:'expert'}),empty=e.board.flat().filter(v=>!v).length;for(let i=0;i<empty;i++){const d=chooseDecision(model,e.obs(),e.legal());assert(!d.action.undo);e.step(d.action);}assert(e.done);assert.equal(e.moves,empty);
});
''';p.write_text(t,encoding='utf-8')
old=json.loads((R/'versions/4.0.0/garry.json').read_text());now=json.loads((R/'web/models/garry.json').read_text());h=48
assert old['w1'][:2483*h]==now['w1'][:2483*h]
assert old['w1'][2483*h:2494*h]==now['w1'][3042*h:3053*h]
assert all(old['w2'][j*3617:(j+1)*3617]==now['w2'][j*3894:j*3894+3617] for j in range(h))
assert old['b1']==now['b1'] and old['b2']==now['b2'][:3617] and old['core']==now['core']
stats={'model_version':now['version'],'architecture':[3055,48,48,3894],'previous_eleven_preserved':True,'model_sha256':hashlib.sha256((R/'web/models/garry.json').read_bytes()).hexdigest(),'external':{},'training':json.loads((R/'training/competitive-5.0.0/report.json').read_text()),'strategy_selection':{}}
for name in ('full-score-01','network-01','random-01'):stats['external'][name]=json.loads((R/'training/external'/name/'status.json').read_text())
for name,s in json.loads((R/'training/strategy-cycle02/fit/selection.json').read_text()).items():stats['strategy_selection'][name]={'selected_epoch':s['best_epoch'],'reason':'No candidate passed all retention gates; previous weights kept'}
stats['tests']={'python':86,'javascript':47,'browser':json.loads((O/'verification-interface.json').read_text(encoding='utf-8'))}
(O/'garry-5-mesures.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf-8')
header='''# Logic Lab — Garry 5.0.0

Garry utilise un seul modèle neuronal pour **treize jeux**, avec l’ajout de **Hex 7 × 7** (règle d’échange) et du **Gomoku 15 × 15 Swap2** (cinq exacts). Ces jeux ont une scène de compétition ; l’interface propose des duels locaux. Garry ne joue pas encore de parties classées contre des humains en ligne.

L’architecture passe à **3 055 → 48 → 48 → 3 894**, soit **339 878 paramètres**. Cet agrandissement justifie la version majeure 5.0.0. Les poids des onze jeux précédents, le module commun, l’évaluateur de Puissance 4 et sa mémoire de recherche sont conservés exactement. La référence précédente est figée dans `versions/4.0.0/`.

Sudoku propose **Facile, Moyen, Difficile, Expert** : 45 grilles vérifiées à solution unique, classées par un solveur fixe. Expert sélectionne le record du catalogue (une grille), sans prétendre définir le sudoku le plus difficile du monde. Le taquin propose **3 × 3, 4 × 4 et 5 × 5**, avec les quatre difficultés. Expert 3 × 3 exige exactement **31 coups**, maximum certifié par l’exploration exhaustive des états résolubles. Les grandes grilles sont toujours résolubles ; leur difficulté repose sur un mélange légal et une borne de Manhattan. Leur maximum absolu n’est pas certifié. Leur recherche A* n’utilise que le plateau public et annonce explicitement si elle trouve un chemin minimal. Les nouvelles tailles utilisent une représentation de 81 caractéristiques ; leurs poids neuronaux n’ont pas encore été entraînés spécifiquement. Sudoku et taquin sont jouables manuellement.

L’onglet **Jeux réels** ouvre le site original de 2048 dans un navigateur et utilise les flèches du clavier. Le score, les apparitions et les transitions sont vérifiés à partir de l’affichage. Une partie complète a obtenu **71 496 points**, une tuile **4096**, et **3 277 coups vérifiés**. Les comparaisons réseau seul (1 112) et hasard (584) ne portent que sur une partie chacune et des tirages différents. La recherche continue après 2048 et conserve une représentation exacte des grandes tuiles.

Pour le harnais réel : `npm ci --prefix tools/real-games`, puis `npx --prefix tools/real-games playwright install chromium`. Définir `PLAYWRIGHT_BROWSERS_PATH` si les navigateurs sont installés dans un dossier particulier. Lancer `python -m logic_arena serve --port 8765`, puis ouvrir http://127.0.0.1:8765. L’adaptateur ne fonctionne pas depuis un simple hébergement statique. Les nouvelles routes sont `/api/external/list`, `/status?id=…`, `/image?id=…`, `/trace?id=…`, POST `/start` et POST `/stop`.

Le premier entraînement séparé atteint **44 %** d’accord avec le professeur sur 50 positions Hex réservées (24 % avant), et **10 %** sur 50 positions Gomoku réservées (0 % avant). Ces taux ne sont pas des taux de victoire et le professeur est borné. Le cycle supplémentaire dames/Percée n’a retenu aucun candidat, pour préserver les compétences contrôlées. Le répertoire contient maintenant **5 717 épreuves d’apprentissage**. Les tests et validations réservés n’y sont pas inclus.

Vérification : **86 tests Python et 47 tests JavaScript**, plus les parcours navigateur sur ordinateur et mobile (duels, tailles, coups manuels, sudoku et lancement/arrêt du vrai 2048). Les niveaux de Garry restent indépendants des difficultés de grille et vont de 0 à 10. Aucune invincibilité universelle n’est annoncée pour les nouveaux jeux.

Règles et compétition : [Hex](https://www.hexwiki.net/index.php/Rules), [championnats Little Golem](https://docs.littlegolem.net/tournaments/calendar/), [Gomoku et Swap2](https://gomoku.renju.net/gomokurules/), [Brno Cup Swap2](https://gomoku.renju.net/tournament/3533/). Site testé : [2048 original](https://classic.play2048.co/).

## Historique de la 4.0.0

'''
p=R/'README.md';t=p.read_text(encoding='utf-8');t=t[t.index('## Nouveautés de la 4.0.0'):];t=t.replace('## Nouveautés de la 4.0.0','### Nouveautés de la 4.0.0',1);t=t.replace('## Architecture actuelle et fusion historique','## Architecture historique et fusion').replace('Les onze modes sont des vues','Les modes sont des vues').replace('Le modèle s\'appelle **garry**, affiché **Garry**, version **4.0.0** pour les onze modes.','Le modèle s\'appelle **garry**, affiché **Garry**, version actuelle **5.0.0** pour treize modes.').replace('garry-4.0.0.json','garry-5.0.0.json');p.write_text(header+t,encoding='utf-8')
print('Reports and docs prepared')
