# Boucle de retour : exécuter les tests et renvoyer l'erreur au cœur (18 octobre 2026, dev)

Cœur : Qwen2.5-Coder-0.5B (base). Départ : demande directe, invite en bloc de code (13/23 sur dev). Si le livrable échoue, il est exécuté, l'erreur est renvoyée au cœur avec son code (« Ce code ne convient pas : … Voici la version corrigée : »), jusqu'à 3 corrections. Le retour est celui qu'un utilisateur verrait : erreur de compilation ou d'exécution, ou « le test n°2 échoue : f([1, 2]) a renvoyé 3 » ; **jamais la valeur attendue**. Pour HTML, les éléments manquants.

| Variante | Réussis avant | Après 1 correction | Après 2 | Après 3 |
|---|---|---|---|---|
| Corrections gloutonnes (messages d'erreur initiaux) | 13/23 | 13 | 13 | 13 |
| Corrections avec température 0,7 | 13/23 | 13 | 13 | 13 |
| Corrections avec température 0,7 **et** vraie erreur de compilation (v2) | 13/23 | 13 | 13 | 13 |

**Aucune réparation sur 30 retours**, quelle que soit la variante. Résultats bruts : `projets/code/bench/results/boucle-dev*.json`.

## Pourquoi

- Le cœur **recopie son code précédent** : pour `somme_pairs` en C++, l'erreur « 'accumulate' was not declared in this scope » lui est renvoyée trois fois et il réécrit trois fois la même fonction sans `#include <numeric>`.
- Pour `est_premier` en Python, l'erreur est « NameError : name 'est_premier' is not defined » ; il garde le nom `is_premier`.
- Pour `aplatir`, il livre un squelette `def une_fonction(listes): pass` et le conserve.
- C'est le comportement d'un **modèle de base** (non entraîné à suivre des consignes) : un bloc de code suivi de « version corrigée » le pousse à répéter. Il a été réputé ne pas convenir aux conversations par sa carte.

## Défaut de mon banc corrigé en cours de route

Les premiers messages C++ étaient la ligne « In function … » du compilateur, sans l'erreur réelle. Corrigé (le message contient maintenant la ligne `error:`), ce qui n'a rien changé au résultat.

## Conséquences

- **Cette boucle ne sert à rien avec ce cœur de base.** Ce n'est pas un échec du principe de boucle : c'est l'absence d'entraînement à suivre une consigne.
- **Candidat évident : Qwen2.5-Coder-0.5B-Instruct** (même taille, Apache 2.0), entraîné à répondre aux consignes et à corriger. Il sert aussi la chaîne principale : comprendre une demande en français est ce que le modèle de base fait mal (squelettes vides, noms changés).
- Le canal interne ne règle pas ce problème : il pose la même question (le cœur sait-il utiliser ce qu'on lui donne ?). À mesurer sur le cœur Instruct avant d'entraîner un projecteur.

Limites : dev uniquement, 23 tâches, une graine par variante, retour d'information à base de nos tests (un utilisateur n'en fournit pas toujours).
