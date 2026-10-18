"""Met à jour PLAN-GLOBAL.md : en-tête, périmètre actif, et sections 9 et suivantes consolidées (18 octobre 2026)."""
import io
import re
from pathlib import Path

p = Path(r"C:\Users\gabor\code\logic-lab\PLAN-GLOBAL.md")
s = p.read_text(encoding="utf-8")

# 1. en-tête
s = s.replace(
    "Mis à jour le 18 octobre 2026. Ce document est le plan principal de la conversation et remplace l’ordre des priorités des anciens rapports. L’exécution commence par l’interface et l’utilisation. Le projet d’agent producteur de code est écarté.",
    "Mis à jour le 18 octobre 2026 (fin de journée). Ce document est le plan principal de la conversation et remplace l’ordre des priorités des anciens rapports. "
    "**Priorité actuelle : la famille Garry et le Lab (Core entraînable, Graine, Loop), puis un modèle de raisonnement entraîné de zéro. "
    "Input est en veille (lot 4 à reprendre) et le projet de cœur de code est mis de côté, avec ses résultats.** Les sections 1 à 8 décrivent l’état de départ ; les sections 9 et suivantes sont l’état à jour.")

# 2. périmètre actif
a = s.index("### Périmètre actif des chantiers")
b = s.index("## 3. Périmètre")
s = s[:a] + """### Périmètre actif des chantiers (mis à jour le 18 octobre 2026)

| Statut | Chantier |
|---|---|
| **Actif** | Famille Garry et Lab : Core entraînable, Graine (croissance et élagage), Loop (cœur récurrent), Lab en direct. Modèle de raisonnement de zéro qui s’appuie sur la même infrastructure. |
| **En veille** | Input : interface prête (lot 1), banc de régression gelé (lot 2), contrat v2 prêt mais non activé (lot 3) ; il reste le lot 4 (données ciblées). Qwen3-0.6B reste la base : Pleias a été essayé et écarté. |
| **Mis de côté (projet séparé)** | Cœur de code relié à Input (`projets/code`) : banc, mesures et conclusions conservés, reprise possible (voir §11). |
| **Références** | HRM et TRM servent de références pour le modèle de raisonnement ; aucun entraînement dédié. |

Le canal latent et le « rapport qualité/coût par neurone » restent des hypothèses à tester, pas des objectifs de livraison.

""" + s[b:]

