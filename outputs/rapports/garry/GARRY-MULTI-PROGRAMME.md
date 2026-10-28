# Garry × multi : programme « maîtriser les jeux, un par un »

Date : 28 octobre 2026. Demande : rendre Garry très fort partout (sauf le Go), d'abord **gagner à coup sûr** aux jeux qui le permettent, puis maîtriser la liste de `multi` (M1 à M4) un jeu à la fois, sans se presser.

## Principes
1. `multi` reste la source de vérité des règles (moteurs TypeScript purs, `BotDef.act(state, seat, rng)`). Garry s'entraîne avec des ports rapides Python/C++, validés par des tests de parité avec le TS. Rien n'est modifié dans `multi` sans suivre son AGENTS.md (pas de commit, pas de nouvelle dépendance).
2. Budget Cloudflare gratuit : un bot en production doit être très bon marché. Donc : tables/livres d'ouverture + petit réseau + recherche courte en TypeScript, pas de gros calcul serveur.
3. Une méthode par famille de jeux :
   - **Jeux résolus** (Puissance 4, Allumettes/Nim, Morpion, Dames anglaises si besoin) : solveur exact → oracle ; Garry distille l'oracle, le bot embarque livre + solveur léger pour la fin de partie.
   - **Recherche + réseau** (Othello, Dames, Moulin, Awalé, Échecs) : Garry Zéro / distillation d'un alpha-bêta fort.
   - **Hasard** (Yams, Cochon, Oie, Chevaux, Serpents) : programmation dynamique ou espérance exacte, le réseau imite la politique optimale.
   - **Information cachée / social** (Bataille navale, Mastermind, Memory, Bluff, Loup-Garou...) : inférence probabiliste calculée, puis réseau ; les jeux sociaux (M3, M4) viennent en dernier.
4. Chaque étape est évaluée contre un adversaire indépendant ou exact, jamais contre le seul professeur.

## Étape 1 faite : le solveur exact de Puissance 4
- `logic_arena/zero/c4solver.cpp` + `c4solver.py` : négamax alpha-bêta en bitboards, table de transposition, symétrie miroir, scores de Pons (signe = résultat théorique). Test de parité avec une recherche exhaustive naïve : `tests/test_c4solver.py` (2 tests passent).
- Vitesse : depuis le 6e coup joué, moins d'une seconde par position ; les 5 premiers coups (jusqu'à ~25 s par position) devront venir d'un **livre d'ouverture** précalculé.

## Écart à la perfection (mesuré)
40 parties par joueur, ouvertures aléatoires de 6 coups (mêmes ouvertures pour chaque paire, camps échangés), adversaire = solveur parfait (au hasard parmi ses coups qui conservent le résultat théorique). « Erreur » = coup qui dégrade le résultat théorique de la position.

| Joueur | Coups | Erreurs | Taux d'erreur | Résultat théorique atteint | Score contre le parfait |
|---|---|---|---|---|---|
| Garry 0.6.0 niveau 10 | 505 | 12 | 2,4 % | 70 % | 0,300 |
| Professeur niveau 10 | 432 | 7 | 1,6 % | 82,5 % | 0,400 |
| Zéro (itération 149, 200 simulations) | 394 | 7 | 1,8 % | 82,5 % | 0,400 |

Lecture : aucun des trois ne joue parfaitement ; sur une partie de ~12 coups chacun, une erreur qui change le résultat arrive dans environ un tiers des parties. Garry 0.6.0 est le plus faible des trois, ce qui contredit l'impression des duels précédents. Limite : 40 parties, une seule graine, positions de départ aléatoires (certaines déjà perdues, d'où un score contre le parfait inférieur à 0,5).

## Prochaines étapes
1. Livre d'ouverture de Puissance 4 (stratégie gagnante du premier joueur, réponses correctes du second) + test « Garry ne perd jamais une position gagnée ».
2. Distillation du solveur dans un Garry agrandi (nouveau jeu `connect4` dans le réseau commun, entrée enrichie par des neurones de menaces écrits à la main), avec contrôle de non-régression sur les 13 autres jeux et sauvegarde des poids actuels.
3. Même schéma pour Allumettes (Nim) et Morpion (déjà parfaits côté `multi`), puis M1 : Dames, Échecs (perft), Petits chevaux, Oie ; M2, M3, M4 dans l'ordre de la liste.
