# Logic Lab — dossier commun de travail

**Dossier : `C:\Users\gabor\code\logic-lab`**

Deux projets sont regroupés ici, avec leurs données, modèles, essais, historiques Git et rapports. Ils conservent leurs architectures et leurs mesures séparées.

## Lire dans cet ordre

1. [PLAN-GLOBAL.md](PLAN-GLOBAL.md) — objectifs, bilan, périmètre actif des modèles, prochaines étapes. Fait autorité sur les anciens rapports.
2. [docs/GUIDE.md](docs/GUIDE.md) — arborescence, lancement, vérifications, sauvegardes, reprise.
3. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — composants et circulation des informations.
4. [docs/DECISIONS.md](docs/DECISIONS.md) — décisions, raisons et sujets ouverts.

Provenance du regroupement (manifeste, empreintes, catalogue fichier par fichier, inventaire justifié) : [docs/regroupement/](docs/regroupement/).

## Points d’entrée des projets

- [Garry / Playi](projets/garry/README.md) : quatorze jeux et leur IA ; version active 0.6.0.
- [Input](projets/input/README.md) : compréhension, français et réponses JSON ; adaptation de Qwen3-0.6B.
- [HRM](recherche/hrm/LATENT_FORK.md) : prototype symbolique sudoku et canal continu expérimental.
- [TRM](recherche/trm/README.md) : référence de recherche, pas un modèle activé dans Input.

Les documents importés avec les projets décrivent parfois des étapes historiques : versions précédentes, ancienne priorité Wikipédia ou ancien canal JSON entre modèles. Les décisions les plus récentes sont dans le plan commun et `docs/DECISIONS.md`.

## Reprise

La priorité est de finir la recette et la stabilisation de l’interface d’Input. Le regroupement ne relance pas les entraînements, ne démarre pas les copies des serveurs et ne modifie pas les originaux. Les conversations privées restent dans le navigateur ; les logiciels installés, dont l’interpréteur Python de base, restent des prérequis de la machine.
