"""API du Lab : observer le réseau de Garry en direct, éteindre des neurones, mesurer leur importance.

Une seule session locale (serveur sur 127.0.0.1). Rien ici n'entraîne ni n'écrit les poids : le Lab travaille sur
une copie en mémoire du réseau actif (`web/models/garry.json`).
"""
from __future__ import annotations

import threading

import numpy as np

from .core import from_garry, encode_observation
from .games import make_game
from .general import GAMES, OUTPUT_OFFSETS, GarryPolicy
from .neural import MODEL_DIR, SPECS, action_index

HIDDEN_LAYERS = ("encodeur", "coeur")


def _label(action):
    return ", ".join(f"{k} {v}" for k, v in action.items()) if isinstance(action, dict) else str(action)


class Lab:
    def __init__(self):
        self.lock = threading.RLock()
        self.policy = None
        self.net = None
        self.env = None
        self.game = None
        self.seed = 0
        self.moves = 0
        self.rng = np.random.default_rng(0)
        self.importance_cache = {}

    # ---- chargement ---------------------------------------------------------
    def _ensure(self):
        if self.net is None:
            path = MODEL_DIR / "garry.json"
            self.policy = GarryPolicy.load(path)
            self.net = from_garry(self.policy)
            self.reference = from_garry(self.policy)

    def describe(self):
        with self.lock:
            self._ensure()
            layers = []
            for layer in self.net.layers:
                layers.append({"name": layer.name, "entrees": int(layer.n_in), "neurones": int(layer.n_out), "activation": layer.activation,
                               "norme_poids": round(float(np.linalg.norm(layer.w)), 3),
                               "eteints": sorted(self.net.muted.get(layer.name, []))})
            return {"version": self.policy_version(), "forme": self.net.shape, "parametres": self.net.parameter_count(), "couches": layers,
                    "jeux": [{"id": g, "entrees": SPECS[g][0], "sorties": SPECS[g][1]} for g in GAMES]}

    def policy_version(self):
        from .identity import AGENT_VERSION
        return AGENT_VERSION

    # ---- partie en cours ----------------------------------------------------
    def new_game(self, game, seed=0):
        if game not in GAMES:
            raise ValueError("Jeu inconnu")
        if type(seed) is not int or not 0 <= seed < 10 ** 9:
            raise ValueError("Graine invalide")
        with self.lock:
            self._ensure()
            self.env, self.game, self.seed, self.moves = make_game(game, seed), game, seed, 0
            self.rng = np.random.default_rng(seed)
            return self.state()

    def _logits(self, net, obs):
        out = net.forward(encode_observation(obs))
        start = OUTPUT_OFFSETS[obs["game"]]
        return out[start:start + SPECS[obs["game"]][1]]

    def state(self, top=8):
        with self.lock:
            self._ensure()
            if self.env is None:
                self.new_game("tictactoe", 0)
            obs = self.env.observation()
            payload = {"jeu": self.game, "coups": self.moves, "termine": bool(obs["done"]), "plateau": obs.get("board"),
                       "joueur": obs.get("current_player"), "eteints": {k: sorted(v) for k, v in self.net.muted.items()}}
            if obs["done"]:
                payload.update(activations={}, actions=[])
                return payload
            legal = self.env.legal_actions()
            trace = {}
            out = self.net.forward(encode_observation(obs), trace)
            start = OUTPUT_OFFSETS[self.game]
            muted_logits = out[start:start + SPECS[self.game][1]]
            full_logits = self._logits(self.reference, obs)
            idx = [action_index(self.game, a) for a in legal]
            order = np.argsort([-float(muted_logits[i]) for i in idx])[:top]
            best_full = int(np.argmax([float(full_logits[i]) for i in idx]))
            payload["activations"] = {k: [round(float(v), 4) for v in trace[k]] for k in HIDDEN_LAYERS}
            payload["actions"] = [{"action": _label(legal[j]), "score": round(float(muted_logits[idx[j]]), 4),
                                   "score_complet": round(float(full_logits[idx[j]]), 4), "choisie": bool(k == 0), "meilleure_complet": bool(j == best_full)}
                                  for k, j in enumerate(order)]
            payload["coups_legaux"] = len(legal)
            payload["choix_change"] = bool(int(order[0]) != best_full)
            return payload

    def step(self, mode="reseau"):
        with self.lock:
            self._ensure()
            if self.env is None:
                self.new_game("tictactoe", 0)
            obs = self.env.observation()
            if obs["done"]:
                return self.state()
            legal = self.env.legal_actions()
            if mode == "hasard":
                action = legal[int(self.rng.integers(len(legal)))]
            elif mode in ("reseau", "complet"):
                net = self.net if mode == "reseau" else self.reference
                values = self._logits(net, obs)
                action = legal[int(np.argmax([float(values[action_index(self.game, a)]) for a in legal]))]
            else:
                raise ValueError("Mode inconnu")
            self.env.step(action)
            self.moves += 1
            return self.state()

    # ---- chirurgie ----------------------------------------------------------
    def mute(self, layer, index, on=True):
        with self.lock:
            self._ensure()
            if layer not in HIDDEN_LAYERS:
                raise ValueError("Couche inconnue")
            if type(index) is not int:
                raise ValueError("Indice invalide")
            if on:
                self.net.mute(layer, [index])
            else:
                self.net.muted.get(layer, set()).discard(index)
            return self.state()

    def reset_mutes(self):
        with self.lock:
            self._ensure()
            self.net.unmute_all()
            return self.state()

    # ---- mesures ------------------------------------------------------------
    def _positions(self, game, count, seed):
        """Positions variées : parties jouées au hasard, quelques coups chacune."""
        rng = np.random.default_rng(seed)
        out = []
        guard = 0
        while len(out) < count and guard < count * 20:
            guard += 1
            env = make_game(game, int(rng.integers(10 ** 6)))
            depth = int(rng.integers(0, 14))
            for _ in range(depth):
                if env.observation()["done"]:
                    break
                legal = env.legal_actions()
                env.step(legal[int(rng.integers(len(legal)))])
            obs = env.observation()
            if not obs["done"]:
                out.append((obs, env.legal_actions()))
        return out

    def _top(self, net, game, obs, legal):
        values = self._logits(net, obs)
        scores = np.array([float(values[action_index(game, a)]) for a in legal])
        return int(np.argmax(scores)), scores

    def importance(self, game, count=40):
        """Pour chaque neurone caché : part des positions où l'extinction change le coup préféré, et décalage moyen des scores."""
        if game not in GAMES:
            raise ValueError("Jeu inconnu")
        with self.lock:
            self._ensure()
            if game in self.importance_cache:
                return self.importance_cache[game]
            positions = self._positions(game, count, seed=101)
            probe = self.reference.copy()
            base = [self._top(probe, game, o, l) for o, l in positions]
            result = []
            for layer in HIDDEN_LAYERS:
                for i in range(probe.layer(layer).n_out):
                    probe.muted = {layer: {i}}
                    flips, shift = 0, 0.0
                    for (o, l), (b_top, b_scores) in zip(positions, base):
                        top, scores = self._top(probe, game, o, l)
                        flips += int(top != b_top)
                        shift += float(np.abs(scores - b_scores).mean())
                    result.append({"couche": layer, "indice": i, "sensibilite": round(flips / len(positions), 4), "decalage": round(shift / len(positions), 4)})
            probe.muted = {}
            data = {"jeu": game, "positions": len(positions), "neurones": result}
            self.importance_cache[game] = data
            return data

    def prune_curve(self, game, steps=(0, 4, 8, 16, 24, 32, 48, 64, 80, 92)):
        """Éteint les k neurones les moins sensibles (mesurés sur 40 positions) ; accord avec le réseau complet sur 60 autres positions."""
        data = self.importance(game)
        ranked = sorted(data["neurones"], key=lambda n: (n["sensibilite"], n["decalage"]))
        held = self._positions(game, 60, seed=202)
        probe = self.reference.copy()
        base = [self._top(probe, game, o, l)[0] for o, l in held]
        curve = []
        for k in steps:
            if k >= 96:
                continue
            probe.muted = {}
            for n in ranked[:k]:
                probe.muted.setdefault(n["couche"], set()).add(n["indice"])
            # une couche ne peut pas être vidée : on garde au moins 2 neurones
            if any(len(v) >= 47 for v in probe.muted.values()):
                break
            agree = sum(int(self._top(probe, game, o, l)[0] == b) for (o, l), b in zip(held, base)) / len(held)
            n1 = 48 - len(probe.muted.get("encodeur", ()))
            n2 = 48 - len(probe.muted.get("coeur", ()))
            params = 4872 * n1 + n1 + n1 * n2 + n2 + n2 * 4259 + 4259
            curve.append({"eteints": k, "parametres": params, "accord": round(agree, 4)})
        return {"jeu": game, "positions": len(held), "courbe": curve, "pleine": self.reference.parameter_count()}


