> Document historique avant Garry 3.0.0. Voir [la progression appliquée](GARRY-3-PROGRESSION.md) pour cette étape ; voir aussi [le cycle de diversité 3.1.0](GARRY-DIVERSITE.md).

# Garry : entraînement réalisé et prochain cap

État au 16 octobre 2026. Projet : `%USERPROFILE%\code\playi`.

Garry a été entraîné et un candidat ciblé sur Puissance 4 a été installé. L'architecture et le code d'inférence restent ceux de **Garry 2.0.0**. Les poids portent la révision `20261016-c4-guarded-01` ; les performances ne déterminent pas le numéro de version.

## Ce qui a réellement progressé

Le candidat installé a reçu 163 840 présentations d'exemples sur 4 096 positions uniques de Puissance 4. Les poids centraux et tous les paramètres effectifs des cinq autres modes sont restés strictement identiques. Cette protection a été vérifiée sur les matrices, et pas seulement sur quelques parties.

| Contrôle | Avant | Après |
|---|---:|---:|
| Réseau seul, victoires contre un adversaire aléatoire, 200 parties | 127 | 144 |
| Réseau seul, défaites sur ces mêmes graines | 72 | 56 |
| Réseau seul, nuls | 1 | 0 |
| Avec recherche, victoires contre la référence 1.0.0, 40 parties | 30 | 30 |
| Avec recherche, défaites | 6 | 6 |
| Avec recherche, nuls | 4 | 4 |

Le réseau seul passe donc de 63,5 % à 72 % de victoires sur ce lot. Les défaites passent de 36 % à 28 %. **Aucun gain de résultat du système hybride n'est démontré par le contrôle de 40 parties.** L'objectif de zéro défaite n'est toujours pas atteint.

Les deux versions du contrôle hybride utilisent le même moteur et trois millions de nœuds par décision. Leur adversaire figé utilise son ancien moteur avec 5 000 nœuds. Ce contrôle mesure l'effet des nouveaux poids ; il ne compare pas les deux générations à temps égal. Les camps alternent et chaque ouverture de six coups est rejouée dans les deux camps.

Les 55 tests automatisés passent. Les anciens poids sont sauvegardés dans le dossier de l'essai ; le remplacement du fichier actif a été atomique. Le rapport suivi dans le dépôt est `web/models/garry-training.json`.

## Ce que les essais ont révélé

Trois essais ont été réalisés, avec sauvegardes séparées :

| Essai | Présentations d'exemples | Résultat et décision |
|---|---:|---|
| Apprentissage commun initial, 60 époques | 368 640 | Imitation améliorée, résultats de jeu dégradés ; rejeté |
| Apprentissage commun sur positions dédupliquées, 60 époques | 1 295 280 | Puissance 4 amélioré sur le réseau seul, progression au sudoku dégradée ; rejeté |
| Apprentissage ciblé avec protection des autres modes, 40 époques | 163 840 | Réseau Puissance 4 amélioré, autres modes préservés, contrôle hybride sans régression observée ; installé |

Dans le premier essai, 1 024 exemples de morpion ne contenaient que **9 positions distinctes**. Les 1 024 exemples de Puissance 4 n'en contenaient que **66**. Des graines différentes produisaient des trajectoires presque identiques. Une validation par graines ne suffisait donc pas à mesurer la généralisation.

Le deuxième essai a corrigé cela : 3 598 positions d'apprentissage au morpion, 4 096 par autre jeu et 512 positions de validation par jeu, sans chevauchement exact. Les symétries du morpion sont séparées entre apprentissage et validation. La collecte introduit des ouvertures variées à Puissance 4.

Ce deuxième essai montre aussi une interférence entre les tâches : à Puissance 4, les victoires du réseau seul passent de 32 à 38 sur 50 parties ; au sudoku, les cases remplies en moyenne passent de 8,60 à 4,72, avec zéro résolution des deux côtés. Une meilleure imitation moyenne ne suffit donc pas à sélectionner un modèle.

Les nouveaux outils distinguent désormais une partie résolue, une défaite, un dépassement de la limite de coups et un gain de score. Un simple dépassement de limite ne compte pas comme un progrès.

## Le prochain cap prioritaire : apprendre à évaluer les positions

Aujourd'hui, le réseau produit des scores de coups. À Puissance 4, il aide principalement à ordonner la recherche. L'évaluation des positions en profondeur repose encore sur des règles programmées. Cela explique pourquoi une amélioration du réseau seul peut ne pas changer les résultats du système complet.

Je recommande de faire prédire à un même modèle :

1. Les coups prometteurs, avec leur distribution plutôt qu'une seule étiquette rigide.
2. L'issue probable : victoire, nul ou défaite.
3. Lorsque l'objectif le permet, une estimation des coups restant avant la réussite.

La première expérience devrait utiliser Puissance 4, avec l'encodeur actuel, pour isoler l'apport de cette estimation. La recherche consulterait alors la valeur apprise aux positions qu'elle ne peut pas explorer jusqu'au bout. Les victoires et menaces prouvées continueraient à avoir priorité sur les estimations du réseau.

