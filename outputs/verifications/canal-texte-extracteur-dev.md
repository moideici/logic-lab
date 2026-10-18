# Canal texte amélioré : Input comme extracteur structuré (18 octobre 2026, séparation dev)

Input extrait de la demande {langage, nom, signature, textes, consigne} en JSON contraint (3 exemples inventés dans l'invite, hors banc), une consigne est composée de façon déterministe, puis le cœur (Qwen2.5-Coder-0.5B, invite en bloc de code) écrit. Deux extracteurs : Qwen3-0.6B de base et Input tel qu'il est (base + adaptation active). Banc de code v1.1.0, dev, 23 demandes. Résultats bruts : `projets/code/bench/results/extraction-dev*.json`.

| Chaîne | Réussites | Langage correct | Nom correct |
|---|---|---|---|
| Demande directe (le langage est **fourni** au cœur : avantage artificiel) | 13/23 | donné | donné |
| Input reformule en français (mesure précédente) | 12/23 | donné | donné |
| Extracteur base, sans règle | 11/23 | 16/23 | 21/23 |
| Extracteur Input, sans règle | 10/23 | 19/23 | 18/23 |
| **Extracteur base + règle de langage** | **13/23** | 23/23 | 21/23 |
| **Extracteur Input + règle de langage** | **12/23** | 23/23 | 18/23 |

La règle est déterministe : sans mention de C++, une fonction est du Python ; la mention de C++ l'emporte. Sans elle, les 7 erreurs de langage de l'extracteur de base (4 pour Input) étaient toutes des demandes de fonction qui ne disent pas « Python » (il devinait C++). Un assistant réel devrait choisir un langage par défaut ou demander.

## Lecture

- **Aucune des chaînes texte ne dépasse la demande directe (13/23).** L'extraction structurée ne produit aucun gain mesurable : 13 contre 13 pour l'extracteur de base, 12 pour Input. L'écart de ±1 cas est dans le bruit.
- **Le goulot est le cœur, pas la communication.** Avec le langage et la signature corrects, le cœur échoue encore sur : des noms de fonction changés malgré la consigne (`inverser_mots` devenu `inverse_mots`, `compter_voyelles` devenu `compteur_voyelles`), des pages HTML sans `<nav>`, `<figure>` ou `<section>` pourtant demandés, des fonctions qui bouclent ou sont trop longues. Ce sont des limites d'un modèle de 0,5 G.
- **Ce que la communication peut gagner est borné.** Le même cœur avec la signature donnée dans l'invite de complétion réussit 17/23 (mesure du 18 octobre) ; avec une demande libre, 13/23. L'interface entre les deux modèles pèse donc au plus **4 cas sur 23** ; le reste dépend de la capacité du cœur.
- **Input comme extracteur est sûr, pas utile.** Il fournit un JSON valide à chaque fois (23/23 extractions valides), mais il invente parfois du contenu dans `textes` (du HTML complet dans un champ) et se trompe sur les noms (18/23 contre 21/23 pour le modèle de base).
- Qualité et pertinence : tous les livrables réussis sont propres (aucune répétition ni bavardage) ; les échecs sont visibles et classés (nom, structure HTML, longueur), pas des erreurs silencieuses.

## Limites

Dev uniquement (23 demandes, test non lu) ; une graine gloutonne ; demandes écrites par moi ; la règle de langage a été décidée après avoir vu les erreurs sur ce même dev, donc son gain est à confirmer sur test.

## Conséquences pour la suite

1. **Le témoin à battre pour le canal interne est 13/23 en dev**, plafond de communication d'environ 17/23 avec ce cœur.
2. **Avant d'entraîner un canal interne**, deux leviers moins chers existent : (a) une **boucle de retour** (exécuter les tests, renvoyer l'erreur au cœur qui corrige) ; (b) un cœur plus gros (Qwen2.5-Coder-1.5B) pour connaître le plafond, hors communication.
3. Le canal interne n'a de sens que s'il apporte plus que ce que le texte laisse sur la table : pour l'instant, au plus 4 cas sur 23.
