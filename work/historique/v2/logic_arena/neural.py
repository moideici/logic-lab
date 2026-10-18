"""Politique MLP NumPy réelle, rétropropagation et export JSON interopérable JS."""
from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from pathlib import Path

import numpy as np

from .agents import Decision, ReferenceAgent
from .games import make_game
from .identity import agent_identity


SPECS = {"tictactoe": (18, 9), "connect4": (84, 7), "2048": (192, 4),
         "sudoku": (891, 730), "minesweeper": (640, 64), "sliding_puzzle": (81, 4)}
DIRECTIONS = ["up", "down", "left", "right"]
TEMPERATURES = [2., 1.4, 1.1, .9, .7, .55, .4, .25, .12, 0.]


def encode(obs):
    name = obs["game"]
    x = np.zeros(SPECS[name][0], dtype=np.float32)
    for i, value in enumerate(v for row in obs["board"] for v in row):
        if name in ("tictactoe", "connect4"):
            if value:
                x[i*2+(0 if value == obs["current_player"] else 1)] = 1
        elif name == "2048":
            if value:
                x[i*12+min(11, int(value).bit_length()-1)] = 1
        elif name == "sudoku":
            x[i*10+value] = 1
            x[810+i] = bool(obs["givens"][i//9][i%9])
        elif name == "minesweeper":
            x[i*10+max(0, value+1)] = 1
        else:
            x[i*9+value] = 1
    return x


def action_index(game, action):
    if game == "sudoku":
        return 729 if "undo" in action else (action["row"]*9+action["col"])*9+action["value"]-1
    if game == "connect4":
        return action["column"]
    if game in ("2048", "sliding_puzzle"):
        return DIRECTIONS.index(action["direction"])
    return action["row"]*(3 if game == "tictactoe" else 8)+action["col"]


class NeuralPolicy:
    def __init__(self, game, hidden=48, seed=0, core=None):
        if game not in SPECS:
            raise ValueError("Jeu inconnu")
        self.game, self.hidden, self.steps = game, hidden, 0
        ni, no = SPECS[game]
        if type(seed) is not int:
            raise ValueError("seed doit être un entier")
        self.rng = np.random.default_rng(seed % (1 << 64))
        self.w1 = (self.rng.standard_normal((ni, hidden))*np.sqrt(2/(ni+hidden))).astype(np.float32)
        self.b1 = np.zeros(hidden, dtype=np.float32)
        self.w2 = (self.rng.standard_normal((hidden, no))*np.sqrt(2/(hidden+no))).astype(np.float32)
        self.b2 = np.zeros(no, dtype=np.float32)
        self.core = core if core is not None else {"w": np.eye(hidden, dtype=np.float32), "b": np.zeros(hidden, dtype=np.float32), "steps": 0}
        if self.core["w"].shape != (hidden, hidden):
            raise ValueError("Dimensions du module partagé incompatibles")
        self._adam = None

    def logits(self, obs):
        if obs["game"] != self.game:
            raise ValueError("Modèle incompatible avec ce jeu")
        encoded = np.tanh(encode(obs)@self.w1+self.b1)
        return np.tanh(encoded@self.core["w"]+self.core["b"])@self.w2+self.b2

    def choose(self, obs, legal, level=10, style="balanced", *, logits=None, rng=None):
        # Validation commune ; la politique utilise les paramètres de difficulté.
        ReferenceAgent(level, style)
        if not legal or obs["done"]:
            raise ValueError("Partie terminée")
        values = self.logits(obs) if logits is None else logits
        scores = values[[action_index(self.game, a) for a in legal]].astype(np.float64)
        from .policy import style_bias
        scores += np.array([style_bias(obs, a, style) for a in legal])
        temperature = TEMPERATURES[level-1]
        if style == "exploratory":
            temperature = max(.6, temperature)
        if temperature == 0:
            return legal[int(scores.argmax())]
        p = np.exp(np.clip((scores-scores.max())/temperature, -50, 0))
        generator = self.rng if rng is None else rng
        return legal[int(generator.choice(len(legal), p=p/p.sum()))]

    def fit(self, x, targets, masks, epochs=20, batch_size=64, lr=.003):
        """Cross-entropie masquée, Adam ; le gradient traverse le module partagé."""
        x = np.asarray(x, dtype=np.float32)
        targets = np.asarray(targets, dtype=np.int64)
        masks = np.asarray(masks, dtype=bool)
        params = [self.w1, self.b1, self.w2, self.b2, self.core["w"], self.core["b"]]
        if self._adam is None:
            self._adam = ([np.zeros_like(p) for p in params], [np.zeros_like(p) for p in params], 0)
        m, v, t = self._adam
        losses = []
        for _ in range(epochs):
            total = 0.
            for start in range(0, len(x), batch_size):
                # Shuffle once per epoch below to preserve efficient vectorization.
                xb = x[start:start+batch_size]
                y = targets[start:start+batch_size]
                mask = masks[start:start+batch_size]
                encoded = np.tanh(xb@self.w1+self.b1)
                hidden = np.tanh(encoded@self.core["w"]+self.core["b"])
                logits = hidden@self.w2+self.b2
                logits = np.where(mask, logits, -1e9)
                exp = np.exp(logits-logits.max(axis=1, keepdims=True))
                p = exp/exp.sum(axis=1, keepdims=True)
                total += float(-np.log(np.maximum(p[np.arange(len(y)), y], 1e-12)).sum())
                p[np.arange(len(y)), y] -= 1
                p /= len(y)
                dh = (p@self.w2.T)*(1-hidden*hidden)
                de = (dh@self.core["w"].T)*(1-encoded*encoded)
                grads = [xb.T@de, de.sum(axis=0), hidden.T@p, p.sum(axis=0), encoded.T@dh, dh.sum(axis=0)]
                t += 1
                for i, (param, grad) in enumerate(zip(params, grads)):
                    np.clip(grad, -5, 5, out=grad)
                    m[i] = .9*m[i]+.1*grad
                    v[i] = .999*v[i]+.001*grad*grad
                    param -= lr*(m[i]/(1-.9**t))/(np.sqrt(v[i]/(1-.999**t))+1e-8)
                self.steps += len(y)
                self.core["steps"] += len(y)
            losses.append(total/max(1, len(x)))
            order = self.rng.permutation(len(x))
            x, targets, masks = x[order], targets[order], masks[order]
        self._adam = m, v, t
        return losses

    def export(self):
        return {"identity": agent_identity(self.game), "format": "logic-arena-mlp-v2", "game": self.game, "input": SPECS[self.game][0],
                "output": SPECS[self.game][1], "hidden": self.hidden, "steps": self.steps,
                "w1": self.w1.ravel().tolist(), "b1": self.b1.tolist(),
                "w2": self.w2.ravel().tolist(), "b2": self.b2.tolist(),
                "core": {"id": "logic-core-v1", "w": self.core["w"].ravel().tolist(), "b": self.core["b"].tolist(), "steps": self.core["steps"]}}

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(self.export(), stream, separators=(",", ":"), allow_nan=False)
            os.replace(temporary, path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    @classmethod
    def from_dict(cls, data):
        if data.get("format") != "logic-arena-mlp-v2" or data.get("game") not in SPECS:
            raise ValueError("Modèle neuronal invalide")
        hidden = data.get("hidden")
        if type(hidden) is not int or not 1 <= hidden <= 256:
            raise ValueError("Taille cachée invalide")
        ni, no = SPECS[data["game"]]
        if data.get("input") != ni or data.get("output") != no:
            raise ValueError("Dimensions de modèle invalides")
        model = cls(data["game"], hidden)
        for name, shape in (("w1", (ni, hidden)), ("b1", (hidden,)), ("w2", (hidden, no)), ("b2", (no,))):
            a = np.asarray(data.get(name), dtype=np.float32)
            if a.size != int(np.prod(shape)) or not np.isfinite(a).all():
                raise ValueError(f"Poids invalides : {name}")
            setattr(model, name, a.reshape(shape))
        steps = data.get("steps", 0)
        if type(steps) is not int or steps < 0:
            raise ValueError("Compteur d'apprentissage invalide")
        model.steps = steps
        core = data.get("core", {})
        if core.get("id") != "logic-core-v1" or type(core.get("steps")) is not int or core["steps"] < 0:
            raise ValueError("Module partagé invalide")
        for name, shape in (("w", (hidden, hidden)), ("b", (hidden,))):
            a = np.asarray(core.get(name), dtype=np.float32)
            if a.size != int(np.prod(shape)) or not np.isfinite(a).all():
                raise ValueError("Poids du module partagé invalides")
            model.core[name] = a.reshape(shape)
        model.core["steps"] = core["steps"]
        return model

    @classmethod
    def load(cls, path):
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def demonstration_data(game, episodes=30, seed=0, max_steps=150, level=6):
    teacher = ReferenceAgent(level, seed=seed)
    x, y, masks = [], [], []
    for episode in range(episodes):
        options = {"scramble": 8+episode%10} if game == "sliding_puzzle" else None
        env = make_game(game, seed+episode, options)
        for _ in range(max_steps):
            obs, legal = env.observation(), env.legal_actions()
            action = teacher.choose(obs, legal).action
            x.append(encode(obs))
            y.append(action_index(game, action))
            mask = np.zeros(SPECS[game][1], dtype=bool)
            mask[[action_index(game, a) for a in legal]] = True
            masks.append(mask)
            env.step(action)
            if env.done:
                break
    return np.array(x), np.array(y), np.array(masks)


MODEL_DIR = Path(__file__).resolve().parents[1]/"web"/"models"


class NeuralSuite:
    """Six encodeurs/têtes, un seul objet core : transfert de gradient effectif."""
    def __init__(self, models):
        if not models:
            raise ValueError("Aucun modèle")
        self.models = models
        core = max(models.values(), key=lambda m: m.core["steps"]).core
        for model in models.values():
            if model.hidden != core["b"].size:
                raise ValueError("Modules partagés incompatibles")
            model.core = core
            model._adam = None
        self.core = core

    @classmethod
    def load(cls, directory=MODEL_DIR):
        return cls({game: NeuralPolicy.load(Path(directory)/f"{game}.json") for game in SPECS})

    def save(self, directory):
        for game, model in self.models.items():
            model.save(Path(directory)/f"{game}.json")

    def train(self, game, episodes=30, epochs=10, seed=0, level=4):
        if game not in self.models or type(episodes) is not int or not 1 <= episodes <= 10000 or type(epochs) is not int or not 1 <= epochs <= 1000:
            raise ValueError("Jeu, épisodes ou époques invalides")
        primary = demonstration_data(game, episodes, seed, level=level)
        # Au total, les cinq autres jeux représentent environ 25 % des exemples.
        replay = {}
        per_other = max(1, len(primary[0])//20)
        for name in self.models:
            if name != game:
                data = demonstration_data(name, max(1, episodes//10), seed+100000, max_steps=per_other, level=level)
                replay[name] = tuple(a[:per_other] for a in data)
        losses = []
        for _ in range(epochs):
            losses.extend(self.models[game].fit(*primary, epochs=1, lr=.001))
            for name, data in replay.items():
                self.models[name].fit(*data, epochs=1, lr=.0003)
        return {"game": game, "episodes": episodes, "epochs": epochs, "samples": len(primary[0]),
                "rehearsal_samples": sum(len(d[0]) for d in replay.values()),
                "losses": losses, "shared_steps": self.core["steps"]}


_MODELS = {}
_MODEL_CACHE_LOCK = threading.Lock()


class NeuralAgent:
    def __init__(self, level=10, style="balanced", seed=0, time_ms=None, planning=True):
        ReferenceAgent(level, style, seed, time_ms)
        self.level, self.style, self.seed = level, style, seed
        if type(seed) is not int:
            raise ValueError("seed doit être un entier")
        self.rng = np.random.default_rng(seed % (1 << 64))
        self._rng_lock = threading.Lock()
        self.time_ms = time_ms
        if type(planning) is not bool:
            raise ValueError("planning doit être un booléen")
        self.planning = planning

    def choose(self, obs, legal):
        started = time.monotonic()
        path = MODEL_DIR/f"{obs['game']}.json"
        if not path.is_file():
            raise ValueError("Poids absents ; lancer examples/bootstrap_models.py")
        stamp = path.stat().st_mtime_ns
        with _MODEL_CACHE_LOCK:
            cached = _MODELS.get(obs["game"])
            if cached is None or cached[0] != stamp:
                _MODELS[obs["game"]] = stamp, NeuralPolicy.load(path)
            model = _MODELS[obs["game"]][1]
        logits = model.logits(obs)
        # Chaque agent avance son propre générateur. Les modèles en cache sont
        # partagés en lecture seule, sans permutation d'un RNG global.
        with self._rng_lock:
            action = model.choose(obs, legal, self.level, self.style, logits=logits, rng=self.rng)
        plan_info = {}
        if self.planning:
            from .planner import plan
            action, plan_info = plan(obs, legal, model, self.level, action, self.time_ms, logits=logits)
            plan_info["optimal_scope"] = "remaining_from_current_state"
        return Decision(action, {"agent": "neural", "identity": agent_identity(obs["game"]), "method": "shared_mlp_policy", "level": self.level,
                                 "style": self.style, "time_ms": round((time.monotonic()-started)*1000, 3),
                                 "training_steps": model.steps, "shared_steps": model.core["steps"], **plan_info})
