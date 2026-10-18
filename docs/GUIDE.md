# Guide : lancer, vérifier, reprendre

Dossier : `C:\Users\gabor\code\logic-lab` (déplacé le 18 octobre 2026 depuis `Documents\Codex\2026-10-16\tra`). Ce guide remplace les anciens LIRE-MOI, EXPLOITATION, VALIDATION et REPRISE.

## Arborescence

| Dossier | Contenu |
|---|---|
| `projets/garry` | Playi / Logic Lab / Garry 0.6.0 : jeux, IA, poids, entraînements, harnais. Dépôt Git propre. |
| `projets/input` | Projet français : Qwen3-0.6B + LoRA, corpus, lexique, interface, tests. Dépôt Git propre. |
| `recherche/hrm`, `recherche/trm` | Expériences de raisonnement récursif, séparées de la production. |
| `outputs/` | Preuves de la conversation : `rapports/{garry,input,hrm}`, `verifications/`, `captures/`, `journaux/`. |
| `work/` | `text-env` (venv), `python-runtime` (Python 3.12 autonome), `python-deps`, `browsers`, `compiler` ; `historique/` = anciens scripts. |
| `docs/` | Ce guide, `ARCHITECTURE.md`, `DECISIONS.md`, `regroupement/` (provenance, empreintes, catalogue, inventaire). |

## Lancer (PowerShell, à la racine du projet)

```powershell
$python = Join-Path $PWD 'work\text-env\Scripts\python.exe'
$env:PYTHONUTF8 = '1'
$env:TOKENIZERS_PARALLELISM = 'false'
```

Input (terminal 1) :

```powershell
Set-Location .\projets\input
& $python serve.py --port 8766
```

Garry (terminal 2, depuis la racine) :

```powershell
$env:PYTHONPATH = (Join-Path $PWD 'work\python-deps')
Set-Location .\projets\garry
& $python -m logic_arena serve --port 8765
```

Adresses : [Garry](http://127.0.0.1:8765/), [Input](http://127.0.0.1:8766/), [bilan Input](http://127.0.0.1:8766/bilan). Ne pas lancer deux serveurs sur le même port. Les conversations Input vivent dans le stockage du navigateur (origine et port compris).

## Environnement

- `work/python-runtime/` est une copie de Python 3.12 ; `work/text-env/pyvenv.cfg` pointe dessus, donc le venv ne dépend plus du cache de Codex. Vérifié : PyTorch 2.7.1+cu126, CUDA disponible, transformers 4.57.6.
- `work/requirements.lock.txt` liste les paquets du venv (`pip freeze`) pour le recréer si besoin.
- Non portable vers une autre machine : chemins absolus Windows, pilotes CUDA locaux.

## Vérifier

Depuis chaque projet : `python -m unittest discover -s tests -v` (Garry : `PYTHONPATH` = `work\python-deps` + dossier du projet).

Mesuré le 18 octobre 2026 après déplacement (Garry, Input) :

| Composant | Résultat |
|---|---|
| Garry | 114 tests réussis en 29 s. Le blocage vu pendant le regroupement ne se reproduit pas : le test visé passe en 1 s ; le modèle répond en moins de 0,02 s sur les 14 jeux aux niveaux 1, 5 et 10. La cause du blocage initial reste inconnue (probable contention avec un processus concurrent), pas un défaut du test. |
| Input | 21 tests réussis. |
| HRM | Non remesuré après déplacement. Mesure du regroupement : 3 tests réussis ; `smoke_hrm.py` : 1 grille publique résolue sur 2 (la seconde échoue déjà dans l'état de référence). |

Ces tests ne remplacent pas la recette navigateur (boutons, streaming, arrêt, conversations, mobile) ni une mesure de la qualité des réponses. Rapports de provenance : `docs/regroupement/`.

## Sauvegarde et doublons

- Git : `projets/garry` et `projets/input` ont leurs commits du 18 octobre 2026 (poids, corpus et caches exclus par `.gitignore`). Le Git de Input n'avait aucun commit avant cette date.
- Les poids (`projets/input/models`, ~14 Go avec caches) ne sont pas versionnés ; seule une copie sur un autre disque ou un service externe les protège. Tout est actuellement sur le disque C:.
- Les originaux `C:\Users\gabor\code\{playi, text-comprehension, latent-reasoner, latent-reasoner-hrm}` ont été supprimés le 18 octobre 2026, après contrôle d'identité avec les copies (`work/historique/cmp_originaux.py`). Ce dossier est désormais la seule copie : d'où l'importance d'une sauvegarde externe des poids.

## Reprise

Prochain livrable : recette de l'interface d'Input (lot 1 de `PLAN-GLOBAL.md`) : serveur et poids réellement chargés, lecture naturelle, JSON copiable, streaming, arrêt, nouvelle tentative, contexte, migration des anciennes conversations, mobile. Une réponse correcte sur une commande ne valide pas la connaissance générale.

Règles de continuité :

- Garry et Input gardent modèles et métriques séparés ; Garry reste 0.6.0 tant que le code ne change pas.
- Trois usages : contraintes, plans, comparaison de scénarios ; JSON strict, Markdown seulement dans `texte` et `justification`.
- Ne pas relancer un ancien script ou un entraînement parce qu'il existe : lire le plan, figer les données, séparer apprentissage, validation et test.
- Les scripts de `work/historique/` sont des archives (voir son README).

## Jeux réels (2048 et COSUMI)

L'onglet « Jeux réels » lance un navigateur Chromium sans fenêtre (Playwright) sur les sites 2048 et COSUMI. Le navigateur du projet est dans `work/browsers` ; le serveur le désigne tout seul (`PLAYWRIGHT_BROWSERS_PATH`). Si les parties échouent avec « Executable doesn't exist », c'est que ce dossier manque ou que la révision de Playwright a changé : relancer `npx playwright install chromium` dans `projets/garry/tools/real-games` avec `PLAYWRIGHT_BROWSERS_PATH` pointant vers `work/browsers`. Vérifié le 18 octobre 2026 : 12 coups de 2048 (12 transitions vérifiées) et 10 étapes de Go 9×9 contre COSUMI niveau 1.
