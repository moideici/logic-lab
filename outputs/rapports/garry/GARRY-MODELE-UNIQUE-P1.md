# Garry Optimus 0.1 (modèle unique multi-jeux) — pilote P1 (9 novembre 2026)

Cadrage : `GARRY-MODELE-UNIQUE-CADRAGE.md` ; P0 : `GARRY-MODELE-UNIQUE-P0.md`. Question : à budget égal en exemples par jeu, un réseau multi-jeux fait-il mieux qu'un réseau par jeu ?

## Protocole
Tronc résiduel 6 × 64, entrées propres à chaque jeu, tête de politique par case partagée entre les jeux de pose, tête de dames séparée, tête de valeur par jeu. Distillation des professeurs (positions de P0), symétries du plateau (8 pour morpion et Gomoku, miroir pour Puissance 4, rotation 180° pour Hex), 30 000 pas × 256 positions, deux graines. Les trois bras voient le même nombre d'exemples par jeu :
- **mono** : un réseau par jeu (513 545 paramètres, dames 1 434 121), 6 000 pas chacun, soit 3,5 M de paramètres au total ;
- **multi** : un réseau pour les cinq jeux (1 705 306 paramètres), 30 000 pas ;
- **famille** : un réseau pour les jeux de pose (715 349) + un réseau de dames.
Mesure : réseau seul, sans recherche, contre les juges indépendants de P0 (30 parties Hex et Gomoku à 100 ms, 24 Puissance 4, 30 dames normal, 20 difficile, 40 morpion par camp).

## Résultats (moyenne de 2 graines)
| Jeu (juge) | mono | famille | multi | Référence P0 |
|---|---|---|---|---|
| Morpion : défaites contre le parfait | 0 | 0 | 0 | professeur 0 |
| Puissance 4 : coups fautifs | 2,3 % | 2,1 % | **1,5 %** | Garry 0.6.0 niveau 10 : 2,4 % ; professeur : 0 % |
| Hex : score contre le moteur (100 ms) | 0,58 | **0,70** | 0,62 | moteur contre lui-même ≈ 0,5 |
| Gomoku : score contre le moteur | 0,10 | 0,10 | **0,17** | idem |
| Dames normal / difficile | 0,43 / 0,20 | 0,43 / 0,20 | 0,39 / 0,20 | professeur 0,93 / 0,75 |

Validation hors-ligne (accord avec le meilleur coup du professeur) : équivalente pour les trois bras (Hex 0,83 à 0,88, Gomoku 0,65 à 0,67, Puissance 4 0,94 à 0,95, dames 0,62 à 0,65 avec le multi légèrement derrière).

## Verdict
- **Le seuil du cadrage est atteint sur le papier** (multi devant mono à Puissance 4, Hex et Gomoku, derrière aux dames, égal ailleurs : 3 jeux sur 5) **mais aucun écart n'est significatif** : l'écart-type d'une mesure de score est d'environ 0,09 (0,065 sur deux graines), celui du taux de coups fautifs d'environ 0,8 point. La validation hors-ligne ne montre aucun gain.
- Ce qui est établi : **le multi-jeux n'est pas moins bon que les réseaux séparés et tient avec la moitié des paramètres** (1,7 M contre 3,5 M). Ce qui n'est pas établi : qu'il améliore les jeux.
- Un fait utile : sans recherche, le réseau égale déjà Garry 0.6.0 au Puissance 4 (1,5 à 2,3 % de coups fautifs contre 2,4 %) et bat le moteur Hex à 100 ms dans plus de la moitié des parties (0,58 à 0,70). Il reste très en dessous aux dames (0,4 contre le bot normal) et au Gomoku (0,10 à 0,17).
- Le jeu de dames (520 000 positions) domine en volume ; Hex et Gomoku n'ont que 33 000 à 35 000 positions : ils sont limités par les données, pas par le réseau.

## Limites
Petits échantillons ; une seule taille de réseau (0,5 à 1,7 M) ; sélection de points de contrôle non faite (dernier pas) ; réseau seul sans recherche ; juges Hex et Gomoku dépendants du temps mural.

## Suite proposée (par ordre de coût)
1. **Test de transfert** (≈ 15 minutes de GPU) : réseau multi-jeux sans Hex, puis ajout de Hex avec 10 % des données, contre un réseau Hex entraîné de zéro. C'est le test le plus sensible pour savoir si les jeux se transmettent quelque chose.
2. Plus de données Hex et Gomoku (≈ 2 minutes pour 30 000 positions) pour retirer le goulot des données.
3. P2 : tronc plus gros (≈ 7 M) si les deux premiers montrent un signal ; sinon abandon du multi-jeux comme levier de force, conservé comme levier de compacité.
