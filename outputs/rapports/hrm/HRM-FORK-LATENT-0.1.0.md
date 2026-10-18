# Logic Lab — cœur de raisonnement latent, prototype 0.1.0

Ce fork de travail local part de **HRM symbolique**, dont la communication
primaire est une séquence de symboles de problème, avec raisonnement récursif
sur des états continus. Il n’utilise pas de vocabulaire de mots français ou
anglais. La première tâche est le sudoku 9×9, avec les poids officiels.

Sources : [code HRM](https://github.com/sapientinc/HRM),
[article](https://arxiv.org/abs/2506.21734),
[poids sudoku](https://huggingface.co/sapientinc/HRM-checkpoint-sudoku-extreme).
La révision du code, celle des poids et leur empreinte figurent dans
`fork_manifest.json`. Le code amont et sa licence Apache-2.0 sont conservés.

## Ce qui est installé

- Chargement strict des poids officiels, vérification SHA-256 et
  `torch.load(weights_only=True)`. Pas de script d’entraînement distant lancé.
- Attention PyTorch portable pour Windows et CPU, en conservant les noms et
  dimensions des poids du checkpoint.
- `inner.forward_embeddings` reçoit directement un tenseur continu au bon
  format et renvoie les états de raisonnement et les scores symboliques.
  L’entrée symbolique d’origine passe par la même méthode.
- `ContinuousAdapter` : adaptateur entraînable à requêtes apprises, reliant
  les états d’Input aux emplacements de l’entrée HRM. Ses liaisons nomment
  explicitement les modèles, poids, couches et dimensions. On peut instancier
  un autre adaptateur pour le retour vers Input.

**L’adaptateur français ↔ HRM n’est pas encore entraîné.** Injecter des
tenseurs de la bonne taille ne prouve pas leur compréhension. Les tests
vérifient l’équivalence de l’ancienne entrée native, la propagation des
gradients vers l’adaptateur et les masques. Les essais sur quelques grilles
sont des contrôles techniques, pas une nouvelle mesure du score publié.

Ce modèle n’est pas un assistant général ni un système de connaissances.
Sa supériorité sur Input n’est pas présumée sur toutes les tâches. Les tâches
prises en charge doivent être apprises et évaluées séparément.

## Architecture visée

Français → états internes d’Input → adaptateur appris → cœur HRM →
états de résultat → adaptateur de retour → réponse française et JSON validé.

Le canal entre les modèles transporte des tenseurs ; le JSON sert à
l’interface, à la configuration et aux mesures. Le runtime de conversation
Input n’est pas encore branché à ce cœur expérimental.

## Vérification locale

Utiliser l’environnement PyTorch du projet Input, avec `einops==0.8.1`.

```
python -m unittest discover -s tests -v
python smoke_hrm.py
```

Le contrôle actuel utilise le CPU pour laisser finir le programme GPU de
30 minutes d’Input. Reproduire les entraînements complets des articles
demanderait des budgets très supérieurs à ce contrôle.

## Prochain protocole expérimental

1. Figer un checkpoint d’Input et les poids HRM. Toute modification des poids
   change l’identité de la représentation et exige une nouvelle évaluation.
2. Préparer des paires français/contexte ↔ problème structuré, sans réponse
   dans l’entrée, séparées par grille et transformation, avec reformulations
   réservées et cas ambigus demandant une clarification.
3. Entraîner l’adaptateur à reproduire l’entrée native puis à résoudre les
   tâches via le cœur gelé. Travailler le retour français séparément.
4. Comparer sur les mêmes cas : voie symbolique native, voie textuelle,
   voie latente, canal coupé et messages permutés. Mesurer les solutions
   exactes, les contraintes conservées, le temps et la mémoire.
5. Activer dans Input seulement après validation. Une amélioration de perte
   ou un bon résultat sur une grille ne suffisent pas.

TRM a également été inspecté comme référence de conception, dans le dossier
voisin `latent-reasoner`. Le prototype actif ici utilise HRM et ses poids
publiés ; il ne réétiquette pas ces poids comme étant ceux de TRM.

## Premier contrôle effectué

Trois tests techniques passent. Avec les poids officiels inchangés, sur CPU, la grille classique du contrôle est résolue en environ 1,55 seconde. La grille presque remplie échoue : des valeurs données sont modifiées. Ce résultat est conservé dans `local_results/native-smoke.json` et ne déclenche aucune réparation cachée. Ce sont deux contrôles publics, pas un banc d’évaluation indépendant.

Les versions de l’environnement réellement utilisé sont enregistrées dans `local_environment.json`.
