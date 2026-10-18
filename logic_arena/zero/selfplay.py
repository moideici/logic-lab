"""Auto-apprentissage : parties contre soi-même guidées par le MCTS, exemples (position, visites, résultat), entraînement du réseau."""
from __future__ import annotations

import time
from collections import deque

import numpy as np
import torch

from .mcts import BatchedMCTS


class Replay:
    def __init__(self, capacity):
        self.x, self.pi, self.z = deque(maxlen=capacity), deque(maxlen=capacity), deque(maxlen=capacity)

    def add(self, x, pi, z):
        self.x.extend(x), self.pi.extend(pi), self.z.extend(z)

    def __len__(self):
        return len(self.x)

    def sample(self, rules, batch, rng):
        idx = rng.integers(0, len(self.x), size=batch)
        x = np.stack([self.x[i] for i in idx])
        pi = np.stack([self.pi[i] for i in idx])
        z = np.array([self.z[i] for i in idx], dtype=np.float32)
        flip = rng.random(batch) < 0.5
        if flip.any() and hasattr(rules, "mirror"):
            for k in np.flatnonzero(flip):
                x[k], pi[k] = rules.mirror(x[k], pi[k])
        return x, pi, z


def self_play(rules, net, device, games=128, sims=100, temp_moves=10, seed=0, c_puct=1.5, max_plies=None):
    """Joue `games` parties en parallèle jusqu'à leur fin. Retourne (positions x, cibles pi, cibles z, statistiques)."""
    mcts = BatchedMCTS(rules, net, device, sims=sims, c_puct=c_puct, seed=seed)
    rng = np.random.default_rng(seed + 1)
    states = rules.initial(games)
    histories = [[] for _ in range(games)]
    alive = np.ones(games, dtype=bool)
    X, PI, Z = [], [], []
    plies, first_player_wins, draws, lengths = 0, 0, 0, []
    cap = max_plies or rules.max_moves
    while alive.any():
        idx = np.flatnonzero(alive)
        visits, _ = mcts.search(states[idx], noise=True)
        enc = rules.encode(states[idx])
        actions = np.zeros(len(idx), dtype=np.int64)
        for k, g in enumerate(idx):
            v = visits[k].astype(np.float64)
            pi = v / v.sum()
            histories[g].append((enc[k], pi.astype(np.float32)))
            if len(histories[g]) <= temp_moves:
                actions[k] = rng.choice(len(pi), p=pi)
            else:
                actions[k] = int(v.argmax())
        new_states, terminal, value = rules.step(states[idx], actions)
        states[idx] = new_states
        plies += 1
        for k, g in enumerate(idx):
            over = bool(terminal[k]) or len(histories[g]) >= cap
            if not over:
                continue
            alive[g] = False
            outcome = float(value[k]) if terminal[k] else 0.0   # du point de vue du joueur maintenant au trait
            T = len(histories[g])
            for t, (x, pi) in enumerate(histories[g]):
                # le joueur qui jouait la position t est celui qui vient de jouer si (T-1-t) est pair : sa valeur est −outcome
                z = -outcome if (T - 1 - t) % 2 == 0 else outcome
                X.append(x), PI.append(pi), Z.append(z)
            lengths.append(T)
            if outcome == 0.0:
                draws += 1
            elif T % 2 == 1:
                first_player_wins += 1
    stats = {"parties": games, "nuls": draws, "victoires_du_premier": first_player_wins, "longueur_moyenne": round(float(np.mean(lengths)), 1)}
    return np.stack(X), np.stack(PI), np.array(Z, dtype=np.float32), stats


def train_steps(net, optimizer, replay, rules, device, steps, batch, rng):
    net.train()
    losses = []
    for _ in range(steps):
        x, pi, z = replay.sample(rules, batch, rng)
        x, pi, z = torch.as_tensor(x, device=device), torch.as_tensor(pi, device=device), torch.as_tensor(z, device=device)
        logits, value = net(x)
        loss_p = -(pi * torch.log_softmax(logits, dim=1)).sum(1).mean()
        loss_v = torch.nn.functional.mse_loss(value, z)
        loss = loss_p + loss_v
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        losses.append((float(loss_p), float(loss_v)))
    return np.mean(losses, axis=0)
