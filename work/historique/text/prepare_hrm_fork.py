"""Acquire official weights only; do not execute upstream training scripts."""
from pathlib import Path
import hashlib,json,subprocess
from huggingface_hub import hf_hub_download

ROOT=Path(r'C:\Users\gabor\code\latent-reasoner-hrm')
REPO='sapientinc/HRM-checkpoint-sudoku-extreme'
REVISION='fbb4eb883766c31c8e863426460ebaa0ceb1a5f2'
EXPECTED='0befd4a9f33a090d46df00728160ddbd69b81bcfdb8064ccfde0c867dd3836b9'
paths={}
for name in ('checkpoint','all_config.yaml'):
    paths[name]=hf_hub_download(REPO,name,revision=REVISION,cache_dir=ROOT/'weight_cache')
actual=hashlib.sha256(Path(paths['checkpoint']).read_bytes()).hexdigest()
if actual!=EXPECTED:raise ValueError('Unexpected checkpoint hash')
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
manifest={'version':'0.1.0','architecture':'HRM-symbolic','upstream':'https://github.com/sapientinc/HRM','upstream_revision':revision,'code_license':'Apache-2.0','checkpoint':{'repo':REPO,'revision':REVISION,'sha256':actual,'path':paths['checkpoint'],'config_path':paths['all_config.yaml']},'scope':'Sudoku 9x9 initial experiment, not a general assistant','input_bridge_trained':False,'pretrained_weights_modified':False}
(ROOT/'fork_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=False))
