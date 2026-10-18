# Inventaire expliqué : contenu, rôle et justification

Le catalogue détaillé [CATALOGUE-FICHIERS.csv](CATALOGUE-FICHIERS.csv) comporte une ligne par fichier copié. Cette page explique les ensembles de manière lisible. Les originaux restent conservés pour éviter une perte pendant le regroupement ; les prochains travaux doivent viser les copies de ce dossier.

## Documentation commune

| Élément | Pourquoi il est ici |
|---|---|
| `PLAN-GLOBAL.md` | Une priorité commune explicite évite de reprendre une ancienne piste ou de relancer des travaux dans le désordre. |
| `README.md`, `docs/GUIDE.md` | Donner un point d’entrée, le chemin du dossier, les commandes et les précautions de reprise. |
| `docs/` à la racine | Expliquer les liens entre projets, les décisions et les limites ; les documentations internes ne couvrent pas tout ce contexte. |
| `docs/regroupement/REGROUPEMENT.json` | Retracer chaque copie, ses empreintes et les chemins adaptés ; rendre le regroupement contrôlable. |
| `docs/regroupement/VERIFICATION-REGROUPEMENT.json` | Distinguer les contrôles effectivement passés des vérifications encore en attente. |
| `docs/regroupement/CATALOGUE-FICHIERS.csv` | Répondre, fichier par fichier, à « quel est son rôle et pourquoi le conserver ? ». Les raisons sont celles de sa catégorie et, pour les modules Python, complétées par leur documentation disponible. |

## `projets/garry/`

| Ensemble | Rôle et raison de conservation |
|---|---|
| `logic_arena/` | Moteur : règles, observations, coups légaux, agents, modèle, recherche, API, sessions et entraînement. Nécessaire pour reproduire les comportements et reprendre le développement. |
| `web/` | Application de jeu, commandes, styles, moteurs navigateur et événements affichés. C’est la partie utilisée pour jouer. |
| `web/models/garry.json` | Poids actifs du modèle partagé. Le code seul ne restituerait pas le niveau appris. |
| `web/agents.json` | Identités et choix proposés par l’interface. Sert à relier les options visibles aux vrais agents. |
| `tests/` | Vérifications des règles, des niveaux, des formats et des comportements ; nécessaires pour détecter les régressions. |
| `examples/` | Programmes de fusion, préparation, entraînement et mesure ; conservés pour reproduire les expériences et comprendre leur protocole. |
| `training/continuous/` | États, données et résultats des sessions continues. Ils expliquent quelles promotions ont été retenues ou rejetées. |
| `training/external/` | Traces des essais sur les sites réels ; utiles pour vérifier les transitions et les résultats annoncés. |
| `training-runs/` | Expériences antérieures et leurs données ; elles sont des archives de comparaison, pas toutes des modèles actifs. |
| `versions/` | Références figées pour les duels et migrations. Les anciens numéros sont historiques et ne remplacent pas la version courante 0.6.0. |
| `tools/wasm/` | Outils et artefacts des moteurs compilés pour accélérer les recherches dans le navigateur. |
| `tools/real-games/` | Harnais reliant les agents aux interfaces des jeux réels. Les sites externes eux-mêmes ne sont pas copiés. |
| `search/` | Sources de recherche spécialisées ; elles expliquent une partie des décisions au-delà du réseau neuronal. |
| `docs/`, `README.md` internes | Protocoles et bilans propres à Garry, à replacer dans leur date et leur version. |
| `.git/`, `.gitignore`, `pyproject.toml` | Historique, règles de fichiers et définition du paquet. Préserver la provenance et permettre de travailler comme dans le dépôt d’origine. |

Les sessions invalidées sont gardées comme preuves d’erreurs de protocole et exclues des preuves de progrès. Les supprimer ferait perdre l’explication d’une restauration de poids ou d’une correction de séparation des données.

## `projets/input/`

