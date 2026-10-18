# Garry — entraînement supplémentaire, cycle 02

Logiciel **3.1.0**, révision des poids **20261016-repertoire-02**. L’architecture et les réglages de réflexion ne changent pas. Référence : Garry actif au début de ce cycle, révision `20261016-repertoire-01`.

## Ce qui a été exécuté

- 18,440 positions au total : 15,240 d’apprentissage, 1,602 de validation et 1,598 de test.
- 12,288 positions inédites générées pour les cinq jeux autres que le morpion ; ses 627 positions canoniques conservent leurs groupes fixes.
- 5,527 anciens exemples d’apprentissage rejoués pour limiter les oublis.
- 3,917 exemples publics proposés dans le magasin de l’application, uniquement issus de l’apprentissage.
- Nouveaux adversaires et tirages, défenses et pièges au Puissance 4, nouvelles grilles uniques de sudoku, frontières publiques du démineur et positions profondes du taquin. Les positions synthétiques de 2048 restent identifiées.

Les anciens lots de validation et de test sont exclus de l’apprentissage et du magasin. Les nouvelles épreuves des cinq jeux excluent aussi les états connus des anciens lots encodés et de l’apprentissage de l’évaluateur de position. Les miroirs reconnus et les familles de parties ou de puzzles sont contrôlés. Le morpion utilise son épreuve exhaustive fixe ; elle ne constitue pas un nouveau test indépendant.

Les points de reprise sont choisis sur les validations nouvelles et anciennes, puis soumis une seule fois aux tests. Le module commun, son biais et l’évaluateur de position du Puissance 4 sont gelés. Chaque mode candidat reste séparé tant qu’il n’a pas passé les contrôles. Les échecs des épreuves restent en quarantaine.

## Choix du réseau seul sur les positions de test

Ce taux mesure le choix d’un coup jugé acceptable par le professeur, sans le planificateur du niveau 10. Il ne mesure pas un taux de victoire. Le professeur est exact pour le morpion et le taquin, et borné en calcul pour le Puissance 4. Les pourcentages finaux concernent les poids effectivement installés.

| Jeu | Positions | Avant | Après installé | Décision |
|---|---:|---:|---:|---|
| Morpion | 62 | 93.5% | 93.5% | Poids précédents conservés |
| Puissance 4 | 768 | 45.1% | 45.1% | Poids précédents conservés |
| 2048 | 192 | 34.9% | 34.9% | Poids précédents conservés |
| Sudoku | 192 | 59.4% | 59.4% | Poids précédents conservés |
| Démineur | 192 | 17.7% | 17.7% | Poids précédents conservés |
| Taquin | 192 | 50.0% | 50.0% | Poids retenus |

Poids installés : Taquin.

Au taquin, le taux sur les anciennes positions réservées passe de 60.00% à 61.25%, sans gain du taux de choix sur les nouvelles positions. La perte d’apprentissage sur les nouvelles épreuves diminue de 1.3675 à 1.3485. Ce progrès modeste justifie de retenir ce candidat, sans conclure à une amélioration des victoires du niveau 10. Le candidat démineur est écarté parce qu’il recule sur les anciennes épreuves malgré son gain sur les nouvelles.

## Parties complètes avec planification

Contrôle solo : 16 parties ou puzzles appariés par jeu, mêmes départs et budgets de calcul avant/après. Ces nombres décrivent les candidats finalistes comparés ; un mode qui échoue à ce contrôle est restauré avant installation. Une partie tronquée n’est jamais comptée comme gagnée ; 2048 est plafonné à 2 000 actions.

| Jeu | Victoires avant | Victoires candidat | Score total avant → candidat | Tronquées avant → candidat |
|---|---:|---:|---:|---:|
| 2048 | 9 / 16 | 9 / 16 | 277000 → 277000 | 0 → 0 |
| Sudoku | 16 / 16 | 16 / 16 | 680 → 680 | 0 → 0 |
| Démineur | 14 / 16 | 14 / 16 | 860 → 860 | 0 → 0 |
| Taquin | 16 / 16 | 16 / 16 | 0 → 0 | 0 → 0 |

Ligue Puissance 4 : 224 parties par modèle face à sept adversaires, deux côtés, départs standards, préfixes variés et positions réservées. Budget : 200,000 nœuds pour les moteurs courants, 5 000 pour l’ancienne IA 1.0 et aucun arbre pour l’adversaire tactique.

- Référence : 139 victoires, 56 défaites, 29 nuls.
- Candidat : 139 victoires, 56 défaites, 29 nuls.

Ces séries limitées ne prouvent ni une supériorité statistique ni l’invincibilité. Le zéro défaite n’est pas atteint. Aucun changement de profondeur ou d’architecture n’est attribué à ce cycle d’entraînement.

## Reproductibilité

Vérification finale : **55 tests Python et 25 tests JavaScript réussis**, soit 80 tests. Le magasin contient exclusivement des exemples d’apprentissage ; son intersection avec les anciennes épreuves réservées est vide.

Lot : `garry-repertoire-20261016-cycle02`, graine 16071200. Les données, journaux d’époques, décisions de sélection, résultats complets, poids avant/après et empreintes sont conservés dans ce dossier sous `training-runs/`. Le rapport installé est `web/models/garry-repertoire-cycle02-evaluation.json`.

L’outil de génération accepte `--history`, `--replay`, `--legacy-archive` et `--position-history`. L’entraînement accepte `--retention-dataset`. Le contrôle solo accepte explicitement le fichier de référence, une graine et un nombre de parties. Les écritures de suivi résistent aux verrouillages temporaires de fichiers sous Windows ; les lots disposent de points de reprise liés au code, aux poids et aux données sources.

Empreinte des poids installés : `4dc2bb549cda1ffac2c149de057cf51ec283c6962d2fa997becd93ec44706692`.
