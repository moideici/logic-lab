"""Copy the entire project state into this chat; retain all originals."""
from pathlib import Path
import os,json,hashlib,shutil,time
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
JOBS=[(Path(r'C:\Users\gabor\code\playi'),ROOT/'projets/garry'),(Path(r'C:\Users\gabor\code\text-comprehension'),ROOT/'projets/input'),(Path(r'C:\Users\gabor\code\latent-reasoner-hrm'),ROOT/'recherche/hrm'),(Path(r'C:\Users\gabor\code\latent-reasoner'),ROOT/'recherche/trm')]
BUFFER=8*1024*1024
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while data:=f.read(BUFFER):h.update(data)
    return h.hexdigest()
def main():
    manifest={'date_utc':datetime.now(timezone.utc).isoformat(),'mode':'complete_copy_originals_retained','projects':[],'relocations':[],'verified':False}
    report=ROOT/'REGROUPEMENT.json';total=0
    def emit():report.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    for source,target in JOBS:
        if target.exists():raise RuntimeError(f'Destination déjà présente : {target}')
        target.mkdir(parents=True)
        project={'source':str(source),'destination':str(target),'files':[],'bytes':0,'verified':False};manifest['projects'].append(project);emit()
        for base,dirs,files in os.walk(source):
            relative=Path(base).relative_to(source);(target/relative).mkdir(exist_ok=True)
            for name in files:
                src=Path(base)/name;dst=target/relative/name
                before=src.stat();sha=hashlib.sha256()
                with src.open('rb') as f,dst.open('wb') as out:
                    while data:=f.read(BUFFER):out.write(data);sha.update(data)
                shutil.copystat(src,dst,follow_symlinks=True)
                expected=sha.hexdigest()
                if digest(dst)!=expected:raise RuntimeError(f'Copie incorrecte : {dst}')
                after=src.stat();size=dst.stat().st_size
                project['files'].append({'path':str(relative/name),'bytes':size,'sha256':expected,'source_symlink_materialized':src.is_symlink(),'source_changed_during_copy':(before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns)})
                project['bytes']+=size;total+=size
        project['verified']=True;emit();print(json.dumps({'copied':str(target),'files':len(project['files']),'gb':round(project['bytes']/1e9,2)},ensure_ascii=False),flush=True)
    mappings={str(src):str(dst) for src,dst in JOBS}
    def relocate(value):
        if isinstance(value,str):
            for old,new in mappings.items():
                if value==old or value.startswith(old+'\\'):return new+value[len(old):]
                if value==old.replace('\\','/') or value.startswith(old.replace('\\','/')+'/'):return new.replace('\\','/')+value[len(old):]
            return value
        if isinstance(value,list):return [relocate(x) for x in value]
        if isinstance(value,dict):return {k:relocate(v) for k,v in value.items()}
        return value
    # Rebind runtime manifests only; preserve historical experiment records.
    inp=ROOT/'projets/input'
    configs=[inp/'models/chat_base.json',inp/'models/chat/active.json',inp/'corpus/manifest.json',ROOT/'recherche/hrm/fork_manifest.json']+list((inp/'models').rglob('adapter_config.json'))
    for p in configs:
        if not p.exists():continue
        value=json.loads(p.read_text(encoding='utf-8-sig'));updated=relocate(value)
        if updated!=value:
            old_hash=digest(p);p.write_text(json.dumps(updated,ensure_ascii=False,indent=2),encoding='utf-8')
            manifest['relocations'].append({'path':str(p.relative_to(ROOT)),'before_sha256':old_hash,'after_sha256':digest(p),'reason':'local_runtime_paths_only'})
    manifest.update(verified=True,total_bytes=total,total_files=sum(len(p['files']) for p in manifest['projects']),finished_utc=datetime.now(timezone.utc).isoformat());emit()
    print(json.dumps({'verified':True,'files':manifest['total_files'],'gb':round(total/1e9,2),'relocated_configs':len(manifest['relocations'])}),flush=True)
if __name__=='__main__':main()
