"""Réseau politique-valeur : petit réseau convolutif résiduel, commun à tous les jeux de plateau de Garry Zéro."""
from __future__ import annotations

import torch
from torch import nn


class ResBlock(nn.Module):
    def __init__(self, c):
        super().__init__()
        self.c1, self.b1 = nn.Conv2d(c, c, 3, padding=1, bias=False), nn.BatchNorm2d(c)
        self.c2, self.b2 = nn.Conv2d(c, c, 3, padding=1, bias=False), nn.BatchNorm2d(c)

    def forward(self, x):
        h = torch.relu(self.b1(self.c1(x)))
        return torch.relu(x + self.b2(self.c2(h)))


class PolicyValueNet(nn.Module):
    def __init__(self, planes_shape, n_actions, channels=64, blocks=4):
        super().__init__()
        cin, h, w = planes_shape
        self.stem = nn.Sequential(nn.Conv2d(cin, channels, 3, padding=1, bias=False), nn.BatchNorm2d(channels), nn.ReLU())
        self.body = nn.Sequential(*[ResBlock(channels) for _ in range(blocks)])
        self.p_conv = nn.Sequential(nn.Conv2d(channels, 4, 1, bias=False), nn.BatchNorm2d(4), nn.ReLU())
        self.p_fc = nn.Linear(4 * h * w, n_actions)
        self.v_conv = nn.Sequential(nn.Conv2d(channels, 2, 1, bias=False), nn.BatchNorm2d(2), nn.ReLU())
        self.v_fc = nn.Sequential(nn.Linear(2 * h * w, 64), nn.ReLU(), nn.Linear(64, 1), nn.Tanh())

    def forward(self, x):
        z = self.body(self.stem(x))
        policy = self.p_fc(self.p_conv(z).flatten(1))
        value = self.v_fc(self.v_conv(z).flatten(1)).squeeze(1)
        return policy, value

    def parameter_count(self):
        return sum(p.numel() for p in self.parameters())
