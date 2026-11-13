"""Joueurs de l'arène autres que Garry : Zéro (Puissance 4, auto-apprentissage) et Garry Optimus (réseau multi-jeux, sans recherche).
Chargés à la demande (PyTorch). Utilisés par la route POST /api/player du serveur ; les poids sont locaux (training-lab/models/)."""
from __future__ import annotations

from pathlib import Path

import numpy as np

MODELS = Path(__file__).resolve().parents[1] / "training-lab" / "models"
_cache: dict = {}

GAMES = {"zero": ["connect4"], "optimus": ["tictactoe", "connect4", "hex", "gomoku"]}
DIRECTIONS = ("up", "down", "left", "right")


def available():
    """Joueurs réellement disponibles sur cette machine (poids présents), avec leurs jeux."""
    out = {}
    if (MODELS / "zero-c4" / "dernier.pt").exists():
        out["zero"] = {"games": GAMES["zero"], "label": "Garry Zéro"}
    games = list(GAMES["optimus"]) if _optimus_dir() else []
    if _w2048():
        games.append("2048")
    if games:
        out["optimus"] = {"games": games, "label": "Garry Optimus", "weights": (_optimus_dir().parent.name + "/" + _optimus_dir().name) if _optimus_dir() else "2048 seul"}
    return out


def _w2048():
    for name in ("best.pt", "last.pt"):
        path = MODELS / "unified" / "optimus-2048" / name
        if path.exists():
            return path
    return None


def _optimus_dir():
    for d in (MODELS / "unified" / "optimus" / "multi-0", MODELS / "unified" / "p1" / "multi-0"):
        if d.is_dir() and any(d.glob("*.pt")):
            return d
    return None


def _zero():
    if "zero" not in _cache:
        import torch
        from .zero.mcts import BatchedMCTS
        from .zero.net import PolicyValueNet
        from .zero.rules import Connect4Rules
        rules = Connect4Rules()
        blob = torch.load(MODELS / "zero-c4" / "dernier.pt", map_location="cpu", weights_only=True)
        net = PolicyValueNet(rules.planes_shape, rules.n_actions, blob.get("channels", 64), blob.get("blocks", 4))
        net.load_state_dict(blob["net"])
        net.eval()
        _cache["zero"] = (rules, BatchedMCTS(rules, net, "cpu", sims=200, seed=1))
    return _cache["zero"]


def _optimus():
    if "optimus" not in _cache:
        import torch
        from .unified.model import UnifiedNet
        from .unified.policy import NetPolicy
        nets = {}
        for path in sorted(_optimus_dir().glob("*.pt")):
            blob = torch.load(path, map_location="cpu", weights_only=True)
            net = UnifiedNet(blob["games"], blob["channels"], blob["blocks"])
            net.load_state_dict(blob["state"])
            for g in blob["games"]:
                nets[g] = net
        _cache["optimus"] = NetPolicy(nets, device="cuda" if torch.cuda.is_available() else "cpu")
    return _cache["optimus"]


def _optimus_2048():
    if "o2048" not in _cache:
        import torch
        from .unified.net2048 import Net2048
        blob = torch.load(_w2048(), map_location="cpu", weights_only=True)
        net = Net2048(blob.get("channels", 128), blob.get("blocks", 6))
        net.load_state_dict(blob["net"])
        net.eval()
        _cache["o2048"] = net
    return _cache["o2048"]


def _choose_2048(obs, legal):
    import torch
    from . import t2048
    net = _optimus_2048()
    e = torch.from_numpy(t2048.exponents([t2048.pack(obs["board"])]))
    with torch.no_grad():
        logits = net(e)[0].numpy()
    best = max(legal, key=lambda a: logits[DIRECTIONS.index(a["direction"])])
    return best


def choose(player, obs, legal):
    game = obs.get("game")
    if player not in GAMES or game not in (available().get(player, {}).get("games") or []):
        raise ValueError(f"{player} ne joue pas à {game}")
    if player == "optimus" and game == "2048":
        return _choose_2048(obs, legal)
    if not legal:
        raise ValueError("aucun coup légal")
    if player == "zero":
        rules, mcts = _zero()
        visits, _ = mcts.search(rules.from_observation(obs), noise=False)
        allowed = {a["column"] for a in legal}
        col = next(int(i) for i in np.argsort(-visits[0], kind="stable") if int(i) in allowed)
        return next(a for a in legal if a["column"] == col)
    return _optimus()(obs, legal)
