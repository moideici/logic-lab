# Garry Loop : un cœur récurrent sur des sudokus 6×6 (18 octobre 2026)

Premier test du modèle de raisonnement : un bloc d'attention limité aux cases voisines (même ligne, colonne ou bloc), repassé plusieurs fois avec les **mêmes poids**, entraîné **de zéro** sur des sudokus 6×6 à solution unique générés à l'infini. Code : `projets/garry/logic_arena/reason/`, expérience : `training-lab/experience_raisonnement.py`, résultats bruts : `training-lab/results/raisonnement-sudoku6.json` (non versionnés, relançables).

## Protocole

- **Données :** 40 000 problèmes d'entraînement avec 8 à 22 cases vides ; trois tranches de test de 500 problèmes chacune (solution unique, jamais vus) : facile 8-14, moyen 15-21, **dur 22-27 (plus de vides que tout l'entraînement)**.
- **Modèles :** *Loop* (poids liés, 8 passes à l'entraînement), *Loop-16* (16 passes), *non lié* (8 blocs différents, une passe chacun), *une passe* (même bloc, aucune récurrence). 5 000 pas, lot de 128, deux graines. Supervision à chaque passe (perte sur les cases vides).
- **Mesure :** exactitude = grille entière valide (vérificateur exact des lignes, colonnes et blocs) ; « passes moyennes » = nombre de passes avant la première grille valide parmi les problèmes résolus (durée de réflexion avec arrêt par vérification).

## Résultats (exactitude, moyenne de 2 graines)

| Modèle (paramètres) | Passes à l'inférence | facile | moyen | dur (jamais vu) |
|---|---|---|---|---|
| **Loop**, 8 passes (53 254) | 4 | 1,000 | 0,936 | 0,260 |
| | **8** | 1,000 | 0,996 | **0,749** |
| | 16 | 1,000 | 0,998 | 0,827 |
| | 32 | 1,000 | 0,998 | **0,841** |
| **Loop-16** (53 254) | 16 | 1,000 | 0,998 | 0,879 |
| | 32 | 1,000 | 0,998 | **0,893** |
| Non lié, 8 blocs (403 142) | 8 | 1,000 | 0,997 | 0,735 |
| Une passe (53 254) | 1 | 0,267 | 0,004 | 0,000 |

Durée de réflexion du Loop (passes avant la première grille valide) : **1,8 passe** (facile), **3,0** (moyen), **6,0** (dur).

## Ce qu'on peut affirmer

1. **La récurrence est ce qui fait le travail.** À même nombre de paramètres, une seule passe ne résout presque rien (0 % sur le moyen et le dur). Un réseau à huit blocs distincts, **huit fois plus gros**, fait un peu moins bien que le Loop de huit passes sur le dur (0,735 contre 0,749) et ne peut pas repasser plus de fois.
2. **On peut réfléchir plus longtemps qu'à l'entraînement.** Entraîné à 8 passes, le Loop passe de 0,749 à 0,841 sur les problèmes durs en passant à 32 passes à l'inférence, sans ré-entraînement.
3. **La durée de réflexion croît avec la difficulté** (1,8, 3,0, puis 6,0 passes), sans qu'on l'ait demandé : c'est exactement ce que Garry Mind devra exploiter (arrêter dès que le vérificateur confirme).
4. **Un bloc de 53 000 paramètres résout à plus de 99 % des problèmes de difficulté moyenne** et 75 à 89 % des problèmes plus durs que tout ce qu'il a vu.

## Limites à garder en tête

- **Biais structurel fort :** l'attention n'a accès qu'aux voisines de contrainte. Le modèle reçoit donc la règle du jeu dans sa structure, pas dans ses données. Ce qui est montré : « la récurrence sur un graphe de contraintes se généralise en nombre de passes et en difficulté », pas « un raisonneur général ». La preuve de généralité vient avec d'autres familles de problèmes décrits par un graphe (coloration, n-reines) et un transfert vers une famille jamais vue.
- **L'arrêt par vérification** utilise un vérificateur exact externe : la « durée de réflexion » mesurée est celle d'un système proposer-vérifier, pas un arrêt appris par le réseau.
- 500 problèmes par tranche, deux graines, un seul problème (sudoku 6×6) ; le sudoku 4×4 est trop facile (99,8 % dès 500 pas) ; le 9×9 n'est pas testé.
- Le « dur » reste de la même famille que l'entraînement (plus de vides) : c'est un test d'extrapolation en difficulté, pas de transfert.

## Suite proposée

1. Affichage dans le Lab de la grille à chaque passe (en cours).
2. Arrêt appris (tête de décision d'arrêt) pour remplacer le vérificateur, puis comparaison des deux.
3. Deuxième famille sur le même modèle : coloration de graphe ou n-reines (autre graphe de contraintes), puis test de transfert.
4. Sudoku 9×9.