# 3. sections 9 et suivantes
a = s.index("## 9. État d'avancement")
s = s[:a] + """## 9. État d'avancement (18 octobre 2026)

| Chantier | Statut | Résultat clé | Preuve |
|---|---|---|---|
| Input, lot 1 (interface) | Fait | Premier texte en 0,5 à 1 s à chaud, arrêt en 53 ms, 0 erreur JavaScript, mobile correct | `outputs/verifications/recette-lot1-input-2026-10-18.md` |
| Input, lot 2 (banc de régression) | Fait | Banc v1.0.0 gelé (2 × 51 cas). Baseline : 54,2 % (dev), 47,7 % (test) ; 86 % de réponses affirmées sans réponse possible | `outputs/verifications/baseline-lot2-input-0.2.0.md` |
| Input, lot 3 (contrat v2) | Prêt, non activé | Sans entraînement, 61,4 % en dev mais 17 erreurs, 26 s de latence médiane et un biais de mesure | `outputs/verifications/contrat2-lot3-input.md` |
| Input, base alternative | Écartée | Pleias-350M adapté : 24,8 % contre 54,2 % pour Qwen3-0.6B | `outputs/rapports/input/COMPARATIF-10-MODELES.md` |
| Input, lot 4 (données) | À faire | Cibles chiffrées fixées au lot 2 (global ≥ 80 %, contexte ≥ 90 %, limite reconnue ≥ 80 %) | rapport du lot 2 |
| Garry Core | Fait | Parité exacte avec les poids 0.6.0 sur 14 jeux | `projets/garry/tests/test_core.py` |
| Lab v1 | Fait | Réseau en direct, extinction, importance par neurone, courbe qualité/coût (`/lab.html`) | `projets/garry/web/lab.html` |
| Core entraînable (PyTorch) | Fait | `labtrain.py` : réseau à deux couches cachées, croissance et élagage, données de professeur variées ; 6 tests | `projets/garry/logic_arena/labtrain.py` |
| Graine | En cours | Voir §10 | `projets/garry/training-lab/` |
| Projet code | Mis de côté | Voir §11 | `outputs/verifications/chaines-code-test-vs-dev.md` |
| Modèle de raisonnement | À concevoir | Voir §12 | — |

Garry : 130 tests Python verts (dont Core et Lab), puis 6 tests de l’entraîneur du Lab.

## 10. Famille Garry et Lab

Un **Garry Core** propre (couches nommées, activations capturables, neurones éteignables ou supprimables) et des variantes qui en sont des configurations, observables dans l’onglet **Lab** du site.

| Variante | Définition retenue | Statut |
|---|---|---|
| **Garry Games** | Le Garry actuel, 14 jeux | Existant (0.6.0) |
| **Graine** | Croissance et élagage de neurones pendant l’apprentissage | En cours |
| **Garry Loop** | Cœur récurrent : un bloc repassé plusieurs fois sur son état, arrêt appris | À faire |
| **Garry Mind** | Amélioration du schéma de boucle des modèles existants pour qu’ils réfléchissent plus, et à plus de choses (budget de calcul adaptatif, proposer-vérifier-corriger) | À faire |
| **Garry Input** | Input rebaptisé dans la famille ; reste Qwen3-0.6B + adaptation | En veille |
| **Garry Prime** | Routeur plus distillation des variantes ; compromis force/taille mesuré, pas de promesse « le plus fort partout » | Plus tard |
| **Règles** | Jouer un jeu jamais vu à partir de ses règles | Plus tard (pari) |

### Graine : ce qui est établi
- Les données doivent être **variées** : un professeur parfait rejoue toujours la même partie. Premier essai avec ce défaut : 4 500 positions, 9 distinctes, un réseau de 71 paramètres atteignait 100 % (résultat sans valeur, corrigé). Désormais : coups aléatoires avec probabilité 0,35 pendant la partie, étiquettes toujours données par le professeur.
- Résultat intermédiaire au morpion (3 graines, 3 000 pas) : accord avec le professeur de 0,77 (2+2 neurones, 71 paramètres) à 0,99 (48+48, 3 705 paramètres). **Graine A (règles prudentes) est moins bonne qu’un réseau fixe de même taille finale** (0,81 contre 0,87) : sa croissance est trop lente et son élagage précoce retire des neurones utiles. Deux variantes plus agressives (B et C) sont en cours de mesure ; le choix se fait sur la validation, jamais sur le test.
- Reste à faire : Nim et Puissance 4, puis l’affichage en direct dans le Lab.

## 11. Projet code (mis de côté, résultats conservés)

Un cœur de code relié à Input (`projets/code`, dépôt Git séparé, banc de code v1.1.0 : Python exécuté, C++ compilé, HTML vérifié).
- **Cœur retenu :** Qwen2.5-Coder-0.5B (base, puis Instruct). Seuls 10 candidats comparés : `outputs/rapports/input/COMPARATIF-10-MODELES-CODE.md`.
- **Mesures :** cœur de base seul 17/23 (dev) et 15/23 (test) avec la signature dans l’invite ; chaîne texte avec Input qui reformule 12/23, avec extracteur 12 à 13/23, boucle de retour sans effet avec le cœur de base ; avec le cœur Instruct, la boucle de retour répare des cas (+1 en dev, +4 en test).
- **Surajustement constaté :** la meilleure chaîne de dev (15/23) fait 9/23 sur test. Chaîne retenue : demande directe → cœur Instruct + boucle de retour (28/46). L’extraction par Input est abandonnée comme canal texte. Le split test est consommé.
- **Conclusion :** le goulot est le cœur de 0,5 G, pas la communication ; le canal interne n’a de marge que s’il égale la demande directe en gagnant ailleurs.
- **Reprise possible :** banc v2 (tâches inédites), cœur 1,5 G pour le plafond, adaptation du cœur sur paires vérifiées, puis canal interne. Rapports : `outputs/verifications/` (`canal-texte-*`, `boucle-de-retour-dev.md`, `coeur-instruct-chaine-dev.md`, `chaines-code-test-vs-dev.md`).

## 12. Modèle de raisonnement entraîné de zéro (idée de l’utilisateur)

« Modèle de calcul » = modèle qui résout des problèmes et raisonne (pas une calculatrice). Souhait exprimé : **un seul modèle** qui fasse énigmes logiques, découverte de règles et comparaison de scénarios, plutôt que trois.
- **Piste :** un cœur récurrent (Loop) entraîné de zéro sur une famille de petits problèmes générés à l’infini et vérifiables exactement, avec un format d’entrée commun (grille ou ensemble d’entités et de contraintes) et des têtes ou encodeurs par famille.
- **Familles, de la plus simple à la plus ambitieuse :** (1) contraintes sur grille (sudoku réduit, n-reines, coloration de graphe) ; (2) planification (ordonnancement, labyrinthes) ; (3) énigmes logiques en tableau (type zèbre) ; (4) règles de grille type ARC simplifié ; (5) comparaison de scénarios avec hypothèses.
- **Mesures :** exactitude selon la difficulté, nombre de passes de réflexion selon la difficulté, transfert vers une famille jamais vue (tenue en réserve), grille de chaque passe visible dans le Lab.
- **Risques :** interférence entre tâches (déjà vue avec les 14 jeux de Garry : vérifier la préservation à chaque ajout), et le format commun, qui est le vrai travail ; la comparaison de scénarios exige des nombres et du langage et vient en dernier.
- **Ordre :** après Graine et la boucle récurrente ; commencer par une ou deux familles qui partagent la même représentation (grilles).

## 13. Prochaines étapes (ordre)

1. Finir Graine : choisir les règles sur la validation, mesurer Nim et Puissance 4 en 3 graines, rapport.
2. Lab en direct : entraînement visible (courbes, neurones qui naissent et disparaissent, comparaison avec les réseaux fixes).
3. Garry Loop : cœur récurrent avec poids liés et arrêt appris, d’abord sur un problème à contraintes.
4. Modèle de raisonnement (§12) sur cette base ; Mind quand le Loop fonctionne.
5. Reprendre Input (lot 4) et, si l’utilisateur le souhaite, le projet code (§11).

Règles d’hygiène retenues : jamais de sélection sur un split réservé ; toute nouvelle sélection sur un banc neuf ; données de professeur variées ; rapports écrits avant d’annoncer un résultat ; limites et incertitudes annoncées avec les chiffres.
"""
p.write_text(s, encoding="utf-8", newline="")
print("plan mis à jour :", len(s), "caractères")
