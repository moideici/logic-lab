from huggingface_hub import HfApi
import json
api=HfApi();out={}
for repo,kind in [('Qwen/Qwen3-0.6B','model'),('wikimedia/wikipedia','dataset'),('OpenAssistant/oasst2','dataset')]:
 info=api.repo_info(repo,repo_type=kind,files_metadata=True);files=[{'name':s.rfilename,'bytes':s.size} for s in info.siblings if (kind=='model' and s.rfilename.endswith(('.safetensors','.json','.txt','.model','.jinja'))) or (repo.endswith('wikipedia') and s.rfilename.startswith('20231101.fr/')) or (repo.endswith('oasst2') and s.rfilename.endswith('.parquet'))];out[repo]={'revision':info.sha,'files':files}
print(json.dumps(out,indent=2))
