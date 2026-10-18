from huggingface_hub import HfApi
info=HfApi().model_info('almanach/camembert-base')
print(info.sha)
print([f.rfilename for f in info.siblings if f.rfilename.endswith(('.safetensors','.json','.model'))])
