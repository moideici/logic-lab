from pathlib import Path
ROOT=Path(r'C:\Users\gabor\code\playi');OUT=Path(__file__).parent/'optimized'
def edit(p,fn):
    f=OUT/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(fn((ROOT/p).read_text(encoding='utf-8')),encoding='utf-8',newline='\n')
edit('search/connect4-search.ts',lambda s:s.replace('''   nextScores[c]=-visit(position^mask,mask|move,depth-1,-WIN,WIN,1);''', '''   const prior=rootScores[c],low=max(-WIN,prior-64),high=min(WIN,prior+64);
   let value=-visit(position^mask,mask|move,depth-1,-high,-low,1);
   if(!expired&&(value<=low||value>=high))value=-visit(position^mask,mask|move,depth-1,-WIN,WIN,1);
   nextScores[c]=value;'''))
edit('examples/benchmark_garry_value.mjs',lambda s:s.replace("'training-runs/garry-value-20261016/head.json'", "process.argv[5]??'training-runs/garry-value-20261016/head.json'").replace('seed:7300000','seed:Number(process.argv[4]??7300000)'))
