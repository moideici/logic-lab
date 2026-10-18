"""Met à jour PLAN-GLOBAL.md avec le résultat de Graine."""
from pathlib import Path

p = Path(r"C:\Users\gabor\code\logic-lab\PLAN-GLOBAL.md")
s = p.read_text(encoding="utf-8")
a = s.index("### Graine : ce qui est établi")
b = s.index("## 11. Projet code")
new = """### Graine : résultat (18 octobre 2026)
Rapport : `outputs/verifications/graine-resultats.md`. Trois jeux, trois graines, trois règles de croissance et d'élagage, comparées à des réseaux fixes de même taille finale.
- **Hypothèse non confirmée** : à taille égale, Graine perd 1 à 6 points d'accord avec le professeur contre un réseau fixe (morpion : 0,812 / 0,924 / 0,940 contre 0,873 / 0,939 / 0,981 ; Nim : 0,711 / 0,911 / 0,941 contre 0,787 / 0,920 / 0,961). Elle trouve une taille raisonnable seule, mais une recherche sur quelques tailles fixes donne autant.
- **Puissance 4 inconclusif** (accord 0,35 à 0,39 pour toutes les tailles) : jeu trop dur pour 6 129 positions et un professeur borné en temps.
- **Données** : un professeur parfait rejoue toujours la même partie (un premier essai avec 9 positions distinctes donnait 100 % à un réseau de 71 paramètres, résultat sans valeur) ; correction : coups aléatoires avec probabilité 0,35, étiquettes du professeur.
- **Décision proposée** : garder Graine dans le Lab comme visualisation, ne pas insister sur le gain, passer à Loop et au modèle de raisonnement.
- **Lab en direct** : entraînement visible dans `/lab.html` (réseau, courbe d'accord et de taille, événements, comparaison de la session), API `/api/lab/train/*`, 11 tests.

"""
s = s[:a] + new + s[b:]
s = s.replace("| Graine | En cours | Voir §10 | `projets/garry/training-lab/` |",
              "| Graine | Fait (résultat négatif) | À taille égale, un réseau fixe fait aussi bien ou mieux (§10) | `outputs/verifications/graine-resultats.md` |")
s = s.replace("| **Graine** | Croissance et élagage de neurones pendant l’apprentissage | En cours |",
              "| **Graine** | Croissance et élagage de neurones pendant l’apprentissage | Fait : gain non confirmé, conservée comme visualisation |")
old = s[s.index("1. Finir Graine"):s.index("Règles d’hygiène retenues")]
s = s.replace(old, """1. Graine et Lab en direct : faits (Graine : résultat négatif, voir §10).
2. Garry Loop : cœur récurrent avec poids liés et arrêt appris, d’abord sur un problème à contraintes.
3. Modèle de raisonnement (§12) sur cette base ; Mind quand le Loop fonctionne.
4. Reprendre Input (lot 4) et, si l’utilisateur le souhaite, le projet code (§11).

""")
p.write_text(s, encoding="utf-8", newline="")
print("ok")
