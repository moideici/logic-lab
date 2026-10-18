"""Garry Loop : un bloc récurrent (poids liés) repassé plusieurs fois sur un graphe de contraintes.

Entrée : une grille (0 = case vide) et le graphe de contraintes (qui doit différer de qui). Chaque case est un nœud ; à chaque passe
un bloc d'attention limitée aux voisines (plus elle-même) et un petit réseau mettent à jour l'état de chaque case, avec réinjection
de l'entrée. Après chaque passe, une tête lit une proposition de chiffre pour chaque case : la « pensée » est visible passe par passe.

Variantes pour les témoins : poids non liés (un bloc différent par passe), ou une seule passe.
"""
from __future__ import annotations

import torch
from torch import nn


class Block(nn.Module):
    def __init__(self, d, heads):
        super().__init__()
        self.n1, self.n2 = nn.LayerNorm(d), nn.LayerNorm(d)
        self.attn = nn.MultiheadAttention(d, heads, batch_first=True)
        self.mlp = nn.Sequential(nn.Linear(d, 4 * d), nn.GELU(), nn.Linear(4 * d, d))

    def forward(self, z, mask):
        h = self.n1(z)
        z = z + self.attn(h, h, h, attn_mask=mask, need_weights=False)[0]
        return z + self.mlp(self.n2(z))


class RecurrentSolver(nn.Module):
    def __init__(self, n_values, max_cells, d=64, heads=4, passes=8, tied=True, use_position=True):
        super().__init__()
        self.n_values, self.passes, self.tied, self.heads, self.use_position = n_values, passes, tied, heads, use_position
        self.digit = nn.Embedding(n_values + 1, d)  # 0 = vide
        self.cell = nn.Embedding(max_cells, d) if use_position else None
        self.blocks = nn.ModuleList([Block(d, heads) for _ in range(1 if tied else passes)])
        self.norm = nn.LayerNorm(d)
        self.head = nn.Linear(d, n_values)

    def forward(self, grid, peers, passes=None, return_states=False, domain=None):
        """grid : (B, N) entiers ; peers : (N, N) ou (B, N, N) booléen (graphe propre à chaque exemple).
        domain : (B,) nombre de valeurs permises par exemple (couleurs) ; les autres valeurs reçoivent une probabilité nulle.
        Retourne les logits de chaque passe : (T, B, N, n_values)."""
        B, N = grid.shape
        steps = self.passes if passes is None else passes
        if not self.tied and steps > len(self.blocks):
            raise ValueError("un réseau à poids non liés ne peut pas faire plus de passes qu'il n'a de blocs")
        allowed = peers | torch.eye(N, dtype=torch.bool, device=peers.device)
        mask = ~allowed  # True = interdit, convention de PyTorch
        if mask.dim() == 3:
            mask = mask.repeat_interleave(self.heads, dim=0)  # (B*têtes, N, N)
        x = self.digit(grid)
        if self.cell is not None:
            x = x + self.cell(torch.arange(N, device=grid.device))[None]
        z = x
        outputs, states = [], []
        for t in range(steps):
            block = self.blocks[0] if self.tied else self.blocks[t]
            z = block(z + x, mask)
            out_t = self.head(self.norm(z))
            if domain is not None:
                forbidden = torch.arange(self.n_values, device=grid.device)[None, :] >= domain[:, None]
                out_t = out_t.masked_fill(forbidden[:, None, :], -1e9)
            outputs.append(out_t)
            if return_states:
                states.append(z.detach())
        out = torch.stack(outputs)
        return (out, states) if return_states else out

    def parameter_count(self):
        return sum(p.numel() for p in self.parameters())


def loss_over_passes(logits, solution, puzzle, nodes=None):
    """Entropie croisée moyenne sur les passes, uniquement sur les cases vides (et les nœuds réels). solution : 1..n (cible - 1)."""
    T, B, N, V = logits.shape
    empty = (puzzle == 0) if nodes is None else (puzzle == 0) & nodes
    target_all = torch.where(solution > 0, solution - 1, torch.zeros_like(solution))
    target = target_all[None].expand(T, B, N)
    ce = nn.functional.cross_entropy(logits.reshape(-1, V), target.reshape(-1), reduction="none").reshape(T, B, N)
    w = empty[None].float().expand(T, B, N)
    return (ce * w).sum() / w.sum().clamp(min=1)


@torch.no_grad()
def predicted_grid(logits_t, puzzle):
    """Grille proposée à une passe : cases données conservées, cases vides = chiffre le plus probable (1..n)."""
    guess = logits_t.argmax(-1) + 1
    return torch.where(puzzle > 0, puzzle, guess)
