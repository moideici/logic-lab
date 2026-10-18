from pathlib import Path
import shutil
R=Path(r'C:\Users\gabor\code\text-comprehension');S=Path(__file__).parent
for f in ('build_benchmark.py','experiment.py','PROTOCOL.md','README.md','requirements.txt','.gitignore'):shutil.copyfile(S/f,R/f)
(R/'tests').mkdir(exist_ok=True);shutil.copyfile(S/'test_benchmark.py',R/'tests/test_benchmark.py')
print('Separate French text project installed')
