"""Entraînement par distillation des professeurs, avec symétries du plateau commun. Tout tient sur le GPU (positions en uint8)."""
from __future__ import annotations

import math
import os
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

from . import dataset
from .model import UnifiedNet
from .spec import CANVAS, CELLS, GAMES, MAX_ACTIONS, N_ACTIONS, SWAP

# échelle des scores du professeur pour la cible de politique : softmax((score - meilleur) / échelle)
SCALE = {"tictactoe": 0.5, "connect4": 0.5, "hex": 40.0, "gomoku": 1500.0, "dames": 6.0}
# tolérance d'« accord » avec le meilleur coup du professeur
TOL = {"tictactoe": 1e-6, "connect4": 1e-6, "hex": 10.0, "gomoku": 200.0, "dames": 2.0}


def _grid():
    y, x = np.divmod(np.arange(CELLS), CANVAS)
    return y, x


def _perm(fy, fx):
    y, x = _grid()
    ny, nx = fy(y, x), fx(y, x)
    return ny * CANVAS + nx


def symmetries(game):
    """Permutations des 225 cases du plateau commun qui sont des symétries du jeu (source → destination)."""
    m = CANVAS - 1
    ident = _perm(lambda y, x: y, lambda y, x: x)
    rot180 = _perm(lambda y, x: m - y, lambda y, x: m - x)
    flipx = _perm(lambda y, x: y, lambda y, x: m - x)
    if game in ("tictactoe", "gomoku"):
        return [ident, rot180, flipx, _perm(lambda y, x: m - y, lambda y, x: x), _perm(lambda y, x: x, lambda y, x: y),
                _perm(lambda y, x: m - x, lambda y, x: m - y), _perm(lambda y, x: x, lambda y, x: m - y), _perm(lambda y, x: m - x, lambda y, x: y)]
    if game == "connect4":
        return [ident, flipx]
    if game == "hex":
        return [ident, rot180]
    return [ident]


class GameData:
    def __init__(self, game, path, device, val_fraction=0.05):
        d = dataset.load(path)
        n = len(d["value"])
        cut = int(n * (1 - val_fraction))
        self.game, self.device = game, device
        self.n_actions = N_ACTIONS[game]
        t = lambda a, dt: torch.from_numpy(a).to(device=device, dtype=dt)
        planes = d["planes"].reshape(n, 8, CELLS)
        self.train = [t(planes[:cut], torch.uint8), t(d["extra"][:cut], torch.float32), t(d["moves"][:cut], torch.int16),
                      t(d["scores"][:cut], torch.float32), t(d["value"][:cut], torch.float32)]
        self.val = [t(planes[cut:], torch.uint8), t(d["extra"][cut:], torch.float32), t(d["moves"][cut:], torch.int16),
                    t(d["scores"][cut:], torch.float32), t(d["value"][cut:], torch.float32)]
        self.n_train = cut
        syms = symmetries(game)
        self.inv = torch.stack([torch.from_numpy(np.argsort(p)) for p in syms]).to(device)

    def batch(self, split, idx, augment):
        planes, extra, moves, scores, value = [a[idx] for a in (self.train if split == "train" else self.val)]
        planes = planes.float()
        target = target_from_labels(moves, scores, self.n_actions, SCALE[self.game])
        if augment and len(self.inv) > 1:
            sym = torch.randint(len(self.inv), (len(idx),), device=self.device)
            inv = self.inv[sym]  # (B, 225)
            planes = torch.gather(planes, 2, inv[:, None, :].expand(-1, planes.shape[1], -1))
            if self.game != "dames":
                cells = torch.gather(target[:, :CELLS], 1, inv)
                target = torch.cat([cells, target[:, CELLS:]], 1)
        return planes.view(len(idx), 8, CANVAS, CANVAS), extra, target, value, moves, scores


def target_from_labels(moves, scores, n_actions, scale):
    m = moves.long()
    valid = m >= 0
    s = torch.where(valid, scores, torch.full_like(scores, -1e30))
    best = s.max(1, keepdim=True).values
    w = torch.exp(torch.clamp((s - best) / scale, min=-30)) * valid
    w = w / w.sum(1, keepdim=True)
    out = torch.zeros(len(m), n_actions, device=m.device)
    out.scatter_add_(1, m.clamp(min=0), w)
    return out


