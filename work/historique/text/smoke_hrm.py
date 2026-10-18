"""Technical smoke check on public example grids; not a benchmark score."""
from pathlib import Path
import json,time,torch
from hrm_local import load_local,batch_grid,initial_continuous,valid_sudoku
torch.set_num_threads(2)
model,manifest=load_local('cpu');results=[]
grids=['530070000600195000098000060800060003400803001700020006060000280000419005000080079','034678912672195348198342567859761423426853791713924856961537284287419635345286179']
for grid in grids:
    start=time.perf_counter();batch=batch_grid(grid)
    with torch.inference_mode():
        embeddings=model.inner._input_embeddings(batch['inputs'],batch['puzzle_identifiers']);carry=initial_continuous(model.inner,embeddings)
        for _ in range(model.config.halt_max_steps):carry,logits,_=model.inner.forward_embeddings(carry,embeddings)
        values=(logits.argmax(-1)[0]-1).tolist()
    results.append({'input':grid,'prediction':values,'valid_solution_preserving_givens':valid_sudoku(values,grid),'seconds':round(time.perf_counter()-start,3),'latent_shape':list(embeddings.shape),'native_steps':model.config.halt_max_steps})
out={'kind':'technical_smoke_not_benchmark','device':'cpu','checkpoint_sha256':manifest['checkpoint']['sha256'],'parameters':sum(p.numel() for p in model.parameters()),'input_bridge_trained':False,'cases':results}
path=Path(__file__).resolve().parent/'local_results/native-smoke.json';path.parent.mkdir(exist_ok=True);path.write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out))
