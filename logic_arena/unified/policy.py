"""Joueur réseau seul (sans recherche) pour les juges : coup légal de plus grand logit."""
from __future__ import annotations

import numpy as np
import torch

from .encode import encode, legal_indices


class NetPolicy:
    def __init__(self, nets, device="cuda"):
        """`nets` : dict jeu → UnifiedNet (un même réseau peut servir plusieurs jeux)."""
        self.nets, self.device = nets, device
        for n in {id(n): n for n in nets.values()}.values():
            n.to(device).eval()

    @torch.no_grad()
    def logits_value(self, obs):
        planes, extra = encode(obs)
        net = self.nets[obs["game"]]
        lg, v = net(obs["game"], torch.from_numpy(planes[None]).float().to(self.device), torch.from_numpy(extra[None]).to(self.device))
        return lg[0].float().cpu().numpy(), float(v[0])

    def __call__(self, obs, legal):
        logits, _ = self.logits_value(obs)
        idx = legal_indices(obs, legal)
        return legal[int(np.argmax(logits[idx]))]
