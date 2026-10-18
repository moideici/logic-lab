# Canal texte de référence : Input → cœur de code (18 octobre 2026, séparation dev)

Cœur : Qwen2.5-Coder-0.5B (base). Input : Qwen3-0.6B **sans adaptation** (consigne de reformulation en invite système, génération gloutonne). Banc de code v1.1.0, séparation dev (12 Python, 5 C++, 6 HTML), 46 demandes réalistes écrites pour l'occasion (`projets/code/bench/demandes.py`). Invite du cœur : la demande puis un bloc de code ouvert. Résultats bruts : `projets/code/bench/results/chaine-texte-dev-v2.json`.

Trois variantes avec le même cœur :
- **précis** : la consigne exacte du banc, avec la signature (témoin « parfaitement posé ») ;
- **direct** : la demande de l'utilisateur telle quelle, sans Input ;
- **input** : la demande reformulée par Input.

| Variante | Réussites | Livrables propres* | Python | C++ | HTML |
|---|---|---|---|---|---|
| précis | 13/23 | 13 | 5/12 | 4/5 | 4/6 |
| **direct** | **13/23** | 13 | 7/12 | 4/5 | 2/6 |
| input | 12/23 | 11 | 5/12 | 3/5 | 4/6 |

\* « propre » = réussi ET sans répétition dégénérée, sans longueur absurde ni bavardage. 2 livrables d'Input réussis ou presque comportaient des répétitions.

## Ce que montrent les chiffres

- **Le canal texte via un Input de 0,6 G n'apporte rien** : 12/23 contre 13/23 en passant la demande telle quelle. L'écart est dans le bruit, mais il n'y a aucun gain.
- **Il corrompt parfois la demande.** Trois reformulations observées sur 23 : « La consigne technique courte et précise est : `def est_palindrome(texte):` » (le sens est perdu) ; « La consigne : `def cliquer(): return "Bonjour"` » pour une page HTML (la demande est devenue du Python) ; d'autres copient la demande presque mot pour mot. Dans quelques cas la reformulation aide (liste_lien et navigation en HTML), sans qu'on puisse dire pourquoi : peut-être le préfixe « Consigne : » plutôt que le fond.
- **L'invite compte plus que la reformulation.** Avec la signature donnée dans le prompt de complétion, le cœur seul réussit 17/23 sur ce même banc (mesure du 18 octobre). Avec une demande libre, il tombe à 13/23. Donner le nom de la fonction et le langage au cœur vaut plus que de reformuler la phrase.
- **Une première version de l'invite (commentaires de code) a donné 4 à 7 réussites sur 23** : le modèle de base inventait des en-têtes (« # Auteur… ») et commentait au lieu de coder. Corrigée avec un bloc de code ouvert (format que les modèles de code connaissent). Les chiffres ci-dessus sont ceux de la version corrigée.

## Qualité et pertinence de ce qui est livré

Lecture de la sortie plutôt que du seul score, comme demandé :
- **Quand ça passe, c'est pertinent et sobre** : les fonctions courtes sont idiomatiques et sans bavardage (`inverser_mots`, `pgcd`) ; les pages HTML ont la bonne structure (formulaire avec champs `nom` et `email`, tableau avec en-tête). Quelques ajouts anodins : un `action="contact.php"` non demandé, des noms d'exemple (« John », « New York »).
- **Quand ça échoue, c'est souvent de peu** : `somme_pairs` en C++ utilise `accumulate` sans l'inclusion `<numeric>` (une ligne manquante) ; certains Python bavardent et boucle (« Remplacer les espaces par des espaces vides » répété).
- **Les échecs nets viennent d'une consigne mal comprise**, pas de la syntaxe : un bouton HTML devenu du PHP, une page demandée en HTML livrée comme exercice vide.

## Limites

- Séparation dev uniquement (23 demandes) ; **test non lu**, réservé pour comparer les canaux plus tard. Un écart d'un cas n'est pas significatif.
- Input est ici le modèle de base Qwen3-0.6B, **sans l'adaptation d'Input** (celle-ci est entraînée à produire du JSON, pas à reformuler). Un Input entraîné pour cette tâche pourrait faire mieux ; cela reste à tester.
- Un seul cœur, une seule génération gloutonne, 46 demandes écrites par moi (non issues d'utilisateurs réels).

## Conséquence pour la suite

Le témoin « texte » à battre est **13/23 en dev** (demande directe). Reformuler en français avec un petit modèle ne sert pas. Ce qui aiderait le cœur est de connaître **le langage, le nom de la fonction et les textes à reprendre**, c'est-à-dire une extraction structurée, ce qu'Input sait déjà faire en JSON (`valeurs`). C'est le candidat pour un meilleur canal texte, et un point de comparaison honnête avant d'entraîner un canal interne.
