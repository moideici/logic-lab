> Rapport historique de Garry 3.0.0. Voir [le cycle de diversité 3.1.0](GARRY-DIVERSITE.md) pour les changements suivants.

# Garry : priorité à la force au niveau 10

Travail appliqué dans `%USERPROFILE%\code\playi`, le 16 octobre 2026.

Garry cherche désormais au moins 20 demi-coups au niveau 10 de Puissance 4 et poursuit plus loin si le budget le permet. Un demi-coup est une action d’un joueur ; 20 demi-coups couvrent donc dix coups de Garry et dix réponses adverses. La cible est un objectif de recherche, pas une profondeur annoncée artificiellement.

## Ce qui fonctionne maintenant

- Recherche du meilleur coup prioritaire au niveau 10, sans calculer le classement complet des mauvais coups.
- Deux secondes par décision et plafond de 200 millions de nœuds ; approfondissement jusqu’aux cases restantes, dans la limite du budget.
- Recherche principale avec fenêtres étroites, nouvelles recherches si nécessaire, table de transpositions de plus d’un million d’entrées et cache des évaluations.
- Détection prouvée des doubles menaces à l’horizon, prolongement des réponses forcées, protection des victoires et blocages immédiats.
- Branche de valeur apprise, intégrée au même fichier Garry et utilisée à l’horizon de la recherche. Elle évalue les positions publiques à partir de 32 caractéristiques de lignes, colonnes et menaces. La politique neuronale commune aux six jeux conserve exactement ses matrices précédentes.
- Profondeur terminée et cible séparées dans les réponses ; les lignes anticipées peuvent être partielles lorsque les entrées correspondantes de la table ont été remplacées. Une victoire forcée est distinguée d’une simple estimation favorable.

## Profondeur réellement mesurée

Mesures locales avec le profil actif de deux secondes ; cinq positions ciblées, sans prétendre à une statistique générale de victoire.

| Coups déjà joués | Profondeur terminée | Résultat de l’analyse |
|---:|---:|---|
| 0 | 21 demi-coups | Estimation bornée, sans preuve du résultat final |
| 6 | 28 demi-coups | Estimation bornée, sans preuve du résultat final |
| 12 | 25 demi-coups | Victoire forcée prouvée |
| 18 | 17 demi-coups | Victoire forcée prouvée |
| 24 | 14 demi-coups | Défaite forcée prouvée |

Une position déjà perdante peut rester perdante même avec le meilleur coup. Une profondeur élevée ne suffit donc pas à définir un agent imbattable.

## Comparaison avec la génération précédente

Même lot de 40 parties, mêmes ouvertures de six coups rejouées dans les deux camps, même graine 9 200 000, même budget de trois millions de nœuds par décision pour les deux générations. L’adversaire reste la référence 1.0.0 figée, limitée à 5 000 nœuds. Le moteur compilé et les poids de Garry 2.0.0 sont conservés pour rejouer le contrôle.

| Agent | Victoires | Défaites | Nuls |
|---|---:|---:|---:|
| Garry 2.0.0 conservé | 30 | 6 | 4 |
| Garry 3.0.0 actif | 32 | 3 | 5 |

Les défaites observées passent de 15 % à 7,5 % sur ce lot. Ce contrôle compare bien les deux générations entre elles à budget identique. Les budgets face à l’adversaire sont différents ; ce n’est pas un test à temps égal ni une preuve statistique d’invincibilité. Les ouvertures aléatoires peuvent aussi imposer une position défavorable avant la première décision de Garry.

Depuis le plateau vide, deux trajectoires distinctes ont été testées : Garry gagne en premier joueur en 35 coups et en second joueur en 34 coups. Ces deux parties ne sont pas artificiellement multipliées en répétant les mêmes décisions déterministes.

Un autre lot de 40 ouvertures, graine 7 900 000 et horizon fixé à 20, donne 35 victoires, 3 défaites, 2 nuls face à la même référence.

## Apprentissage et sélection

Deux sessions de 400 et 1 600 trajectoires ont été terminées. Le professeur est un moteur de recherche figé ; les cibles sont ses scores après une recherche plus profonde. Il s’agit de distillation de recherche, pas encore d’un entraînement complet par autojeu avec cibles de résultat final.

