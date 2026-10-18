# Garry 3.2.0 — zéro défaite sur les duels demandés

**Le contrôle depuis le plateau vide est réussi, dans les deux camps, contre la version précédente 3.1.0 figée : une victoire, une nulle, aucune défaite.** Garry gagne également les deux duels face aux IA 1.0.0 originales à leur niveau 10.

Ce périmètre a été confirmé par l’utilisateur avant la validation finale : « Duels depuis le plateau vide contre l’ancienne version, dans les deux camps ». Il ne s’agit pas d’une affirmation d’invincibilité universelle.

## Comparaison par le circuit réel

Le moteur 3.1.0 utilise son binaire et ses poids archivés, sans bénéficier de la nouvelle recherche ni de sa mémoire. Les limites des deux Garry sont identiques : 2 000 ms, 200 millions de nœuds au maximum et une profondeur maximale de 42 demi-coups. La limite de temps reste active. L’IA 1.0 utilise son circuit complet original de niveau 10 : 100 000 nœuds et 30 ms. Aucun départ aléatoire ni préremplissage n’est imposé.

| Adversaire | Camp de Garry 3.2.0 | Résultat |
|---|---|---|
| Garry 3.1.0 figé | Premier joueur | Nulle |
| Garry 3.1.0 figé | Deuxième joueur | Victoire |
| IA 1.0.0 originale | Premier joueur | Victoire |
| IA 1.0.0 originale | Deuxième joueur | Victoire |

Sur le même contrôle, Garry 3.1.0 contre sa propre version obtient deux nulles ; le nouveau Garry transforme la partie en second en victoire. Ce contrôle au budget réel n’avait donc déjà aucune défaite pour la référence : le progrès observé est une victoire supplémentaire, et la confirmation du zéro défaite demandé. Les anciens résultats avec d’autres budgets et des ouvertures imposées ne sont pas mélangés avec ce résultat.

Un contrôle préalable du prototype, avec les mêmes limites réelles et deux passages dans chaque camp contre 3.1.0, donne deux victoires et deux nulles. Ces répétitions servent à vérifier la stabilité ; elles ne représentent pas quatre stratégies d’ouverture indépendantes.

## Ce qui change

La recherche peut maintenant établir une preuve exacte de victoire, de nulle ou de défaite, et conserver une action dont elle a prouvé qu’elle ne perd pas lorsqu’elle n’a pas encore résolu toute la position. Les estimations heuristiques restent séparées de cette table de preuves. L’analyse compare aussi les positions symétriques pour réutiliser les calculs.

L’exploration de réponses au moteur précédent a produit un petit répertoire de **sept positions**, embarqué dans le même fichier de modèle. Une entrée contient une réponse d’ouverture choisie par expérience ; elle n’est jamais affichée comme une preuve. Les six autres contiennent des coups vérifiés hors ligne : victoire, nulle ou non-défaite. Une preuve de non-défaite n’est pas présentée comme une preuve de nulle ni comme une distance de mat connue.

Les poids neuronaux, les compteurs d’apprentissage, les six jeux et les dimensions 1 912 → 48 → 48 → 818 restent identiques à 3.1.0. Le modèle possède toujours 134 290 paramètres neuronaux et de valeur, auxquels s’ajoutent les sept entrées discrètes de recherche. **3.2.0 est une évolution compatible du code et du stockage de connaissances**, sans changement des dimensions du réseau ; ce numéro n’est pas calculé à partir des performances.

Les sauvegardes du navigateur datant de 3.1.0 reçoivent le nouveau répertoire en conservant leurs poids personnels et leurs compteurs. L’export reste un seul fichier Garry. Les niveaux de 0 à 10 restent disponibles ; la mémoire d’ouverture et les preuves renforcent la décision maximale, tandis que l’analyse complète des actions est conservée pour les autres niveaux.

## Vérifications et limites

- **59 tests Python et 28 tests JavaScript réussis**, soit 87 tests.
- Résultats et coups du nouveau solveur conformes à un oracle indépendant sur **200 fins de partie**, y compris victoires, nulles et défaites.
- Les six jeux sont contrôlés dans le navigateur aux niveaux 0 et 10, avec entraînement, export, rechargement et un seul modèle dans IndexedDB.
- Une sauvegarde 3.1.0 avec des poids personnels modifiés est migrée dans un navigateur réel : poids et compteurs conservés, sept entrées présentes, décisions du worker vérifiées.
- Le binaire installé est identique à une recompilation de ses sources avec le compilateur épinglé.

Sur **256 positions inédites de milieu et fin de partie**, au budget réduit de 200 000 nœuds et sans le nouveau répertoire d’ouverture, les erreurs de résultat passent de 7 à 3, et les coups qui transforment une position sauvable en défaite passent de 4 à 1. Il reste donc une erreur perdante sur ce contrôle distinct : aucune promesse de zéro défaite n’est faite pour des positions arbitraires ou tous les adversaires.

Les défaites des anciens départs imposés restent dans leurs rapports. Les essais d’ouverture infructueux sont également archivés. La victoire au Puissance 4 dépend du camp et des réponses adverses ; la source primaire [Connect 4 Solver](https://connect4.gamesolver.org/en/) explique la stratégie gagnante théorique du premier joueur. La recherche exacte s’appuie sur les principes exposés dans le [tutoriel de résolution](https://blog.gamesolver.org/), avec une implémentation locale dans Garry.

## Reproduire

Depuis la racine du dépôt :

```powershell
node examples/benchmark_garry_empty_board.mjs --output training-runs/garry-zero-20261017/recheck.json --repetitions 1 --opponents previous,legacy1 --compare
python -m unittest discover -s tests
node --test tests/garry.test.mjs tests/web.test.mjs tests/levels.test.mjs tests/repertoire.test.mjs tests/certified.test.mjs
```

Les traces complètes de tous les coups figurent dans `training-runs/garry-zero-20261017/public-api-duels.json`. Les sources et poids précédents sont conservés sous `versions/3.1.0/`, avec empreintes vérifiées. Les anciens rapports ne sont pas écrasés.

Poids installés : `747ab285bba25373e5c9fe8055bb0273094a78594726d1e6d4444fd16fbdf9cb`.

Moteur installé : `90944af5bebac4343e089b20a0be6c3ab1352beaf8cc5d6f57e338b5e0ab052d`.
