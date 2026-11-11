"""Petit Transformer décodeur, caractère par caractère : `état>étape$`. Moins d'un million de paramètres, entraîné de zéro.

Pas de masque de remplissage : le remplissage est toujours à droite et le masque causal l'empêche d'influencer les positions utiles.
Les positions sont apprises (absolues) : la généralisation à des séquences plus longues que l'entraînement est donc une vraie question,
mesurée par le hors distribution, pas une propriété acquise.
"""
from __future__ import annotations

import torch
import torch.utils.checkpoint
from torch import nn

from .data import EOS, MAX_LEN, PAD, VOCAB_SIZE, decode, encode_prompt


class MathLM(nn.Module):
    def __init__(self, d=128, layers=4, heads=4, ff=512, max_len=MAX_LEN, dropout=0.0):
        super().__init__()
        self.cfg = {"d": d, "layers": layers, "heads": heads, "ff": ff, "max_len": max_len, "dropout": dropout}
        self.max_len = max_len
        self.tok = nn.Embedding(VOCAB_SIZE, d)
        self.pos = nn.Embedding(max_len, d)
        layer = nn.TransformerEncoderLayer(d, heads, ff, dropout, activation="gelu", batch_first=True, norm_first=True)
        self.blocks = nn.TransformerEncoder(layer, layers, enable_nested_tensor=False)
        self.norm = nn.LayerNorm(d)
        self.head = nn.Linear(d, VOCAB_SIZE, bias=False)
        self.grad_ckpt = False  # recalcul des activations à la rétropropagation : moins de mémoire GPU, environ 30 % de calcul en plus
        self.head.weight = self.tok.weight  # poids liés : le même tableau lit et écrit les caractères
        for emb in (self.tok, self.pos):  # écart-type 1 par défaut : avec les poids liés, la perte initiale vaudrait ~23 au lieu de ~3
            nn.init.normal_(emb.weight, std=0.02)

    def forward(self, ids):
        T = ids.shape[1]
        x = self.tok(ids) + self.pos(torch.arange(T, device=ids.device))
        mask = torch.nn.Transformer.generate_square_subsequent_mask(T, device=ids.device)
        if self.grad_ckpt and self.training and torch.is_grad_enabled():
            for layer in self.blocks.layers:
                x = torch.utils.checkpoint.checkpoint(lambda t, layer=layer: layer(t, src_mask=mask, is_causal=True), x, use_reentrant=False)
        else:
            x = self.blocks(x, mask=mask, is_causal=True)
        return self.head(self.norm(x))

    def parameter_count(self):
        return sum(p.numel() for p in self.parameters())


def loss_on_outputs(model, X, plen, per_row=False):
    """Entropie croisée sur la sortie seulement (après `>`), `$` compris. `per_row` : renvoie aussi, pour chaque exemple, la perte de son
    pire jeton (une seule faute de chiffre y est visible, alors que la moyenne la dilue)."""
    ids = X[:, :-1].long()
    tgt = X[:, 1:].long()
    logits = model(ids)
    pos = torch.arange(tgt.shape[1], device=X.device)[None]
    mask = (pos >= (plen[:, None].long() - 1)) & (tgt != PAD)
    ce = nn.functional.cross_entropy(logits.reshape(-1, logits.shape[-1]), tgt.reshape(-1), reduction="none").view_as(tgt)
    loss = (ce * mask).sum() / mask.sum()
    if per_row:
        return loss, (ce * mask).max(1).values.detach()
    return loss


