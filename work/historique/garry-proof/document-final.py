from pathlib import Path
import json,hashlib,shutil
root=Path.cwd();run=root/'training-runs/garry-zero-20261017';work=Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
trials=json.loads((run/'public-api-duels.json').read_text());stability=json.loads((run/'memory-duels.json').read_text());holdout=json.loads((run/'positions-heldout.json').read_text());migration=json.loads((run/'browser-migration.json').read_text())
assert trials['completed'] and trials['zero_defeats'] and stability['completed'] and stability['losses']==0
for name,stats in trials['opponents'].items():
    assert stats['after']['losses']==0
    for p in (1,2):assert sum(stats['seats'][str(p)].values())==trials['repetitions']
model=json.loads((root/'web/models/garry.json').read_text());before=json.loads((root/'versions/3.1.0/garry.json').read_text())
for key in ('w1','b1','w2','b2','core','position_head','steps','game_steps','input','hidden','output'):assert model[key]==before[key]
manifest=json.loads((root/'versions/3.1.0/manifest.json').read_text())
for name,expected in manifest['sha256'].items():assert sha(root/'versions/3.1.0'/name)==expected
assert sha(root/'web/connect4-search.wasm')==sha(work/'rebuilt.wasm')
assert migration['learned_weights_and_steps_preserved'] and migration['errors']==[]
assert 'Ran 59 tests' in (run/'python-tests.log').read_text() and '\nOK' in (run/'python-tests.log').read_text()
assert 'pass 28' in (run/'node-tests.log').read_text() and 'fail 0' in (run/'node-tests.log').read_text()
report={'format':'garry-zero-defeat-evaluation-v1','software_version':'3.2.0','architecture_changed':False,'policy_weights_revision':'20261016-repertoire-02','search_revision':'20261017-certified-opening-01','scope':'Duels depuis le plateau vide contre la version précédente 3.1.0, dans les deux camps, réglages niveau 10 originaux.','zero_defeats_verified':True,'claim_scope':'observed_duels_at_original_level10_settings','universal_invincibility_claim':False,'opponents':trials['opponents'],'default_budget':{'nodes':200000000,'time_ms':2000,'max_depth':42},'full_game_trace_file':'training-runs/garry-zero-20261017/public-api-duels.json','prototype_stability':{k:stability[k] for k in ('wins','losses','draws','completed')},'independent_position_control':{k:holdout[k] for k in ('seed','requested','nodes','before','after','paired_known')},'validation':{'python_tests':59,'javascript_tests':28,'independent_endgame_oracle_cases':200,'six_game_browser_smoke':True,'browser_migration':migration,'binary_rebuild_identical':True,'frozen_reference_manifest_verified':True,'all_neural_weights_and_steps_preserved':True},'search_memory_entries':len(model['search_memory']['entries']),'source_model_sha256':sha(root/'versions/3.1.0/garry.json'),'installed_model_sha256':sha(root/'web/models/garry.json'),'frozen_wasm_sha256':sha(root/'versions/3.1.0/connect4-search.wasm'),'installed_wasm_sha256':sha(root/'web/connect4-search.wasm'),'limitations':['The empty-board games against a deterministic opponent do not establish universal invincibility against every strategy or arbitrary position.','The first defensive opening entry is learned from adversarial exploration and has no mathematical non-loss guarantee. The other six entries hold offline win/draw/non-loss proofs.','A non-loss certificate does not mean a draw is proved, nor that a fastest win is known.','The independent 256-position low-budget control still contains one losing blunder; those arbitrary starts remain outside the user-confirmed empty-board goal.','Historical random-prefix defeats and unsuccessful exploration trials remain archived without deletion.']}
for p in (run/'evaluation.json',root/'web/models/garry-zero-evaluation.json'):p.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
history=json.loads((root/'web/models/garry-training.json').read_text());history['active_model']={'version':'3.2.0','weights_revision':report['policy_weights_revision'],'search_revision':report['search_revision'],'sha256':report['installed_model_sha256'],'architecture_changed':False};history['certified_search']={k:report[k] for k in ('software_version','search_revision','search_memory_entries','zero_defeats_verified','scope','source_model_sha256','installed_model_sha256','installed_wasm_sha256')};(root/'web/models/garry-training.json').write_text(json.dumps(history,indent=2)+'\n',encoding='utf-8')
doc=f"""# Garry 3.2.0 — zéro défaite sur les duels demandés

**Le contrôle depuis le plateau vide est réussi, dans les deux camps, contre la version précédente 3.1.0 figée : une victoire, une nulle, aucune défaite.** Garry gagne également les deux duels face aux IA 1.0.0 originales à leur niveau 10.

Ce périmètre a été confirmé par l’utilisateur avant la validation finale : « Duels depuis le plateau vide contre l’ancienne version, dans les deux camps ». Il ne s’agit pas d’une affirmation d’invincibilité universelle.

## Comparaison par le circuit réel

Le moteur 3.1.0 utilise son binaire et ses poids archivés, sans bénéficier de la nouvelle recherche ni de sa mémoire. Les limites des deux Garry sont identiques : 2 000 ms, 200 millions de nœuds au maximum et une profondeur maximale de 42 demi-coups. La limite de temps reste active. L’IA 1.0 utilise son circuit complet original de niveau 10 : 100 000 nœuds et 30 ms. Aucun départ aléatoire ni préremplissage n’est imposé.

| Adversaire | Camp de Garry 3.2.0 | Résultat |
|---|---|---|
| Garry 3.1.0 figé | Premier joueur | Nulle |
| Garry 3.1.0 figé | Deuxième joueur | Victoire |
| IA 1.0.0 originale | Premier joueur | Victoire |
| IA 1.0.0 originale | Deuxième joueur | Victoire |

Sur le même contrôle, Garry 3.1.0 contre sa propre version obtient deux nulles ; le nouveau Garry transforme la partie en second en victoire. Ce contrôle au budget réel n’avait donc déjà aucune défaite pour la référence : le progrès observé est une victoire supplémentaire, et la confirmation du zéro défaite demandé. Les anciens résultats avec d’autres budgets et des ouvertures imposées ne sont pas mélangés avec ce résultat.

Un contrôle préalable du prototype, avec les mêmes limites réelles et deux passages dans chaque camp contre 3.1.0, donne deux victoires et deux nulles. Ces répétitions servent à vérifier la stabilité ; elles ne représentent pas quatre stratégies d’ouverture indépendantes.

## Ce qui change

La recherche peut maintenant établir une preuve exacte de victoire, de nulle ou de défaite, et conserver une action dont elle a prouvé qu’elle ne perd pas lorsqu’elle n’a pas encore résolu toute la position. Les estimations heuristiques restent séparées de cette table de preuves. L’analyse compare aussi les positions symétriques pour réutiliser les calculs.

L’exploration de réponses au moteur précédent a produit un petit répertoire de **sept positions**, embarqué dans le même fichier de modèle. Une entrée contient une réponse d’ouverture choisie par expérience ; elle n’est jamais affichée comme une preuve. Les six autres contiennent des coups vérifiés hors ligne : victoire, nulle ou non-défaite. Une preuve de non-défaite n’est pas présentée comme une preuve de nulle ni comme une distance de mat connue.

Les poids neuronaux, les compteurs d’apprentissage, les six jeux et les dimensions 1 912 → 48 → 48 → 818 restent identiques à 3.1.0. Le modèle possède toujours 134 290 paramètres neuronaux et de valeur, auxquels s’ajoutent les sept entrées discrètes de recherche. **3.2.0 est une évolution compatible du code et du stockage de connaissances**, sans changement des dimensions du réseau ; ce numéro n’est pas calculé à partir des performances.

Les sauvegardes du navigateur datant de 3.1.0 reçoivent le nouveau répertoire en conservant leurs poids personnels et leurs compteurs. L’export reste un seul fichier Garry. Les niveaux de 0 à 10 restent disponibles ; la mémoire d’ouverture et les preuves renforcent la décision maximale, tandis que l’analyse complète des actions est conservée pour les autres niveaux.

## Vérifications et limites

- **59 tests Python et 28 tests JavaScript réussis**, soit 87 tests.
- Résultats et coups du nouveau solveur conformes à un oracle indépendant sur **200 fins de partie**, y compris victoires, nulles et défaites.
- Les six jeux sont contrôlés dans le navigateur aux niveaux 0 et 10, avec entraînement, export, rechargement et un seul modèle dans IndexedDB.
- Une sauvegarde 3.1.0 avec des poids personnels modifiés est migrée dans un navigateur réel : poids et compteurs conservés, sept entrées présentes, décisions du worker vérifiées.
- Le binaire installé est identique à une recompilation de ses sources avec le compilateur épinglé.

Sur **256 positions inédites de milieu et fin de partie**, au budget réduit de 200 000 nœuds et sans le nouveau répertoire d’ouverture, les erreurs de résultat passent de 7 à 3, et les coups qui transforment une position sauvable en défaite passent de 4 à 1. Il reste donc une erreur perdante sur ce contrôle distinct : aucune promesse de zéro défaite n’est faite pour des positions arbitraires ou tous les adversaires.

Les défaites des anciens départs imposés restent dans leurs rapports. Les essais d’ouverture infructueux sont également archivés. La victoire au Puissance 4 dépend du camp et des réponses adverses ; la source primaire [Connect 4 Solver](https://connect4.gamesolver.org/en/) explique la stratégie gagnante théorique du premier joueur. La recherche exacte s’appuie sur les principes exposés dans le [tutoriel de résolution](https://blog.gamesolver.org/), avec une implémentation locale dans Garry.

## Reproduire

Depuis la racine du dépôt :

```powershell
node examples/benchmark_garry_empty_board.mjs --output training-runs/garry-zero-20261017/recheck.json --repetitions 1 --opponents previous,legacy1 --compare
python -m unittest discover -s tests
node --test tests/garry.test.mjs tests/web.test.mjs tests/levels.test.mjs tests/repertoire.test.mjs tests/certified.test.mjs
```

Les traces complètes de tous les coups figurent dans `training-runs/garry-zero-20261017/public-api-duels.json`. Les sources et poids précédents sont conservés sous `versions/3.1.0/`, avec empreintes vérifiées. Les anciens rapports ne sont pas écrasés.

Poids installés : `{report['installed_model_sha256']}`.

Moteur installé : `{report['installed_wasm_sha256']}`.
"""
(root/'docs/GARRY-ZERO-DEFAITE.md').write_text(doc,encoding='utf-8')
out=Path(r'C:\Users\gabor\code\logic-lab\outputs');(out/'Garry-zero-defaite.md').write_text(doc,encoding='utf-8');(out/'Garry-zero-defaite-resultats.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
readme=(root/'README.md').read_text();readme=readme.replace('# Logic Lab — Garry 3.1.0','# Logic Lab — Garry 3.2.0',1)
at=readme.index('## Un répertoire varié pour apprendre')
intro="""## Zéro défaite depuis le plateau vide

Garry **3.2.0** passe les duels demandés contre la **3.1.0 figée**, dans les deux camps, aux réglages de niveau 10 : **une victoire, une nulle, zéro défaite**. Il gagne aussi les deux duels contre la 1.0.0 originale. Les répétitions et limites sont détaillées dans [le rapport zéro défaite](docs/GARRY-ZERO-DEFAITE.md) ; ce résultat ne promet pas l’invincibilité contre toutes les stratégies ou depuis toutes les positions.

La nouvelle recherche distingue les issues prouvées des estimations, et les coups dont la non-défaite est établie. Sept entrées d’ouverture voyagent dans le fichier du modèle, dont une réponse choisie par expérience et six coups certifiés. Les poids et dimensions du réseau sont préservés. **3.2.0 correspond à ces nouvelles fonctions compatibles**, sans changement d’architecture neuronale.

"""
readme=readme[:at]+intro+readme[at:];readme=readme.replace('## Un répertoire varié pour apprendre','## Historique : le répertoire de la 3.1.0',1).replace('la version logicielle reste **3.1.0**','la version logicielle de ce cycle était **3.1.0**',1).replace('Le zéro défaite n’est pas atteint.','Sur ces départs imposés historiques, le zéro défaite n’était pas atteint.',1).replace('version **3.1.0** pour les six modes','version **3.2.0** pour les six modes')
readme=readme.replace('`versions/3.0.0/` conserve','`versions/3.1.0/` conserve le moteur et les poids précédant la recherche certifiée. `versions/3.0.0/` conserve',1)
(root/'README.md').write_text(readme,encoding='utf-8')
paths=['web/models/garry.json','web/connect4-search.wasm','search/connect4-search.ts','web/connect4-runtime.js','logic_arena/connect4_wasm.py','web/search-memory.js','logic_arena/search_memory.py','web/engine.js','logic_arena/general.py','web/planner.js','logic_arena/planner.py','web/app.js','examples/benchmark_garry_empty_board.mjs','web/agents.json','training-runs/garry-zero-20261017/public-api-duels.json']
(run/'manifest.json').write_text(json.dumps({'version':'3.2.0','sha256':{p:sha(root/p) for p in paths}},indent=2)+'\n',encoding='utf-8')
for p in work.glob('*.cjs'):shutil.copyfile(p,run/p.name)
shutil.copyfile(Path(__file__),run/'document-final.py')
print(json.dumps({'objective_verified':True,'public_api_after':{k:v['after'] for k,v in trials['opponents'].items()},'tests':87,'outputs':str(out/'Garry-zero-defaite.md')}))
