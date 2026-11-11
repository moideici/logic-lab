# Maths, vague 1 : premiers résultats (31 octobre 2026)

Protocole : [maths-protocole.md](maths-protocole.md), fixé avant les entraînements. Code : `projets/garry/logic_arena/maths/`, entraîneur `training-lab/maths_train.py`, analyse d'erreurs `training-lab/maths_errors.py`, résultats bruts `training-lab/results/maths-{curriculum,flat}-s0.json` (non versionnés), points de contrôle `training-lab/models/maths/`. Tests : `tests/test_maths_*.py` (34 verts).

## Ce qui a tourné
Un seul modèle (Transformer décodeur, 812 416 paramètres, caractère par caractère) pour les six niveaux, 30 000 pas, lots de 256, bf16, graine 0, une seule graine par régime. Point de contrôle choisi sur la validation, test et hors distribution (OOD) mesurés une fois à la fin.
- `curriculum-s0` : les niveaux arrivent un par un pendant les 60 % premiers pas, puis tous. Point retenu : pas 28 000.
- `flat-s0` : tous les niveaux dès le début. Point retenu : pas 30 000 (le dernier : la validation montait encore).
Durées : 15 min (curriculum) et 14 min (plat) sur RTX 4060 partagée, environ 30 pas par seconde.

## Résultats sur le test (étape exacte / problème résolu)
| Niveau | Test états | Curriculum | Plat | OOD curriculum | OOD plat |
|---|---|---|---|---|---|
| N1 `+ -` | 806 | 1,000 / 1,000 | 0,999 / 0,998 | 0,000 / 0,000 | 0,000 / 0,002 |
| N2 `*` | **118** | 0,831 / 0,831 | 0,975 / 0,975 | 0,009 / 0,010 | 0,048 / 0,046 |
| N3 `/` | **66** | 0,833 / 0,833 | 0,955 / 0,955 | 0,004 / 0,002 | 0,001 / 0,000 |
| N4 priorités | 1000 | 0,973 / 0,972 | 0,999 / 1,000 | 0,464 / 0,090 | 0,669 / 0,232 |
| N5 parenthèses | 1000 | 0,911 / 0,798 | 0,991 / 0,976 | 0,252 / 0,002 | 0,487 / 0,044 |
| N6 équations | 1000 | 0,949 / 0,922 | 1,000 / 1,000 | 0,193 / 0,008 | 0,330 / 0,082 |
| Moyenne résolu N4 à N6 | | 0,897 | **0,992** | 0,033 | 0,119 |

Niveaux « appris » (critère annoncé : étape exacte ≥ 0,99 et résolu ≥ 0,95) : curriculum, N1 seulement ; plat, **N1, N4, N5, N6**. N2 (0,975) et N3 (0,955) restent sous le seuil.

## Ce qu'on peut affirmer
1. **La méthode est apprise, les chiffres le sont moins bien.** Sur la validation, les erreurs sont presque toutes des valeurs fausses, jamais une règle de réécriture mal choisie (étape valide mais différente de la référence : 0,3 % en N5 pour le curriculum, nul pour le plat ; forme invalide : au plus 0,1 %). Exemples : `37*11` → `307` (retenue oubliée), `284/4` → `76`, `20-91-2+4` → `-81-2+4`, `38-(-102)` → `240`, `792/12` → `61` pour 66. Pour le modèle plat, les erreurs restantes sont des fautes de chiffre sur des résultats à 3 chiffres ou avec un négatif.
2. **Le mélange plat fait mieux que le curriculum à budget égal** : 0,992 contre 0,897 de problèmes résolus en moyenne sur N4 à N6 (écart 0,095, au-dessus du seuil de 0,05 annoncé). Le curriculum passe 60 % des pas avec un sous-ensemble de niveaux ; sa validation à 18 000 pas est 0,82 contre 0,95 pour le plat.
3. **Toujours en progrès à 30 000 pas** pour le plat (validation 0,88 → 0,93 → 0,95 → 0,97 → 0,98 à 6, 12, 18, 24, 30 mille pas) : le budget limite, pas la capacité.

## Ce qu'on ne peut pas affirmer
- **Curriculum contre plat n'est pas conclu.** Le protocole exige au moins deux graines pour déclarer cette différence ; il n'y en a qu'une par régime. L'écart est grand, mais un seul tirage. Le curriculum a aussi moins de pas sur chaque niveau difficile : le résultat compare des programmes à budget égal, pas des programmes à connaissance égale.
- **N2 et N3 sont mal mesurés.** Le nombre d'états distincts est minuscule (≈ 2 600 multiplications, ≈ 1 300 divisions possibles) : le test n'a que 118 et 66 états, au lieu des 1 000 annoncés. Incertitude d'environ ±3 points (N2) et ±5 points (N3) ; la validation (127 et 68 états) est tout aussi petite. On ne distingue pas mémoire d'une table et début d'algorithme.
- **Aucune extrapolation.** Hors distribution, tout s'effondre : N1 avec des nombres de 4 chiffres, 0 % pour les deux modèles ; N2, N3 ≈ 0 à 5 % ; N4 à N6 : 0,044 à 0,232 de problèmes résolus pour le plat (étapes isolées : 0,33 à 0,67). Les positions apprises sont absolues et les opérandes à 4 chiffres n'existent pas à l'entraînement ; ce n'est pas un algorithme d'addition indépendant de la longueur. Ce résultat est le principal problème ouvert.
- Les états intermédiaires d'un problème de test ont pu être vus à l'entraînement (seul l'état de départ est dans le test) ; c'est sans effet sur les mesures « étape », qui sont disjointes.
- Une graine, 30 000 pas, pas de recherche d'hyperparamètres : aucune comparaison avec d'autres tailles de modèle.

## Écarts au protocole
- Tests N2/N3 plus petits que prévu (118 et 66 états au lieu de 1 000), parce que l'espace d'entrée est plus petit : à corriger en élargissant les plages, ce qui est un changement de protocole à documenter.
- Une seule graine par régime (protocole : au moins deux pour conclure).
- Analyse d'erreurs faite sur la validation, jamais sur le test.

## Suite proposée (à décider)
1. Deuxième graine des deux régimes (≈ 30 min) pour fermer la question curriculum contre plat.
2. Vague 1b, avec amendement de protocole daté et banc de test neuf : plages de N2 et N3 élargies (grand facteur jusqu'à 999) ; nombres plus longs à l'entraînement ; plus de pas (le plat montait encore) ; essayer des positions relatives (RoPE) ou la multiplication par chiffres pour attaquer l'effondrement hors distribution.
3. Ensuite seulement : carte « Maths en direct » dans le Lab.
