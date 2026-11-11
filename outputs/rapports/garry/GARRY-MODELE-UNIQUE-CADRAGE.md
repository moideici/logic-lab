# Garry : un seul gros modèle pour tous les jeux — cadrage (9 novembre 2026)

> Nom retenu : **Garry Optimus 0.1** (9–11 novembre 2026).

Demande : un modèle « gros » unique pour tous les jeux, dont le fait d'être multi-jeux le rende **meilleur** à chaque jeu ; plusieurs jeux de poids acceptés si utile.

## 1. Ce qu'on sait déjà (preuves du projet)
- Garry 0.6.0 est déjà un réseau unique pour 14 jeux, mais petit (444 979 paramètres, MLP 4 872 → 48 → 48 → 4 259). Le **réseau seul n'est pas meilleur que la recherche** : Puissance 4, 2,4 % de coups fautifs (professeur 1,6 %), distillation du solveur 2,5 % ; dames : réseau seul 0,19 contre la recherche renforcée.
- Le projet signale déjà de l'**interférence entre jeux** (§12 du plan) et un goulot de **données**, pas de taille (distillation Puissance 4).
- Un réseau convolutif résiduel commun aux jeux de plateau existe (`logic_arena/zero/net.py`, 304 300 paramètres) mais il est entraîné **un jeu à la fois**.
- Nouveau : des **professeurs à la main solides** (Gomoku 0,938 contre l'ancien, Hex ≈ 0,75, solveur exact Puissance 4, dames par recherche renforcée) : sources de données et juges indépendants.
- Matériel : RTX 4060 8 Go, PyTorch CUDA (`work/text-env`), 16 cœurs.

**Conséquence : « multi-jeux donc meilleur » est une hypothèse à prouver, pas un acquis.** Le cadrage est donc d'abord une expérience, ensuite une montée en taille.

## 2. Architecture visée
Un seul **tronc** partagé, des **entrées/sorties propres à chaque jeu** (c'est le « plusieurs poids si tu veux », mais borné aux bords du modèle).
- Plateau commun 19 × 19 avec masque (les petits jeux sont centrés) : mêmes filtres pour lignes, connexions, libertés, captures.
- Tronc convolutif résiduel (essai : 6 blocs × 64 canaux ≈ 0,5 M ; cible : 10 blocs × 192 canaux ≈ 7 M, tient en 8 Go).
- Par jeu : un petit encodeur d'entrée (plans de pierres, trait, phase) + un identifiant de jeu injecté (FiLM) ; une tête de politique et une tête de valeur.
- Jeux sans grille (Nim, 2048, démineur…) et puzzles : hors phase 1 ; les puzzles relèvent plutôt du cœur récurrent Loop/Mind.
- Le Go reste hors périmètre (décision antérieure).

## 3. Protocole : prouver que le multi-jeux aide
Même budget de calcul (pas, exemples vus) pour chaque bras, mesure **contre un adversaire indépendant, jamais contre le seul professeur** :
1. **Mono-jeu** : un réseau par jeu.
2. **Multi-jeux complet** : un réseau, tous les jeux de la phase.
3. **Multi-jeux par familles** : alignements (morpion, Puissance 4, Gomoku), connexion (Hex), captures (dames).
4. **Transfert** : entraîner sans un jeu, puis l'ajouter avec 10 % du budget ; comparer à un départ à zéro (vitesse d'apprentissage).

Juges : Puissance 4 = solveur exact (taux de coups fautifs, base 2,4 %) ; Gomoku et Hex = les moteurs à la main de ce lot ; dames = recherche renforcée ; Morpion = minimax. Seuils fixés **avant** la mesure : le multi-jeux « aide » si, à budget égal, il bat le mono-jeu sur au moins la moitié des jeux sans perdre plus de 2 points d'erreur sur aucun. Sinon : ajouter d'abord des adaptateurs par jeu, ou n'utiliser que les familles qui aident.

## 4. Données et entraînement
1. **Distillation** des professeurs (politique = scores de tous les coups légaux, valeur = résultat/score de recherche) : les moteurs JS tournent sur 14 cœurs ; ordre de grandeur 200 000 positions étiquetées par heure. Ouvertures variées pour éviter la partie unique répétée (leçon du Graine).
2. **Auto-apprentissage avec recherche** (MCTS guidé, `zero/mcts.py`, `zero_train.py` à rendre multi-jeux) : tirage de jeux pondéré par la perte, rejeu des anciens jeux contre l'oubli, arène périodique contre les juges.
3. Règle d'hygiène : sélection sur validation, test réservé, hasard des graines consigné, anciens poids conservés avec empreintes.

## 5. Phases et critères d'arrêt
| Phase | Contenu | Durée estimée | Critère |
|---|---|---|---|
| P0 | Encodage commun, jeux Puissance 4, Gomoku, Hex, dames (+ morpion), générateur de données multi-professeurs, juges automatiques | 1 à 2 jours | parité règles/encodages testée, base de mesures figée |
| P1 | Pilote 0,5 M : bras 1 à 3 à budget égal | ½ journée de GPU | décision « le multi-jeux aide ou non » selon les seuils |
| P2 | Si oui : tronc 7 M, distillation | 1 à 2 jours | ≥ niveau des professeurs réseau seul sur les jeux de la phase |
| P3 | Auto-apprentissage avec recherche, arène | plusieurs jours | bat les professeurs à temps égal (écart mesuré, pas promis) |
| P4 | Ajout un jeu à la fois (Reversi, Breakthrough, puis autres), non-régression à chaque ajout | continu | aucun jeu antérieur ne recule |
| P5 | Distillation vers le Garry navigateur (« Prime ») | à décider | compromis taille/force mesuré |

Règle d'arrêt reprise du plan : deux essais sans gain sur validation, on abandonne et on documente.

## 6. Risques
- Interférence entre jeux (tâches trop différentes) : parades = familles, adaptateurs, tirage pondéré, rejeu.
- 8 Go de VRAM : plafond ≈ 10 à 15 M paramètres à l'entraînement ; au-delà, il faudrait du matériel ou du nuage.
- Un gros modèle ne tourne **pas** tel quel dans le navigateur ni sur le plan gratuit de `multi` (10 ms de processeur) : il sert localement et de professeur ; la version embarquée est une distillation (P5).
- Les professeurs à la main plafonnent la distillation : la vraie montée de niveau vient de P3.

## 7. Décisions à confirmer (défauts proposés, je démarre avec eux sauf avis contraire)
1. **Lieu d'exécution** : local (serveur Python / PyTorch) d'abord, navigateur plus tard par distillation.
2. **Jeux de la phase 1** : Puissance 4, Gomoku, Hex, dames, morpion.
3. **Budget** : le pilote P1 seul d'abord (½ journée de GPU), la suite décidée sur ses résultats.
