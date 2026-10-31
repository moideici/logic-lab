"""Données pour l'emplacement « dames » de Garry : positions de parties jouées par le réseau de Zéro (MCTS), avec les visites de la racine comme cible.

Les parties redémarrent en continu (lot constant). Sortie .npz : states (n,66) int8, idx (n,K) int16, prob (n,K) float32 (visites normalisées, K plus grandes),
z (n,) float32 (résultat de la partie du point de vue du joueur au trait).
Usage : python training-lab/dames_garry_data.py --net training-lab/models/dames-zero/dernier.pt --minutes 30 --out training-lab/data/dames-garry-1.npz"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from logic_arena.zero import dames_net as dn  # noqa: E402
from logic_arena.zero.dames_rules import DamesRules  # noqa: E402
from logic_arena.zero.mcts import BatchedMCTS  # noqa: E402

K = 48


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--net", required=True)
    ap.add_argument("--minutes", type=float, default=30)
    ap.add_argument("--games", type=int, default=96)
    ap.add_argument("--sims", type=int, default=80)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    rules = DamesRules()
    blob = torch.load(a.net, map_location=device, weights_only=True)
    net = dn.build_net(blob["channels"], blob["blocks"]).to(device)
    net.load_state_dict(blob["net"])
    mcts = BatchedMCTS(rules, net, device, sims=a.sims, seed=a.seed)
    rng = np.random.default_rng(a.seed + 1)
    G = a.games
    states = rules.initial(G)
    age = np.zeros(G, dtype=np.int64)
    # ouvertures variées : quelques coups aléatoires au départ de chaque partie
    hist = [[] for _ in range(G)]  # (état, idx, prob) par partie en cours
    S, I, P, Z = [], [], [], []
    deadline = time.time() + a.minutes * 60
    total = 0

    def random_opening(g, plies):
        nonlocal states
        for _ in range(plies):
            legal = np.flatnonzero(rules.legal(states[g:g + 1])[0])
            if len(legal) == 0:
                break
            ns, term, _ = rules.step(states[g:g + 1], np.array([int(rng.choice(legal))]))
            if term[0]:
                states[g:g + 1] = rules.initial(1)
                break
            states[g:g + 1] = ns
    for g in range(G):
        random_opening(g, int(rng.integers(0, 7)))
    while time.time() < deadline:
        visits, _ = mcts.search(states, noise=True)
        acts = np.zeros(G, dtype=np.int64)
        for g in range(G):
            v = visits[g].astype(np.float64)
            pi = v / v.sum()
            top = np.argsort(-pi)[:K]
            hist[g].append((states[g].copy(), top.astype(np.int16), pi[top].astype(np.float32)))
            acts[g] = int(rng.choice(len(pi), p=pi)) if age[g] < 20 or rng.random() < 0.05 else int(v.argmax())
        new, term, value = rules.step(states, acts)
        states = new
        age += 1
        for g in range(G):
            over = bool(term[g]) or age[g] >= rules.max_moves
            if not over:
                continue
            outcome = float(value[g]) if term[g] else 0.0  # point de vue du joueur maintenant au trait
            T = len(hist[g])
            for t, (s, ix, pb) in enumerate(hist[g]):
                S.append(s), I.append(ix), P.append(pb)
                Z.append(-outcome if (T - 1 - t) % 2 == 0 else outcome)
            total += T
            hist[g] = []
            states[g:g + 1] = rules.initial(1)
            age[g] = 0
            random_opening(g, int(rng.integers(0, 7)))
        if total and total % 20000 < G:
            print(total, "positions", flush=True)
    idx = np.zeros((len(S), K), dtype=np.int16)
    prob = np.zeros((len(S), K), dtype=np.float32)
    for n, (ix, pb) in enumerate(zip(I, P)):
        idx[n, :len(ix)] = ix
        prob[n, :len(pb)] = pb
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(a.out, states=np.array(S, dtype=np.int8), idx=idx, prob=prob, z=np.array(Z, dtype=np.float32))
    print(len(S), "positions écrites")


if __name__ == "__main__":
    main()