def legal_mask(game, planes, extra, target):
    if game == "dames":
        return target > 0
    mask = torch.zeros(len(planes), N_ACTIONS[game], dtype=torch.bool, device=planes.device)
    mask[:, :CELLS] = planes[:, 5].flatten(1) > 0
    if game == "hex":
        mask[:, SWAP] = extra[:, 0] > 0
    return mask | (target > 0)


def game_loss(game, out, planes, extra, target, value, vweight=0.5):
    logits, v = out
    mask = legal_mask(game, planes, extra, target)
    logp = F.log_softmax(logits.float().masked_fill(~mask, -1e9), dim=1)
    policy = -(target * logp).sum(1).mean()
    return policy + vweight * F.mse_loss(v.float(), value)


@torch.no_grad()
def validate(net, data, batch=1024):
    net.eval()
    n = len(data.val[4])
    agree = vsum = vsign = 0.0
    for s in range(0, n, batch):
        idx = torch.arange(s, min(n, s + batch), device=data.device)
        planes, extra, target, value, moves, scores = data.batch("val", idx, False)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            logits, v = net(data.game, planes, extra)
        mask = legal_mask(data.game, planes, extra, target)
        pick = logits.float().masked_fill(~mask, -1e9).argmax(1)
        m = moves.long()
        valid = m >= 0
        sc = torch.where(valid, scores, torch.full_like(scores, -1e30))
        got = torch.where((m == pick[:, None]) & valid, sc, torch.full_like(sc, -1e30)).max(1).values
        agree += (got >= sc.max(1).values - TOL[data.game]).float().sum().item()
        vsum += ((v.float() - value) ** 2).sum().item()
        vsign += ((torch.sign(v.float()) == torch.sign(value)) | (value.abs() < 0.05)).float().sum().item()
    net.train()
    return {"top1_agreement": round(agree / n, 4), "value_mse": round(vsum / n, 4), "value_sign": round(vsign / n, 4), "n_val": n}


PAUSE_FILE = Path(__file__).resolve().parents[2] / "training-lab" / "PAUSE"


def train_model(games, datas, steps, seed, device="cuda", batch=256, lr=2e-3, channels=64, blocks=6, log_every=2000, label="", ckpt=None):
    """Un réseau pour `games`, `steps` pas ; chaque pas tire batch/len(games) positions par jeu."""
    torch.manual_seed(seed)
    net = UnifiedNet(games, channels, blocks).to(device)
    opt = torch.optim.AdamW(net.parameters(), lr=lr, weight_decay=1e-4)
    per = max(1, batch // len(games))
    t0 = time.time()
    history = []
    start = 1
    if ckpt and Path(ckpt).exists():  # reprise après interruption
        blob = torch.load(ckpt, map_location=device, weights_only=False)
        net.load_state_dict(blob["net"])
        opt.load_state_dict(blob["opt"])
        history, start = blob["history"], blob["step"] + 1
        print(f"[{label}] reprise au pas {start}", flush=True)
    for step in range(start, steps + 1):
        if step % 50 == 0:
            while PAUSE_FILE.exists():  # `training-lab/PAUSE` présent : veille sans calcul (la mémoire GPU reste prise)
                time.sleep(5)
        f = min(1.0, step / 300) * (0.5 * (1 + math.cos(math.pi * step / steps)) * 0.98 + 0.02)
        for g in opt.param_groups:
            g["lr"] = lr * f
        opt.zero_grad(set_to_none=True)
        batches = {}
        for game in games:
            d = datas[game]
            idx = torch.randint(d.n_train, (per,), device=device)
            batches[game] = d.batch("train", idx, True)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            outs = net.forward_multi({g: (b[0], b[1]) for g, b in batches.items()})
            loss = sum(game_loss(g, outs[g], b[0], b[1], b[2], b[3]) for g, b in batches.items()) / len(games)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(net.parameters(), 2.0)
        opt.step()
        if step % log_every == 0 or step == steps:
            val = {g: validate(net, datas[g]) for g in games}
            history.append({"step": step, "val": val})
            if ckpt:
                torch.save({"net": net.state_dict(), "opt": opt.state_dict(), "step": step, "history": history}, str(ckpt) + ".tmp")
                os.replace(str(ckpt) + ".tmp", ckpt)
            print(f"[{label}] step {step}/{steps} {time.time() - t0:.0f}s " + " ".join(f"{g}:{v['top1_agreement']:.3f}" for g, v in val.items()), flush=True)
    return net, history
