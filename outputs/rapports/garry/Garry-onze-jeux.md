# Garry 4.0.0 — onze jeux et premiers apprentissages

Les **dames internationales** et **Percée** sont maintenant jouables contre Garry, observables en duel et accessibles à l’entraînement. Reversi, Nim et Lights Out ont aussi été ajoutés : le même modèle couvre désormais onze jeux. Aucun jeu d’échecs n’a été ajouté.

## Nouveaux jeux

| Jeu | Jouabilité | Analyse de Garry |
| --- | --- | --- |
| Dames internationales · 10 × 10 | Sélection du pion puis de la destination ; rafles en plusieurs étapes, prise maximale obligatoire, prise arrière des pions, dames à longue portée, promotion en fin de rafle, nulles | Recherche adversariale, prolongation des rafles jusqu’à leur fin, apprentissage des coups |
| Percée · 8 × 8 | Avancer, prendre en diagonale et atteindre la dernière rangée | Recherche adversariale et apprentissage des courses de pions |
| Reversi · 6 × 6 | Encadrer les pions adverses ; passer lorsqu’aucune pose n’est possible | Recherche, mobilité et contrôle des coins |
| Nim · trois tas | Retirer des allumettes d’un seul tas ; prendre la dernière gagne | Analyse exacte de toutes les configurations représentables |
| Lights Out · 5 × 5 | Allumer/éteindre en croix ; éteindre le plateau | Résolution exacte avec le minimum de pressions |

Les règles des dames suivent l’[annexe 1 de la FMJD](https://www.fmjd.org/downloads/FMJD_Annexes_2024_8-sig.pdf). Les pièces prises bloquent les diagonales jusqu’à la fin de la rafle ; les nulles comprennent la répétition et les limites de finales. Les déplacements et captures de Percée suivent les [règles de Breakthrough](https://superdupergames.org/rules/break.pdf).

## Premières parties complètes aux dames et à Percée

Face aux nouvelles capacités initialisées avant leur apprentissage, **avec le réseau seul**, quatre départs ont été joués dans les deux camps :

| Jeu | Victoires | Nulles | Défaites |
| --- | --- | --- | --- |
| Dames internationales | 7 | 1 | 0 |
| Percée | 8 | 0 | 0 |

Au niveau 10 avec planification, quatre parties supplémentaires par jeu contre des choix aléatoires donnent **4 victoires aux dames et 4 à Percée**. Les départs et résultats individuels sont conservés dans `training/strategy-4.0.0/full-games.json`.

Ces échantillons ne prouvent pas l’invincibilité. La référence de ces nouveaux duels est leur initialisation avant apprentissage : les anciennes versions à six jeux ne savaient pas y jouer. Le précédent résultat « zéro défaite contre la 3.1.0 » garde son périmètre historique et n’est pas étendu aux onze jeux.

## Apprentissage et limites

Les cinq nouvelles capacités ont reçu 2 180 positions d’apprentissage distinctes, 400 positions de validation et 400 positions de test. Les points de sauvegarde sont choisis sur la validation. Les tests sont ensuite ouverts pour mesurer les résultats. Les dames et Percée ont reçu respectivement 4 680 et 6 120 présentations d’exemples pour les points retenus. Le répertoire partagé contient désormais **4 757 épreuves d’apprentissage**, sans les états réservés.

Les taux suivants concernent le **réseau seul** : ils mesurent son accord avec les coups du professeur sur des positions réservées, pas un taux de victoire. Les professeurs de Reversi, des dames et de Percée effectuent une recherche bornée.

| Jeu | Positions de test | Avant apprentissage | Après apprentissage |
| --- | --- | --- | --- |
| Reversi | 70 | 31,4 % | 62,9 % |
| Nim | 150 | 7,3 % | 4,7 % |
| Lights Out | 100 | 52,0 % | 45,0 % |
| Dames internationales | 40 | 55,0 % | 57,5 % |
| Percée | 40 | 12,5 % | 47,5 % |

L’apprentissage initial du réseau seul reste insuffisant à Nim et à Lights Out et recule sur ce premier test réservé. Leur niveau 10 avec planification utilise les solveurs exacts ; il ne dépend donc pas de la qualité de ces seuls scores appris. Les recherches aux dames, à Percée et au Reversi restent bornées ; aucune profondeur de vingt coups n’y est annoncée.

## Conservation des acquis et version

La nouvelle architecture est **2 494 → 48 → 48 → 3 617**, avec 299 377 paramètres, dans un seul fichier. L’agrandissement des entrées et sorties justifie **4.0.0** ; la numérotation ne dépend pas des résultats sportifs.

Les coefficients des six jeux existants, le module central, l’évaluateur de Puissance 4 et sa mémoire d’ouverture sont conservés exactement. L’apprentissage des dames et de Percée conserve ensuite les neuf modes précédents. La 3.2.0 est archivée avec empreintes dans `versions/3.2.0/`.

Les anciens exports sont migrés. Dans l’interface, les nouveaux blocs entraînés sont ajoutés aux modèles personnels importés sans remplacer leurs anciens coefficients ni leur module central.

## Vérifications

**75 tests Python et 39 tests JavaScript réussis : 114 au total.** Les contrôles incluent les rafles, les victimes bloquantes, les promotions, les nulles, les masques de coups, les échanges de modèles, les anciens solveurs et les oracles indépendants pour Nim, Lights Out et des finales de Percée.

Les essais dans le navigateur couvrent les cinq nouveaux jeux joués manuellement, les réponses de Garry, le passage au Reversi, une rafle aux dames, la résolution de Lights Out, les cinq workers d’entraînement, l’import/export ancien et le rendu mobile sans débordement. Aucune erreur de page n’a été détectée.

Commandes de vérification depuis le projet :

```text
python -m unittest discover -s tests
node --test tests/garry.test.mjs tests/web.test.mjs tests/levels.test.mjs tests/repertoire.test.mjs tests/certified.test.mjs tests/new-games.test.mjs tests/strategy.test.mjs
node examples/benchmark_strategy.mjs
```
