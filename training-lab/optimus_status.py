"""Ecrit web/optimus-status.json pour la page du Lab. Usage : optimus_status.py <running 0|1> "<texte>" """
import json
import sys
import time
from pathlib import Path

out = Path(__file__).resolve().parents[1] / "web" / "optimus-status.json"
out.write_text(json.dumps({"running": sys.argv[1] == "1", "text": sys.argv[2], "t": time.strftime("%Y-%m-%d %H:%M")}, ensure_ascii=False), encoding="utf-8")
