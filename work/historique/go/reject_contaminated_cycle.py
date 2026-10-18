from pathlib import Path
import json,hashlib,os,time
from datetime import datetime,timezone
root=Path(r'C:\Users\gabor\code\playi');job=root/'training/continuous/19159dcbbae2412c876e1c729a3b606f';p=job/'status.json';state=json.loads(p.read_text(encoding='utf-8'))
if state['state']!='stopped':raise RuntimeError('Le processus doit être arrêté proprement')
for folder in job.parent.iterdir():
 status=folder/'status.json'
 if folder!=job and status.is_file() and json.loads(status.read_text(encoding='utf-8')).get('state')=='running' and time.time()-status.stat().st_mtime<60:raise RuntimeError('Autre entraînement actif')
model=root/'web/models/garry.json';raw=model.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
if sha(raw)!=state['model_sha256']:raise RuntimeError('Modèle actif changé ailleurs')
initial=(job/'initial.json').read_bytes()
tmp=model.with_suffix('.restore.tmp');tmp.write_bytes(initial);os.replace(tmp,model)
audit=json.loads(Path(r'C:\Users\gabor\code\logic-lab\outputs\audit-splits-continuous.json').read_text(encoding='utf-8'))
audit.update(operation='reject_cross_session_overlap_and_restore_initial',rejected_model_sha256=sha(raw),restored_model_sha256=sha(initial),at=datetime.now(timezone.utc).isoformat())
(job/'cross-session-audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
state.update(assessment_valid=False,superseded_reason='cross_session_reserved_states_reused',active_model_restored_from='initial.json',active_model_sha256=sha(initial),split_audit='cross-session-audit.json')
p.write_text(json.dumps(state,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
report=job/'report.json'
if report.is_file():
 d=json.loads(report.read_text(encoding='utf-8'));d.update(assessment_valid=False,superseded_reason='cross_session_reserved_states_reused');report.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print(json.dumps({'state':'rejected_and_restored','version':json.loads(initial)['version'],'restored_model_sha256':sha(initial)}))