Le principe « politique + estimation de l'issue + recherche + parties générées par l'agent » est étayé par [AlphaZero](https://arxiv.org/pdf/1712.01815). C'est une direction d'expérimentation pour Garry, pas une promesse de reproduire ses résultats ou ses moyens de calcul. L'étude d'AlphaZero entraînait des instances distinctes selon les jeux ; notre objectif de poids communs aux six modes ajoute une difficulté.

## Boucle d'apprentissage à construire

Une génération joue contre plusieurs adversaires : l'ancienne référence, des versions récentes de Garry, un adversaire aléatoire et des joueurs tactiques. Les parties conservent les états publics, les coups explorés, le résultat final et le budget de réflexion. Les défaites alimentent une réserve de situations difficiles ; les anciennes compétences alimentent une réserve de protection.

Le réseau apprend ensuite la distribution proposée par une recherche plus forte et les résultats réellement obtenus. Le candidat est évalué séparément avant toute promotion. Cette boucle réduit la dépendance à l'imitation d'un professeur fixe et peut exploiter les erreurs propres à Garry.

Les données doivent couvrir les fins de partie, les pièges tactiques et les états difficiles. Pour 2048, cela implique des plateaux encombrés et de grandes tuiles, au-delà des seuls débuts de partie. Pour le sudoku, le générateur actuel transforme surtout une même grille de départ : il faut ajouter d'autres grilles à solution unique et plusieurs difficultés pour parler d'une compétence générale au sudoku.

## Protéger le modèle général

Le gel ciblé employé dans l'essai retenu est une protection utile à court terme. Il ne résout pas l'apprentissage commun à long terme, puisqu'il empêche les représentations centrales de progresser pendant cet essai.

Pour continuer à apprendre ensemble, je recommande des lots équilibrés, la répétition de compétences anciennes et un contrôle des régressions par jeu. On pourra ensuite mesurer les conflits entre gradients. Si ces conflits sont fréquents, une méthode comme [PCGrad](https://arxiv.org/abs/2001.06782) constitue une piste à tester ; elle n'est pas encore implémentée et son bénéfice pour Garry reste à mesurer.

La sélection doit surveiller le jeu le plus dégradé, et pas seulement la moyenne des six jeux. Les jeux déjà résolus exactement restent des garde-fous et des sources d'exemples ; l'essentiel de l'effort de progression doit porter sur Puissance 4, 2048 et le démineur.

## Architecture à tester après la valeur apprise

La fusion actuelle est un MLP de 134 258 paramètres, avec un passage central de 48 neurones. Les jeux utilisent des zones d'entrée distinctes. C'est un modèle unique, mais il dispose de peu de structure explicite pour représenter les relations spatiales entre cases.

Une évolution plausible serait un encodeur de plateau commun : une case devient une représentation de sa ligne, de sa colonne, de son contenu et de son état visible ; l'identifiant du jeu donne le contexte. Des couches résiduelles ou de l'attention pourraient partager des notions spatiales entre les modes.

Cela reste une hypothèse à comparer à un MLP plus large. Il faut mesurer séparément l'apport de la capacité, de la structure spatiale et de la valeur apprise. Un réseau plus gros peut ralentir la recherche et annuler le gain de qualité. La RTX 4060 de 8 Go détectée sur la machine peut servir aux futurs entraînements ; les essais actuels, de petite taille, ont utilisé NumPy sur CPU.

Le modèle resterait un seul artefact avec des paramètres communs. Une nouvelle version majeure sera justifiée lorsque son architecture ou ses dimensions changeront effectivement, après validation des prototypes.

## Adapter la recherche aux règles

| Jeu | Prochaine priorité |
|---|---|
| Morpion | Garder le solveur exact ; vérifier aussi les décisions du réseau seul sur les 4 520 états jouables |
| Puissance 4 | Valeur apprise, réserve de pièges, parties contre plusieurs générations, comparaison à temps égal |
| 2048 | Valeur tenant compte des apparitions aléatoires et apprentissage des positions encombrées |
| Sudoku | Diversité de grilles, récupération après erreur et distinction entre coup légal et coup compatible avec une solution |
| Démineur | Probabilités calibrées à partir des seules observations publiques ; conserver la priorité absolue aux coups prouvés sûrs |
| Taquin | Garder la table exacte comme professeur et garantie de chemin minimal |

Une recherche conçue pour un duel entièrement observable ne s'applique pas directement au hasard de 2048 ni aux informations cachées du démineur. Pour ce dernier, les simulations doivent partir de configurations compatibles avec les indices visibles, et jamais des mines cachées de la partie réelle.

## Critères pour déclarer un cap franchi

- Une baisse reproductible des défaites contre les références fortes, avec les mêmes budgets de temps.
- Des résultats séparés pour le réseau seul et le système avec recherche.
- Aucun recul important sur les autres jeux, y compris la progression quand aucune partie n'est résolue.
- Des ouvertures, positions et graines de contrôle indépendantes des données qui servent à choisir les checkpoints.
- Des mesures du temps de décision et du nombre de coups, en plus des victoires.
- Plusieurs lots de contrôle ; zéro défaite observée sur un lot reste distinct d'une garantie universelle.

La prochaine réalisation la plus utile est donc un prototype **valeur apprise + génération de parties + recherche guidée**, d'abord sur Puissance 4, avant de généraliser aux jeux stochastiques et à information cachée.
