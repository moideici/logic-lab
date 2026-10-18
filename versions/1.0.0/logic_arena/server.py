"""HTTP JSON + Server-Sent Events ; frontend servi à la même origine."""
from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .harness import Arena, json_line

WEB = Path(__file__).resolve().parents[1]/"web"


class Handler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def __init__(self, *args, arena, **kwargs):
        self.arena = arena
        super().__init__(*args, directory=str(WEB), **kwargs)

    def send_json(self, value, status=200):
        data = json.dumps(value, ensure_ascii=False, allow_nan=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
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
            except (BrokenPipeError, ConnectionResetError):
                pass
            self.close_connection = True
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
