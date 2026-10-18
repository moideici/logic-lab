# Cœur Instruct, chaîne et boucle de retour (18 octobre 2026, séparation dev)

Modèle ajouté : `Qwen/Qwen2.5-Coder-0.5B-Instruct` (Apache 2.0, révision ea3f247, 988 Mo, téléchargé depuis Hugging Face avec accord). Même taille que le cœur de base, entraîné à suivre des consignes. Banc de code v1.1.0, dev, 23 demandes réalistes. Un passage donne le 1er essai et le cumul après 1 à 3 corrections. Résultats bruts : `projets/code/bench/results/instruct-*.json`.

## Tableau d'ensemble (dev, 23 tâches)

| Chaîne | 1er essai | Après corrections | Livrables propres (1er essai) |
|---|---|---|---|
| Cœur de base, demande directe | 13 | 13 | 13 |
| Cœur de base, Input reformule en texte | 12 | – | 11 |
| Cœur de base, Input extrait + règle de langage | 13 | – | 13 |
| Cœur de base, boucle de retour (3 corrections) | 13 | 13 | 13 |
| **Cœur Instruct, demande directe** | 14 | 15 | 11 |
| **Cœur Instruct + Input extrait** | 14 | 15 | 14 |
| **Cœur Instruct + Input extrait + début de réponse imposé** | **15** | 15 | **15 (tous)** |
| Cœur de base, complétion avec la signature exacte (meilleure invite, sans Input) | 17 | – | – |

Par langage pour la meilleure chaîne (Instruct + extraction + début imposé) : Python 7/12, C++ 4/5, HTML 4/6.

## Ce que montre la série

- **Le cœur Instruct apporte peu en nombre (+1 à +2) mais il répare un cas** avec la boucle de retour (le tableau HTML) : le modèle de base ne répare rien.
- **La qualité des livrables progresse nettement avec la chaîne** : de 11 livrables propres sur 14 réussis (demande directe) à 15 sur 15. Le contrôle de propreté exclut répétitions, longueurs absurdes et bavardage. L'extracteur et le début imposé évitent surtout les dérives (mauvais langage, code non demandé).
- **Imposer le début de la réponse aide le HTML** (`<!DOCTYPE html>` : de 2/6 à 4/6) et fixe le langage ; pour le code il faut vérifier que la signature correspond au langage retenu (un premier essai l'a rappelé : signature C++ imposée dans un bloc Python, 12/23).
- **Le reste des échecs est la capacité du modèle** : noms de fonction extraits ou écrits faux (`texto`, `inverser_mots` non défini), signature à deux arguments pour une fonction qui en demande un, chiffres romains (le cas `chiffres_romains(4)` renvoie 4), page sans `<script>` demandé. Une boucle de retour ne les corrige pas.
- **Le 17/23 du cœur de base avec la signature exacte** reste le meilleur score : la signature exacte dans l'invite vaut plus que n'importe quelle reformulation. Elle ne vient que d'une consigne très précise, pas d'une demande d'utilisateur.

## Pour juger la qualité plutôt que la quantité (consigne du jour)

Sur ce qui est livré, la meilleure chaîne produit **15 livrables corrects et propres**, sans bavardage, sans répétition, avec le bon langage et le bon nom de fonction ; les 8 autres échecs sont nets (le test échoue, la balise manque) et non des erreurs silencieuses. C'est le résultat à retenir, plutôt que le nombre brut de réussites.

## Limites

- Dev uniquement : **test non lu**, réservé pour confirmer. Un écart d'un ou deux cas n'est pas significatif ; seules les différences de propreté (11 contre 15) et l'absence de réparation du cœur de base sont assez nettes.
- Une graine (gloutonne, ou température 0,7 pour certaines corrections) ; 23 tâches par séparation ; demandes écrites par moi ; extracteur = Qwen3-0.6B de base à 3 exemples dans l'invite (l'adaptation actuelle d'Input ne fait pas mieux).
- La règle de langage par défaut et la vérification signature/langage ont été décidées en regardant ce même dev : leur gain est à confirmer sur test.

## Conséquences pour la suite

1. **Retenir comme canal texte de référence : Input extrait {langage, nom, signature, textes, consigne}, une consigne et un début de réponse sont composés de façon déterministe, le cœur Instruct écrit.** Score dev 15/23, 15 livrables propres.
2. **Le canal interne doit battre ces 15/23 et cette propreté**, pas le 13/23 du premier témoin, avec des témoins coupé et permuté. Marge théorique de communication : jusqu'à 17/23 pour le cœur de base avec une invite parfaite.
3. **Le cœur est le goulot.** Qwen2.5-Coder-1.5B donnerait le plafond hors communication (téléchargement d'environ 3 Go, à décider).
