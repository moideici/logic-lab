from pathlib import Path
import json,hashlib,os
from datetime import datetime,timezone

root=Path(r'C:\Users\gabor\code\playi')
page=root/'web/index.html'
text=page.read_text(encoding='utf-8')
link='<a id="logiclab-input-link" class="nav" href="http://127.0.0.1:8766/" title="LogicLabInput · discuter en français"><span aria-hidden="true">Aa</span><small>Input</small></a>'
if 'id="logiclab-input-link"' not in text:
    text=text.replace('</button></nav>','</button>'+link+'</nav>',1)
    if link not in text:raise RuntimeError('Navigation attendue absente')
    page.write_text(text,encoding='utf-8')
css=root/'web/style.css'
style=css.read_text(encoding='utf-8')
rule='\n/* Shared navigation to the separate French text project. */\na.nav:hover,a.nav:focus-visible{background:#2e5144;color:var(--green)}\n'
if rule not in style:css.write_text(style+rule,encoding='utf-8')

job=root/'training/continuous/2c34213841c64bc29b19a24651403b5b'
status=json.loads((job/'status.json').read_text(encoding='utf-8'))
if status['state']!='completed':raise RuntimeError('Entraînement non terminé')
model=root/'web/models/garry.json'
raw=model.read_bytes();old_hash=hashlib.sha256(raw).hexdigest()
data=json.loads(raw)
audit_path=job/'version-normalization.json'
if data['version']=='6.0.0':
    if old_hash!=status['model_sha256']:raise RuntimeError('Modèle modifié depuis la fin de la session')
    frozen=(job/'latest-accepted.json').read_bytes()
    if hashlib.sha256(frozen).hexdigest()!=old_hash:raise RuntimeError('Point de référence final différent du modèle actif')
    # Change the root version label only, keeping every other byte unchanged.
    needle=b'"version":"6.0.0"'
    if raw.count(needle)!=1:raise RuntimeError('Étiquette non unique')
    normalized=raw.replace(needle,b'"version":"0.6.0"',1)
    renamed=json.loads(normalized)
    renamed['version']='6.0.0'
    if renamed!=data:raise RuntimeError('Modification autre que le numéro de version')
    if model.read_bytes()!=raw:raise RuntimeError('Écriture concurrente détectée')
    temporary=model.with_suffix('.version.tmp');temporary.write_bytes(normalized);os.replace(temporary,model)
    new_hash=hashlib.sha256(normalized).hexdigest()
    audit={'operation':'version_alias_normalization','from_version':'6.0.0','to_version':'0.6.0','training_model_sha256':old_hash,'active_model_sha256':new_hash,'unchanged':'all bytes except the root version string','frozen_reference':'latest-accepted.json','normalized_at':datetime.now(timezone.utc).isoformat()}
    audit_path.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    # Preserve the training hash and its final frozen model; record the deployment separately.
    status.update(active_model_version='0.6.0',active_model_sha256=new_hash,version_normalization='version-normalization.json')
    temporary=job/'status.version.tmp';temporary.write_text(json.dumps(status,ensure_ascii=False,separators=(',',':')),encoding='utf-8');os.replace(temporary,job/'status.json')
elif data['version']!='0.6.0':raise RuntimeError('Version inattendue')
print(json.dumps({'input_link':'http://127.0.0.1:8766/','active_version':json.loads(model.read_bytes())['version'],'audit':str(audit_path)}))
