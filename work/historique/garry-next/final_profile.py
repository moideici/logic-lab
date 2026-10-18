from pathlib import Path
ROOT=Path(r'C:\Users\gabor\code\playi');OUT=Path(__file__).parent/'final-profile'
def edit(p,fn):
    f=OUT/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(fn((ROOT/p).read_text(encoding='utf-8')),encoding='utf-8',newline='\n')
edit('web/planner.js',lambda s:s.replace('maxDepth:20,positionHead:', 'maxDepth:level===10?42:20,positionHead:'))
edit('logic_arena/planner.py',lambda s:s.replace('max_depth=20,position_head=', 'max_depth=42 if level==10 else 20,position_head='))
edit('tests/test_deep.py',lambda s:s.replace("self.assertLessEqual(d.info['depth'],20)","self.assertLessEqual(d.info['depth'],42)"))
edit('examples/probe_garry_depth.mjs',lambda s:s.replace('maxDepth:20,positionHead:', 'maxDepth:42,positionHead:'))
edit('examples/benchmark_garry.mjs',lambda s:s.replace('maxDepth:20,positionHead:', 'maxDepth:42,positionHead:'))
edit('examples/compare_garry_checkpoints.mjs',lambda s:s.replace('maxDepth:20,positionHead:', 'maxDepth:42,positionHead:'))
# Keep the fixed-20-horizon value-head validation reproducible; those scripts
# deliberately do not silently inherit changes to the live playing profile.
