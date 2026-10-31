# Garry Universel : protocole fixé avant les résultats (31 octobre 2026)

Question : un seul réseau qui lit la vue JSON et les coups légaux de n'importe quel jeu de `multi`, sans encodage écrit à la main, apprend-il quelque chose qui sert sur un jeu qu'il n'a jamais vu ?

## Jeux
- **Entraînement** : morpion, puissance-4, othello, dames, allumettes (5 jeux à information complète, tour par tour, deux joueurs).
- **Réservés** (jamais vus à l'entraînement, ni leurs positions) : morpion-ultime (famille alignement), moulin (alignement avec pièces et captures), awalé (famille éloignée : semis).
- Exclus pour l'instant : jeux à information cachée, jeux simultanés ou chronométrés, jeux à plus de deux joueurs, échecs (trop lourds pour un premier essai).

## Professeur universel
UCT générique (parties aléatoires jusqu'au bout, aucune connaissance du jeu) dans le pont Node : `bridge.mjs`, opération `uct`. Même professeur pour tous les jeux, y compris les jeux réservés. Le réseau imite la distribution des visites de la racine (« recherche amortie »).

## Mesures (parties jouées, camps échangés, graines appariées, ouvertures aléatoires de 2 coups)
1. **Jeux d'entraînement** : score du réseau seul (coup de plus haut score parmi les légaux, sans recherche) contre le hasard, contre UCT à 50 simulations et contre UCT à 400 simulations.
2. **Zéro-coup sur les jeux réservés** : score contre le hasard, comparé au score 0,5 du hasard contre le hasard.
3. **Adaptation** (le résultat principal) : sur chaque jeu réservé, on ajuste (a) le réseau préentraîné et (b) le même réseau initialisé au hasard, avec le même budget de données (100, 300, 1 000 parties de professeur UCT 200) et le même nombre de pas ; on compare leur score contre le hasard et contre UCT à 50 simulations (200 parties chacun).

## Critères d'arrêt (annoncés avant)
- Si le réseau préentraîné ne bat pas le réseau initialisé au hasard d'au moins 0,05 de score moyen sur au moins deux des trois jeux réservés dans la mesure 3, à budget de 300 parties, on conclut à l'absence de transfert démontré et on s'arrête sans étendre.
- Les jeux réservés ne servent à aucune sélection (hyperparamètres choisis sur les jeux d'entraînement seulement).
- Toute différence inférieure à 0,05 de score avec 200 parties est considérée comme du bruit.
