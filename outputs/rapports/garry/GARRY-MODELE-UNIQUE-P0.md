# Modèle unique multi-jeux — phase P0 terminée (9 novembre 2026)

Cadrage : `GARRY-MODELE-UNIQUE-CADRAGE.md`. P0 = infrastructure commune, professeurs, juges, base de mesures. **Aucun réseau n'est entraîné dans cette phase.**

## Livré (`projets/garry/`)
- `logic_arena/unified/` : `spec.py` (plateau commun 15 × 15, 8 plans, vecteur annexe, 228 actions de pose + 1 024 actions de dames), `adapters.py` (interface unique des cinq jeux), `encode.py` (observation → plans, action → indice, toujours du point de vue du joueur au trait ; Hex transposé pour que « mes » pierres relient toujours haut-bas ; Puissance 4 = case d'atterrissage), `dataset.py` (format .npz, cible de politique), `teachers.py`, `judge.py`.
- Professeurs : morpion (minimax exact, 4 520 positions), Puissance 4 (51 194 étiquettes du solveur exact), dames (520 771 étiquettes de la recherche renforcée), Gomoku et Hex (auto-parties des moteurs à la main, `tools/teachers/teacher-data.mjs`, valeur = résultat réel de la partie ; 35 060 et 33 034 positions). Fichiers : `training-lab/data/unified/*-1.npz` (régénérables : `training-lab/unified_make_data.py`).
- Juges indépendants (`judge.py`, `tools/teachers/engine-server.mjs`) : morpion contre minimax exact et hasard ; Puissance 4 contre le solveur exact (taux de coups fautifs) ; Hex et Gomoku contre les moteurs à la main (100 ms par coup) ; dames contre le bot de `multi` (normal, difficile) .
- Tests : `tests/test_unified.py`, 12 tests verts (formes, indices d'action uniques et sur cases libres, perspective, transposition Hex, étiquettes exactes, aller-retour du format).

## Base de mesures figée (`outputs/verifications/baselines-unifie-2026-11-09.json`, 20 parties par cellule)
| Jeu | Hasard | Professeur (plafond) |
|---|---|---|
| Morpion | 16 défaites sur 20 contre le parfait | 0 défaite, 20 nuls ; 20/20 contre le hasard |
| Puissance 4 | 7,3 % de coups fautifs, score 0,05 | 0 % de coups fautifs, résultat théorique atteint 100 % |
| Hex | 0,00 | 0,45 (moteur contre lui-même : ≈ 0,5 attendu) |
| Gomoku | 0,00 | 0,50 (idem) |
| Dames | 0,00 / 0,00 (normal / difficile) | 0,925 / 0,75 |

Lecture : un réseau devra se situer entre ces deux colonnes ; « égaler le professeur » vaut ≈ 0,5 aux jeux où le juge est le même moteur.

## Limites et points d'attention
- Gomoku : le joueur testé ne joue que la phase « play » ; les ouvertures Swap2 sont jouées par le moteur (non unifiées, comme au réel).
- Hex et Gomoku : peu de positions (≈ 35 000 chacun) face aux dames (520 000) : le pilote P1 équilibrera les jeux ou en générera davantage (≈ 2 minutes pour 30 000 positions).
- Puissance 4 : étiquettes à trois valeurs (gain/nul/perte), pas de scores exacts ; peu de signal pour distinguer les coups gagnants.
- Les juges Hex/Gomoku dépendent du temps mural (100 ms) : ±0,1 de bruit à 20 parties ; l'écart-type d'une mesure est de l'ordre de 0,11.
- Dames : règles de `multi` (pas les dames internationales de Garry 0.6.0).

## Suite : P1 (pilote)
Tronc convolutif 6 × 64 (≈ 0,5 M), trois bras à budget égal (mono-jeu, multi-jeux complet, par familles), mesure par les juges ci-dessus, décision selon les seuils du cadrage.
