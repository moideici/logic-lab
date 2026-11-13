"""HTTP JSON + Server-Sent Events ; frontend servi à la même origine."""
from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .harness import Arena, json_line
from .external import ExternalArena
EXTERNAL=ExternalArena()
from .continuous_service import ContinuousTraining
from . import lab as lab_api
CONTINUOUS=ContinuousTraining()

WEB = Path(__file__).resolve().parents[1]/"web"


class Handler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def __init__(self, *args, arena, **kwargs):
        self.arena = arena
        super().__init__(*args, directory=str(WEB), **kwargs)

    def send_header(self, keyword, value):
        if keyword.lower() == "cache-control":
            self._cc = True
        super().send_header(keyword, value)

    def end_headers(self):
        if not getattr(self, "_cc", False):  # fichiers statiques : toujours revalider (sinon un ancien module JS reste en cache)
            super().send_header("Cache-Control", "no-cache")
        self._cc = False
        super().end_headers()

    def send_json(self, value, status=200):
        data = json.dumps(value, ensure_ascii=False, allow_nan=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def lab(self, method):
        parsed = urlparse(self.path)
        body = {}
        if method == "POST":
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 <= size <= 4096:
                    raise ValueError("Taille JSON invalide")
                body = json_line(self.rfile.read(size).decode("utf-8")) if size else {}
                if not isinstance(body, dict):
                    raise ValueError("Objet JSON requis")
            except (ValueError, UnicodeError) as error:
                self.send_json({"ok": False, "error": str(error)}, 400)
                return
        status, payload = lab_api.handle(method, parsed.path, parse_qs(parsed.query), body)
        self.send_json(payload, status)

    def do_POST(self):
        if urlparse(self.path).path == "/api/maths/solve":
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 4096:
                    raise ValueError("Taille JSON invalide")
                data = json_line(self.rfile.read(size).decode("utf-8"))
                from . import maths_api
                model, verified = data.get("model", "best"), bool(data.get("verified"))
                if model == "best":
                    result = maths_api.solve_best(data["expression"])
                elif model == "all":
                    result = maths_api.solve_all(data["expression"], verified)
                else:
                    result = maths_api.solve(data["expression"], model, verified)
                self.send_json({"ok": True, "result": result})
            except (ValueError, KeyError) as error:
                self.send_json({"ok": False, "error": str(error)}, 400)
            except Exception as error:
                self.send_json({"ok": False, "error": "Calcul impossible : " + str(error)}, 500)
            return
        if urlparse(self.path).path == "/api/player":
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 1048576:
                    raise ValueError("Taille JSON invalide")
                data = json_line(self.rfile.read(size).decode("utf-8"))
                from . import players
                self.send_json({"ok": True, "action": players.choose(data["player"], data["observation"], data["legal"])})
            except Exception as error:  # joueur absent, jeu non pris en charge, poids manquants
                self.send_json({"ok": False, "error": str(error)}, 400)
            return
        if urlparse(self.path).path.startswith('/api/lab/'):
            self.lab("POST");return
        if urlparse(self.path).path.startswith('/api/continuous/'):
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=4096:raise ValueError('Taille JSON invalide')
                data=json_line(self.rfile.read(size).decode('utf-8'));op=urlparse(self.path).path.rsplit('/',1)[-1]
                if not isinstance(data,dict):raise ValueError('Objet JSON requis')
                if op=='start' and set(data)<={'seconds','profile'}:result=CONTINUOUS.start(data.get('seconds',3600),data.get('profile','balanced'))
                elif op=='stop' and set(data)=={'id'}:result=CONTINUOUS.stop(data['id'])
                else:raise ValueError('Opération continue invalide')
                self.send_json({'ok':True,'result':result})
            except (ValueError,TypeError,UnicodeError) as error:self.send_json({'ok':False,'error':str(error)},400)
            return
        if urlparse(self.path).path.startswith('/api/external/'):
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=4096:raise ValueError('Taille JSON invalide')
                data=json_line(self.rfile.read(size).decode('utf-8'));op=urlparse(self.path).path.rsplit('/',1)[-1]
                if op=='start':result=EXTERNAL.start(data)
                elif op=='stop' and isinstance(data,dict):result=EXTERNAL.stop(data.get('id'))
                else:raise ValueError('Opération externe inconnue')
                self.send_json({'ok':True,'result':result})
            except (ValueError,TypeError,UnicodeError) as error:self.send_json({'ok':False,'error':str(error)},400)
            return
        if urlparse(self.path).path != "/api":
            self.send_json({"ok": False, "error": "Route inconnue"}, 404)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 1048576:
                self.close_connection = True
                raise ValueError("Taille JSON invalide (maximum 1 Mo)")
            data = json_line(self.rfile.read(size).decode("utf-8"))
            result = self.arena.dispatch(data)
            self.send_json(result, 200 if result["ok"] else 400)
        except (ValueError, UnicodeError) as error:
            self.send_json({"protocol": "logic-arena.v1", "id": None, "ok": False,
                            "error": {"code": "invalid_json", "message": str(error)}}, 400)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith('/api/lab/'):
            self.lab('GET');return
        if parsed.path=='/api/continuous/status':
            self.send_json({'ok':True,'result':CONTINUOUS.get()});return
        if parsed.path.startswith('/api/external/'):
            try:
                op=parsed.path.rsplit('/',1)[-1];identifier=parse_qs(parsed.query).get('id',[''])[0]
                if op=='list':self.send_json({'ok':True,'result':EXTERNAL.list()});return
                if op=='status':self.send_json({'ok':True,'result':EXTERNAL.get(identifier)});return
                if op in ('image','trace'):
                    path=EXTERNAL.image(identifier) if op=='image' else EXTERNAL._path(identifier)/'trace.jsonl'
                    if not path.is_file():self.send_json({'ok':False,'error':'Partie en préparation'},404);return
                    raw=path.read_bytes();self.send_response(200);self.send_header('Content-Type','image/png' if op=='image' else 'application/x-ndjson');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw);return
                raise ValueError('Opération externe inconnue')
            except (ValueError,OSError) as error:self.send_json({'ok':False,'error':str(error)},400)
            return
        parts = parsed.path.strip("/").split("/")
        if len(parts) == 3 and parts[0] == "sessions" and parts[2] == "events":
            try:
                session = self.arena.session(parts[1])
                cursor = int(self.headers.get("Last-Event-ID", parse_qs(parsed.query).get("after", ["0"])[0]))
                if cursor < 0:
                    raise ValueError("Curseur négatif")
            except ValueError as error:
                self.send_json({"ok": False, "error": str(error)}, 400)
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()
            try:
                while True:
                    with session.condition:
                        if cursor < session.events[0]["seq"]-1 or cursor > session.sequence:
                            events = [{"seq": session.sequence, "type": "resync", **session.snapshot()}]
                        else:
                            events = [e for e in session.events if e["seq"] > cursor]
                        if not events:
                            if session.deleted or session.events[-1]["type"] == "stopped":
                                break
                            session.condition.wait(10)
                        terminal = session.events[-1]["type"] in ("stopped", "deleted")
                    if not events:
                        self.wfile.write(b": heartbeat\n\n")
                        self.wfile.flush()
                        continue
                    for event in events:
                        data = json.dumps(event, ensure_ascii=False, allow_nan=False)
                        self.wfile.write(f"id: {event['seq']}\nevent: {event['type']}\ndata: {data}\n\n".encode())
                        self.wfile.flush()
                        cursor = event["seq"]
                    if events[-1]["type"] in ("stopped", "deleted") or (events[-1]["type"] == "resync" and terminal):
                        break
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass
            self.close_connection = True
            return
        if parsed.path == "/api/maths/models":
            try:
                from . import maths_api
                self.send_json({"ok": True, "models": maths_api.models()})
            except Exception as error:
                self.send_json({"ok": True, "models": [], "note": str(error)})
            return
        if parsed.path == "/api/players":
            try:
                from . import players
                self.send_json({"ok": True, "players": players.available()})
            except Exception as error:
                self.send_json({"ok": True, "players": {}, "note": str(error)})
            return
        if parsed.path == "/api/catalog":
            self.send_json(self.arena.dispatch({"op": "catalog"}))
            return
        super().do_GET()


def serve(host="127.0.0.1", port=8000):
    arena = Arena()
    server = ThreadingHTTPServer((host, port), partial(Handler, arena=arena))
    print(f"Logic Lab : http://{host}:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        arena.close()
        server.server_close()
