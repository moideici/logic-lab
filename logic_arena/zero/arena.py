"""Duels de Garry Zéro contre des adversaires de Garry, avec les règles de Garry comme arbitre (le moteur vectorisé ne juge jamais seul)."""
from __future__ import annotations

import numpy as np

from ..agents import ReferenceAgent
from ..games import make_game
from .mcts import BatchedMCTS


class RandomOpponent:
    name = "aléatoire"

    def __init__(self, seed=0):
        self.rng = np.random.default_rng(seed)

    def choose(self, obs, legal):
        return legal[int(self.rng.integers(len(legal)))]


class TeacherOpponent:
    def __init__(self, level, time_ms=60, seed=0):
        self.name = f"professeur niveau {level}"
        self.agent = ReferenceAgent(level, seed=seed, time_ms=time_ms)

    def choose(self, obs, legal):
        return self.agent.choose(obs, legal).action


class GarryOpponent:
    def __init__(self, level=10, time_ms=100, seed=0):
        from ..neural import NeuralAgent
        self.name = f"Garry niveau {level}"
        self.agent = NeuralAgent(level=level, seed=seed, time_ms=time_ms)

    def choose(self, obs, legal):
        return self.agent.choose(obs, legal).action


def match(rules, net, make_opponent, games=40, sims=200, device="cpu", seed=1000, game_name="connect4", options=None):
    """`games` parties depuis le plateau vide, Zéro jouant alternativement premier et second. Score : victoire 1, nul 0,5, défaite 0.

    Les règles de Garry arbitrent : Zéro ne peut jouer que les coups que Garry juge légaux (superko compris). Au Go, la phase de comptage
    est acceptée par les deux camps sans retirer de pierres (surface de Tromp-Taylor, comme à l'entraînement).
    """
    mcts = BatchedMCTS(rules, net, device, sims=sims, seed=seed)
    envs = [make_game(game_name, seed + g, options) for g in range(games)]
    zero_is = [1 + g % 2 for g in range(games)]
    opponents = [make_opponent(seed + g) for g in range(games)]
    guard = 0
    while not all(e.done for e in envs) and guard < 400:
        guard += 1
        for e in envs:  # comptage du Go : on accepte tout de suite
            while not e.done and getattr(e, "go_state", None) and e.go_state["phase"] == "scoring":
                e.step({"accept": True})
        mine = [g for g, e in enumerate(envs) if not e.done and e.observation()["current_player"] == zero_is[g]]
        if mine:
            states = np.concatenate([rules.from_observation(envs[g].observation()) for g in mine])
            visits, _ = mcts.search(states, noise=False)
            for k, g in enumerate(mine):
                allowed = {rules.garry_index(a) for a in envs[g].legal_actions()} - {None}
                order = np.argsort(-visits[k], kind="stable")
                pick = next((int(i) for i in order if int(i) in allowed), None)
                if pick is None:
                    envs[g].step({"resign": True} if game_name == "go" else envs[g].legal_actions()[0])
                else:
                    envs[g].step(rules.action_to_garry(pick))
        for g, e in enumerate(envs):
            if not e.done and e.observation()["current_player"] != zero_is[g]:
                obs, legal = e.observation(), e.legal_actions()
                e.step(opponents[g].choose(obs, legal))
    wins = draws = losses = 0
    for g, e in enumerate(envs):
        if e.winner in (None, 0):
            draws += 1
        elif e.winner == zero_is[g]:
            wins += 1
        else:
            losses += 1
    return {"adversaire": opponents[0].name, "parties": games, "victoires": wins, "nuls": draws, "defaites": losses, "score": round((wins + 0.5 * draws) / games, 3)}