La variante installée utilise 2 872 positions d’apprentissage, avec 735 positions réservées à la validation et séparées par trajectoire. Les paramètres de régularisation sont choisis sur une autre partie des données d’apprentissage. Les doublons exacts et leurs miroirs sont filtrés ; les poids respectent la symétrie du plateau et inversent le signe lorsque les joueurs sont échangés.

L’erreur de l’évaluation historique vaut 161,05 sur ces positions ; celle du candidat brut vaut 118,35. Le candidat brut a cependant donné davantage de défaites sur un contrôle indépendant : il n’a pas été installé tel quel. L’évaluation active mélange à parts égales les coefficients historiques et appris : erreur 131,72, révision `20261016-position-02-mix50`.

Sur un nouveau lot indépendant de 200 duels face à Garry 2.0.0, les deux variantes utilisent le même moteur renforcé, un horizon maximal de 20 et 100 000 nœuds :

| Évaluation | Victoires | Défaites | Nuls |
|---|---:|---:|---:|
| Historique | 97 | 96 | 7 |
| Mélange retenu | 94 | 91 | 15 |

Le mélange réduit les défaites sur ce lot et augmente légèrement le score victoires + moitié des nuls. Il est plus coûteux à calculer ; ce contrôle en nœuds ne démontre pas à lui seul un gain à temps égal. Le gain reste modeste, sans affirmation de supériorité statistiquement établie. Le candidat entraîné sur 9 963 positions, avec 2 527 positions de validation, n’a pas été retenu : davantage de données n’a pas suffi à améliorer les parties de sélection.

## Versions et conservation

Le passage à **3.0.0** correspond à l’ajout effectif de la branche d’évaluation de position au modèle, et au format `garry-mlp-v2`. Il ne découle pas du taux de victoire. Le réseau de politique conserve ses dimensions 1 912 → 48 → 48 → 818 ; la branche supplémentaire possède 32 coefficients, soit 134 290 paramètres au total. Elle est actuellement spécialisée sur Puissance 4 ; elle ne constitue pas un réseau de valeur partagé appris pour les six jeux.

Un seul modèle est chargé, sauvegardé et exporté. Les exports 2.0.0 restent lisibles ; la migration du navigateur conserve leurs politiques et ajoute l’évaluateur livré. Les cinq autres modes n’ont subi aucune modification de poids lors de cette formation de valeur.

Le réglage 0–10 existe dans l’interface, les workers et l’API. Les niveaux inférieurs sélectionnent des rangs de qualité ; 0 choisit le pire coup selon l’analyse disponible. Le niveau 10 réserve son effort au meilleur coup trouvé. Les garanties exactes du morpion et du taquin sont conservées. Les scores issus d’une recherche bornée restent des estimations.

## Vérification et reproduction

67 tests passent : 45 Python et 22 JavaScript. Ils couvrent notamment les 4 520 états jouables du morpion, les extrêmes de difficulté, des fins de partie de Puissance 4 vérifiées par un oracle indépendant, les prévisions légales, la cohérence Python/JavaScript/WebAssembly, la conservation des poids, l’import et l’export.

Le navigateur a aussi été vérifié sur les six jeux : suggestions et coups dans le worker aux niveaux 0 et 10, entraînement, export unique, stockage, rechargement et migration 2.0.0 → 3.0.0. Aucun message d’erreur de page.

Dans le dépôt :

```text
python -m unittest discover -s tests
node --test tests/garry.test.mjs tests/web.test.mjs tests/levels.test.mjs
node examples/probe_garry_depth.mjs
node examples/compare_garry_generations.mjs
python examples/train_garry_value.py --games 1600 --output training-runs/nouvelle-session
```

Rapports : `web/models/garry-generations-evaluation.json`, `garry-reference-evaluation.json`, `garry-strength-evaluation.json`, `garry-depth.json`, et historique dans `garry-training.json`. Les candidats restent dans `training-runs/` ; entraîner ne remplace pas automatiquement le modèle actif.

**L’objectif de zéro défaite n’est pas encore atteint.** Le niveau 10 est renforcé et l’amélioration est mesurée, avec trois défaites restantes sur le contrôle comparatif de 40 parties.
