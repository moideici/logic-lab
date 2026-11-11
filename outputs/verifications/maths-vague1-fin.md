# Maths, vague 1 : objectif « 1/1 » sur les plages actuelles (31 octobre 2026)

Suite de [maths-vague1-resultats.md](maths-vague1-resultats.md) (premiers modèles). Protocole : [maths-protocole.md](maths-protocole.md). Objectif donné par l'utilisateur : atteindre 1/1 partout sur ces plages, puis augmenter la difficulté.

## Résultat : modèle `recette-D`, mesuré sur le test une seule fois
Même architecture qu'avant (Transformer décodeur, 812 416 paramètres, un seul modèle pour les six niveaux). Test = états tirés dans la tranche « test » du hachage, plages du protocole.

| Niveau | États de test | Étape exacte | Problèmes de test | Problème résolu | Majorant à 95 % du taux d'échec |
|---|---|---|---|---|---|
| N1 `+ -` | 806 | 0,999 (805/806) | 500 | **500/500** | 0,6 % |
| N2 `*` | 118 | 1,000 | 118 | **118/118** | 2,5 % |
| N3 `/` | 66 | 1,000 | 66 | **66/66** | 4,5 % |
| N4 priorités | 1 000 | 1,000 | 500 | **500/500** | 0,6 % |
| N5 parenthèses | 1 000 | 0,998 (998/1 000) | 500 | **500/500** | 0,6 % |
| N6 équations | 1 000 | 1,000 | 500 | **500/500** | 0,6 % |

Étape « valide » (évaluateur indépendant) = étape exacte pour chaque niveau. Toutes les étapes de tous les problèmes de test résolus sont valides et chaque résultat final est exact. Les six niveaux franchissent les seuils annoncés (étape exacte ≥ 0,99 et résolu ≥ 0,95).

**Lecture honnête de « 1/1 ».**
- Au niveau du **problème résolu**, c'est 1,000 sur les six niveaux.
- Au niveau de l'**étape**, ce n'est pas 1,000 partout : une faute sur 806 états en N1 et deux sur 1 000 en N5. Elles ne coûtent aucun problème sur ces 500 départs, mais elles existent.
- Le majorant à 95 % (colonne de droite, règle de trois sur zéro échec) montre ce qu'un « 1,000 » prouve vraiment : pour N2 et N3, au plus 2,5 % et 4,5 % d'échec ; pour les autres niveaux, au plus 0,6 %. Sur la validation, qui est plus large, le taux d'erreur par étape est d'environ 0,13 % en N5 (8/6 000) et 0,08 % en N4 (4/4 744), 0 sur N1, N2, N3, N6.

## Comment on y est arrivé (toutes les mesures de réglage sont sur la validation)
| Étape | Changement | Validation (moyenne) | Durée |
|---|---|---|---|
| v1 plat | 30 000 pas, plages du protocole | 0,982 | 14 min |
| A | poids 1:5:5:2:5:2, N2 et N3 entraînés avec grand facteur et quotient jusqu'à 999, 45 000 pas | 0,9988 | 39 min |
| B | affinage de A, N1 entraîné jusqu'à 999, 25 000 pas | 0,9992 | 15 min |
| C | affinage de B, ajout d'opérandes négatifs, de produits à deux facteurs de 2 chiffres, de diviseurs jusqu'à 99 | 0,9997 | 20 min |
| D | affinage de C, 40 000 pas, taux plus doux | 0,9997 (plateau) | 19 min |
Cumul d'entraînement du modèle retenu : environ 125 000 pas (A + B + C + D jusqu'au pas retenu). Même taux d'erreur par étape entre C et D à la précision de la mesure (14 contre 12 erreurs sur 10 744 étapes de validation N4 + N5) : j'ai retenu D, un peu meilleur et plus entraîné. Règle d'arrêt du plan appliquée : D n'améliore pas C sur la validation, le réglage s'arrête là.

