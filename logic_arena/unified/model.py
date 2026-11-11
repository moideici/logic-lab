"""Réseau unifié : une entrée propre à chaque jeu, un tronc résiduel partagé, une tête de politique par case partagée (jeux de pose),
une tête spéciale par jeu, une tête de dames, une tête de valeur partagée puis un petit étage par jeu."""
from __future__ import annotations

import torch
from torch import nn

from .spec import CANVAS, CELLS, EXTRA, GAMES, N_ACTIONS, PLACEMENT_ACTIONS, PLANES

PLACEMENT = ("tictactoe", "connect4", "hex", "gomoku")


class ResBlock(nn.Module):
    def __init__(self, c):
        super().__init__()
        self.c1, self.b1 = nn.Conv2d(c, c, 3, padding=1, bias=False), nn.BatchNorm2d(c)
        self.c2, self.b2 = nn.Conv2d(c, c, 3, padding=1, bias=False), nn.BatchNorm2d(c)

    def forward(self, x):
        h = torch.relu(self.b1(self.c1(x)))
        return torch.relu(x + self.b2(self.c2(h)))


class UnifiedNet(nn.Module):
    def __init__(self, games=GAMES, channels=64, blocks=6):
        super().__init__()
        self.games, self.channels = tuple(games), channels
        cin = PLANES + EXTRA
        self.stems = nn.ModuleDict({g: nn.Sequential(nn.Conv2d(cin, channels, 3, padding=1, bias=False), nn.BatchNorm2d(channels), nn.ReLU()) for g in self.games})
        self.body = nn.Sequential(*[ResBlock(channels) for _ in range(blocks)])
        pose = [g for g in self.games if g in PLACEMENT]
        self.cell_head = nn.Sequential(nn.Conv2d(channels, channels // 2, 1), nn.ReLU(), nn.Conv2d(channels // 2, 1, 1)) if pose else None
        self.special = nn.ModuleDict({g: nn.Linear(channels, 3) for g in pose})
        if "dames" in self.games:
            self.dames_head = nn.Sequential(nn.Conv2d(channels, 4, 1), nn.ReLU(), nn.Flatten(), nn.Linear(4 * CELLS, N_ACTIONS["dames"]))
        self.v_conv = nn.Sequential(nn.Conv2d(channels, 4, 1), nn.ReLU())
        self.v_fc = nn.ModuleDict({g: nn.Sequential(nn.Linear(4 * CELLS, 64), nn.ReLU(), nn.Linear(64, 1), nn.Tanh()) for g in self.games})

    def _x(self, planes, extra):
        return torch.cat([planes, extra[:, :, None, None].expand(-1, -1, CANVAS, CANVAS)], 1)

    def forward_multi(self, inputs):
        """inputs : dict jeu → (planes (B,8,15,15), extra (B,8)). Les jeux passent ensemble dans le tronc (statistiques de normalisation communes).
        Renvoie dict jeu → (logits (B, A_jeu), value (B,))."""
        games = list(inputs)
        feats = torch.cat([self.stems[g](self._x(*inputs[g])) for g in games], 0)
        z = self.body(feats)
        out, start = {}, 0
        for g in games:
            n = len(inputs[g][0])
            zg = z[start:start + n]
            start += n
            if g == "dames":
                logits = self.dames_head(zg)
            else:
                logits = torch.cat([self.cell_head(zg).flatten(1), self.special[g](zg.mean((2, 3)))], 1)
            out[g] = (logits, self.v_fc[g](self.v_conv(zg).flatten(1)).squeeze(1))
        return out

    def forward(self, game, planes, extra):
        return self.forward_multi({game: (planes, extra)})[game]

    def parameter_count(self):
        return sum(p.numel() for p in self.parameters())
