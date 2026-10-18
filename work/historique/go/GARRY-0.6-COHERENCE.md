# Garry 0.6.0 — cohérence de l’arène

La maintenance adapte désormais les commandes à chaque jeu et au joueur réellement actif. Le modèle texte reste dans un autre projet ; le lien **Input** ouvre `http://127.0.0.1:8766/` dans le même onglet.

## Jouer

Les quatorze jeux sont jouables manuellement. En solo manuel, les niveaux, styles, commandes de lecture et recherche de l’IA sont masqués. En duel, les réglages de l’adversaire restent accessibles. Le bouton de coup unique est réservé à l’observation des IA. Les coups illégaux, cases occupées et directions sans effet ne sont pas proposés.

| Jeux | Commande humaine | Particularité visible |
| --- | --- | --- |
| Morpion, Puissance 4 | Case ou colonne légale | X/O ou rouge/jaune |
| 2048 | Boutons de direction ou flèches du clavier | Tuiles affichées en lecture seule |
| Sudoku | Case, chiffre, annulation | Trois vies en mode IA ; difficulté de grille distincte du niveau |
| Démineur | Case cachée | Premier clic protégé |
| Taquin | Tuile voisine du vide | Tailles 3, 4 et 5 ; difficulté de grille distincte du niveau |
| Reversi | Case légale ; passe si nécessaire | Noir/blanc |
| Nim | Nombre d’allumettes retirées d’un tas | Le dernier retrait gagne |
| Lights Out | Lampe | Les voisines en croix basculent |
| Dames, Percée | Pièce puis destination légale | Rafle obligatoire aux dames |
| Hex | Case ; échange à l’ouverture | Bords à connecter indiqués |
| Gomoku | Pierre ; choix de couleur lors du Swap2 | Cinq exacts |
| Go | Intersection, passe, comptage ou abandon | Noir/blanc, komi et égalité correctement affichés |

Une partie Go terminée masque ses actions. Une égalité avec un komi permettant les scores égaux est affichée comme une égalité, sans attribuer la victoire à Blanc. Un komi personnalisé reçu par le protocole reste visible dans le sélecteur.

## Niveaux et styles

Les niveaux 0 et 10 choisissent les pires et meilleurs coups **évalués**, avec la portée de la recherche disponible. Les niveaux intermédiaires des puzzles utilisent une fréquence croissante de meilleurs coups. Des niveaux différents peuvent donc produire des coups équivalents ; les réglages ne représentent pas une force Elo.

Le sélecteur de style montre seulement les préférences que le moteur prend effectivement en compte. Nim et Lights Out n’en proposent pas. Puissance 4 au niveau 10 choisit directement le résultat de la recherche. Les puzzles aux niveaux 1 à 9 suivent leur tirage de qualité et n’utilisent pas le style. Pour les autres situations, les libellés précisent si le style influence une évaluation stratégique ou départage uniquement des coups de même qualité. Le réseau seul peut conserver les mêmes décisions malgré le style.

## Jeux réels et apprentissage

Les commandes et métriques du panneau externe changent selon le jeu. Les mesures de sondes 2048 sont masquées au Go. Un lancement en cours bloque les réglages de la prochaine partie ; les traces apparaissent seulement lorsqu’elles existent. Les anciennes sessions sans mise à jour sont signalées, sans réécriture de leurs journaux. La partie réelle Go arrêtée après 252 coups n’a pas de résultat final établi et n’a pas été relancée.

La première heure terminée a produit **271 174 coups**, **1 778 cycles** et **49 promotions**. Son évaluation finale mesure l’accord avec le professeur borné : Go **7,54 → 19,74 %** sur 4 732 positions ; Hex **28,68 → 44,06 %** sur 774 ; Gomoku **17,86 → 22,55 %** sur 980. Ce sont des résultats internes au protocole de cette session, sans preuve d’invincibilité.

Un audit de la reprise a révélé des recoupements avec des lots réservés d’anciennes sessions. Cette reprise a été arrêtée, ses résultats marqués non valides pour l’évaluation entre sessions et sa promotion écartée. Ses fichiers sont conservés ; les poids de départ de cette reprise ont été restaurés. Le mécanisme inclut désormais une quarantaine de tous les états historiques, avec index invalidé si sa source change, et une graine différente par session. La nouvelle heure protégée, identifiant `5ed011499eae4dac96a63e9c83244eff`, était réellement active après correction, avec **66 890 états historiques exclus**. Un contrôle de ses 2 281 premières nouvelles positions n’a trouvé aucun recoupement. Sa fin prévue était le **17 octobre à 21 h 59 (Paris)** ; son dossier de statut fait foi pour l’état ultérieur.

## Vérification

**107 tests Python et 65 tests JavaScript réussis.** Le parcours navigateur a joué un coup humain dans chacun des quatorze jeux, sur ordinateur et mobile, sans erreur JavaScript ni débordement horizontal. Il a aussi vérifié les flèches 2048, l’annulation au sudoku, la fin du Go par comptage, l’égalité au Go, les 31 coups minimaux du taquin Expert 3 × 3, un entraînement local, l’import/export du modèle et une requête du protocole.

Ces parcours couvrent les flux vérifiés, pas toutes les positions de tous les jeux. Les recherches bornées des grands plateaux et les règles de fin de Go avec appréciation des groupes restent des limites de jeu réelles.
