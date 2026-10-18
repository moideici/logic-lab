import hashlib
import json
from pathlib import Path
import sys

ROOT=Path.cwd();sys.path.insert(0,str(ROOT))
from logic_arena.general import GarryPolicy
from examples.train_garry_guarded import protected_weights_equal
from examples.train_garry_curriculum import atomic_json,compare_game

run=ROOT/'training-runs'/'garry-guarded-20261016-211530'
report=json.loads((run/'report.json').read_text(encoding='utf-8'))
hybrid=json.loads((run/'hybrid-evaluation.json').read_text(encoding='utf-8'))
active=ROOT/'web'/'models'/'garry.json'
assert hashlib.sha256(active.read_bytes()).hexdigest()==report['source_sha256'],'Le modèle actif a changé'
before=GarryPolicy.load(active);candidate=GarryPolicy.load(run/'best.json')
assert protected_weights_equal(before,candidate,'connect4'),'Poids protégés différents'
assert report['after']['wins']>report['before']['wins'] and report['after']['losses']<report['before']['losses']
assert hybrid.get('no_observed_regression') is True,'Régression du système hybride'
candidate.save(active)
metadata={'name':'garry','software_version':'2.0.0','weights_revision':'20261016-c4-guarded-01',
          'architecture_changed':False,'source_sha256':report['source_sha256'],'trained_sha256':hashlib.sha256(active.read_bytes()).hexdigest(),
          'training_run':run.name,'training_examples':candidate.steps-before.steps,'game':'connect4','training_unique_positions':4096,
          'other_games_weights_preserved':True,'checkpoint_epoch':report['best_epoch'],'policy_only_evaluation':{'before':report['before'],'after':report['after']},
          'hybrid_evaluation':{'episodes':hybrid['episodes'],'before':hybrid['before'],'after':hybrid['after'],
                               'current_node_budget':hybrid['current_node_budget'],'reference_node_budget':hybrid['reference_node_budget']},
          'zero_defeat_target_met':False,'active_model_replaced':True,
          'note':'Le gain constaté porte sur le réseau seul contre un adversaire aléatoire. Le contrôle hybride ne montre aucun gain de résultat. Les cinq autres modes ont exactement les mêmes poids effectifs.'}
atomic_json(ROOT/'web'/'models'/'garry-training.json',metadata)
atomic_json(run/'installation.json',metadata)
# Les essais généraux ne sont pas promus ; corriger le bilan des progrès
# pour distinguer un gain de score d'un simple dépassement de limite.
for trial in ('garry-20261016-210424','garry-20261016-210905'):
    path=ROOT/'training-runs'/trial/'report.json';old=json.loads(path.read_text(encoding='utf-8'))
    audit={g:compare_game(results['before'],results['after']) for g,results in old['test_results'].items()}
    atomic_json(path.with_name('selection-audit.json'),{'regressions':[g for g,a in audit.items() if a['regression']],
                'improvements':[g for g,a in audit.items() if a['improvement']],'active_model_replaced':False,
                'note':'Un dépassement de limite ne compte pas comme un progrès. Une baisse du score de progression est contrôlée même si aucune partie n’est résolue.'})
print(json.dumps(metadata,indent=2))
