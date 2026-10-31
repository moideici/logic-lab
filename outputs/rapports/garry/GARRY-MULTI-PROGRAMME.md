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

## Étape 2 : première distillation du solveur (28 octobre, fin de journée)
51 194 positions étiquetées (solveur exact, parties mi-aléatoires mi-optimales, à partir du 6e coup), réseau résiduel de 1,0 million de paramètres, 20 minutes sur GPU.
- Précision sur 4 095 positions réservées : **94,4 % de coups optimaux au mieux (pas 2 000)**, puis **surapprentissage** (90,8 % à la fin des 56 000 pas). Le point de contrôle retenu est donc celui du pas 2 000.
- Mesure contre le jeu parfait (même protocole, réseau seul sans recherche, 40 parties) : 9 coups fautifs sur 361, soit **2,5 %**, résultat théorique atteint dans 80 % des parties. Ce n'est **pas meilleur** que Zéro (1,8 %) ni que le professeur (1,6 %).
- Conclusion honnête : le goulot est la quantité de données, pas le réseau. Étiqueter coûte ~0,4 s par position et par cœur ; 50 000 positions ne suffisent pas à un réseau d'un million de paramètres. Rien n'est promu dans Garry.
- Pistes : (1) plus de données avec un solveur plus rapide (meilleur ordre des coups, table plus grosse, étiquettes de score exact pour plus de signal par position) ; (2) combiner réseau + recherche courte au lieu du réseau seul ; (3) livre d'ouverture pour les 5 premiers coups.

## Étape 3 : livre d'ouverture et joueur parfait (31 octobre)
- **Livre du premier joueur** (`logic_arena/zero/c4_book.json`, 56 entrées, plis 0, 2 et 4) calculé avec le solveur sur 14 processus : coup central, puis toutes les colonnes qui conservent le gain.
- **Joueur parfait** (`c4perfect.py` : livre puis solveur exact) : **60 parties gagnées sur 60** en jouant premier (`training-lab/c4_oracle_check.py`), contre un adversaire aléatoire ou jouant au mieux avec probabilité 0,5 ou 1 après le 6e coup. C'est la garantie « gagner à coup sûr » côté Python ; elle n'est pas encore dans `multi` (solveur trop lourd pour le plan gratuit Cloudflare).
- **Réseau distillé + veto tactique** (jamais de perte forcée dans la limite de profondeur, gain forcé joué d'abord), contre le jeu parfait, 40 parties : profondeur 8 → 1,85 % de coups fautifs ; profondeur 14 → 2,4 %. Réseau seul : 2,5 %. Les écarts sont dans le bruit de mesure (environ ±0,7 point sur ~430 coups) : **la recherche tactique n'apporte pas de gain démontré**, les erreurs restantes sont stratégiques, pas tactiques.
- Conclusion : pour garantir un résultat parfait, il faut le livre + une recherche exacte (ou un livre beaucoup plus profond), pas un réseau seul. Prochaine étape pour `multi` : port TypeScript d'un solveur à budget de nœuds limité + livre en données, et validation par parité avec le solveur C++.
