from pathlib import Path
import json

root = Path(r'C:\Users\gabor\code\playi')
def edit(name, before, after):
    p=root/name
    text=p.read_text(encoding='utf-8')
    if before not in text:raise RuntimeError(f'Missing expected text in {name}: {before[:70]}')
    p.write_text(text.replace(before,after),encoding='utf-8')

manifest=root/'web/agents.json'
d=json.loads(manifest.read_text(encoding='utf-8'))
d['version']='0.6.0'
for identity in d['agents'].values():identity['version']='0.6.0'
d['version_aliases']=['6.0.0']
manifest.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
edit('pyproject.toml','version = "6.0.0"','version = "0.6.0"')
edit('web/index.html','6.0.0','0.6.0')
edit('logic_arena/general.py',"if (data.get('format'),data.get('version')) != ('garry-mlp-v3','6.0.0')", "if data.get('format')!='garry-mlp-v3' or data.get('version') not in (AGENT_VERSION,'6.0.0')")
edit('logic_arena/migration.py','import copy','import copy\nfrom .identity import AGENT_VERSION')
edit('logic_arena/migration.py',"version='6.0.0'","version=AGENT_VERSION")
edit('web/engine.js',"d.version==='6.0.0'","[AGENT_VERSION,'6.0.0'].includes(d.version)")
edit('web/engine.js',"games.length===6?'2.0.0':'6.0.0'","games.length===6?'2.0.0':AGENT_VERSION")
edit('web/migration.js',"export const LEGACY_GAMES", "import {AGENT_VERSION} from './agents.js';\nexport const LEGACY_GAMES")
edit('web/migration.js',"version:'6.0.0'","version:AGENT_VERSION")
for name in ('tests/garry.test.mjs','tests/new-games.test.mjs','tests/levels.test.mjs','tests/test_versions.py'):
    edit(name,"'6.0.0'","'0.6.0'")