LAB = Lab()


def handle(method, path, query, body):
    """Retourne (statut, JSON). Les erreurs de validation donnent 400."""
    try:
        if method == "GET" and path == "/api/lab/net":
            return 200, {"ok": True, "result": LAB.describe()}
        if method == "GET" and path == "/api/lab/state":
            return 200, {"ok": True, "result": LAB.state()}
        if method == "GET" and path == "/api/lab/importance":
            return 200, {"ok": True, "result": LAB.importance(query.get("game", ["tictactoe"])[0])}
        if method == "GET" and path == "/api/lab/prune-curve":
            return 200, {"ok": True, "result": LAB.prune_curve(query.get("game", ["tictactoe"])[0])}
        if method == "GET" and path == "/api/lab/train/status":
            from .labtrain_api import JOB
            return 200, {"ok": True, "result": JOB.status()}
        if method == "POST" and path == "/api/lab/train/start":
            from .labtrain_api import JOB
            JOB.start(body.get("game"), body.get("mode", ""), body.get("steps", 3000), body.get("pause_ms", 4))
            return 200, {"ok": True, "result": JOB.status()}
        if method == "POST" and path == "/api/lab/train/stop":
            from .labtrain_api import JOB
            JOB.stop()
            return 200, {"ok": True, "result": JOB.status()}
        if method == "GET" and path == "/api/lab/reason/info":
            from .reason import service
            return 200, {"ok": True, "result": service.info()}
        if method == "POST" and path == "/api/lab/reason/new":
            from .reason import service
            return 200, {"ok": True, "result": service.new_puzzle(body.get("empties", 18), body.get("seed", 0))}
        if method == "POST" and path == "/api/lab/reason/solve":
            from .reason import service
            return 200, {"ok": True, "result": service.solve(body.get("puzzle"), body.get("passes", 16), body.get("solution"))}
        if method == "POST" and path == "/api/lab/new":
            return 200, {"ok": True, "result": LAB.new_game(body.get("game"), body.get("seed", 0))}
        if method == "POST" and path == "/api/lab/step":
            return 200, {"ok": True, "result": LAB.step(body.get("mode", "reseau"))}
        if method == "POST" and path == "/api/lab/mute":
            return 200, {"ok": True, "result": LAB.mute(body.get("layer"), body.get("index"), bool(body.get("on", True)))}
        if method == "POST" and path == "/api/lab/reset":
            return 200, {"ok": True, "result": LAB.reset_mutes()}
        return 404, {"ok": False, "error": "Route du Lab inconnue"}
    except (ValueError, KeyError) as error:
        return 400, {"ok": False, "error": str(error)}