@torch.no_grad()
def generate(model, prompts, device="cpu", max_new=48, batch=512):
    """Décodage glouton. Les invites de même longueur sont groupées (positions absolues : pas de remplissage à gauche)."""
    was_training = model.training
    model.eval()
    results = [None] * len(prompts)
    groups = {}
    for idx, p in enumerate(prompts):
        groups.setdefault(len(p), []).append(idx)
    for length, idxs in groups.items():
        for s in range(0, len(idxs), batch):
            chunk = idxs[s:s + batch]
            ids = torch.tensor([encode_prompt(prompts[i]) for i in chunk], dtype=torch.long, device=device)
            done = torch.zeros(len(chunk), dtype=torch.bool, device=device)
            for _ in range(max_new):
                if ids.shape[1] >= model.max_len:
                    break
                nxt = model(ids)[:, -1].argmax(-1)
                nxt = torch.where(done, torch.full_like(nxt, PAD), nxt)
                ids = torch.cat([ids, nxt[:, None]], 1)
                done |= nxt == EOS
                if bool(done.all()):
                    break
            for row, i in enumerate(chunk):
                results[i] = decode(ids[row, length + 1:].tolist())
    model.train(was_training)
    return results


@torch.no_grad()
def beam_generate(model, prompts, beam=8, device="cpu", max_new=48, chunk=64):
    """Pour chaque invite, jusqu'à `beam` sorties candidates (texte), de la plus probable à la moins probable (recherche en faisceau).

    Les invites de même longueur sont groupées (positions absolues). Une hypothèse terminée (`$`) continue en remplissage sans coût."""
    was_training = model.training
    model.eval()
    results = [None] * len(prompts)
    groups = {}
    for idx, p in enumerate(prompts):
        groups.setdefault(len(p), []).append(idx)
    V = VOCAB_SIZE
    for length, idxs in groups.items():
        for s in range(0, len(idxs), chunk):
            sub = idxs[s:s + chunk]
            n = len(sub)
            base = torch.tensor([encode_prompt(prompts[i]) for i in sub], dtype=torch.long, device=device)
            ids = base[:, None, :].expand(n, beam, base.shape[1]).reshape(n * beam, -1).contiguous()
            scores = torch.zeros(n, beam, device=device)
            scores[:, 1:] = -1e9  # une seule hypothèse au départ, sinon le faisceau est rempli de copies
            done = torch.zeros(n * beam, dtype=torch.bool, device=device)
            rows = (torch.arange(n, device=device) * beam)[:, None]
            for _ in range(max_new):
                if ids.shape[1] >= model.max_len:
                    break
                logp = torch.log_softmax(model(ids)[:, -1].float(), -1)
                logp[done] = -1e9
                logp[done, PAD] = 0.0
                top, flat = (scores.reshape(-1, 1) + logp).reshape(n, beam * V).topk(beam, dim=1)
                src, tok = flat // V, flat % V
                sel = (rows + src).reshape(-1)
                tok = tok.reshape(-1)
                ids = torch.cat([ids[sel], tok[:, None]], 1)
                done = done[sel] | (tok == EOS) | (tok == PAD)
                scores = top
                if bool(done.all()):
                    break
            ids = ids.view(n, beam, -1)
            for r, i in enumerate(sub):
                results[i] = [decode(ids[r, b, length + 1:].tolist()) for b in range(beam)]
    model.train(was_training)
    return results


def load_compatible(model, state):
    """Charge `state` même si le modèle a grandi depuis.

    Vocabulaire plus grand : les lignes des anciens caractères sont copiées, les nouvelles gardent leur initialisation (les caractères sont
    ajoutés en queue, voir `data.VOCAB`). Modèle plus profond : les couches présentes dans `state` sont copiées et les couches ajoutées sont
    initialisées pour ne rien changer (projections de sortie de l'attention et du réseau à zéro : le bloc résiduel ajoute 0), donc le modèle
    agrandi calcule d'abord exactement la même fonction. Retourne le nombre de couches ajoutées."""
    own = model.state_dict()
    merged = {}
    for k, v in state.items():
        if k in own and own[k].shape != v.shape:
            new = own[k].clone()
            new[:v.shape[0]] = v
            merged[k] = new
        else:
            merged[k] = v
    missing = [k for k in own if k not in merged]
    for k in missing:
        merged[k] = torch.zeros_like(own[k]) if ("out_proj" in k or "linear2" in k) else own[k]
    model.load_state_dict(merged)
    return len({k.split(".")[2] for k in missing if k.startswith("blocks.layers.")})
