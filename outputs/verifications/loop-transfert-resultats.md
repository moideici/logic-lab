# Loop : un seul modèle pour deux familles de problèmes, et transfert (18 octobre 2026)

Deuxième famille ajoutée au modèle de raisonnement : la **coloration de graphe** (nœuds reliés par des arêtes, couleurs voisines différentes, solution unique), à côté du sudoku 6×6. Le modèle est le même Loop (un bloc d'attention limité aux voisines, repassé 16 fois avec les mêmes poids), sans embedding de position pour que seule la structure du graphe compte. Code : `logic_arena/reason/graphs.py`, `multi.py` ; expérience : `training-lab/experience_transfert.py` ; résultats bruts : `training-lab/results/transfert.json`.

## Protocole

Trois entraînements de 6 000 pas, 2 graines chacun : **S** (sudoku seul), **C** (coloration seule : 12 à 24 nœuds, 4 couleurs), **SC** (les deux, tirage égal). Six jeux de test de 500 problèmes à solution unique, jamais vus : sudoku moyen et dur, coloration dans la distribution, **plus grands graphes (26 à 32 nœuds)**, **5 couleurs** (jamais vues), **graphes plus denses**.

## Résultats (grille entière valide, 32 passes, moyenne de 2 graines)

| Entraîné sur | sudoku moyen | sudoku dur | coloration | plus grands graphes | 5 couleurs | plus denses |
|---|---|---|---|---|---|---|
| S : sudoku seul | 1,00 | 0,95 | 0,51 | 0,41 | 0,61 | 0,88 |
| C : coloration seule | 0,00 | 0,00 | 0,99 | 0,96 | 0,20 | 1,00 |
| **SC : les deux** | **1,00** | **0,94** | **0,99** | **0,95** | **0,69** | **1,00** |

Passes moyennes avant la première grille valide : sudoku 3,1 (moyen) et 6,1 à 6,5 (dur) ; colorations de 2,3 à 4,2.

## Ce qu'on peut affirmer

1. **Un seul modèle fait aussi bien que deux spécialistes.** SC égale S sur le sudoku (1,00 / 0,94 contre 1,00 / 0,95) et C sur la coloration (0,99 / 0,95 contre 0,99 / 0,96) : pas d'interférence mesurable entre les deux familles, avec les mêmes 53 000 paramètres.
2. **Il généralise en taille de graphe** : les graphes de 26 à 32 nœuds, plus grands que tout l'entraînement (12 à 24), sont résolus à 0,95 à 0,96.
3. **Le transfert existe, il est partiel et asymétrique.** Entraîné uniquement au sudoku, le modèle résout 51 % des colorations qu'il n'a jamais vues (88 % des graphes denses, qui sont plus contraints donc plus faciles) : il a retenu une partie de la règle « les voisines sont différentes », pas seulement le sudoku. L'inverse échoue (coloration seule vers sudoku : 0,00).
4. **La réflexion suit toujours la difficulté** : plus de passes pour le sudoku dur (6 à 6,5) que pour les problèmes faciles (2,3 à 3,3).

## Limites à ne pas oublier

- **L'asymétrie est en partie un artefact de vocabulaire** : le modèle entraîné à la coloration n'a jamais vu les valeurs 5 et 6 (4 couleurs seulement) ; le sudoku en utilise six. Il échoue donc au sudoku autant par symboles inconnus que par structure. Le résultat « 5 couleurs » (0,20 pour C) a la même cause.
- Une grille entière valide est exigée ; le modèle ne produit pas de « je ne sais pas ».
- Toujours **une règle de contrainte unique** (couleurs différentes entre voisines) et une structure d'attention donnée par le graphe : la généralité vers d'autres types de règles (n-reines, planification, énigmes avec contraintes d'ordre) reste à montrer.
- 500 problèmes par test, 2 graines ; la coloration dans la distribution n'a que des graphes aléatoires à couleurs plantées.

## Suite proposée

Une troisième famille avec une règle de nature différente (par exemple n-reines, ou un ordonnancement avec dépendances) pour tester le transfert au-delà de « voisines différentes » ; arrêt appris ; sudoku 9×9.
