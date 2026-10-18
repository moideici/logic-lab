"""Met à jour PLAN-GLOBAL.md : entraînement de Garry relancé, jeux réels réparés, trois modèles ambitieux proposés."""
from pathlib import Path

p = Path(r"C:\Users\gabor\code\logic-lab\PLAN-GLOBAL.md")
s = p.read_text(encoding="utf-8")
add = """### Garry : entraînement relancé et orientation (18 octobre 2026)

- **Décision de l'utilisateur :** Garry est le modèle phare ; les autres expériences (Graine, Loop, Pleias, projet code) n'ont pas la même ambition. L'effort se concentre sur Garry.
- **Entraînement relancé** : session continue de 60 minutes, profil « points faibles » (Go, Hex, Gomoku), par imitation gardée : un candidat n'est promu que s'il fait au moins aussi bien que le champion sur validation et sur positions fraîches. Poids de départ : Garry 0.6.0, empreinte `ae54c06d…`, sauvegardés dans `projets/garry/training-runs/sauvegardes/` et `work/`. Résultats à consigner à la fin de la session.
- **Jeux réels réparés** : le serveur désigne maintenant le navigateur Playwright du projet (`work/browsers`) ; 2048 (12 coups vérifiés) et Go 9×9 contre COSUMI niveau 1 (10 étapes) fonctionnent depuis l'onglet « Jeux réels ».
- **Trois modèles ambitieux proposés** (`outputs/rapports/garry/PROPOSITIONS-3-MODELES-AMBITIEUX.md`) : **Garry Zéro** (auto-apprentissage avec recherche, sans professeur, pour dépasser les références ; jalon Puissance 4 puis Hex 7×7), **Garry Règles** (joueur universel qui lit les règles, test sur des jeux écartés), **Garry Délibération** (cœur récurrent dont le niveau est le nombre de passes, appuyé sur le Loop validé). Ordre recommandé : Zéro, Délibération, Règles. Aucune n'est lancée.

"""
marker = "## 11. Projet code"
s = s.replace(marker, add + marker, 1)
p.write_text(s, encoding="utf-8", newline="")
print("ok")
