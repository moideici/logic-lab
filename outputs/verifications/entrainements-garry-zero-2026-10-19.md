# Entraînements du 18 au 19 octobre 2026 : Garry 0.6 et Garry Zéro (Puissance 4, Go 9×9)

## 1. Garry 0.6 (le vrai Garry), session de 60 minutes, profil « points faibles »

Méthode actuelle : imitation d'un professeur borné, avec promotion d'un candidat seulement s'il fait au moins aussi bien que le champion sur validation et sur positions fraîches. Poids de départ : empreinte `ae54c06d…` (sauvegardés dans `projets/garry/training-runs/sauvegardes/` et `work/`) ; poids d'arrivée : `a604d324…`.

614 cycles, 154 688 coups d'entraînement, **16 promotions**. Accord optimal avec le professeur sur positions réservées :

| Jeu | Avant | Après |
|---|---|---|
| Go (4 460 positions) | 14,62 % | **14,46 %** (pas d'amélioration) |
| Hex (256) | 43,36 % | 44,92 % |
| Gomoku (340) | 19,12 % | 22,65 % |

Les onze autres jeux sont préservés (contrôle de non-régression). 174 tests Python et 65 tests JavaScript passent avec les nouveaux poids. L'évaluation du rapport le dit elle-même : accord avec un professeur borné, **pas une force de jeu certifiée**. Conclusion : l'imitation sur ce professeur a atteint son plateau, surtout au Go ; c'est la motivation de Garry Zéro.

## 2. Garry Zéro, Puissance 4 (auto-apprentissage, sans professeur)

149 itérations, environ 28 600 parties d'auto-apprentissage en une heure ; réseau de 304 300 paramètres, recherche de 100 simulations (200 en duel).

**Correction d'une première lecture.** Les duels du journal (40 parties, depuis le plateau vide) montraient 100 % contre le professeur niveau 10 à partir de l'itération 90. C'était un artefact : le réseau et le professeur sont déterministes, donc les parties se répétaient. Avec **des ouvertures aléatoires de 4 coups, identiques par paire de parties (camps échangés), 100 parties** par adversaire (point de contrôle de l'itération 149) :

| Adversaire | Victoires | Nuls | Défaites | Score |
|---|---|---|---|---|
| Aléatoire | 100 | 0 | 0 | 1,000 |
| Professeur niveau 10 | 43 | 14 | 43 | 0,500 |
| **Garry 0.6.0 niveau 10** | 37 | 11 | 52 | **0,425** |

Zéro égale le professeur de niveau 10 et reste un peu en dessous de Garry 0.6.0 (qui combine réseau et recherche alpha-bêta profonde). Il est passé de 25 % contre le niveau 10 (itération 10) à ce niveau sans aucun professeur. Il ne dépasse pas encore les références : il faut plus de calcul, une recherche plus longue, ou un réseau plus gros. Courbe d'apprentissage bruyante au début (scores de 0,06 à 0,99 contre le niveau 10 d'un point de contrôle au suivant, sur des parties répétées).

## 3. Garry Zéro, Go 9×9 (en cours au moment de ce rapport)

Moteur de Go en C++ identique aux règles de Garry (plateaux, coups légaux et scores de surface vérifiés sur des parties aléatoires). 63 itérations, environ 8 000 parties d'auto-apprentissage : perte de politique 2,40, perte de valeur 0,45 (le Go converge bien plus lentement que Puissance 4), parties de 92 coups en moyenne.

Duels toutes les 10 itérations, 20 parties : **20 victoires sur 20 contre Garry niveau 1 et niveau 4** à chaque point de contrôle depuis l'itération 10, 19 à 20 sur 20 contre l'aléatoire. Parties examinées à la main : coups plausibles, victoires de 2,5 points. Ce résultat confirme surtout la faiblesse connue du Go actuel de Garry ; il ne mesure pas la vraie force de Zéro. Le test de référence est **COSUMI** (moteur indépendant, site réel) : pas encore fait.

## Limites

- Garry : mesures d'accord avec le professeur, pas de duels contre l'ancienne version ni de campagne complète.
- Zéro Puissance 4 : une graine, une session ; 100 parties par adversaire avec des ouvertures aléatoires (des positions peuvent être déséquilibrées, compensé par l'échange des camps).
- Zéro Go : pas de test contre un adversaire indépendant ; 20 parties par duel ; score de surface sans retrait de pierres mortes ; superko arbitré par Garry en duel mais pas dans l'entraînement.
