# Logic Lab — Garry 0.6.0

Garry utilise un seul modèle neuronal pour **quatorze jeux**, dont le **Go en 9 × 9, 13 × 13 et 19 × 19**. Son architecture est **4 872 → 48 → 48 → 4 259**, soit **444 979 paramètres**, avec des zones propres à chaque jeu et un module central commun. Les modèles figés dans `versions/` restent inchangés.

La version courante s’appelle désormais **0.6.0** : le projet reste en développement avant sa première version stable. Cette correction de numérotation ne modifie ni les dimensions ni les poids. Les exports historiques **6.0.0** sont compatibles et les prochains exports portent **0.6.0**. Les numéros décrivent les évolutions du code, jamais les performances. Les dossiers et rapports historiques conservent leur nom d’origine.

## Jouer et regarder les coups

Lancer `python -m logic_arena serve --port 8765`, puis ouvrir http://127.0.0.1:8765. En duel, les niveaux de **l’IA 1 et de l’IA 2** sont indépendants, de 0 à 10. Le navigateur affiche chaque transition, y compris au **2048**. Les quatorze jeux disposent d’un mode humain : 2048 utilise les flèches ou ses boutons de direction ; le démineur se joue au clic. Les réglages IA sont masqués quand vous résolvez seul, et les styles sans effet pour le moteur choisi ne sont pas proposés. Le lien **Input** ouvre le projet séparé de français sur http://127.0.0.1:8766/. Les styles changent les préférences stratégiques lorsque plusieurs coups restent admissibles ; une issue prouvée reste prioritaire.

Le Go gère les captures, le suicide interdit, le superko positionnel, le komi et l’abandon. Deux passes ouvrent le comptage ; chaque camp peut marquer les groupes morts, accepter ou reprendre. Les IA évitent les passes tant qu’elles trouvent une pose utile, puis acceptent automatiquement un comptage sans contestation. Une limite d’analyse de deux fois le nombre d’intersections les fait passer et compter : c’est une politique de l’IA, pas une règle ajoutée au Go. La qualité de ce consentement n’est pas une preuve de vie ou de mort des groupes.

Sudoku propose **Facile, Moyen, Difficile, Expert** : 45 grilles à solution unique, classées par un solveur fixe. Expert est le record du catalogue, sans prétendre être le sudoku le plus difficile du monde. En mode IA, Garry a **trois vies** : un chiffre faux laisse la case vide, ne sera pas rejoué à l’identique et coûte une vie ; la troisième erreur termine la partie. Un solveur du plateau public évalue les propositions, sans utiliser une solution privée. Les styles privilégient aussi des cases différentes.

Le taquin propose **3 × 3, 4 × 4 et 5 × 5**, avec quatre difficultés de grille. En 3 × 3, Expert demande exactement **31 coups** au minimum. Les niveaux 1 à 9 suivent le chemin optimal avec une probabilité croissante, de **55 % à 95 %** à chaque décision ; le niveau 10 choisit toujours un meilleur coup évalué, et le niveau 0 le pire. Les grandes grilles sont résolubles, mais leur recherche est bornée et leur difficulté maximale n’est pas certifiée. Sudoku et taquin restent jouables manuellement.

## Entraînement continu et jeux réels

L’onglet **Apprendre** lance une session locale bornée et montre son plateau en direct. Les nouveaux exemples sont séparés par familles entre apprentissage, validation et test. Un candidat doit préserver la validation fixe et récente avant installation ; les tests ne sélectionnent pas les poids. Les gains mesurés sont un accord avec un professeur borné, pas une garantie d’invincibilité. Le module central et les blocs des onze jeux antérieurs sont gelés lors des cycles Go, Hex et Gomoku.

Le premier cycle Go avait augmenté l’accord avec le professeur de **6,25 % à 23,75 %** sur 80 positions réservées. Le répertoire initial de cette étape contient **6 377 épreuves**. Les cycles continus consignent leurs propres exemples et résultats dans `training/continuous/` ; leurs promotions sont distinctes de la version logicielle.

