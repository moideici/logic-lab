# Compréhension du français — prototype 0.1.0

Projet indépendant de Garry/Playi. Première tâche : lire un court texte français et classer une affirmation comme **confirmée**, **contredite** ou **indéterminée**. Il ne s’agit pas encore d’un assistant conversationnel.

Le [protocole](PROTOCOL.md) compare un petit Transformer initialisé au hasard à CamemBERT adapté sur les mêmes exemples. Trois graines par approche ; sélection sur la validation uniquement. Les résultats incluent des reformulations et noms inédits, des chaînes plus longues et un témoin qui ignore le texte.

## Reproduire

Python 3.12, PyTorch 2.7.1 (CUDA 12.6 sur cette machine), Transformers 4.57.6. Installer les dépendances dans un environnement distinct. Pour le GPU : `pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cu126`, puis `pip install -r requirements.txt`.

1. `python build_benchmark.py` fige les données et leurs empreintes.
2. `python -m unittest discover -s tests` vérifie leur séparation.
3. `python experiment.py` entraîne les six candidats puis évalue les tests réservés. Le premier passage télécharge le modèle français public, révision figée, uniquement en safetensors, sans code distant.
4. Lire `results/report.json` et `results/status.json`. Les poids sont dans `models/`.

Sur cette machine, l’environnement d’expérience est `C:\Users\gabor\Documents\Codex\2026-10-16\tra\work\text-env`. Les données et les poids appartiennent à ce dépôt, pas à Playi. Les entraînements utilisent la RTX 4060 ; Garry reste sur le CPU.

## Limites

Les textes sont synthétiques et les hypothèses du générateur sont explicites. Les deux architectures ont des tailles et des historiques d’apprentissage différents. Ces résultats mesurent une petite tâche d’inférence contrôlée ; ils ne prouvent ni compréhension générale ni robustesse sur du français libre. Les scores du témoin sans contexte servent à détecter des indices exploitables sans lire le texte. Les probabilités ne sont pas calibrées.
