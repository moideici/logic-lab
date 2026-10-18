from pathlib import Path
ROOT = Path(__file__).parent
def change(file, old, new):
    path=ROOT/file
    text=path.read_text(encoding='utf-8')
    assert text.count(old)==1,(file,old[:70],text.count(old))
    path.write_text(text.replace(old,new),encoding='utf-8')

change('web/fast-search.js', "import {actionIndex} from './engine.js';", "import {actionIndex} from './engine.js';\nimport {connectDecision} from './connect4-runtime.js';")
change('web/fast-search.js','export function connectSearch(o,legal,logits,budget){', 'export function connectSearch(o,legal,logits,budget,options={}){\n if(Number.isInteger(budget.limit))return connectDecision(o,legal,logits,budget,options);\n // Compatibilité des intégrations historiques qui fournissent seulement tick().\n return connectSearchLegacy(o,legal,logits,budget);\n}\nexport function connectSearchLegacy(o,legal,logits,budget){')
change('web/planner.js', "import {candidates,actionIndex,clone}", "import {CONNECT_LIMITS,CONNECT_TIMES} from './connect4-runtime.js';\nimport {candidates,actionIndex,clone}")
change('web/planner.js', "const result=solver(o,legal,logits,budget);", "if(o.game==='connect4'){budget.limit=CONNECT_LIMITS[level-1];budget.tick=function(){if(this.nodes++>=this.limit||performance.now()-began>=CONNECT_TIMES[level-1])throw Error('budget');};}\n  const result=solver(o,legal,logits,budget,o.game==='connect4'?{timeMs:CONNECT_TIMES[level-1]}:{});")
change('logic_arena/planner.py','from .connect4 import search\n        action,info=search(obs,legal,Budget(LIMITS[level-1],budget_ms),logits=logits)', 'from .connect4_wasm import search, CONNECT_LIMITS, CONNECT_TIMES\n        search_ms=CONNECT_TIMES[level-1] if time_ms is None else time_ms\n        action,info=search(obs,legal,Budget(CONNECT_LIMITS[level-1],search_ms),logits=logits)')
change('logic_arena/agents.py','from .connect4 import search', 'from .connect4_wasm import search')
change('pyproject.toml','version = "0.1.0"', 'version = "1.1.0"')
change('pyproject.toml','dependencies = ["numpy>=1.24"]', 'dependencies = ["numpy>=1.24", "wasmtime==49.0.0"]')
