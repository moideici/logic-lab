from pathlib import Path

ROOT = Path(__file__).parent

def change(file, old, new):
    path = ROOT / file
    text = path.read_text(encoding="utf-8")
    assert text.count(old) == 1, (file, old[:80], text.count(old))
    path.write_text(text.replace(old, new), encoding="utf-8")

change('web/engine.js', "export const NAMES=", "import {agentIdentity} from './agents.js';\nexport const NAMES=")
change('web/engine.js', "info:{agent:'neural',level,style,confidence:", "info:{agent:'neural',identity:agentIdentity(this.game),level,style,confidence:")
change('web/engine.js', "export(){const d={format:", "export(){const d={identity:agentIdentity(this.game),format:")
change('web/app.js', "import {LIMITS,TIMES}", "import {AGENTS,AGENT_VERSION,agentIdentity} from './agents.js';\nimport {LIMITS,TIMES}")
change('web/app.js', "${['tictactoe','connect4'].includes(name)?'DUEL':'SOLO'} · MODULE CONNECTÉ", "${AGENTS[name].codename} · V${AGENTS[name].version}")
change('web/app.js', "$('model-status').textContent=`Poids appris", "$('model-status').textContent=`${AGENTS[game.name].codename} v${AGENTS[game.name].version} · Poids appris")
change('web/app.js', "players:['tictactoe','connect4'].includes(id)?2:1})),styles:", "players:['tictactoe','connect4'].includes(id)?2:1,ai:agentIdentity(id)})),agent_version:AGENT_VERSION,styles:")
change('logic_arena/neural.py', "from .games import make_game", "from .games import make_game\nfrom .identity import agent_identity")
change('logic_arena/neural.py', 'return {"format": "logic-arena-mlp-v2",', 'return {"identity": agent_identity(self.game), "format": "logic-arena-mlp-v2",')
change('logic_arena/neural.py', 'return Decision(action, {"agent": "neural",', 'return Decision(action, {"agent": "neural", "identity": agent_identity(obs["game"]),')
change('logic_arena/agents.py', 'from .games import slide_2048, sudoku_candidates', 'from .games import slide_2048, sudoku_candidates\nfrom .identity import agent_identity')
change('logic_arena/agents.py', 'return Decision(action, {"agent": "reference",', 'return Decision(action, {"agent": "reference", "identity": agent_identity(observation["game"]),')
change('logic_arena/harness.py', 'from .games import GAMES, make_game', 'from .games import GAMES, make_game\nfrom .identity import agent_identity, AGENT_VERSION')
change('logic_arena/harness.py', '"games": [{"id": k, "players": g.players, "action": ACTION_SCHEMAS[k]}', '"agent_version": AGENT_VERSION, "games": [{"id": k, "players": g.players, "action": ACTION_SCHEMAS[k], "ai": agent_identity(k)}')
