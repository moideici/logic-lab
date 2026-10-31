"""Transformeur universel de Garry : lit les jetons d'une vue et note chacun des coups légaux (le jeu n'apparaît nulle part dans l'architecture).

Les coups ne se regardent pas entre eux : chaque coup voit la vue et ses propres jetons. Noter 64 coups d'un coup ou 8 fois 8 donne les mêmes scores.
Sorties : un score par coup, et une valeur de position (de -1 à 1) pour le joueur qui a le trait.
"""
from __future__ import annotations

import torch
from torch import nn

from . import tokens as tk


class UniversalPlayer(nn.Module):
    def __init__(self, d=128, layers=4, heads=4, ff=256, dropout=0.0):
        super().__init__()
        self.d, self.heads = d, heads
        self.e_key = nn.Embedding(tk.KEY_BUCKETS, d)
        self.e_num = nn.Embedding(tk.NUM, d)       # partagé : indices de tableau, valeurs entières
        self.e_num2 = nn.Embedding(tk.NUM, d)      # second indice
        self.e_str = nn.Embedding(tk.STR_BUCKETS, d)
        self.e_type = nn.Embedding(8, d)
        self.e_seg = nn.Embedding(3, d)
        self.f_proj = nn.Linear(1, d)
        layer = nn.TransformerEncoderLayer(d, heads, ff, dropout, batch_first=True, norm_first=True, activation="gelu")
        self.encoder = nn.TransformerEncoder(layer, layers, enable_nested_tensor=False)
        self.norm = nn.LayerNorm(d)
        self.score = nn.Sequential(nn.Linear(2 * d, d), nn.GELU(), nn.Linear(d, 1))
        self.value = nn.Sequential(nn.Linear(d, d), nn.GELU(), nn.Linear(d, 1), nn.Tanh())

    def embed(self, ints, floats):
        key, i1, i2, vt, val, seg = (ints[..., k] for k in range(6))
        is_str = (vt == tk.T_STR).unsqueeze(-1)
        v = torch.where(is_str, self.e_str(val.clamp(max=tk.STR_BUCKETS - 1)), self.e_num(val.clamp(max=tk.NUM - 1)))
        return self.e_key(key) + self.e_num(i1) + self.e_num2(i2) + self.e_type(vt) + v + self.e_seg(seg) + self.f_proj(floats.unsqueeze(-1))

    def attention_mask(self, ints, mask):
        seg, slot = ints[..., 5], ints[..., 6]
        B, L = seg.shape
        shared = (seg != tk.SEG_ACTION)  # vue et méta : visibles de tous
        same_action = (seg.unsqueeze(2) == tk.SEG_ACTION) & (slot.unsqueeze(2) == slot.unsqueeze(1)) & (seg.unsqueeze(1) == tk.SEG_ACTION)
        view_query = (seg.unsqueeze(2) != tk.SEG_ACTION) & (seg.unsqueeze(1) != tk.SEG_ACTION)
        action_query = (seg.unsqueeze(2) == tk.SEG_ACTION) & shared.unsqueeze(1)
        allowed = (view_query | action_query | same_action) & mask.unsqueeze(1)
        allowed = allowed | torch.eye(L, dtype=torch.bool, device=ints.device).unsqueeze(0)  # les jetons de remplissage se voient eux-mêmes
        return (~allowed).repeat_interleave(self.heads, dim=0)

    def forward(self, batch, max_actions=tk.MAX_ACTIONS):
        ints, floats, mask = batch["ints"], batch["floats"], batch["mask"]
        h = self.encoder(self.embed(ints, floats), mask=self.attention_mask(ints, mask))
        h = self.norm(h)
        seg, slot = ints[..., 5], ints[..., 6]
        view_w = ((seg != tk.SEG_ACTION) & mask).float().unsqueeze(-1)
        summary = (h * view_w).sum(1) / view_w.sum(1).clamp(min=1)
        B, L, d = h.shape
        onehot = ((seg == tk.SEG_ACTION) & mask).unsqueeze(-1) & (slot.unsqueeze(-1) == torch.arange(max_actions, device=h.device))
        onehot = onehot.float()                                   # (B, L, A)
        counts = onehot.sum(1).clamp(min=1)                      # (B, A)
        vecs = torch.einsum("bla,bld->bad", onehot, h) / counts.unsqueeze(-1)
        scores = self.score(torch.cat([vecs, summary.unsqueeze(1).expand(-1, max_actions, -1)], -1)).squeeze(-1)
        valid = torch.arange(max_actions, device=h.device).unsqueeze(0) < batch["n_actions"].unsqueeze(1)
        return scores.masked_fill(~valid, -1e9), self.value(summary).squeeze(-1)

    def parameter_count(self):
        return sum(p.numel() for p in self.parameters())
