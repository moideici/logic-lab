"""Entraînement du Lab (PyTorch) : réseau à deux couches cachées, croissance et élagage de neurones pendant l'apprentissage (Graine).

Même structure que Garry (encodeur → cœur → sortie, tanh), entraîné par imitation d'un professeur (`ReferenceAgent`) sur un seul jeu.
Ce module n'écrit jamais dans `web/models` : il produit des réseaux de laboratoire que le Lab affiche via `core.Net`.
"""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import torch
from torch import nn

from .agents import ReferenceAgent
from .core import Dense, Net
from .games import make_game
from .neural import SPECS, action_index, encode

CACHE = Path(__file__).resolve().parents[1] / "training-lab" / "data"
TEACHERS = {"tictactoe": (10, None), "nim": (10, None), "connect4": (8, 30)}  # (niveau, délai ms)
SPLITS = {"train": 1000, "val": 50000, "test": 90000}  # graines de départ des parties


# ------------------------------------------------------------------ données ----
def build_dataset(game, split, episodes, level=None, time_ms=None, cache=True, explore=0.35):
    """Positions variées étiquetées par le professeur : (x, cible, masque des coups légaux). Mises en cache.

    La partie avance avec un coup aléatoire de probabilité `explore` (sinon le coup du professeur) ; l'étiquette est toujours le coup du
    professeur. Sans cette exploration, un professeur parfait rejoue la même partie et le jeu de données ne contient que quelques positions.
    """
    lvl, ms = TEACHERS[game]
    level = lvl if level is None else level
    time_ms = ms if time_ms is None else time_ms
    path = CACHE / f"{game}-{split}-{episodes}-L{level}-{time_ms}-e{int(explore * 100)}.npz"
    if cache and path.exists():
        d = np.load(path)
        return d["x"], d["y"], d["mask"]
    teacher = ReferenceAgent(level, seed=SPLITS[split], time_ms=time_ms)
    x, y, masks = [], [], []
    n_out = SPECS[game][1]
    for ep in range(episodes):
        env = make_game(game, SPLITS[split] + ep)
        rng = np.random.default_rng(SPLITS[split] + ep)
        while not env.done:
            obs, legal = env.observation(), env.legal_actions()
            action = teacher.choose(obs, legal).action
            x.append(encode(obs))
            y.append(action_index(game, action))
            m = np.zeros(n_out, dtype=bool)
            m[[action_index(game, a) for a in legal]] = True
            masks.append(m)
            env.step(legal[int(rng.integers(len(legal)))] if rng.random() < explore else action)
    x, y, mask = np.array(x, dtype=np.float32), np.array(y, dtype=np.int64), np.array(masks)
    if cache:
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(path, x=x, y=y, mask=mask)
    return x, y, mask


