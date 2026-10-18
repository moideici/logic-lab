"""Recherche arborescente de Monte-Carlo par lots : des centaines de parties avancent ensemble, un seul appel réseau par simulation.

Arbres stockés dans des tableaux numpy (parties × nœuds × actions). Chaque simulation descend selon PUCT dans toutes les parties à la fois,
crée un nouveau nœud par partie, évalue tous les nouveaux nœuds par le réseau en un lot, puis remonte la valeur (signe alterné).
Valeurs : toujours du point de vue du joueur au trait dans le nœud considéré.
"""
from __future__ import annotations

import numpy as np
import torch


class BatchedMCTS:
    def __init__(self, rules, net, device="cpu", sims=100, c_puct=1.5, dirichlet_alpha=0.6, dirichlet_weight=0.25, seed=0):
        self.rules, self.net, self.device = rules, net, device
        self.sims, self.c_puct = sims, c_puct
        self.alpha, self.weight = dirichlet_alpha, dirichlet_weight
        self.rng = np.random.default_rng(seed)

    @torch.no_grad()
    def evaluate(self, states):
        """Priorités (softmax sur les actions légales) et valeur du réseau pour un lot d'états."""
        x = torch.as_tensor(self.rules.encode(states), device=self.device)
        self.net.eval()
        logits, value = self.net(x)
        logits = logits.float().cpu().numpy()
        legal = self.rules.legal(states)
        logits = np.where(legal, logits, -np.inf)
        logits -= logits.max(1, keepdims=True)
        p = np.exp(logits)
        p /= p.sum(1, keepdims=True)
        return p.astype(np.float32), value.float().cpu().numpy(), legal

    def search(self, states, noise=True, sims=None):
        """Retourne les visites (G, A) à la racine pour chaque partie. `states` : (G, W)."""
        rules, G = self.rules, len(states)
        S = self.sims if sims is None else sims
        A, Nn, W = rules.n_actions, S + 2, states.shape[1]
        state = np.zeros((G, Nn, W), dtype=states.dtype)
        term = np.zeros((G, Nn), dtype=bool)
        tval = np.zeros((G, Nn), dtype=np.float32)
        P = np.zeros((G, Nn, A), dtype=np.float32)
        N = np.zeros((G, Nn, A), dtype=np.int32)
        Wsum = np.zeros((G, Nn, A), dtype=np.float32)
        child = np.full((G, Nn, A), -1, dtype=np.int32)
        lmask = np.zeros((G, Nn, A), dtype=bool)
        count = np.ones(G, dtype=np.int64)
        gi = np.arange(G)
        state[:, 0] = states
        p, _, legal = self.evaluate(states)
        if noise:
            eta = self.rng.dirichlet([self.alpha] * A, size=G).astype(np.float32)
            p = np.where(legal, (1 - self.weight) * p + self.weight * eta, 0.0)
            p /= p.sum(1, keepdims=True)
        P[:, 0], lmask[:, 0] = p, legal
        max_depth = rules.max_moves + 1
        for _ in range(S):
            cur = np.zeros(G, dtype=np.int64)
            active = np.ones(G, dtype=bool)
            path_n = np.full((max_depth, G), -1, dtype=np.int64)
            path_a = np.full((max_depth, G), -1, dtype=np.int64)
            length = np.zeros(G, dtype=np.int64)
            leaf_node = np.zeros(G, dtype=np.int64)
            leaf_new = np.zeros(G, dtype=bool)   # nœud créé, non terminal : à évaluer par le réseau
            leaf_value = np.zeros(G, dtype=np.float32)
            for depth in range(max_depth):
                idx = np.flatnonzero(active)
                if len(idx) == 0:
                    break
                n = cur[idx]
                is_term = term[idx, n]
                if is_term.any():  # nœud terminal déjà connu : sa valeur exacte est la feuille
                    t = idx[is_term]
                    leaf_node[t], leaf_value[t] = n[is_term], tval[t, n[is_term]]
                    active[t] = False
                    idx, n = idx[~is_term], n[~is_term]
                    if len(idx) == 0:
                        continue
                visits = N[idx, n]
                q = np.where(visits > 0, Wsum[idx, n] / np.maximum(visits, 1), 0.0)
                total = visits.sum(1, keepdims=True)
                score = q + self.c_puct * P[idx, n] * np.sqrt(total + 1.0) / (1.0 + visits)
                score = np.where(lmask[idx, n], score, -np.inf)
                a = score.argmax(1)
                path_n[depth, idx], path_a[depth, idx] = n, a
                length[idx] += 1
                ch = child[idx, n, a]
                fresh = ch < 0
                cur[idx[~fresh]] = ch[~fresh]
                if fresh.any():
                    f = idx[fresh]
                    nf, af = n[fresh], a[fresh]
                    new_id = count[f]
                    count[f] += 1
                    child[f, nf, af] = new_id
                    ns, nterm, nval = rules.step(state[f, nf], af)
                    state[f, new_id], term[f, new_id], tval[f, new_id] = ns, nterm, nval
                    leaf_node[f] = new_id
                    leaf_value[f] = np.where(nterm, nval, 0.0)
                    leaf_new[f] = ~nterm
                    active[f] = False
            need = np.flatnonzero(leaf_new)
            if len(need):
                p2, v2, l2 = self.evaluate(state[need, leaf_node[need]])
                P[need, leaf_node[need]], lmask[need, leaf_node[need]] = p2, l2
                leaf_value[need] = v2
            for t in range(max_depth):
                valid = np.flatnonzero(length > t)
                if len(valid) == 0:
                    break
                sign = np.where(((length[valid] - t) % 2) == 0, 1.0, -1.0).astype(np.float32)
                nt, at = path_n[t, valid], path_a[t, valid]
                N[valid, nt, at] += 1
                Wsum[valid, nt, at] += sign * leaf_value[valid]
        return N[:, 0].copy(), (Wsum[:, 0] / np.maximum(N[:, 0], 1)).astype(np.float32)
