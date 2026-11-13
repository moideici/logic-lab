"""Réseau 2048 de Garry Optimus : 17 plans (un par exposant de tuile) sur la grille 4×4, tronc résiduel, 4 logits (haut, bas, gauche, droite).
Identique à la classe de training-lab/t2048_train.py (mêmes noms de paramètres : les points de contrôle sont interchangeables)."""
from __future__ import annotations

import torch.nn as nn
import torch.nn.functional as F


class Block(nn.Module):
    def __init__(self, ch):
        super().__init__()
        self.c1, self.b1 = nn.Conv2d(ch, ch, 3, padding=1, bias=False), nn.BatchNorm2d(ch)
        self.c2, self.b2 = nn.Conv2d(ch, ch, 3, padding=1, bias=False), nn.BatchNorm2d(ch)

    def forward(self, x):
        return F.relu(x + self.b2(self.c2(F.relu(self.b1(self.c1(x))))))


class Net2048(nn.Module):
    def __init__(self, ch=128, blocks=6):
        super().__init__()
        self.ch, self.blocks = ch, blocks
        self.inp = nn.Sequential(nn.Conv2d(17, ch, 3, padding=1, bias=False), nn.BatchNorm2d(ch), nn.ReLU())
        self.trunk = nn.Sequential(*[Block(ch) for _ in range(blocks)])
        self.head = nn.Sequential(nn.Flatten(), nn.Linear(ch * 16, 256), nn.ReLU(), nn.Linear(256, 4))

    def forward(self, e):
        x = F.one_hot(e.long().clamp(max=16), 17).permute(0, 3, 1, 2).float()
        return self.head(self.trunk(self.inp(x)))

    def parameter_count(self):
        return sum(p.numel() for p in self.parameters())