# ------------------------------------------------------------------ réseau ----
class TorchMLP(nn.Module):
    def __init__(self, n_in, n_out, h1, h2, seed=0):
        super().__init__()
        g = torch.Generator().manual_seed(seed)
        self.encodeur, self.coeur, self.sortie = nn.Linear(n_in, h1), nn.Linear(h1, h2), nn.Linear(h2, n_out)
        for layer in (self.encodeur, self.coeur, self.sortie):
            nn.init.xavier_normal_(layer.weight, generator=g)
            nn.init.zeros_(layer.bias)

    def forward(self, x, mute=None, trace=None):
        """`mute` : {"encodeur": indices, "coeur": indices} neurones forcés à 0."""
        h1 = torch.tanh(self.encodeur(x))
        if mute and mute.get("encodeur"):
            h1 = h1.clone()
            h1[:, list(mute["encodeur"])] = 0
        h2 = torch.tanh(self.coeur(h1))
        if mute and mute.get("coeur"):
            h2 = h2.clone()
            h2[:, list(mute["coeur"])] = 0
        if trace is not None:
            trace["encodeur"], trace["coeur"] = h1, h2
        return self.sortie(h2)

    @property
    def sizes(self):
        return self.encodeur.out_features, self.coeur.out_features

    def parameter_count(self):
        return sum(p.numel() for p in self.parameters())

    @torch.no_grad()
    def grow(self, layer, count, scale=0.05, seed=0):
        """Ajoute `count` neurones : poids sortants nuls, donc la fonction du réseau ne change pas."""
        g = torch.Generator().manual_seed(seed)
        src, nxt = (self.encodeur, self.coeur) if layer == "encodeur" else (self.coeur, self.sortie)
        fresh = torch.randn(count, src.in_features, generator=g) * scale
        src.weight = nn.Parameter(torch.cat([src.weight, fresh]))
        src.bias = nn.Parameter(torch.cat([src.bias, torch.zeros(count)]))
        src.out_features += count
        nxt.weight = nn.Parameter(torch.cat([nxt.weight, torch.zeros(nxt.out_features, count)], dim=1))
        nxt.in_features += count

    @torch.no_grad()
    def prune(self, layer, indices):
        """Supprime des neurones (lignes de la couche, colonnes de la suivante)."""
        src, nxt = (self.encodeur, self.coeur) if layer == "encodeur" else (self.coeur, self.sortie)
        drop = set(int(i) for i in indices)
        keep = [i for i in range(src.out_features) if i not in drop]
        if len(keep) < 1:
            raise ValueError("couche vidée")
        src.weight = nn.Parameter(src.weight[keep].clone())
        src.bias = nn.Parameter(src.bias[keep].clone())
        src.out_features = len(keep)
        nxt.weight = nn.Parameter(nxt.weight[:, keep].clone())
        nxt.in_features = len(keep)

    def to_core(self):
        """Copie numpy au format `core.Net` (poids transposés), pour l'affichage et les tests de parité."""
        def dense(name, lin, act):
            return Dense(name, lin.weight.detach().cpu().numpy().T.astype(np.float32).copy(), lin.bias.detach().cpu().numpy().astype(np.float32).copy(), act)
        return Net([dense("encodeur", self.encodeur, "tanh"), dense("coeur", self.coeur, "tanh"), dense("sortie", self.sortie, "linear")])


def masked_loss(logits, y, mask):
    logits = logits.masked_fill(~mask, -1e9)
    return nn.functional.cross_entropy(logits, y)


@torch.no_grad()
def evaluate(model, data, mute=None):
    x, y, mask = [torch.as_tensor(a) for a in data]
    logits = model(x, mute=mute).masked_fill(~mask, -1e9)
    return float(nn.functional.cross_entropy(logits, y)), float((logits.argmax(1) == y).float().mean())


@torch.no_grad()
def neuron_importance(model, data):
    """Hausse de la perte de validation si on éteint chaque neurone (plus c'est bas, plus il est inutile)."""
    base, _ = evaluate(model, data)
    out = {}
    for layer, n in zip(("encodeur", "coeur"), model.sizes):
        out[layer] = [evaluate(model, data, mute={layer: [i]})[0] - base for i in range(n)]
    return out


# ----------------------------------------------------------- force de jeu ----
@torch.no_grad()
def strength(model, game, level=4, games=20, seed=777):
    """Score (victoire 1, nul 0,5) du réseau contre le professeur de niveau donné, la moitié des parties dans chaque camp."""
    model.eval()
    teacher = ReferenceAgent(level, seed=seed, time_ms=20)
    score = 0.0
    for g in range(games):
        env = make_game(game, seed + g)
        net_player = 1 + g % 2  # joueur 1 ou 2
        guard = 0
        while not env.done and guard < 200:
            guard += 1
            obs, legal = env.observation(), env.legal_actions()
            if obs.get("current_player", 1) == net_player:
                logits = model(torch.as_tensor(encode(obs))[None])[0].numpy()
                action = max(legal, key=lambda a: logits[action_index(game, a)])
            else:
                action = teacher.choose(obs, legal).action
            env.step(action)
        winner = getattr(env, "winner", None)
        score += 0.5 if winner in (None, 0) else float(winner == net_player)
    return score / games