p=root/'README.md'
text=p.read_text(encoding='utf-8')
oldintro=text[:text.index('## Historique de la 4.0.0')]
intro='''# Logic Lab — Garry 0.6.0

Garry utilise un seul modèle neuronal pour **quatorze jeux**, dont le **Go en 9 × 9, 13 × 13 et 19 × 19**. Son architecture est **4 872 → 48 → 48 → 4 259**, soit **444 979 paramètres**, avec des zones propres à chaque jeu et un module central commun. Les modèles figés dans `versions/` restent inchangés.

La version courante s’appelle désormais **0.6.0** : le projet reste en développement avant sa première version stable. Cette correction de numérotation ne modifie ni les dimensions ni les poids. Les exports historiques **6.0.0** sont compatibles et les prochains exports portent **0.6.0**. Les numéros décrivent les évolutions du code, jamais les performances. Les dossiers et rapports historiques conservent leur nom d’origine.

## Jouer et regarder les coups

Lancer `python -m logic_arena serve --port 8765`, puis ouvrir http://127.0.0.1:8765. En duel, les niveaux de **l’IA 1 et de l’IA 2** sont indépendants, de 0 à 10. Le navigateur affiche chaque transition, y compris au **2048**. Les styles changent les préférences stratégiques lorsque plusieurs coups restent admissibles ; une issue prouvée reste prioritaire.

Le Go gère les captures, le suicide interdit, le superko positionnel, le komi et l’abandon. Deux passes ouvrent le comptage ; chaque camp peut marquer les groupes morts, accepter ou reprendre. Les IA évitent les passes tant qu’elles trouvent une pose utile, puis acceptent automatiquement un comptage sans contestation. Une limite d’analyse de deux fois le nombre d’intersections les fait passer et compter : c’est une politique de l’IA, pas une règle ajoutée au Go. La qualité de ce consentement n’est pas une preuve de vie ou de mort des groupes.

Sudoku propose **Facile, Moyen, Difficile, Expert** : 45 grilles à solution unique, classées par un solveur fixe. Expert est le record du catalogue, sans prétendre être le sudoku le plus difficile du monde. En mode IA, Garry a **trois vies** : un chiffre faux laisse la case vide, ne sera pas rejoué à l’identique et coûte une vie ; la troisième erreur termine la partie. Un solveur du plateau public évalue les propositions, sans utiliser une solution privée. Les styles privilégient aussi des cases différentes.

Le taquin propose **3 × 3, 4 × 4 et 5 × 5**, avec quatre difficultés de grille. En 3 × 3, Expert demande exactement **31 coups** au minimum. Les niveaux 1 à 9 suivent le chemin optimal avec une probabilité croissante, de **55 % à 95 %** à chaque décision ; le niveau 10 choisit toujours un meilleur coup évalué, et le niveau 0 le pire. Les grandes grilles sont résolubles, mais leur recherche est bornée et leur difficulté maximale n’est pas certifiée. Sudoku et taquin restent jouables manuellement.

## Entraînement continu et jeux réels

L’onglet **Apprendre** lance une session locale bornée et montre son plateau en direct. Les nouveaux exemples sont séparés par familles entre apprentissage, validation et test. Un candidat doit préserver la validation fixe et récente avant installation ; les tests ne sélectionnent pas les poids. Les gains mesurés sont un accord avec un professeur borné, pas une garantie d’invincibilité. Le module central et les blocs des onze jeux antérieurs sont gelés lors des cycles Go, Hex et Gomoku.

Le premier cycle Go avait augmenté l’accord avec le professeur de **6,25 % à 23,75 %** sur 80 positions réservées. Le répertoire initial de cette étape contient **6 377 épreuves**. Les cycles continus consignent leurs propres exemples et résultats dans `training/continuous/` ; leurs promotions sont distinctes de la version logicielle.

L’onglet **Jeux réels** ouvre [2048 original](https://classic.play2048.co/) ou [COSUMI](https://www.cosumi.net/en/) dans un navigateur et joue avec les contrôles normaux du site. Chaque transition est vérifiée et reproduite en direct dans l’interface ; le navigateur conserve aussi une capture. COSUMI utilise le comptage japonais avec 6,5 points de komi : son résultat final fait foi, distinct du comptage de surface local. Une limite de coups ou une erreur du site ne compte jamais comme une partie terminée ou une victoire.

Pour le harnais réel : `npm ci --prefix tools/real-games`, puis `npx --prefix tools/real-games playwright install chromium`. Définir `PLAYWRIGHT_BROWSERS_PATH` si nécessaire. Le serveur Python est requis pour les routes `/api/external/` et `/api/continuous/` ; les duels locaux restent disponibles sur un hébergement statique.

Les sections ci-dessous conservent les résultats historiques sous leurs numéros d’origine. Elles ne constituent pas une garantie de performance de la version courante.

'''
text=intro+text[len(oldintro):]
start=text.index('Le modèle s\'appelle **garry**, affiché **Garry**, version actuelle')
end=text.index('\n\n',start)
text=text[:start]+"Le modèle s’appelle **garry**, affiché **Garry**, version actuelle **0.6.0** pour quatorze jeux. La série 0.x décrit les étapes de développement avant la version stable. Les évolutions de code et de dimensions déterminent les versions ; les résultats et compteurs d’entraînement restent séparés. L’ancien nom 6.0.0 est accepté comme alias de la même architecture. Les références 1.0.0 à 5.0.0 restent identifiables sous leurs noms historiques."+text[end:]
text=text.replace('garry-5.0.0.json','garry-0.6.0.json').replace('3.2.0 et 4.0.0, ou','3.2.0, 4.0.0, 5.0.0, 6.0.0 et 0.6.0, ou')
text=text.replace('Le modèle actuel totalise 299 377 paramètres.','Cette architecture historique totalisait 299 377 paramètres.')
text=text.replace('Les six modes utilisent ensuite les poids mis à jour.','Les quatorze modes utilisent ensuite les poids mis à jour.')
p.write_text(text,encoding='utf-8')
print('Version courante 0.6.0 installée ; aucun fichier de poids ou historique modifié.')
