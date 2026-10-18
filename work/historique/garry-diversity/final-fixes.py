from pathlib import Path
root=Path(r'C:\Users\gabor\code\playi');out=Path(r'C:\Users\gabor\code\logic-lab\work\garry-diversity\final-fixes')
def edit(p,fn):
    f=out/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(fn((root/p).read_text(encoding='utf-8')),encoding='utf-8',newline='\n')
edit('tests/test_levels.py',lambda s:s.replace('test_value_is_antisymmetric_python_wasm_and_policy_weights_are_preserved','test_value_is_antisymmetric_python_wasm_and_value_head_is_preserved').replace("old=GarryPolicy.load(ROOT/'versions/2.0.0/garry.json')\n        for key in ('w1','b1','w2','b2'):np.testing.assert_array_equal(getattr(old,key),getattr(self.model,key))", "old=GarryPolicy.load(ROOT/'versions/3.0.0/garry.json')\n        self.assertEqual(old.position_head,self.model.position_head)\n        np.testing.assert_array_equal(old.b1,self.model.b1)"))
for p in ('examples/train_garry_curriculum.py','examples/train_garry_guarded.py','examples/fuse_garry.py','examples/benchmark_garry.mjs'):
    edit(p,lambda s:s.replace("'software_version':'3.0.0'","'software_version':'3.1.0'").replace("version:'3.0.0'","version:'3.1.0'").replace("'version':'3.0.0'","'version':'3.1.0'"))