L’onglet **Jeux réels** ouvre [2048 original](https://classic.play2048.co/) ou [COSUMI](https://www.cosumi.net/en/) dans un navigateur et joue avec les contrôles normaux du site. Chaque transition est vérifiée et reproduite en direct dans l’interface ; le navigateur conserve aussi une capture. COSUMI utilise le comptage japonais avec 6,5 points de komi : son résultat final fait foi, distinct du comptage de surface local. Une limite de coups ou une erreur du site ne compte jamais comme une partie terminée ou une victoire.

Pour le harnais réel : `npm ci --prefix tools/real-games`, puis `npx --prefix tools/real-games playwright install chromium`. Définir `PLAYWRIGHT_BROWSERS_PATH` si nécessaire. Le serveur Python est requis pour les routes `/api/external/` et `/api/continuous/` ; les duels locaux restent disponibles sur un hébergement statique.

Les sections ci-dessous conservent les résultats historiques sous leurs numéros d’origine. Elles ne constituent pas une garantie de performance de la version courante.

## Historique de la 4.0.0

### Nouveautés de la 4.0.0

Les cinq nouveaux jeux sont jouables et intégrés à l’apprentissage. Les dames gèrent les rafles maximales obligatoires, les prises arrière des pions, les dames à longue portée, les promotions et les nulles. Percée propose des courses de pions et des captures diagonales. Les nouveaux modes reçoivent leurs propres entrées et actions dans les matrices communes : **2 494 → 48 → 48 → 3 617**, 299 377 paramètres. Cet agrandissement justifie la version majeure.

Les premiers duels du réseau seul contre les nouveaux blocs initialisés donnent 7 victoires et 1 nulle aux dames, puis 8 victoires à Percée. Ce sont des échantillons limités. Les poids utilisés par les modes précédents sont conservés exactement pendant cette première campagne. Les anciens exports sont migrés ; dans l’interface, les nouvelles capacités entraînées sont ajoutées aux modèles personnels. Le répertoire contient 4 757 épreuves.

Le [rapport des nouveaux jeux](docs/GARRY-4-NOUVEAUX-JEUX.md) détaille règles, apprentissages, résultats et limites, notamment les premiers résultats mixtes du réseau seul à Nim et Lights Out. Les niveaux restent réglables de 0 à 10. La suite de vérification compte 114 tests réussis.

Les sections historiques ci-dessous décrivent les étapes précédentes ; leurs duels ne constituent pas une garantie d’invincibilité sur les nouveaux jeux.

## Historique 3.2.0 : zéro défaite depuis le plateau vide

Garry **3.2.0** passe les duels demandés contre la **3.1.0 figée**, dans les deux camps, aux réglages de niveau 10 : **une victoire, une nulle, zéro défaite**. Il gagne aussi les deux duels contre la 1.0.0 originale. Les répétitions et limites sont détaillées dans [le rapport zéro défaite](docs/GARRY-ZERO-DEFAITE.md) ; ce résultat ne promet pas l’invincibilité contre toutes les stratégies ou depuis toutes les positions.

La nouvelle recherche distingue les issues prouvées des estimations, et les coups dont la non-défaite est établie. Sept entrées d’ouverture voyagent dans le fichier du modèle, dont une réponse choisie par expérience et six coups certifiés. Les poids et dimensions du réseau sont préservés. **3.2.0 correspond à ces nouvelles fonctions compatibles**, sans changement d’architecture neuronale.

## Historique : le répertoire de la 3.1.0

La version **3.1.0** propose un magasin de **3,917 épreuves** pour les six jeux, sans changer l’architecture. Le dernier cycle réunit 18,440 positions d’apprentissage, de validation et de test, dont 12,288 nouveaux états pour les cinq jeux autres que le morpion. Les anciens exemples d’apprentissage sont aussi rejoués pour limiter les oublis.

Les poids retenus au cours de ce cycle concernent : taquin. Les candidats qui reculent sur les compétences contrôlées ou sur les parties complètes sont écartés. Le module commun et l’évaluateur de Puissance 4 sont préservés. La révision d’entraînement est **20261016-repertoire-02** ; la version logicielle de ce cycle était **3.1.0**.

Les résultats et limites sont détaillés dans [le dernier rapport d’entraînement](docs/GARRY-ENTRAINEMENT-CYCLE02.md). Le [premier rapport de diversité](docs/GARRY-DIVERSITE.md) conserve les résultats du cycle précédent. Les progrès du réseau seul sont distingués des victoires avec planification. L’entraînement enseigne plusieurs bonnes réponses quand elles existent ; les épreuves réservées restent exclues du magasin et des mises à jour.

## Niveau 10 : recherche renforcée

Garry vise 20 demi-coups au Puissance 4, puis poursuit si le temps le permet, avec deux secondes par décision. Sur les cinq sondes locales, il atteint notamment 21 demi-coups depuis le départ et 28 après six coups. La profondeur effectivement terminée est affichée séparément de la cible.

Sur les mêmes 40 duels, aux mêmes budgets et face à la même référence figée, Garry 2.0.0 obtient 30 victoires, 6 défaites et 4 nuls ; Garry 3.0.0 obtient 32 victoires, 3 défaites et 5 nuls. Sur ces départs imposés historiques, le zéro défaite n’était pas atteint. Les détails, limites et commandes de reproduction sont dans [le rapport de progression](docs/GARRY-3-PROGRESSION.md).

Les niveaux vont de 0 à 10 : le niveau 0 choisit le pire coup évalué, les niveaux intermédiaires sélectionnent des rangs, le niveau 10 recherche directement le meilleur coup. Une recherche bornée ne prouve pas la qualité absolue de tous les coups.

## Architecture historique et fusion

```text
Observation publique + identifiant du jeu
                 ↓
  encodeur unique : 2 494 → 48, tanh
                 ↓
  module central : 48 → 48, tanh
                 ↓
  sortie unique : 48 → 3 617
                 ↓
  masque des actions légales du jeu
```

Une branche de valeur supplémentaire de 32 coefficients évalue les positions de Puissance 4 dans la recherche. Elle est apprise par distillation d’un moteur figé et sauvegardée dans le même fichier ; la politique principale conserve ses dimensions. Cette architecture historique totalisait 299 377 paramètres.

Les modes sont des vues sur **les mêmes matrices** en mémoire. Un seul encodeur, un seul biais d'entrée, un seul module central, une seule matrice de sortie, un optimiseur Adam pour la politique dans Python et un seul fichier de sauvegarde atomique. Les vues ne possèdent aucun poids autonome. La branche linéaire de valeur est ajustée séparément par régression régularisée.

La fusion historique de la 2.0.0 est algébrique : 1 906 caractéristiques réparties en zones propres aux jeux et six indicateurs de jeu forment l'entrée. Les biais des anciens encodeurs sont intégrés aux lignes correspondant à ces indicateurs. Les sorties sont réunies dans la matrice globale de 818 actions. Le jeu sélectionne les caractéristiques et les actions autorisées. Cette architecture conditionnée conserve les savoirs existants ; elle ne prouve pas une généralisation à un jeu inconnu. Les biais communs et le module central permettent le transfert entre tâches ; l'entraînement répète les autres jeux pour limiter l'oubli.

La vérification de fusion porte sur **1 223 positions** : les 1 223 choix gloutons sont conservés, avec un écart maximal de logits de `3,82e-6`. Aucun réentraînement n'a été effectué pendant la fusion. Rapport : `web/models/garry-fusion.json`.

## Nom et versions

Le modèle s’appelle **garry**, affiché **Garry**, version actuelle **0.6.0** pour quatorze jeux. La série 0.x décrit les étapes de développement avant la version stable. Les évolutions de code et de dimensions déterminent les versions ; les résultats et compteurs d’entraînement restent séparés. L’ancien nom 6.0.0 est accepté comme alias de la même architecture. Les références 1.0.0 à 5.0.0 restent identifiables sous leurs noms historiques.

`versions/3.2.0/` conserve le modèle avant l’agrandissement aux onze jeux. `versions/3.1.0/` conserve le moteur et les poids précédant la recherche certifiée. `versions/3.0.0/` conserve les poids et le moteur avant ce cycle de diversité. `versions/2.0.0/` conserve aussi les poids et le moteur compilé précédents, avec empreintes. `versions/1.0.0/` conserve les IA locales présentes à la fin du travail précédent, avec un manifeste SHA-256 vérifié par les tests.

## Démarrer et apprendre

Python 3.11+, NumPy et Wasmtime ; Node.js 22+ pour les tests JavaScript.

```bash
python -m pip install -e .
python -m logic_arena serve --port 8000
```

Ouvrir http://127.0.0.1:8000. La plateforme fonctionne aussi sur un hébergement statique : calcul et apprentissage restent locaux. Les sessions du navigateur et du serveur Python sont distinctes. IndexedDB utilise une seule clé pour Garry dans une base dédiée. L'export produit un seul fichier `garry-0.6.0.json`. L’import accepte les formats Garry 2.0.0, 3.0.0, 3.1.0, 3.2.0, 4.0.0, 5.0.0, 6.0.0 et 0.6.0, ou une ancienne suite complète de six modèles dont les poids centraux concordent. Les anciennes données du navigateur restent dans leur base d'origine.

```bash
python -m logic_arena train --game tictactoe --episodes 30 --epochs 10 --output trained-models
python -m logic_arena evaluate --game tictactoe --models trained-models --episodes 100
python -m logic_arena evaluate --game sudoku --planning --max-steps 100
python examples/fuse_garry.py --output training-data/garry-initial.json
```

L'entraînement sauvegarde `trained-models/garry.json` et son rapport. Les quatorze modes utilisent ensuite les poids mis à jour. `--models` accepte le dossier ou le fichier Garry. La commande de fusion recrée les poids initiaux depuis la référence figée.

### Entraînement et révision des poids du 16 octobre 2026

La politique de la révision `20261016-c4-guarded-01`, entraînée avant la branche de valeur, est conservée dans le modèle actif. Ce premier entraînement ne modifiait pas l’architecture 2.0.0. Sur 200 parties de Puissance 4 contre un adversaire aléatoire, le réseau seul passe de 127 à 144 victoires et de 72 à 56 défaites. Les poids effectifs des cinq autres modes sont strictement préservés. Sur 40 duels de contrôle contre la référence figée, le système avec recherche obtient les mêmes résultats avant/après : 30 victoires, 6 défaites, 4 nuls. Aucun gain du système hybride n'est donc démontré par ce lot.

Le rapport `web/models/garry-training.json` identifie les poids par leurs empreintes, séparément du numéro de version. Les mesures de fusion ci-dessus décrivent les poids initiaux, avant cet apprentissage. Le diagnostic et le plan d'évolution sont dans `docs/GARRY-PROGRESSION.md`.

L'entraînement commun dispose d'un outil dédié avec positions dédupliquées, validation sans chevauchement exact et séparation des symétries du morpion. Il conserve les candidats séparément du modèle actif. L'adaptation ciblée gèle les paramètres des autres jeux ; elle doit ensuite passer les contrôles de jeu avant installation.

```bash
python examples/train_garry_curriculum.py --output training-runs/session --samples 4096 --validation-samples 512 --epochs 60 --learning-rate 0.0001
python examples/train_garry_guarded.py --dataset training-runs/session/dataset.npz --output training-runs/guarded --game connect4 --epochs 40
```

Les dossiers contiennent `before.json`, `best.json`, les rapports et le statut. Un dépassement de la limite de coups ne compte pas comme un progrès ; la sélection surveille aussi les scores des jeux non résolus. Le gel ciblé protège les acquis, et ne remplace pas une méthode d'apprentissage commun à long terme.

## Niveau de jeu et objectif zéro défaite

Les scores de Garry guident les solveurs locaux : minimax exact au morpion, table exacte des 181 440 taquins résolubles, recherche/cache au sudoku, expectimax à 2048 et contraintes publiques au démineur. Ces solveurs sont des composants du programme, distincts des poids appris.

Puissance 4 utilise une recherche en bitboards compilée en WebAssembly et partagée entre Python et le navigateur : menaces immédiates, coups sûrs, doubles menaces, table de transpositions bornée, approfondissement progressif et prolongement des réponses forcées. Un repli reste disponible sans WebAssembly. Le niveau 10 autorise jusqu'à 30 millions de nœuds et 300 ms coopératives pour ce jeu. Les autres jeux gardent leurs propres budgets. Les workers conservent la réactivité de l'interface.

**L'objectif de 0 % de défaite n'est pas atteint.** Rapport : `web/models/garry-evaluation.json`.

| Jeu | Résultat de Garry sur le lot de 20 |
|---|---|
| Morpion contre la référence | 20 nuls, aucune défaite |
| Puissance 4 contre la référence | 13 victoires, 6 défaites, 1 nul |
| 2048 | 20 réussites |
| Sudoku | 20 réussites |
| Démineur | 18 réussites, 2 échecs |
| Taquin | 20 réussites |

Les duels alternent les camps et rejouent les ouvertures ; Puissance 4 commence par six coups aléatoires. Le benchmark donne 3 millions de nœuds à Garry et 5 000 à la référence, avec un plafond de sécurité de dix secondes : les budgets diffèrent, ce n'est pas une comparaison à temps égal. Les jeux solo sont rejoués sur les mêmes graines ; leurs échecs sont distingués des régressions de réussite/score par rapport à la référence. Aucune régression solo n'a été observée sur ce lot. Ces petits échantillons ne sont ni un classement Elo ni une garantie pour toutes les positions. Les budgets muraux et les arrondis peuvent modifier les décisions selon la machine.

```bash
node examples/benchmark_garry.mjs --episodes 20 --seed 1100000 --output web/models/garry-evaluation.json
```

Les niveaux 1–10, les six styles et l'option de planification restent disponibles ; ils ne constituent pas des niveaux Elo calibrés.

## Vérifier et reconstruire

```bash
python -m unittest discover -s tests -v
node --test tests/web.test.mjs tests/garry.test.mjs
```

Sous Windows, `PYTHON` peut indiquer aux tests Node le chemin de Python. Les tests couvrent la fusion, les matrices réellement communes, l'apprentissage, la sauvegarde unique, les masques légaux, la parité Python/JavaScript, les tactiques, les règles, HTTP/SSE et les empreintes de la référence.

Le protocole `logic-arena.v1` reste compatible : `catalog`, `create`, `observe`, `suggest`, `play`, `step`, `run`, `stop`, `delete`, via `python -m logic_arena jsonl` ou `POST /api`. SSE : `/sessions/ID/events`. Le catalogue et les décisions indiquent le nom, la version et le mode de Garry. L'API navigateur expose toujours `window.logicArena.requestAsync`, `getSnapshot` et `subscribe`.

- `logic_arena/general.py`, `web/engine.js` : modèle général et vues de jeu.
- `web/models/garry.json` : unique fichier de poids actif.
- `web/trainer.js`, `web/inference-worker.js` : workers communs.
- `search/connect4-search.ts`, `web/connect4-search.wasm` : source et moteur Puissance 4.
- `logic_arena/connect4_wasm.py` : instance du même moteur par thread Python.
- `versions/1.0.0/` : référence figée indépendante du modèle actif.

Pour reconstruire le moteur : `npm install --ignore-scripts` puis `npm run build` dans `tools/wasm`. Le compilateur [AssemblyScript](https://www.assemblyscript.org/compiler.html) est verrouillé dans le projet ; Python exécute le binaire avec [Wasmtime](https://github.com/bytecodealliance/wasmtime-py). Aucun service distant ne décide des coups.

Le [bilan de cohérence 0.6.0](docs/GARRY-0.6-COHERENCE.md) décrit les contrôles disponibles, les vérifications et la protection des évaluations entre sessions.

## Licence

Code publié sous [licence MIT](LICENSE). Historique des versions : [CHANGELOG.md](CHANGELOG.md).