Le moteur du progrès : les erreurs de la v1 étaient des fautes de retenue sur des résultats à 3 chiffres, des opérandes négatifs, des produits de deux nombres à 2 chiffres et des diviseurs au-dessus de 12. Ces cas n'apparaissaient qu'au détour des étapes de N4 et N5. L'entraînement a été **élargi** (`--wide`) à ces cas pour N1, N2 et N3 ; la validation et le test sont restés sur les plages du protocole, et un test unitaire vérifie qu'aucun état de validation ou de test n'entre dans l'entraînement.

## Réserves
1. **Plages d'entraînement élargies : amendement du protocole.** Le protocole fixait les plages d'entraînement de N1 à N3. Les recettes A à D les ont élargies (nombres jusqu'à 999 et négatifs, deux facteurs de 2 chiffres, diviseurs jusqu'à 99). Les plages d'évaluation sont inchangées, donc les chiffres restent comparables à la v1.
2. **Le test a été regardé plusieurs fois, sur les mêmes états.** Deux modèles de la v1 (curriculum et plat, graine 0), puis `recette-D`. Aucun réglage de A à D ne s'est fait sur le test, mais les premières mesures de test (N2 et N3 trop petits, N5 à 0,98) ont orienté les pistes de la recette. Les mêmes états de test sont donc connus de mon travail ; un banc neuf est nécessaire avant d'affirmer davantage.
3. **N2 et N3 : 118 et 66 états de test seulement** (espace d'entrée limité). Un 1,000 y prouve peu (majorants 2,5 % et 4,5 %).
4. **Une seule graine de modèle final.** La chaîne A à D est une trajectoire unique. Aucune conclusion sur la variabilité d'une graine à l'autre, ni sur curriculum contre plat (une graine chacun, résultats de la v1).
5. **Hors distribution : toujours mauvais.** Test OOD de `recette-D` (étape exacte / résolu) : N1 0,001 / 0,002 ; N2 0,220 / 0,192 ; N3 0,139 / 0,126 ; N4 0,673 / 0,228 ; N5 0,519 / 0,030 ; N6 0,488 / 0,268. L'élargissement de l'entraînement a aidé N2, N3 et N6 (v1 plat : 0,05 / 0,00 / 0,08 de problèmes résolus), mais le réseau n'extrapole pas à des nombres de 4 chiffres ni à des expressions plus longues. C'est la difficulté à augmenter ensuite (positions relatives, multiplication par chiffres, entraînement avec des longueurs variées).
6. Résultat sur une famille d'états générés par nos règles : aucune garantie sur une écriture libre d'un utilisateur (espaces, `×`, `÷`, fractions, puissances, etc.).

## Reproduction
Entraînements (`projets/garry/training-lab/maths_train.py`, tous `--regime flat --wide --no-final`, vitesse ≈ 30 pas/s sur la RTX 4060 partagée) :
- A : `--steps 45000 --seed 0 --tag recette-A --weights 1,5,5,2,5,2`
- B : `--steps 25000 --seed 2 --tag recette-B --init recette-A --lr 3e-4 --weights 2,3,2,4,5,2`
- C : `--steps 25000 --seed 3 --tag recette-C --init recette-B --lr 3e-4 --weights 2,3,3,3,5,1`
- D : `--steps 40000 --seed 4 --tag recette-D --init recette-C --lr 1.5e-4 --weights 2,2,2,4,6,1`
- Test et hors distribution : `--eval-only --tag recette-D`. Analyse d'erreurs : `maths_errors.py recette-D --n 6000`.
Points de contrôle et résultats bruts (non versionnés) : `training-lab/models/maths/recette-*.pt`, `training-lab/results/maths-recette-*.json`. Tests : `tests/test_maths_*.py` (37 verts).

## Suite
La vague 1 est jugée atteinte au sens « problème résolu 1,000 sur les six niveaux ». Vague 2 : exposants, fractions, racines, équations de ces trois ([protocole figé](maths-protocole-vague2.md)). N1 à N6 resteront en non-régression, avec les chiffres ci-dessus comme référence.
