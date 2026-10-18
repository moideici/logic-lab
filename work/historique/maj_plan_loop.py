"""Met à jour PLAN-GLOBAL.md avec le premier résultat du Loop (sudoku 6×6)."""
from pathlib import Path

p = Path(r"C:\Users\gabor\code\logic-lab\PLAN-GLOBAL.md")
s = p.read_text(encoding="utf-8")

row_graine = "| Graine | Fait (résultat négatif) |"
i = s.index(row_graine)
j = s.index("\n", i)
s = s[:j + 1] + "| Garry Loop (cœur récurrent) | Premier résultat positif | Sudoku 6×6 : 99,8 % (moyen) et 75 à 89 % (plus dur que l'entraînement) avec 53 254 paramètres ; la récurrence est ce qui compte | `outputs/verifications/loop-sudoku6-resultats.md` |\n" + s[j + 1:]

s = s.replace("| Modèle de raisonnement | À concevoir | Voir §12 | — |", "| Modèle de raisonnement | Démarré (famille 1) | Voir §12 | `projets/garry/logic_arena/reason/` |")
s = s.replace("| **Garry Loop** | Cœur récurrent : un bloc repassé plusieurs fois sur son état, arrêt appris | À faire |",
              "| **Garry Loop** | Cœur récurrent : un bloc repassé plusieurs fois sur son état, arrêt appris | Fait pour le sudoku 6×6 (arrêt encore par vérification) |")

add = """
### Premier résultat (18 octobre 2026) : sudoku 6×6
Rapport : `outputs/verifications/loop-sudoku6-resultats.md`. Un bloc d'attention limité aux voisines de contrainte, repassé avec les mêmes poids (53 254 paramètres), entraîné de zéro sur des sudokus à solution unique générés à l'infini.
- **La récurrence fait le travail** : une seule passe ne résout presque rien ; un réseau à huit blocs distincts (8× plus gros) fait un peu moins bien sur le dur (0,735 contre 0,749).
- **Réfléchir plus longtemps qu'à l'entraînement aide** : de 8 à 32 passes à l'inférence, les problèmes durs passent de 0,749 à 0,841 (0,893 pour le Loop entraîné à 16 passes).
- **La durée de réflexion suit la difficulté** : 1,8 passe (facile), 3,0 (moyen), 6,0 (dur), mesurée avec arrêt par vérificateur exact.
- **Limite principale** : l'attention ne voit que les voisines de contrainte, la règle est donc dans la structure ; la généralité reste à prouver sur une autre famille de problèmes (coloration de graphe, n-reines) et un transfert vers une famille jamais vue.
- **Lab** : section « Réflexion en direct » (`/lab.html`), grille proposée à chaque passe avec confiance et cases fausses, API `/api/lab/reason/*`. Modèle régénérable par `training-lab/entrainer_loop.py` (4 minutes).
- Tests : 155 verts (dont problèmes, modèle, service).
"""
marker = "## 13. Prochaines étapes"
s = s.replace(marker, add.lstrip("\n") + "\n" + marker, 1)

old = s[s.index("## 13. Prochaines étapes"):s.index("Règles d’hygiène retenues")]
s = s.replace(old, """## 13. Prochaines étapes (ordre)

1. Graine, Lab en direct, Loop sur sudoku 6×6 : faits.
2. **Deuxième famille sur le même modèle** (coloration de graphe ou n-reines, autre graphe de contraintes) et **test de transfert** vers une famille jamais vue : c'est la question centrale du modèle unique.
3. Arrêt appris (tête de décision d'arrêt) comparé à l'arrêt par vérificateur ; Mind.
4. Sudoku 9×9 pour une difficulté réelle ; autres familles (planification, énigmes logiques, règles de grille).
5. Reprendre Input (lot 4) et, si l'utilisateur le souhaite, le projet code (§11).

""")
p.write_text(s, encoding="utf-8", newline="")
print("ok")
