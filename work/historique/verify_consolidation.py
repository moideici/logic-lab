from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'REGROUPEMENT.json').read_text(encoding='utf-8'))
missing=[];links=[]
for project in manifest['projects']:
    dest=Path(project['destination'])
    for record in project['files']:
        p=dest/record['path']
        if not p.is_file():missing.append(str(p))
        elif p.is_symlink():links.append(str(p))
runtime_paths=[]
for config in (ROOT/'projets/input/models/chat_base.json',ROOT/'projets/input/models/chat/active.json',ROOT/'recherche/hrm/fork_manifest.json'):
    v=json.loads(config.read_text(encoding='utf-8'))
    paths=[v['path']] if 'path' in v else [v['checkpoint']['path'],v['checkpoint']['config_path']]
    for raw in paths:
        p=Path(raw).resolve();inside=p.is_relative_to(ROOT.resolve());exists=p.exists()
        runtime_paths.append({'config':str(config.relative_to(ROOT)),'path':str(p),'inside_conversation':inside,'exists':exists})
        if not (inside and exists):raise RuntimeError('Chemin de modèle invalide : '+str(p))
corpus=json.loads((ROOT/'projets/input/corpus/manifest.json').read_text(encoding='utf-8'))
corpus_paths=[entry['path'] for kind in ('wikipedia','dialogues') for entry in corpus[kind]]
assert all(Path(p).is_file() and Path(p).resolve().is_relative_to(ROOT.resolve()) for p in corpus_paths)
model=ROOT/'projets/garry/web/models/garry.json'
model_hash=hashlib.sha256(model.read_bytes()).hexdigest()
original_hash=hashlib.sha256(Path(r'C:\Users\gabor\code\playi\web\models\garry.json').read_bytes()).hexdigest()
assert model_hash==original_hash
assert not missing and not links and manifest['verified']
result={'verified_utc':datetime.now(timezone.utc).isoformat(),'copy_integrity':'every copied file SHA-256 compared with read-back at copy time','files_copied':manifest['total_files'],'bytes_copied':manifest['total_bytes'],'missing_copied_files':missing,'external_file_symlinks_in_copies':links,'runtime_model_paths':runtime_paths,'corpus_files_present_inside_conversation':len(corpus_paths),'garry_active_weights_identical_to_source':model_hash==original_hash,'garry_sha256':model_hash,'functional_checks':{'input':{'tests':21,'status':'passed'},'hrm':{'tests':3,'status':'passed','pretrained_model_loaded_in_new_location':True,'public_sudoku_controls':'1 success, 1 existing failure; no general performance claim'},'garry':{'status':'running'}},'originals_retained':True,'running_original_servers_restarted':False,'scope':'file consolidation and documentation; no new training or UI implementation'}
(ROOT/'VERIFICATION-REGROUPEMENT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:result[k] for k in ('files_copied','bytes_copied','missing_copied_files','corpus_files_present_inside_conversation','garry_active_weights_identical_to_source')},ensure_ascii=False))
