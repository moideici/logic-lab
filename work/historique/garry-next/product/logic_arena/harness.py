"""Sessions, protocole JSON v1 et diffusion d'événements."""
from __future__ import annotations

from collections import deque
import json
import math
import threading
import time
import uuid

from .agents import NODE_LIMITS, STYLES, TIME_LIMITS, ReferenceAgent
from .games import GAMES, make_game
from .identity import agent_identity, AGENT_VERSION


ACTION_SCHEMAS = {
    "tictactoe": {"row": "0..2", "col": "0..2"},
    "2048": {"direction": "up|down|left|right"},
    "sudoku": [{"row": "0..8", "col": "0..8", "value": "1..9"}, {"undo": True}],
    "connect4": {"column": "0..6"},
    "minesweeper": {"row": "0..7", "col": "0..7"},
    "sliding_puzzle": {"direction": "up|down|left|right"},
}


def catalog():
    from .planner import LIMITS, TIMES
    from .connect4_wasm import CONNECT_LIMITS,CONNECT_TIMES
    return {"protocol": "logic-arena.v1", "agent_version": AGENT_VERSION, "model": {"name":"garry","version":AGENT_VERSION,"format":"garry-mlp-v2","architecture":[1912,48,48,818],"position_head":{"game":"connect4","features":32,"outputs":1},"files":1}, "games": [{"id": k, "players": g.players, "action": ACTION_SCHEMAS[k], "ai": agent_identity(k)} for k, g in GAMES.items()],
            "styles": STYLES, "levels": [{"level":i,"quality_quantile":i/10,"reference_nodes":NODE_LIMITS[-1],"reference_time_ms":TIME_LIMITS[-1],"planning_nodes":LIMITS[-1],"planning_time_ms":TIMES[-1],"connect4_nodes":CONNECT_LIMITS[-1],"connect4_time_ms":CONNECT_TIMES[-1],"connect4_target_depth":20} for i in range(11)],
            "operations": ["catalog", "create", "observe", "step", "suggest", "play", "run", "stop", "delete"],
            "realtime": "SSE /sessions/{session_id}/events", "default_level": 10, "default_interval_ms": 0, "objective": "win_then_fewest_moves"}


def agent_config(config):
    config = {} if config is None else config
    if not isinstance(config, dict) or set(config)-{"type", "level", "style", "seed", "time_ms", "planning"}:
        raise ValueError("agent attend type, level, style, seed, time_ms, planning")
    config = dict(config)
    kind = config.pop("type", "neural")
    if kind == "reference":
        return ReferenceAgent(**config)
    if kind != "neural":
        raise ValueError("type doit être neural ou reference")
    from .neural import NeuralAgent
    return NeuralAgent(**config)


class Session:
    def __init__(self, game, seed, options):
        self.id = uuid.uuid4().hex
        self.game = make_game(game, seed, options)
        self.seed, self.options = seed, options or {}
        self.condition = threading.Condition(threading.RLock())
        self.events = deque(maxlen=256)
        self.revision = 0
        self.sequence = 0
        self.running = False
        self.deleted = False
        self.cancel = threading.Event()
        self.thread = None
        self.emit("created", {})

    def snapshot(self):
        return {"session_id": self.id, "revision": self.revision, "running": self.running,
                "seed": self.seed, "options": self.options,
                "observation": self.game.observation(), "legal_actions": self.game.legal_actions()}

    def emit(self, kind, extra):
        with self.condition:
            self.sequence += 1
            event = {"seq": self.sequence, "type": kind, "timestamp": time.time(), **self.snapshot(), **extra}
            self.events.append(event)
            self.condition.notify_all()
            return event

    def apply(self, action, info=None):
        player = self.game.current_player
        reward = self.game.step(action)
        self.revision += 1
        return self.emit("finished" if self.game.done else "step", {"action": action, "reward": reward, "actor": player, "info": info or {}})


