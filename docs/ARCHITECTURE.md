# Architecture et flux de données

## Vue d’ensemble

```text
Dossier de conversation
├── projets/garry       → serveur 8765 → interface jeux / arène / entraînement
├── projets/input       → serveur 8766 → conversation / bilan d’apprentissage
├── recherche/hrm       → expériences locales, sans connexion active à Input
├── recherche/trm       → source de référence
├── work                → environnements, dépendances, préparations historiques
├── outputs             → preuves et rapports historiques
└── documentation commune → périmètre et ordre des travaux
```

Les liens entre les deux interfaces sont des liens de navigation. Ils ne signifient pas que les modèles partagent déjà leurs poids ou leur mémoire. Chacun garde son dépôt Git et ses données.

## Garry : fonctionnement courant

Le navigateur affiche les jeux et peut utiliser les moteurs et poids présents dans `web/`. Le serveur Python ajoute l’API, les événements de partie, les sessions d’entraînement et les harnais de sites réels. Le code des environnements et des règles se trouve dans `logic_arena/`.

Garry possède un modèle partagé, avec des zones d’entrée et de sortie par jeu et un module commun. L’entraînement produit des candidats ; les critères de validation déterminent les promotions. Les poids actifs de référence sont dans `web/models/garry.json`. Les versions figées permettent les comparaisons avec d’anciennes IA.

Une décision peut utiliser le réseau, un moteur de recherche, un professeur borné ou un solveur selon le mode et le jeu. « Accord avec le professeur » ne veut donc pas dire « taux de victoire de toute l’application ». Les preuves de recherche doivent rester distinctes des estimations neuronales.

Le navigateur peut conserver des poids personnels plus anciens dans son stockage local. La prochaine recette doit rendre l’identité des poids réellement utilisés explicite.

## Input : fonctionnement courant

```text
Message et historique récent dans le navigateur
    → validation de la requête par le serveur
    → fenêtre de contexte bornée
    → Qwen3-0.6B + adaptation LoRA sélectionnée
    → décodage contraint du JSON
    → validation et sérialisation
    → présentation de la réponse dans l’interface
```

`serve.py` expose les pages et API. `chat.py` gère le dialogue, le contexte et le chargement du modèle. `decoding.py` borne la génération et les sorties JSON. `json_output.py` contrôle notamment les types, les nombres non finis, les doublons de clés et les collisions après simplification.

La première refonte utilise `streaming.py` et `/api/chat/stream` pour afficher le texte en cours. Un texte partiel n’est pas une réponse JSON finalisée. L’annulation et le contexte après interruption doivent faire partie de la recette du lot 1 ; les tests unitaires ne suffisent pas à valider toute l’interface.

L’API `/analyse` conserve la première expérience de classification de phrases. Elle ne représente pas le fonctionnement du dialogue actuel. La page `/bilan` publie les données disponibles, les exemples réellement vus et les mesures des cycles.

Les pointeurs `models/chat_base.json` et `models/chat/active.json` indiquent la base et l’adaptation à charger. Les poids de base restent distincts des adaptations. L’historique du navigateur ne se transforme pas automatiquement en apprentissage des poids.

## Recherche latente : état et objectif

HRM reçoit actuellement des symboles de sudoku ou un tenseur de sa propre représentation d’entrée. L’adaptateur continu préparé est entraînable, mais ne sait pas encore convertir une demande française en une représentation utile à HRM.

Architecture souhaitée à évaluer :

```text
Français → Input → adaptateur appris → cœur de raisonnement
                                    → résultat vérifiable
         ← réponse française / JSON ← adaptateur ou interface de retour
```

Le cœur définitif reste à choisir selon les problèmes à contraintes, la planification et la comparaison de scénarios. Les dimensions de tenseurs compatibles ne prouvent pas une compréhension commune. La qualité, le temps et la mémoire doivent être comparés aux autres interfaces possibles.

## Informations, connaissances et vérification

Le système cible doit distinguer informations fournies, résultats calculés, faits vérifiés et inconnues. Une phrase bien formée et un JSON valide ne prouvent pas la vérité de leur contenu.

Le recentrage vers le français, les maths, le contexte et le fonctionnement réel doit être appliqué au prochain programme d’apprentissage. Conserver les corpus Wikipédia dans l’archive ne les réintroduit pas automatiquement dans ce programme. Les scripts d’entraînement historiques doivent être relus avant réutilisation : certains mélangent encore des textes encyclopédiques.
