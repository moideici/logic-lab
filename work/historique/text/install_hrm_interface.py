from pathlib import Path
import shutil
root=Path(r'C:\Users\gabor\code\latent-reasoner-hrm');source=Path(__file__).parent
p=root/'models/layers.py';s=p.read_text(encoding='utf-8')
old='''except ImportError:
    # Fallback to FlashAttention 2
    from flash_attn import flash_attn_func  # type: ignore[import]'''
new='''except ImportError:
    try:
        from flash_attn import flash_attn_func  # type: ignore[import]
    except ImportError:
        flash_attn_func = None  # Portable CPU/Windows backend.
'''
assert old in s;s=s.replace(old,new)
old='''        attn_output = flash_attn_func(q=query, k=key, v=value, causal=self.causal)
        if isinstance(attn_output, tuple):  # fa2 and fa3 compatibility
            attn_output = attn_output[0]

        attn_output = attn_output.view(batch_size, seq_len, self.output_size)'''
new='''        if flash_attn_func is not None and query.is_cuda and query.dtype in (torch.float16, torch.bfloat16):
            attn_output = flash_attn_func(q=query, k=key, v=value, causal=self.causal)
            if isinstance(attn_output, tuple):
                attn_output = attn_output[0]
        else:
            attn_output = F.scaled_dot_product_attention(
                query.transpose(1, 2), key.transpose(1, 2), value.transpose(1, 2),
                is_causal=self.causal,
            ).transpose(1, 2)

        attn_output = attn_output.reshape(batch_size, seq_len, self.output_size)'''
assert old in s;s=s.replace(old,new);p.write_text(s,encoding='utf-8')
p=root/'models/hrm/hrm_act_v1.py';s=p.read_text(encoding='utf-8')
old='''        seq_info = dict(
            cos_sin=self.rotary_emb() if hasattr(self, "rotary_emb") else None,
        )

        # Input encoding
        input_embeddings = self._input_embeddings(batch["inputs"], batch["puzzle_identifiers"])

        # Forward iterations'''
new='''        input_embeddings = self._input_embeddings(batch["inputs"], batch["puzzle_identifiers"])
        return self.forward_embeddings(carry, input_embeddings)

    def forward_embeddings(self, carry: HierarchicalReasoningModel_ACTV1InnerCarry, input_embeddings: torch.Tensor):
        """Consume a continuous representation, without decoding it into symbols.

        Its shape, scale and semantic alignment must match this checkpoint.
        An arbitrary sender's hidden states are not a compatible representation.
        """
        expected = (carry.z_H.shape[0], self.config.seq_len + self.puzzle_emb_len, self.config.hidden_size)
        if input_embeddings.shape != expected or not input_embeddings.is_floating_point():
            raise ValueError("Continuous HRM input has an incompatible shape or dtype")
        if input_embeddings.device != carry.z_H.device or input_embeddings.dtype != carry.z_H.dtype:
            raise ValueError("Continuous input and reasoning state must share device and dtype")
        if not torch.isfinite(input_embeddings).all():
            raise ValueError("Continuous HRM input must be finite")
        seq_info = dict(cos_sin=self.rotary_emb() if hasattr(self, "rotary_emb") else None)

        # Forward iterations'''
assert old in s;s=s.replace(old,new);p.write_text(s,encoding='utf-8')
for name,target in [('latent_channel.py','latent_channel.py'),('hrm_local.py','hrm_local.py'),('test_hrm_latent.py','tests/test_hrm_latent.py'),('smoke_hrm.py','smoke_hrm.py'),('LATENT_FORK.md','LATENT_FORK.md')]:
    destination=root/target;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/name,destination)
p=root/'.gitignore';s=p.read_text(encoding='utf-8');s+='\n/weight_cache/\n/local_results/\n';p.write_text(s,encoding='utf-8')
print('Portable HRM and continuous input interface installed')
