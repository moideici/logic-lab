from pathlib import Path
ROOT=Path(__file__).parent
def edit(file,old,new):
 p=ROOT/file;s=p.read_text(encoding='utf-8');assert old in s,(file,old[:60]);p.write_text(s.replace(old,new),encoding='utf-8')
edit('tests/web.test.mjs','../web/models/${','../versions/1.0.0/web/models/${')
edit('examples/benchmark_express.mjs','Game,Network,NAMES','Game,GarryModel,NAMES')
edit('examples/benchmark_express.mjs',"for(const name of Object.keys(NAMES)){", "const general=new GarryModel(JSON.parse(fs.readFileSync(new URL('../web/models/garry.json',import.meta.url))));\nfor(const name of Object.keys(NAMES)){")
edit('examples/benchmark_express.mjs',"new Network(JSON.parse(fs.readFileSync(new URL(`../web/models/${name}.json`,import.meta.url))))","general.forGame(name)")
edit('examples/benchmark_connect4.mjs',"'../web/models/connect4.json'","'../versions/1.0.0/web/models/connect4.json'")
edit('examples/bootstrap_models.py','directory=Path(__file__).resolve().parents[1]/"web"/"models"','directory=Path(__file__).resolve().parents[1]/"training-data"/"legacy-bootstrap"')
edit('examples/bootstrap_models.py',"print('saved six models with one shared core',flush=True)","from logic_arena.general import GarryPolicy\n    GarryPolicy.fuse(models).save(Path(__file__).resolve().parents[1]/'web'/'models'/'garry.json')\n    print('saved Garry as one general model',flush=True)")
edit('logic_arena/harness.py','"agent_version": AGENT_VERSION, "games":', '"agent_version": AGENT_VERSION, "model": {"name":"garry","version":AGENT_VERSION,"format":"garry-mlp-v1","architecture":[1912,48,48,818],"files":1}, "games":')
edit('web/app.js','agent_version:AGENT_VERSION,styles:',"agent_version:AGENT_VERSION,model:{name:'garry',version:AGENT_VERSION,format:'garry-mlp-v1',architecture:[1912,48,48,818],files:1},styles:")
