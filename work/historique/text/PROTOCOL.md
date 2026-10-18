# Compréhension de texte — comparaison 0.1.0

Ce projet est distinct de Garry et de Playi. Il possède son propre dépôt, ses données, ses modèles et ses mesures.

## Question expérimentale

Sur des textes courts en français, un petit modèle entraîné de zéro peut-il distinguer une affirmation confirmée par le texte, une affirmation contredite et une information indéterminée ? Quelle différence pratique apporte l’adaptation d’un encodeur français préentraîné ?

Ce premier banc d’essai mesure une compétence limitée d’inférence. Une réussite ne démontre pas la compréhension générale du langage.

## Données figées avant l’apprentissage

- 3 600 exemples d’apprentissage ; 600 de validation.
- Quatre tests de 600 exemples : situations du même type, reformulations inédites, nouveaux prénoms, et composition spatiale à trois liens au lieu de deux.
- Cinq familles : négation, rôles dans un échange, chronologie, références pronominales et chaînes de lieux.
- Les trois réponses sont équilibrées dans chaque jeu de données.
- Une situation et ses trois affirmations restent dans une seule partition. Les doublons texte/affirmation sont interdits.
- Les connaissances préentraînées n’autorisent pas à inventer une information absente : on répond uniquement d’après le texte. Dans ces situations contrôlées, deux villes, deux contenants terminaux ou deux bâtiments nommés sont supposés disjoints. Les inclusions emboîtées restent permises : être dans une pièce implique être dans le bâtiment qui la contient. Dans l’échange unique décrit, donneur et receveur ont des rôles distincts. Ces conventions simplifient le monde ; elles devront être retirées ou exprimées dans le contexte pour évaluer du français libre.
- Les identifiants, familles et empreintes des fichiers sont enregistrés. Les tests ne sélectionnent ni l’époque ni les paramètres.

## Deux approches

1. **De zéro** : petit Transformer, deux couches, largeur 96, quatre têtes, entrée en octets UTF-8. Aucun poids ni vocabulaire préentraîné. Jusqu’à 30 époques, sélection sur la validation.
2. **Préentraîné** : CamemBERT-base français, environ 110 millions de paramètres, adapté avec une tête à trois sorties. Jusqu’à quatre époques, sélection sur la même validation. Seuls les fichiers de poids sûrs sont chargés ; aucun code distant n’est exécuté.

Les architectures et le préentraînement initial ont des coûts différents. On compare deux voies pratiques, sans attribuer causalement toute différence au seul préentraînement. Les budgets exacts, nombres de paramètres et volumes de données sont publiés.

Chaque approche est entraînée avec trois graines. Les tests sont ouverts après la sélection de tous les candidats. Un témoin fondé uniquement sur les mots de l’affirmation sert à détecter des raccourcis du jeu de données.

## Mesures

- Exactitude globale et par famille ; moyenne et dispersion sur trois graines.
- Matrice de confusion, dont les erreurs « information absente ».
- Réussite des groupes de trois affirmations d’une même situation.
- Temps d’apprentissage, nombre d’exemples présentés, mémoire du processus et mémoire GPU maximale.
- Latence sur le même appareil et exemples d’erreurs conservés.

Les données sont synthétiques et contrôlées. Les résultats devront ensuite être confrontés à des textes naturels rédigés indépendamment des générateurs.

## Sources techniques

- [CamemBERT : fiche du modèle et préentraînement](https://huggingface.co/almanach/camembert-base).
- [Adaptation à la classification de texte](https://huggingface.co/docs/transformers/tasks/sequence_classification).
- [Installation et vérification de PyTorch](https://pytorch.org/get-started/locally/).
