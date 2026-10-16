# Logic Lab

Plateforme web et harnais Python pour **six jeux**, avec un **véritable réseau neuronal partagé**, entraînement, jeu autonome et duel humain/IA.

Jeux : morpion, 2048, sudoku, puissance 4, démineur 8×8 et taquin 3×3.

## Démarrage

Python 3.11+ et NumPy. Depuis ce dossier :

```bash
python -m pip install -e .
OPENBLAS_NUM_THREADS=1 python -m logic_arena serve --port 8000
```

Ouvrir **http://127.0.0.1:8000**. L’interface s’exécute entièrement dans le navigateur ; les routes `/api` et SSE fournissent en parallèle le harnais Python. Les sessions du navigateur et celles du serveur sont distinctes.

Le site hébergé sert la plateforme statique : inférence, entraînement par Web Worker, stockage IndexedDB et protocole JavaScript local fonctionnent sans serveur Python. Pour l’API HTTP et SSE, lancer le projet Python.

## Réseaux connectés

```text
Morpion ───── encodeur 18→48 ──┐                ┌─ tête 48→9
2048 ──────── encodeur 192→48 ─┤                ├─ tête 48→4
Sudoku ────── encodeur 891→48 ─┤ MODULE COMMUN  ├─ tête 48→730
Puissance 4 ─ encodeur 84→48 ──┤    48→48       ├─ tête 48→7
Démineur ──── encodeur 640→48 ─┤     tanh       ├─ tête 48→64
Taquin ────── encodeur 81→48 ──┘                └─ tête 48→4
```

Les six politiques partagent **le même objet de poids** pour le module commun. Un entraînement sur un jeu modifie donc les représentations utilisées par les cinq autres. Les encodeurs et les têtes restent propres à chaque jeu. Les masques d’actions légales sont communs à l’inférence et à l’apprentissage.

Les modèles initiaux apprennent par **imitation des solveurs**, avec cross-entropie masquée et rétropropagation : Adam sous NumPy, SGD en ligne dans le navigateur. Pendant l’entraînement web, un exemple principal sur quatre déclenche un exemple de répétition d’un autre jeu, en alternance sur les cinq jeux. Les six modèles sont ensuite sauvegardés ensemble avec leur nouveau module partagé.

Le partage rend le transfert possible ; il ne prouve pas un gain de performance. Il peut aussi provoquer de l’oubli ou du transfert négatif. Le projet fournit des évaluations séparées, sans professeur, pour comparer avant/après.

Un **planificateur commun** réutilise en plus le même algorithme de recherche guidée par le réseau au sudoku et au taquin. Seuls les adaptateurs de règles changent. L’interface permet de le désactiver et d’observer la politique neuronale seule. Les coups assistés sont identifiés `neural+planner` ; la probabilité de la politique n’est pas présentée comme celle du résultat de recherche.

## Dix niveaux, six styles

Les niveaux neuronaux modulent la température de sélection, de `2.0` à `0` : le niveau 10 équilibré choisit le score maximal. Le planificateur ajoute des budgets croissants de 8 à 25 000 nœuds et de 1 à 150 ms. `time_ms` permet un budget de planification explicite côté Python. Les délais sont des budgets coopératifs, pas des garanties de temps réel matériel.

Styles : `balanced`, `aggressive`, `defensive`, `greedy`, `positional`, `exploratory`. Ils ajoutent de petites préférences explicites aux scores du réseau ; `exploratory` conserve une température minimale de 0,6. La planification privilégie l’objectif du puzzle et peut effacer les différences de style. Ces dix réglages ne constituent pas dix niveaux Elo calibrés.

Les solveurs de référence (`type: "reference"`) ont leurs propres budgets croissants de recherche, disponibles dans `catalog`.

## Entraîner et évaluer

Dans l’onglet **Apprendre**, choisir le jeu, les épisodes, le taux d’apprentissage et la graine. L’arrêt conserve les poids déjà appris, y compris ceux du module commun et des autres jeux répétés. Exporter la suite JSON pour la conserver ou l’utiliser dans Python.

Depuis Python :

```bash
OPENBLAS_NUM_THREADS=1 python -m logic_arena train --game tictactoe --episodes 100 --epochs 10 --output trained-models
OPENBLAS_NUM_THREADS=1 python -m logic_arena evaluate --game tictactoe --models trained-models --episodes 100 --seed 1000000
OPENBLAS_NUM_THREADS=1 python -m logic_arena evaluate --game sudoku --episodes 15 --planning --max-steps 100
```

L’entraînement CLI utilise aussi une répétition sur les autres jeux. `--models` charge une suite préexistante, ce qui permet de poursuivre l’apprentissage. `--output` contient les six fichiers et un rapport.

Les fichiers `web/models/report.json`, `evaluation.json` et `planning-evaluation.json` donnent respectivement les pertes d’apprentissage et les évaluations sans professeur, avec et sans planification. Les succès pendant l’entraînement mêlent des coups de l’élève et du professeur : ils ne sont pas un taux de victoire du réseau seul.

La politique initiale seule est un **point de départ**, pas un champion des six jeux. L’évaluation initiale sur 100 duels contre un adversaire aléatoire donne 87 victoires, 13 nuls et 0 défaite au morpion, puis 67 victoires et 33 défaites à puissance 4. Sur les autres jeux, les premières politiques seules restent faibles ; les rapports les montrent aussi. Le démineur peut exiger des paris et 2048 contient des apparitions aléatoires. Aucune garantie de victoire universelle.

