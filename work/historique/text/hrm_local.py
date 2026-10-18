"""Offline HRM checkpoint loader and native symbolic/continuous test paths."""
from pathlib import Path
import hashlib,json
import torch,yaml
from models.hrm.hrm_act_v1 import HierarchicalReasoningModel_ACTV1,HierarchicalReasoningModel_ACTV1InnerCarry
ROOT=Path(__file__).resolve().parent

def load_local(device='cpu'):
    manifest=json.loads((ROOT/'fork_manifest.json').read_text(encoding='utf-8'))
    p=Path(manifest['checkpoint']['path'])
    if hashlib.sha256(p.read_bytes()).hexdigest()!=manifest['checkpoint']['sha256']:raise ValueError('Checkpoint fingerprint changed')
    config=yaml.safe_load(Path(manifest['checkpoint']['config_path']).read_text(encoding='utf-8'))['arch']
    config={k:v for k,v in config.items() if k not in ('name','loss')}
    config.update(batch_size=1,seq_len=81,vocab_size=11,num_puzzle_identifiers=1,forward_dtype='bfloat16' if device=='cuda' else 'float32')
    state=torch.load(p,map_location='cpu',weights_only=True)
    prefix='_orig_mod.model.'
    if not all(k.startswith(prefix) for k in state):raise ValueError('Unexpected checkpoint layout')
    model=HierarchicalReasoningModel_ACTV1(config)
    model.load_state_dict({k[len(prefix):]:v for k,v in state.items()},strict=True)
    return model.to(device).eval(),manifest

def batch_grid(grid,device='cpu'):
    grid=''.join(grid.split()).replace('.','0')
    if len(grid)!=81 or any(c not in '0123456789' for c in grid):raise ValueError('Expected 81 sudoku cells')
    return {'inputs':torch.tensor([[int(c)+1 for c in grid]],device=device,dtype=torch.int32),'puzzle_identifiers':torch.zeros(1,device=device,dtype=torch.int32)}

def initial_continuous(core, embeddings):
    shape=embeddings.shape
    return HierarchicalReasoningModel_ACTV1InnerCarry(core.H_init.view(1,1,-1).expand(shape).clone(),core.L_init.view(1,1,-1).expand(shape).clone())

def valid_sudoku(values,givens):
    if len(values)!=81 or any(type(x)is not int or not 1<=x<=9 for x in values):return False
    if any(g and int(g)!=v for g,v in zip(givens,values) if g!='0'):return False
    groups=[values[i*9:i*9+9] for i in range(9)]+[values[i::9] for i in range(9)]+[[values[(r+a)*9+c+b] for a in range(3) for b in range(3)] for r in (0,3,6) for c in (0,3,6)]
    return all(set(group)==set(range(1,10)) for group in groups)
