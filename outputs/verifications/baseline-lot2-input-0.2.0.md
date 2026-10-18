# Lot 2 : banc de régression et baseline d'Input 0.2.0 (18 octobre 2026)

Banc v1.0.0 : `projets/input/bench/` (cas `dev.jsonl` et `test.jsonl`, empreintes dans `manifest.json`, générateur `build_regression.py`, vérificateurs `checks.py`, lanceur `run_regression.py`). 51 cas par séparation, 11 catégories. Chaque cas est joué 3 fois (le serveur échantillonne à 0,7) : 153 essais par séparation. Modèle mesuré : Qwen3-0.6B + `focus-20261017-210925/checkpoint-1000`, GPU, via l'API réelle `/api/chat`.

Règles : `test` est réservé, jamais utilisé pour entraîner, filtrer des données ni régler ; `dev` sert au diagnostic. Le lanceur refuse une mesure si l'empreinte ne correspond plus. Toute modification du banc crée une version 1.x.

## Baseline

| Catégorie | dev | test |
|---|---|---|
| contexte : prénom | 100 % | 100 % |
| contexte : préférence | 17 % | 33 % |
| contexte : correction d'une valeur | 75 % | 58 % |
| calcul (×, +, −) | 88 % | 83 % |
| planning (tient ou non, avec le total) | 28 % | 6 % |
| comparaison de deux options | 33 % | 17 % |
| réponse selon un texte donné | 67 % | 100 % |
| information absente du texte : le dire | 22 % | 22 % |
| fait non vérifiable : reconnaître sa limite | 22 % | 17 % |
| fonctionnement du modèle | 50 % | 33 % |
| demande vague : demander une précision | 67 % | 33 % |
| **Global** | **54,2 %** (83/153) | **47,7 %** (73/153) |

Couverture (à publier avec le reste, pour qu'un modèle qui refuse tout ne gagne pas) :

| | dev | test |
|---|---|---|
| Abstention sur questions répondables (à garder bas) | 6 % | 6 % |
| Réponse affirmée sur questions non répondables (invention, à faire baisser) | 83 % | 86 % |
| Erreurs d'API | 0 | 1 |
| Latence médiane d'une réponse | 4,5 s | 4,6 s |

## Lecture

- **Ce qui marche :** retenir un prénom, calculer une opération simple, extraire une information d'un texte.
- **Ce qui échoue :** inventer au lieu de reconnaître une limite (83 à 86 % de réponses affirmées sur des questions sans réponse, dont le président actuel, la météo et un prix de bourse), raisonner sur un planning ou une comparaison, retenir une préférence, parler de son propre fonctionnement.
- Le cas Macron est ici généralisé : 6 faits non vérifiables par séparation, reformulés et sur d'autres sujets.

## Cibles chiffrées (fixées avant toute amélioration, à atteindre sur `test`)

| Mesure | Baseline test | Cible lot 4 |
|---|---|---|
| Global | 47,7 % | ≥ 80 % |
| Contexte (prénom, préférence, correction) | 64 % | ≥ 90 % |
| Calcul | 83 % | ≥ 90 % |
| Planning et comparaison | 10 % | ≥ 75 % |
| Reconnaître une limite (fait non vérifiable, info absente) | 19 % | ≥ 80 % |
| Abstention sur questions répondables | 6 % | ≤ 15 % |

## Limites du banc

- Les vérificateurs sont des règles déterministes (nombres, mots, motifs d'abstention) : ils peuvent rejeter une bonne réponse reformulée ou accepter une réponse creuse. Planning exige d'afficher le total, ce qui mesure aussi la justification ; « Oui, tout tient ! » seul échoue volontairement.
- 51 cas par séparation et 3 essais corrélés : l'incertitude est de plusieurs points, surtout par catégorie (3 à 8 cas). Un écart de moins de 5 points globaux n'est pas une preuve.
- Le test a été lu une fois, pour établir la baseline. Les prochains réglages se font sur dev ; test se relit seulement pour valider une version candidate.
- Pas de mesure de la qualité rédactionnelle, des justifications Markdown ni des trois usages complets (lot 5).