Pour recréer les modèles, y compris le préentraînement sur les 4 520 états jouables du morpion et la répétition multijeu :

```bash
OPENBLAS_NUM_THREADS=1 PYTHONPATH=. python examples/bootstrap_models.py
```

## JSON commun

Une requête et une réponse par ligne sur stdin/stdout :

```bash
python -m logic_arena jsonl
```

Créer une session :

```json
{"protocol":"logic-arena.v1","id":"1","op":"create","game":"tictactoe","seed":42}
```

Copier `result.session_id` dans les requêtes suivantes. Demander une décision sans modifier le plateau :

```json
{"id":"2","op":"suggest","session_id":"ID_RETOURNÉ","agent":{"type":"neural","level":8,"style":"balanced","seed":42,"planning":true}}
```

Appliquer un coup externe avec protection contre une observation périmée :

```json
{"id":"3","op":"step","session_id":"ID_RETOURNÉ","expected_revision":0,"action":{"row":1,"col":1}}
```

Réponse type :

```json
{"protocol":"logic-arena.v1","id":"2","ok":true,"result":{"revision":0,"action":{"row":1,"col":1},"info":{"agent":"neural","method":"shared_mlp_policy","level":8,"style":"balanced","time_ms":0.3,"training_steps":497200,"shared_steps":1082890}}}
```

Les temps et actions ci-dessus sont illustratifs. `catalog` fournit les noms de jeux, schémas d’actions, styles et réglages de niveau. Les coordonnées commencent à zéro.

| Jeu | Identifiant | Action |
|---|---|---|
| Morpion | `tictactoe` | `{"row":0,"col":0}` |
| 2048 | `2048` | `{"direction":"left"}` |
| Sudoku | `sudoku` | `{"row":0,"col":2,"value":4}` ou `{"undo":true}` |
| Puissance 4 | `connect4` | `{"column":3}` |
| Démineur | `minesweeper` | `{"row":0,"col":0}` |
| Taquin | `sliding_puzzle` | `{"direction":"up"}` |

Autres opérations : `observe`, `play` (décider et appliquer), `run`, `stop`, `delete`. Au taquin, `options: {"scramble":30}` règle le mélange initial, toujours résoluble. Le sudoku utilise une grille à solution unique transformée par des symétries, plutôt qu’un générateur de grilles arbitraires.

Chaque transition contient `observation`, `legal_actions`, `reward`, `actor`, `revision`. Pour deux joueurs, la récompense appartient à celui qui vient de jouer. `winner` vaut 1/2 pour un gagnant, 0 pour un nul multijoueur ou un échec solo, et `null` pendant la partie. Sudoku permet l’annulation pour récupérer des choix localement valides mais globalement faux.

## HTTP et temps réel

`POST /api` accepte les mêmes requêtes JSON. `GET /api/catalog` retourne le catalogue.

```json
{"op":"run","session_id":"ID_RETOURNÉ","max_steps":500,"interval_ms":100,"agents":{"1":{"type":"neural","level":8,"style":"aggressive"},"2":{"type":"neural","level":10,"style":"defensive"}}}
```

Puis se connecter à `GET /sessions/ID_RETOURNÉ/events` avec `EventSource` ou `curl -N`. Événements SSE : `created`, `started`, `step`, `finished`, `stopped`, `run_error`, `deleted`. Le client peut reprendre avec `Last-Event-ID` ou `?after=N`. Les 256 derniers événements sont conservés ; `resync` fournit une observation complète si le curseur est trop ancien. `stopped` précise `reason` et `truncated` lorsque le budget de coups est épuisé.

L’interface propose aussi :

```js
const state = window.logicArena.getSnapshot();
const reply = window.logicArena.request({op:'suggest', session_id:state.session_id, agent:{level:8}});
const unsubscribe = window.logicArena.subscribe(event => console.log(event));
```

Cette API de navigateur pilote sa session courante. L’export JSONL contient les observations publiques, actions et récompenses de la partie. Les graines Python et JavaScript sont reproductibles **dans leur runtime**, mais leurs générateurs aléatoires ne produisent pas les mêmes parties.

## Vérification

```bash
OPENBLAS_NUM_THREADS=1 python -m unittest discover -s tests -v
node --test tests/web.test.mjs
```

Couverture : règles et fins de partie, erreurs sans mutation, observations sans mines cachées, masques légaux, apprentissage et transfert effectif entre jeux, sauvegarde/rechargement, parité des encodages et logits Python/JavaScript, sessions, révisions, HTTP et SSE. Le test HTTP et le lanceur Node nécessitent l’accès au réseau local.

Une vérification réelle sous Chromium contrôle aussi les duels humain/IA, les six moteurs, la résolution des deux puzzles avec planification, le worker d’entraînement, la persistance IndexedDB, le protocole JSON et l’affichage mobile.

## Fichiers

- `logic_arena/games.py` : règles et observations.
- `logic_arena/neural.py` : réseaux, rétropropagation et module partagé.
- `logic_arena/planner.py` : recherche commune sudoku/taquin.
- `logic_arena/agents.py` : solveurs professeurs et références.
- `logic_arena/harness.py`, `server.py` : protocole, sessions, HTTP et SSE.
- `web/` : interface, moteurs JavaScript, réseau interopérable et worker.
- `logic_arena/training.py` : Q-learning tabulaire expérimental complémentaire ; il n’est pas l’agent neuronal affiché.

Pas de compte utilisateur ni de stockage cloud des entraînements. Les sessions Python résident en mémoire et disparaissent à l’arrêt du serveur. Les modèles web restent sur l’appareil, sauf export explicite.
