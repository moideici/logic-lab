# Graine : un réseau qui pousse et s'élague bat-il un réseau fixe ? (18 octobre 2026)

**Réponse courte : non, pas sur ces trois jeux.** À taille finale égale, un réseau fixe entraîné directement fait aussi bien ou mieux que Graine ; Graine ne trouve pas de réseau plus petit ou plus précis que ce qu'une simple recherche de taille donnerait.

## Protocole

Trois jeux (morpion, Nim, Puissance 4), un professeur (`ReferenceAgent`, niveau 10 pour morpion et Nim, niveau 8 avec 30 ms par coup pour Puissance 4), des positions **variées** (la partie avance avec un coup aléatoire de probabilité 0,35, l'étiquette est toujours le coup du professeur). Réseau à deux couches cachées de même largeur, 3 000 pas, lot de 128, trois graines. Données train / validation / test séparées par graines de parties (test jamais vu à l'entraînement ni pour choisir). Mesure : **accord** = part des positions de test où le réseau choisit le coup du professeur. Code : `projets/garry/logic_arena/labtrain.py`, `training-lab/experience_graine.py` ; résultats bruts : `training-lab/results/graine-*.json` (non versionnés, relançables par `training-lab/lancer_experiences.sh`).

Trois règles de Graine, toutes avec départ à 2 + 2 neurones :
- **A (prudente)** : croissance de 2 neurones par couche quand la validation gagne moins de 3 % sur deux évaluations ; élagage tous les 400 pas des neurones dont l'extinction coûte moins de 0,001 de perte.
- **B (croît vite, élague à la fin)** : croissance si le gain est inférieur à 6 % sur une évaluation ; élagage seulement après 60 % des pas, avec tolérance de 1 % de la perte.
- **C (croît seule)** : comme B, sans élagage.

Pour chaque Graine, un réseau fixe **de la même taille finale** est entraîné avec la même graine et le même budget.

## Résultats (accord de test, moyenne de 3 graines)

**Morpion**

| Réseau | Paramètres | Accord |
|---|---|---|
| fixe 2+2 / 4+4 / 8+8 / 16+16 / 48+48 | 71 / 141 / 305 / 729 / 3 705 | 0,767 / 0,825 / 0,898 / 0,954 / 0,988 |
| Graine A (→ 5 à 7 neurones par couche) | 206 | 0,812, fixe de même taille : **0,873** |
| Graine B (→ 12 à 15) | 546 | 0,924, fixe de même taille : **0,939** |
| Graine C (→ 30 à 32) | 1 900 | 0,940, fixe de même taille : **0,981** |

**Nim**

| Réseau | Paramètres | Accord |
|---|---|---|
| fixe 2+2 / 4+4 / 8+8 / 16+16 / 48+48 | 239 / 441 / 869 / 1 821 / 6 909 | 0,522 / 0,713 / 0,843 / 0,939 / 0,996 |
| Graine A (→ 6 à 7) | 687 | 0,711, fixe de même taille : 0,787 |
| Graine B (→ 14 à 15) | 1 632 | 0,911, fixe de même taille : 0,920 |
| Graine C (→ 18 à 30) | 2 831 | 0,941, fixe de même taille : 0,961 |

**Puissance 4** : accord de 0,35 à 0,39 pour **toutes** les tailles (4+4 à 60+60, Graine comprise). Le résultat est inconclusif : le jeu est bien plus dur (84 entrées, 7 colonnes) et le professeur, borné en temps, donne des étiquettes imparfaites sur seulement 6 129 positions d'entraînement. La force de jeu contre le professeur varie de façon incohérente avec la taille (0,07 pour 48+48, 0,60 pour 4+4) : 20 parties par mesure, trop peu.

## Lecture

- **À taille égale, Graine perd de 1 à 6 points d'accord** contre un réseau fixe (écart plus faible pour la règle B sur Nim, dans le bruit). Les neurones ajoutés en cours d'entraînement sont moins bien appris que ceux d'un réseau entraîné d'un bloc, et le redémarrage de l'optimiseur après chaque changement coûte aussi.
- **L'élagage n'apporte rien ici** : le réseau est déjà petit, presque tous les neurones servent. La règle C, sans élagage, finit plus grosse sans gagner en précision par paramètre.
- **Ce que Graine fait vraiment :** il trouve une taille raisonnable seul (14 à 15 neurones pour Nim avec la règle B, proche des 16 d'un réseau fixe à 0,939) sans qu'on ait à la deviner. Une recherche sur 4 ou 5 tailles fixes donne le même résultat pour un coût comparable.
- **Limites :** trois graines ; trois jeux dont un inconclusif ; 3 000 pas ; règles de Graine peu réglées (trois variantes comparées, pas de balayage) ; accord avec le professeur n'est pas la force de jeu (au morpion, 16+16 neurones et plus égalent le professeur de niveau 8 en jeu, alors que l'accord n'est que de 0,95 : l'accord est une mesure sévère).

## Conséquence

L'hypothèse « la croissance et l'élagage trouvent un réseau meilleur ou plus petit » **n'est pas confirmée**. Proposition : ne pas poursuivre sur Graine seule.
1. Garder l'outil dans le Lab comme **visualisation** (neurones qui naissent et disparaissent, comparaison en direct avec un réseau fixe), ce qui reste utile et pédagogique.
2. Passer à **Loop** (cœur récurrent) et au modèle de raisonnement. Graine pourra y servir de recherche de taille, pas de promesse de gain.
3. Si on reprend Graine : conserver l'état de l'optimiseur à travers les changements, initialiser les nouveaux neurones par le gradient (méthodes de type GradMax), et tester sur un jeu où les réseaux fixes ne saturent pas (Puissance 4 avec davantage de données et un professeur exact).
