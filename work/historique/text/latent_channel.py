"""Trainable continuous channel. No natural-language decoding on this path."""
from dataclasses import dataclass
import torch
from torch import nn

@dataclass(frozen=True)
class Representation:
    model: str
    weights: str
    width: int
    layer: str

    def __post_init__(self):
        if type(self.width) is not int or self.width<1 or any(not isinstance(s,str) or not s.strip() for s in (self.model,self.weights,self.layer)):
            raise ValueError('A representation needs a width and pinned model/weights/layer identities')

class ContinuousAdapter(nn.Module):
    """Learn query slots in the receiver's input space.

    This is an untrained architecture until fitted and evaluated on paired
    tasks. Matching dimensions alone does not establish a shared semantics.
    """
    def __init__(self, sender: Representation, receiver: Representation, slots: int, heads=8):
        super().__init__()
        if type(slots)is not int or slots<1 or receiver.width%heads:
            raise ValueError('Invalid slot count or attention head count')
        self.sender,self.receiver,self.slots=sender,receiver,slots
        self.source=nn.Sequential(nn.LayerNorm(sender.width),nn.Linear(sender.width,receiver.width))
        self.queries=nn.Parameter(torch.randn(slots,receiver.width)*.02)
        self.attention=nn.MultiheadAttention(receiver.width,heads,batch_first=True,dropout=0.)
        self.output=nn.LayerNorm(receiver.width)

    def forward(self, states, mask, *, sender: Representation, receiver: Representation):
        if sender!=self.sender or receiver!=self.receiver:
            raise ValueError('The channel is not bound to these model weights/layers')
        if states.ndim!=3 or states.shape[-1]!=sender.width or mask.shape!=states.shape[:2] or not states.is_floating_point():
            raise ValueError('Invalid continuous source shape')
        if mask.device!=states.device or not ((mask==0)|(mask==1)).all() or not mask.bool().any(dim=1).all():
            raise ValueError('Each source must have a valid nonempty binary attention mask')
        states=torch.where(mask.bool().unsqueeze(-1),states,0.)
        if not torch.isfinite(states).all():raise ValueError('Source contains nonfinite active states')
        encoded=self.source(states)
        query=self.queries.unsqueeze(0).expand(states.shape[0],-1,-1)
        out,_=self.attention(query,encoded,encoded,key_padding_mask=~mask.bool(),need_weights=False)
        return self.output(query+out)
