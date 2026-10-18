# Trois modèles ambitieux dans l'esprit de Garry (18 octobre 2026)

Constat de départ : Garry est le modèle abouti du projet (14 jeux, un cœur partagé, niveaux 0 à 10, harnais sur sites réels). Les expériences du Lab (Graine, Loop) étaient des tests ; ces trois propositions visent le même niveau d'ambition que Garry, avec un critère de réussite mesurable pour chacune. Matériel de référence : une RTX 4060 de 8 Go.

## 1. Garry Zéro : apprendre par soi-même, sans professeur

**L'idée.** Aujourd'hui Garry apprend en imitant un « professeur » écrit à la main, à la recherche bornée : il ne peut donc pas le dépasser, et c'est pourquoi le Go reste faible (défaite de 285,5 points contre COSUMI niveau 1). Garry Zéro joue contre lui-même : un réseau (politique + valeur) guide une recherche arborescente (MCTS), les parties produisent les exemples, le réseau s'améliore, la recherche aussi. Le professeur disparaît.

**Pourquoi c'est ambitieux.** C'est la voie qui a donné les meilleurs joueurs de Go, d'échecs et de shogi. Elle peut faire passer Garry de « bon imitateur » à « meilleur que ses références ».

**Critères de réussite (à fixer avant).**
- Jeux courts d'abord (Puissance 4, Hex 7×7, Gomoku 9×9) : Zéro bat Garry 0.6.0 et le professeur niveau 10 en duels depuis le plateau vide, dans les deux camps, avec au moins 60 % de victoires sur 100 parties.
- Go 9×9 : Zéro gagne contre COSUMI niveau 1 puis niveau 3 sur le site réel (jeux réels réparés).

**Risques, honnêtement.**
- Coût de calcul : l'auto-apprentissage demande des centaines de milliers de parties ; sur une carte de 8 Go, Puissance 4 et Hex 7×7 sont réalisables en heures ou jours, le Go 9×9 demande une version réduite et de la patience.
- Vitesse de la recherche : il faut un moteur de règles rapide (les moteurs JavaScript/WASM existent pour certains jeux) et une inférence par lots.
- Premier jalon réaliste : Puissance 4 (jeu résolu, donc évaluation exacte possible).

## 2. Garry Règles : un joueur universel qui lit les règles

**L'idée.** Un seul réseau qui joue à **n'importe quel jeu décrit par ses règles**, y compris un jeu jamais vu. On entraîne sur un générateur de jeux (alignement de k pions sur un plateau m×n, tailles, règles de capture, conditions de victoire) et sur dix des quatorze jeux de Garry ; on teste sur les quatre jeux écartés.

**Pourquoi c'est ambitieux.** Ce n'est plus « un modèle par jeu avec un cœur commun » mais un modèle qui généralise à des règles nouvelles : une forme de joueur général. Rare à cette échelle sur du matériel individuel.

**Critères de réussite.**
- Sur un jeu écarté jamais vu, victoire contre un joueur aléatoire à plus de 80 % sans réentraînement, et supérieure à un Garry non adapté.
- Courbe : plus on entraîne de jeux différents, mieux il joue sur un jeu inconnu.

**Risques.** Représenter les règles de façon uniforme est le vrai travail ; le résultat honnête peut être « il généralise mal » (ce qui serait déjà un résultat). Pari élevé, étapes courtes : commencer par la famille des jeux d'alignement (morpion, Gomoku, Puissance 4 comme cas particuliers d'un même générateur).

## 3. Garry Délibération : réfléchir plus longtemps, appris

**L'idée.** Remplacer les niveaux 0 à 10 (recherches écrites à la main de plus en plus longues) par un **cœur récurrent** dont le niveau est le nombre de passes de réflexion. Les mêmes poids jouent aux jeux de plateau et résolvent les puzzles de Garry (sudoku, taquin, Lights Out, démineur).

**Pourquoi c'est ambitieux et crédible.** Le Lab l'a déjà montré sur un seul problème : le Loop 6×6 passe de 75 % à 89 % de grilles dures résolues en ajoutant des passes, sans réentraînement, et son temps de réflexion croît avec la difficulté. L'étendre à l'ensemble de Garry en fait un modèle à calcul variable appris, au lieu d'un moteur de recherche externe.

**Critères de réussite.**
- La force de jeu augmente avec le nombre de passes (mesure en arène par niveaux de passes), au moins jusqu'à égaler la version actuelle du niveau 10 à temps de calcul égal.
- Un seul modèle récurrent résout les quatre puzzles de Garry à un niveau au moins égal à leurs solveurs actuels.

**Risques.** Les jeux à information adverse sont plus durs que les puzzles ; le gain face à une recherche arborescente classique n'est pas garanti. Lien naturel avec Zéro : le cœur récurrent peut servir de réseau de politique-valeur.

## Ordre que je recommande

1. **Zéro d'abord sur Puissance 4 puis Hex 7×7** : le jalon le plus mesurable (duels, jeu résolu), et il s'attaque à la vraie faiblesse de Garry.
2. **Délibération** ensuite : elle s'appuie sur le Loop déjà validé et améliore Zéro.
3. **Règles** en pari, après deux jalons.

Aucune de ces trois pistes n'est lancée ; l'entraînement de Garry 0.6.0 par la méthode actuelle (imitation gardée, profil « points faibles ») a été relancé séparément et sert de référence.
