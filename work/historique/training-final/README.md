# Logic Lab — Garry 2.0.0

**Garry est un modèle neuronal général unique pour six jeux** : morpion, Puissance 4, 2048, sudoku, démineur et taquin. L'interface, les workers et le serveur Python utilisent `web/models/garry.json`.

## Architecture et fusion

```text
Observation publique + identifiant du jeu
                 ↓
  encodeur unique : 1 912 → 48, tanh
                 ↓
  module central : 48 → 48, tanh
                 ↓
  sortie unique : 48 → 818
                 ↓
  masque des actions légales du jeu
```

Les six modes sont des vues sur **les mêmes matrices** en mémoire. Un seul encodeur, un seul biais d'entrée, un seul module central, une seule matrice de sortie, un seul optimiseur Adam dans Python et un seul fichier de sauvegarde atomique. Les vues ne possèdent aucun poids autonome.

La fusion est algébrique : 1 906 caractéristiques réparties en zones propres aux jeux et six indicateurs de jeu forment l'entrée. Les biais des anciens encodeurs sont intégrés aux lignes correspondant à ces indicateurs. Les sorties sont réunies dans la matrice globale de 818 actions. Le jeu sélectionne les caractéristiques et les actions autorisées. Cette architecture conditionnée conserve les savoirs existants ; elle ne prouve pas une généralisation à un jeu inconnu. Les biais communs et le module central permettent le transfert entre tâches ; l'entraînement répète les autres jeux pour limiter l'oubli.

La vérification de fusion porte sur **1 223 positions** : les 1 223 choix gloutons sont conservés, avec un écart maximal de logits de `3,82e-6`. Aucun réentraînement n'a été effectué pendant la fusion. Rapport : `web/models/garry-fusion.json`.

## Nom et versions

Le modèle s'appelle **garry**, affiché **Garry**, version **2.0.0** pour les six modes. MAJEUR change lors d'une évolution de l'architecture ou des dimensions ; MINEUR lors d'une fonctionnalité compatible ; CORRECTIF lors d'une correction compatible. La fusion en 1 912 → 48 → 48 → 818 justifie 2.0.0. Les résultats d'évaluation sont indépendants de cette numérotation ; les compteurs d'entraînement figurent séparément dans les poids.

`versions/1.0.0/` conserve les IA locales présentes à la fin du travail précédent, avec un manifeste SHA-256 vérifié par les tests.

## Démarrer et apprendre

Python 3.11+, NumPy et Wasmtime ; Node.js 22+ pour les tests JavaScript.

```bash
python -m pip install -e .
python -m logic_arena serve --port 8000
```

Ouvrir http://127.0.0.1:8000. La plateforme fonctionne aussi sur un hébergement statique : calcul et apprentissage restent locaux. Les sessions du navigateur et du serveur Python sont distinctes. IndexedDB utilise une seule clé pour Garry dans une base dédiée. L'export produit un seul fichier `garry-2.0.0.json`. L'import accepte Garry ou une ancienne suite complète de six modèles dont les poids centraux concordent. Les anciennes données du navigateur restent dans leur base d'origine.

```bash
python -m logic_arena train --game tictactoe --episodes 30 --epochs 10 --output trained-models
python -m logic_arena evaluate --game tictactoe --models trained-models --episodes 100
python -m logic_arena evaluate --game sudoku --planning --max-steps 100
python examples/fuse_garry.py --output training-data/garry-initial.json
```

L'entraînement sauvegarde `trained-models/garry.json` et son rapport. Les six modes utilisent ensuite les poids mis à jour. `--models` accepte le dossier ou le fichier Garry. La commande de fusion recrée les poids initiaux depuis la référence figée.

### Entraînement et révision des poids du 16 octobre 2026

La révision `20261016-c4-guarded-01` est installée dans `web/models/garry.json`, sans changer l'architecture ni la version logicielle 2.0.0. Sur 200 parties de Puissance 4 contre un adversaire aléatoire, le réseau seul passe de 127 à 144 victoires et de 72 à 56 défaites. Les poids effectifs des cinq autres modes sont strictement préservés. Sur 40 duels de contrôle contre la référence figée, le système avec recherche obtient les mêmes résultats avant/après : 30 victoires, 6 défaites, 4 nuls. Aucun gain du système hybride n'est donc démontré par ce lot.

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