| Ensemble | Rôle et raison de conservation |
|---|---|
| `chat.py`, `serve.py`, `decoding.py`, `streaming.py` | Chargement, contexte, génération, API et diffusion progressive. Nécessaires au dialogue et à sa recette. |
| `json_output.py` | Contrat de sérialisation et validation. La conformité du JSON doit dépendre du programme complet, pas seulement d’une compétence apprise. |
| `web/` | Conversation et bilan. L’affichage doit rester distinct de la validité syntaxique et de la vérité du contenu. |
| `models/chat_base.json` | Pointeur local de la base préentraînée avec son identité et sa révision. |
| `models/chat/active.json` | Pointeur de l’adaptation sélectionnée. Évite d’utiliser simplement le dernier fichier créé. |
| `models/chat/` | Adaptations, checkpoints et rapports ; nécessaires à la reproduction et au retour à une version précédente. |
| `chat_cache/` | Poids et tokenizer Qwen importés, avec la structure du cache. Permet de recharger sans télécharger à nouveau. |
| `chat_data/` | Dialogues et exercices supervisés avec leurs séparations et empreintes. Ils expliquent réellement ce qui a été entraîné. |
| `corpus/`, `sources.json` | Provenance, révisions, tailles et chemins des corpus. Nécessaires à l’attribution et à la reproduction. |
| `corpus_cache/` | Articles et dialogues importés. Archive disponible, sans valeur de preuve d’apprentissage et sans obligation de les réutiliser. |
| `lexicon/` | Petit lexique, sens, partitions et provenance. Sert aux essais de vocabulaire ; ce n’est pas un dictionnaire exhaustif. |
| `data/`, `build_benchmark.py`, `experiment.py` | Premier banc de classification, conservé pour comparer apprentissage de zéro et préentraînement sur une tâche limitée. |
| `models/scratch/`, `models/pretrained/`, `models/tokenizer/`, `cache/` | Poids et tokenizer des premiers classifieurs. Archives expérimentales, distinctes du modèle de conversation actif. |
| `train_language.py`, `train_focus.py`, préparateurs | Protocoles historiques reproductibles. Les relire avant un nouveau cycle, notamment pour retirer le mélange Wikipédia non souhaité. |
| `results/`, `telemetry.py` | Bilans, états, journaux et mesures matérielles. Distinguer progrès réel, échec et coût de calcul. |
| `bridge.py`, `BRIDGE.md` | Contrat JSON de diagnostic et témoin textuel. Il ne constitue pas la communication latente demandée. |
| `LATENT.md` | État de la recherche à sa date ; à compléter par le plan commun pour les décisions actuelles. |
| `tests/`, `.git/`, `requirements.txt` | Vérification, provenance et dépendances nécessaires à la maintenance. |

Les caches contiennent parfois à la fois des blobs et des chemins de snapshot. Leur structure est conservée pour compatibilité avec les chargeurs. Une optimisation de stockage ultérieure devra vérifier les usages avant de retirer des doublons. Les liens de fichiers ont été matérialisés lors de la copie pour éviter de dépendre des originaux.

## Recherche et ressources communes

| Ensemble | Pourquoi le conserver |
|---|---|
| `recherche/hrm/` | Fork réel, licence, poids officiels et prototype de canal continu. Base d’essai pour le raisonnement symbolique ; ne pas le présenter comme un assistant général. |
| `recherche/trm/` | Code de référence inspecté pour comparer les architectures récursives. Aucune connexion active à Input et aucun poids préentraîné téléchargé ici. |
| `work/text-env/` | Environnement Python déjà utilisé pour les expériences. Évite de perdre les versions installées ; son interpréteur de base reste un prérequis de la machine. |
| `work/python-deps/`, `work/browsers/`, `work/compiler/` | Dépendances, navigateur de test et compilation utilisés par les harnais. Gardés pour réexécuter les contrôles locaux. |
| Autres dossiers de `work/` | Étapes préparatoires, anciens cycles et scripts intermédiaires. Archives de travail, pas des copies actives à modifier à la place de `projets/`. |
| `outputs/` | Captures, rapports et traces de cette conversation. Ils étayent les affirmations mais certains décrivent des étapes désormais remplacées. |
| Répertoires `.git/` des projets | Conserver leurs historiques séparés évite de confondre une expérience Input avec une évolution de Garry. Aucun push ou commit supplémentaire n’a été réalisé par le regroupement. |

Les bibliothèques système, l’installation Codex et les sites web distants ne sont pas des sources du projet. Leur installation n’est pas dupliquée intégralement ; les prérequis et chemins nécessaires sont documentés.