class Arena:
    def __init__(self, max_sessions=100):
        self.sessions = {}
        self.lock = threading.RLock()
        self.max_sessions = max_sessions

    def session(self, identifier):
        if not isinstance(identifier, str):
            raise ValueError("session_id requis")
        with self.lock:
            session = self.sessions.get(identifier)
        if session is None:
            raise ValueError("Session inconnue")
        return session

    def dispatch(self, request):
        request_id = request.get("id") if isinstance(request, dict) else None
        try:
            if not isinstance(request, dict):
                raise ValueError("La requête doit être un objet JSON")
            if request.get("protocol", "logic-arena.v1") != "logic-arena.v1":
                raise ValueError("Version de protocole non supportée")
            result = self.handle(request)
            return {"protocol": "logic-arena.v1", "id": request_id, "ok": True, "result": result}
        except (ValueError, TypeError, KeyError) as error:
            return {"protocol": "logic-arena.v1", "id": request_id, "ok": False, "error": {"code": "invalid_request", "message": str(error)}}

    def handle(self, req):
        op = req.get("op")
        if op == "catalog":
            return catalog()
        if op == "create":
            session = Session(req.get("game", "tictactoe"), req.get("seed", 0), req.get("options"))
            with self.lock:
                if len(self.sessions) >= self.max_sessions:
                    raise ValueError("Limite de sessions atteinte ; supprimer une session")
                self.sessions[session.id] = session
            return session.snapshot()
        if op not in ("observe", "step", "suggest", "play", "run", "stop", "delete"):
            raise ValueError("Opération inconnue")
        session = self.session(req.get("session_id"))
        with session.condition:
            if session.deleted:
                raise ValueError("Session supprimée")
            if op == "observe":
                return session.snapshot()
            if op == "stop":
                session.cancel.set()
                return {"stop_requested": True, **session.snapshot()}
            if op == "delete":
                session.cancel.set()
                session.deleted = True
                session.emit("deleted", {})
                with self.lock:
                    self.sessions.pop(session.id, None)
                return {"deleted": session.id}
            if session.running and op != "suggest":
                raise ValueError("Session en cours ; envoyer stop et attendre stopped")
            if "expected_revision" in req and (type(req["expected_revision"]) is not int or req["expected_revision"] != session.revision):
                raise ValueError("Révision obsolète ; relire l'observation")
            if op == "step":
                return session.apply(req.get("action"))
            if op in ("suggest", "play"):
                agent = agent_config(req.get("agent"))
                decision = agent.choose(session.game.observation(), session.game.legal_actions())
                if op == "suggest":
                    return {"revision": session.revision, **decision.as_dict()}
                return session.apply(decision.action, decision.info)
            if session.game.done:
                raise ValueError("Partie terminée")
            limit, interval = req.get("max_steps", 5000), req.get("interval_ms", 0)
            if type(limit) is not int or not 1 <= limit <= 10000:
                raise ValueError("max_steps doit être entre 1 et 10000")
            if type(interval) not in (int, float) or not math.isfinite(interval) or not 0 <= interval <= 10000:
                raise ValueError("interval_ms doit être entre 0 et 10000")
            configs = req.get("agents", {})
            if not isinstance(configs, dict) or set(configs)-{"1", "2"}:
                raise ValueError("agents attend les clés '1' et/ou '2'")
            agents = {p: agent_config(configs.get(str(p), req.get("agent"))) for p in (1, 2)}
            session.running = True
            session.cancel.clear()
            session.emit("started", {})
            session.thread = threading.Thread(target=self._run, args=(session, agents, limit, interval/1000), daemon=True)
            session.thread.start()
            return session.snapshot()

    def _run(self, session, agents, limit, interval):
        reason = "max_steps"
        try:
            for _ in range(limit):
                with session.condition:
                    if session.cancel.is_set():
                        reason = "cancelled"
                        break
                    if session.game.done:
                        reason = "terminal"
                        break
                    agent = agents[session.game.current_player]
                    revision = session.revision
                    observation, legal = session.game.observation(), session.game.legal_actions()
                # Ne pas bloquer observe/stop pendant toute la réflexion.
                choice = agent.choose(observation, legal)
                with session.condition:
                    if session.cancel.is_set() or session.deleted:
                        reason = "cancelled"
                        break
                    if session.revision != revision:
                        continue
                    session.apply(choice.action, choice.info)
                    if session.game.done:
                        reason = "terminal"
                        break
                if session.cancel.wait(interval):
                    reason = "cancelled"
                    break
        except Exception as error:
            reason = "error"
            with session.condition:
                session.emit("run_error", {"message": str(error)})
        finally:
            with session.condition:
                session.running = False
                session.emit("stopped", {"reason": reason, "truncated": reason == "max_steps"})

    def close(self):
        with self.lock:
            sessions = list(self.sessions.values())
        for session in sessions:
            session.cancel.set()
        for session in sessions:
            if session.thread:
                session.thread.join(timeout=11)


def json_line(line):
    try:
        return json.loads(line, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(f"Constante JSON invalide : {x}")))
    except json.JSONDecodeError as error:
        raise ValueError(f"JSON invalide : {error.msg}") from error
