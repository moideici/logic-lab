"""Identité de la génération logicielle, partagée avec le navigateur."""
import json
from pathlib import Path

_MANIFEST = json.loads((Path(__file__).resolve().parents[1] / "web" / "agents.json").read_text(encoding="utf-8"))
AGENT_VERSION = _MANIFEST["version"]


def agent_identity(game):
    return dict(_MANIFEST["agents"][game])