# ------------------------------------------------------------- entraînement ----
def train(model, train_data, val_data, steps=2000, batch=128, lr=3e-3, seed=0, graine=None, on_event=None, stop=None, eval_every=100):
    """Entraîne `model`. `graine` : dict {grow_by, plateau, patience, prune_every, prune_tol, max, min} active la croissance et l'élagage."""
    rng = np.random.default_rng(seed)
    x, y, mask = [torch.as_tensor(a) for a in train_data]
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    history, events = [], []
    best = float("inf")
    since_growth = 0
    last_growth_val = None
    started = time.time()

    def emit(kind, **kw):
        ev = {"type": kind, "step": step, **kw}
        events.append(ev) if kind != "point" else history.append(ev)
        if on_event:
            on_event(ev)

    for step in range(1, steps + 1):
        if stop is not None and stop():
            break
        model.train()
        idx = torch.as_tensor(rng.integers(0, len(x), size=batch))
        loss = masked_loss(model(x[idx]), y[idx], mask[idx])
        opt.zero_grad()
        loss.backward()
        opt.step()
        if step % eval_every == 0 or step == steps:
            v_loss, v_acc = evaluate(model, val_data)
            best = min(best, v_loss)
            emit("point", loss=float(loss), val_loss=v_loss, val_acc=v_acc, h1=model.sizes[0], h2=model.sizes[1], parametres=model.parameter_count(),
                 secondes=round(time.time() - started, 1))
            if graine:
                since_growth += 1
                # croissance : la perte de validation n'a plus baissé assez depuis la dernière évaluation de référence
                if last_growth_val is None:
                    last_growth_val = v_loss
                elif since_growth >= graine["patience"]:
                    gain = (last_growth_val - v_loss) / max(last_growth_val, 1e-9)
                    if gain < graine["plateau"] and max(model.sizes) < graine["max"]:
                        for layer in ("encodeur", "coeur"):
                            model.grow(layer, graine["grow_by"], seed=step)
                        opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
                        emit("croissance", h1=model.sizes[0], h2=model.sizes[1], gain_relatif=round(gain, 4))
                    last_growth_val, since_growth = v_loss, 0
                # élagage : neurones dont l'extinction ne dégrade presque pas la perte de validation
                if graine.get("prune_every") and step % graine["prune_every"] == 0 and step >= graine.get("prune_start", 0) * steps:
                    imp = neuron_importance(model, val_data)
                    removed = {}
                    for layer, n in zip(("encodeur", "coeur"), model.sizes):
                        order = np.argsort(imp[layer])
                        limit = max(0, min(int(n * 0.25), n - graine.get("min", 2)))
                        tol = graine["prune_rel"] * v_loss if graine.get("prune_rel") else graine["prune_tol"]
                        drop = [int(i) for i in order[:limit] if imp[layer][int(i)] < tol]
                        if drop:
                            model.prune(layer, drop)
                            removed[layer] = len(drop)
                    if removed:
                        opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
                        emit("elagage", h1=model.sizes[0], h2=model.sizes[1], supprimes=removed)
    return {"historique": history, "evenements": events}


# ------------------------------------------------- règles de Graine (partagées) ----
VARIANTES = {
    "A": {"nom": "Graine A (prudente)", "grow_by": 2, "plateau": 0.03, "patience": 2, "prune_every": 400, "prune_tol": 0.001, "max": 64, "min": 2},
    "B": {"nom": "Graine B (croît vite, élague à la fin)", "grow_by": 2, "plateau": 0.06, "patience": 1, "prune_every": 200, "prune_rel": 0.01, "prune_start": 0.6, "max": 64, "min": 2},
    "C": {"nom": "Graine C (croît seule)", "grow_by": 2, "plateau": 0.06, "patience": 1, "max": 64, "min": 2},
}
