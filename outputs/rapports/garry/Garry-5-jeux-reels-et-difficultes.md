# Garry 5.0.0 — jeux, difficultés et parties réelles

L’arène est accessible sur [http://127.0.0.1:8765](http://127.0.0.1:8765). Le serveur est laissé en marche. Si une ancienne page est ouverte, l’actualiser pour charger les nouveaux contrôles.

## Sudoku et taquin

Sudoku propose **Facile, Moyen, Difficile et Expert**, indépendamment du niveau 0–10 de Garry. Les **45 grilles** ont été vérifiées à solution unique. Le classement utilise un solveur fixe : singles, singles cachés, puis recherche. Expert sélectionne son record : une grille de 23 indices, avec un score de 154 216. Ce score est propre à cette méthode ; il ne certifie pas le sudoku le plus difficile au monde. Il n’existe pas de définition universelle de cette difficulté. Le catalogue Expert contient actuellement une seule grille.

Le sudoku peut être joué à la main : choisir une case vide, puis un chiffre ; « Annuler » retire la dernière saisie. Garry a résolu Expert en **58 saisies, sans annulation**.

| Taquin | Difficultés | Garantie |
|---|---|---|
| 3 × 3 | Facile, Moyen, Difficile, Expert | Distances minimales exactes ; Expert exige 31 coups, maximum sur tous les états résolubles. |
| 4 × 4 | Les quatre difficultés | Grilles résolubles par construction ; mélange et borne de Manhattan croissants. |
| 5 × 5 | Les quatre difficultés | Même garantie de résolubilité ; mélanges plus longs et bornes plus élevées. |

Les catégories 3 × 3 couvrent respectivement 1–8, 9–16, 17–24 et 31 coups minimaux. Les catégories 4 × 4 et 5 × 5 ne certifient pas un maximum absolu. Garry utilise A* sur le plateau public et conserve les chemins complets trouvés. Il indique quand un chemin minimal est démontré ; sinon sa recherche reste bornée. Les nouvelles tailles utilisent 81 caractéristiques, sans agrandir encore le réseau. Leurs poids neuronaux n’ont pas reçu d’entraînement spécifique : leur résolution dépend actuellement de la recherche. Le joueur peut déplacer les tuiles voisines du vide en cliquant.

## Deux nouveaux duels

L’arène passe à **treize jeux** avec **Hex 7 × 7**, échange des couleurs après le premier coup, et **Gomoku 15 × 15 Swap2**, victoire par cinq pierres exactes, sans victoire par suralignement.

Les ouvertures Swap2 gèrent les trois premières pierres posées par le premier joueur, le choix des couleurs ou l’ajout de deux pierres par le second, puis le choix final. Les règles sont comparées entre Python et JavaScript sur des parties complètes. Ces jeux disposent d’une scène compétitive ; Garry joue ici des duels locaux. Aucun classement en ligne contre des humains n’a été testé.

Sources : [règles de Hex](https://www.hexwiki.net/index.php/Rules), [calendrier des championnats Little Golem](https://docs.littlegolem.net/tournaments/calendar/), [règles officielles Gomoku et Swap2](https://gomoku.renju.net/gomokurules/), [Brno Cup Swap2](https://gomoku.renju.net/tournament/3533/).

Pour les prochains ajouts : **Quoridor** pour les chemins et barrières, puis **Abalone** pour les poussées et les formations. Ils ne sont pas encore implémentés.

## Apprentissage et versions

Garry reste un seul fichier et un seul ensemble de matrices. Son architecture devient **3 055 → 48 → 48 → 3 894**, soit **339 878 paramètres**. Cette extension des dimensions justifie **5.0.0** ; les performances ne déterminent pas ce numéro. La 4.0.0 est conservée avec son manifeste dans le dépôt.

Les poids utilisés par les onze jeux précédents, leurs indicateurs de jeu, le module central, les biais, l’évaluateur de Puissance 4 et sa mémoire sont préservés. Leur conservation a été vérifiée.

| Premier apprentissage | Positions entraînées | Positions de test réservées | Accord avec le professeur avant → après |
|---|---:|---:|---:|
| Hex | 180 | 50 | 24 % → 44 % |
| Gomoku | 180 | 50 | 0 % → 10 % |

Chaque jeu dispose aussi de 50 positions de validation. Ces taux mesurent l’accord avec un professeur borné, pas des victoires ni des coups mathématiquement optimaux. La recherche tactique reste essentielle, particulièrement au Gomoku.

Le cycle supplémentaire dames/Percée a varié les adversaires et produit 920 nouvelles positions. Aucun candidat n’a passé tous les contrôles de conservation : les poids précédents ont donc été gardés. Le magasin comprend maintenant **5 717 épreuves d’apprentissage**, sans les validations ni les tests réservés.

## Le vrai site 2048

L’onglet **Jeux réels** permet de lancer Garry sur [2048 original](https://classic.play2048.co/), de suivre la capture du plateau et d’arrêter la partie. Le navigateur lit les tuiles visibles et le score, puis utilise les touches directionnelles. Il ne remplace ni le plateau ni les tirages. Chaque transition vérifie la fusion, son score et l’apparition d’une unique tuile 2 ou 4. Garry continue après 2048 jusqu’à la fin de la partie.

| Partie complète | Score du site | Meilleure tuile | Coups vérifiés |
|---|---:|---:|---:|
| Garry avec recherche | **71 496** | **4096** | **3 277** |
| Réseau seul | 1 112 | 128 | 118 |
| Référence aléatoire | 584 | 64 | 80 |

Une seule partie par mode, avec des tirages différents : ce tableau fournit une première référence, pas une mesure statistique de progression. Le premier essai partiel interrompu par la fenêtre de cookies est conservé dans l’historique avec son erreur et exclu de ces parties complètes.

Sur la partie Garry, 132 sondes comparent les décisions à une analyse plus longue : **113 accords, soit 85,6 %**. L’écart moyen d’évaluation est 19 016,8 unités internes ; ce ne sont pas des points de score à gagner. Le harnais conserve traces, captures, budgets et empreintes du modèle. La représentation passe à des tableaux pour les très grandes tuiles, afin d’éviter la limite de la représentation compacte au-delà de 32 768.

2048 est le premier adaptateur externe disponible. Les autres jeux restent dans l’arène locale. L’accès au site réel nécessite le serveur Python, Node et Playwright ; la procédure d’installation est dans le README du dépôt.

## Vérification

**86 tests Python et 48 tests JavaScript réussis, soit 134 tests.** Les contrôles couvrent règles, actions légales, migrations, conservation des anciens poids, parité entre langages, unicité des sudokus, permutations résolubles, Expert 3 × 3, recherche sur grandes grilles et transitions du site réel.

Les parcours navigateur ont aussi été vérifiés : Hex et Gomoku dans le worker, sélection des difficultés, taquin 5 × 5 à la main, sudoku avec saisie et annulation, résolution, historique 2048, lancement et arrêt d’une partie réelle, et affichage mobile sans débordement horizontal.

Les mesures détaillées se trouvent dans `garry-5-mesures.json`, avec les captures de l’interface. Ces résultats ne constituent pas une preuve d’invincibilité sur les nouveaux jeux.
