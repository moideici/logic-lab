"""Q-learning tabulaire, auto-jeu et évaluation sur des graines distinctes."""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import random
import tempfile

from .agents import ReferenceAgent
from .games import make_game


def action_key(action):
    return json.dumps(action, sort_keys=True, separators=(",", ":"))


def state_key(obs):
    # Les indices immuables du sudoku font partie de l'état pour l'action undo.
    data = {k: obs[k] for k in ("game", "board", "current_player", "givens", "history") if k in obs}
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


class TabularAgent:
    def __init__(self, game, seed=0, q=None):
        make_game(game, seed)  # validate identifier
        self.game, self.q = game, q or {}
        self.rng = random.Random(seed)

    def choose(self, obs, legal, epsilon=0.):
        if obs["game"] != self.game or not legal:
            raise ValueError("Modèle incompatible ou partie terminée")
        if self.rng.random() < epsilon:
            return self.rng.choice(legal)
        values = self.q.get(state_key(obs), {})
        best = max(values.get(action_key(a), 0.) for a in legal)
        return self.rng.choice([a for a in legal if values.get(action_key(a), 0.) == best])

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {"format": "logic-arena-q-v1", "game": self.game, "q": self.q}
        with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False, encoding="utf-8") as f:
            temporary = f.name
            json.dump(data, f, allow_nan=False)
        os.replace(temporary, path)

    @classmethod
    def load(cls, path, seed=0):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if data.get("format") != "logic-arena-q-v1" or not isinstance(data.get("q"), dict):
            raise ValueError("Format de modèle invalide")
        if any(not isinstance(row, dict) or any(type(v) not in (float, int) or not math.isfinite(v) for v in row.values()) for row in data["q"].values()):
            raise ValueError("Valeurs Q invalides")
        return cls(data["game"], seed, data["q"])


def train(game="tictactoe", episodes=1000, seed=0, max_steps=200, alpha=.2, gamma=.98, model=None, options=None):
    if type(episodes) is not int or not 1 <= episodes <= 1000000:
        raise ValueError("episodes doit être entre 1 et 1000000")
    if type(max_steps) is not int or not 1 <= max_steps <= 10000:
        raise ValueError("max_steps doit être entre 1 et 10000")
    if not 0 < alpha <= 1 or not 0 <= gamma <= 1:
        raise ValueError("alpha doit être dans ]0,1] et gamma dans [0,1]")
    agent = model or TabularAgent(game, seed)
    if agent.game != game:
        raise ValueError("Le modèle ne correspond pas au jeu")
    stats = {"episodes": episodes, "completed": 0, "truncated": 0, "wins": 0, "draws": 0, "mean_reward": 0.}
    rewards = 0.
    for episode in range(episodes):
        env = make_game(game, seed+episode, options)
        epsilon = .05 + .95*(1-episode/max(1, episodes-1))
        for step in range(max_steps):
            obs, legal = env.observation(), env.legal_actions()
            action = agent.choose(obs, legal, epsilon)
            reward = env.step(action)
            rewards += reward
            next_obs, next_legal = env.observation(), env.legal_actions()
            values = agent.q.setdefault(state_key(obs), {})
            next_values = agent.q.get(state_key(next_obs), {})
            future = 0. if env.done or step+1 == max_steps else max((next_values.get(action_key(a), 0.) for a in next_legal), default=0.)
            sign = -1 if env.players == 2 else 1
            old = values.get(action_key(action), 0.)
            values[action_key(action)] = old + alpha*(reward+sign*gamma*future-old)
            if env.done:
                break
        stats["completed" if env.done else "truncated"] += 1
        stats["wins"] += int(env.winner in (1, 2))
        stats["draws"] += int(env.players == 2 and env.winner == 0)
    stats["mean_reward"] = rewards/episodes
    stats["states"] = len(agent.q)
    stats["note"] = "En auto-jeu à deux joueurs, wins compte les parties décisives, pas le taux de victoire d'un joueur."
    return agent, stats


def evaluate(model, episodes=100, seed=1000000, max_steps=500, opponent_level=1, options=None):
    if type(episodes) is not int or not 1 <= episodes <= 1000000:
        raise ValueError("episodes invalide")
    if type(max_steps) is not int or not 1 <= max_steps <= 10000:
        raise ValueError("max_steps invalide")
    opponent = ReferenceAgent(opponent_level, seed=seed)
    stats = {"episodes": episodes, "wins": 0, "draws": 0, "losses": 0, "truncated": 0, "mean_score": 0.}
    for i in range(episodes):
        env = make_game(model.game, seed+i, options)
        model_player = 1+i%2 if env.players == 2 else 1
        for _ in range(max_steps):
            obs, legal = env.observation(), env.legal_actions()
            action = model.choose(obs, legal) if env.current_player == model_player else opponent.choose(obs, legal).action
            env.step(action)
            if env.done:
                break
        if not env.done:
            stats["truncated"] += 1
        elif env.winner == model_player:
            stats["wins"] += 1
        elif env.players == 2 and env.winner == 0:
            stats["draws"] += 1
        else:
            stats["losses"] += 1
        stats["mean_score"] += env.score/episodes
    return stats
