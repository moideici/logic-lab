# Garry « à la main » : Gomoku et Hex sans entraînement (9 novembre 2026)

Demande : rendre nettement meilleur le jeu écrit à la main (pas d'entraînement, seulement de l'optimisation et des paramètres pertinents). Choix : les deux jeux où le planificateur à la main était le plus faible et le plus simple (Go exclu, hors périmètre). Les poids du réseau ne sont pas touchés.

## Ce qui a changé (navigateur, `web/`)
- **Gomoku** : `gomoku-engine.js` remplace le planificateur 1 coup + 1 réponse (`gomoku-planner.js`, conservé comme référence et pour la phase Swap2).
  - Table de motifs sur 11 cases par ligne : cinq **exact** (le six ne gagne pas), quatre ouvert, quatre, trois ouvert, trois fermé ; mise à jour incrémentale à chaque pierre.
  - Alpha-bêta à approfondissement itératif, table de transposition, défense forcée, détection des doubles menaces, extension **VCF** (suite de quatres) aux feuilles et à la racine.
  - Coefficients dans `PARAMS` (largeur de faisceau par profondeur, pondération attaque/défense).
- **Hex** : `hex-engine.js` remplace la recherche à 3 plis avec copie profonde.
  - Distance de connexion avec **ponts** et **bords virtuels**, tri des coups par « longueur du meilleur chemin qui traverse la case » (4 Dijkstra par nœud au lieu de 2 par case vide).
  - Alpha-bêta à table de transposition, faisceau étroit hors fin de partie, première pierre non centrale (le centre serait échangé).
- `planner.js` utilise les deux moteurs. `teachers.js` garde les anciens planificateurs comme **professeurs figés** : les mesures d'accord des entraînements restent comparables.

## Mesures (duels, camps échangés, mêmes budgets : 200 ms et 100 000 nœuds par coup)
| Duel | Parties | V / N / D | Score |
|---|---|---|---|
| Gomoku nouveau contre ancien | 96 | 84 / 12 / 0 | 0,938 |
| Hex nouveau contre ancien (4 lots de 96, ouverture imposée aléatoire) | 384 | — | 0,70 à 0,84 (≈ 0,75) |

Réglages à la main (variante contre défauts, 96 parties chacune, bruit ≈ ±0,05) :
- Gomoku : largeur de faisceau, poids défense, poids du second meilleur coup, profondeur VCF : tout dans le bruit (0,47 à 0,56) ; plateau, défauts conservés.
- Hex : **ponts** (0,31 sans eux), **terme de centre** (0,08 sans lui) et **faisceau étroit** (0,64 contre faisceau large 0,24 à 0,40, car la profondeur compte plus que la largeur) sont les vrais leviers ; le reste est dans le bruit.
- Règle d'échange de connaissance (pierres intérieures échangées) : 0,56 contre la recherche seule, aucun gain démontré, désactivée (`swapRule`). Une carte d'ouvertures par auto-parties (30 parties par case) s'est révélée trop bruitée pour décider (centre à 0,47 alors qu'il est connu gagnant) : non utilisée.

## Limites
- Les adversaires sont l'ancien planificateur et le moteur lui-même : **aucune mesure contre un moteur tiers** ni contre des humains ; ce n'est pas un classement Elo.
- Ouvertures Swap2 du Gomoku non améliorées (ancien évaluateur de déséquilibre).
- **Pas de port Python** : `logic_arena/gomoku_planner.py` et `hex_planner.py` restent les anciens ; le serveur Python et les tests Python n'ont pas changé. Le navigateur et Python ne choisissent donc plus les mêmes coups à ces deux jeux.
- Nuls du Gomoku : parties arrêtées à 260 coups ou plateau plein.

## Reproduire
```bash
node --test tests/*.test.mjs                       # 77 tests JS (dont gomoku-engine, hex-engine)
bench/run-parallel.sh bench/gomoku-duel.mjs 12 8   # nouveau contre ancien, 96 parties
bench/run-parallel.sh bench/hex-duel.mjs 12 8
bench/run-parallel.sh bench/gomoku-duel.mjs 12 8 --b engine --params '{"own2":0.6}'   # variante contre défauts
```
