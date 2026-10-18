import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import torch
from models.hrm.hrm_act_v1 import HierarchicalReasoningModel_ACTV1
from hrm_local import initial_continuous
from latent_channel import Representation,ContinuousAdapter

class NativeChannelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):torch.set_num_threads(2)

    def core(self):
        return HierarchicalReasoningModel_ACTV1(dict(batch_size=1,seq_len=4,vocab_size=5,num_puzzle_identifiers=1,puzzle_emb_ndim=16,H_cycles=2,L_cycles=2,H_layers=1,L_layers=1,hidden_size=16,expansion=2,num_heads=2,pos_encodings='rope',halt_max_steps=2,halt_exploration_prob=0.,forward_dtype='float32')).eval().inner

    def test_native_symbols_and_direct_continuous_input_are_equivalent(self):
        core=self.core();batch={'inputs':torch.tensor([[1,2,3,4]]),'puzzle_identifiers':torch.tensor([0])}
        with torch.no_grad():
            embeddings=core._input_embeddings(batch['inputs'],batch['puzzle_identifiers'])
            a,logits_a,q_a=core(initial_continuous(core,embeddings),batch)
            b,logits_b,q_b=core.forward_embeddings(initial_continuous(core,embeddings),embeddings)
        torch.testing.assert_close(logits_a,logits_b,rtol=0,atol=0)
        torch.testing.assert_close(a.z_H,b.z_H,rtol=0,atol=0)

    def test_adapter_receives_gradients_through_frozen_recursive_core(self):
        torch.manual_seed(12);core=self.core().requires_grad_(False)
        sender=Representation('input','base_hash',12,'last_hidden');receiver=Representation('hrm','checkpoint_hash',16,'scaled_input')
        adapter=ContinuousAdapter(sender,receiver,slots=5,heads=2)
        embeddings=adapter(torch.randn(1,7,12),torch.ones(1,7,dtype=torch.bool),sender=sender,receiver=receiver)
        _,logits,_=core.forward_embeddings(initial_continuous(core,embeddings),embeddings)
        torch.nn.functional.cross_entropy(logits.reshape(-1,5),torch.tensor([1,2,3,4])).backward()
        self.assertGreater(sum(float(p.grad.abs().sum()) for p in adapter.parameters() if p.grad is not None),0)
        self.assertTrue(all(p.grad is None for p in core.parameters()))

    def test_padding_and_binding_cannot_silently_change_the_message(self):
        sender=Representation('input','v1',12,'last');receiver=Representation('hrm','v1',16,'input')
        adapter=ContinuousAdapter(sender,receiver,slots=5,heads=2).eval();states=torch.randn(1,4,12);mask=torch.tensor([[1,1,0,0]])
        a=adapter(states,mask,sender=sender,receiver=receiver);states[:,2:]=float('nan')
        b=adapter(states,mask,sender=sender,receiver=receiver);torch.testing.assert_close(a,b)
        with self.assertRaises(ValueError):adapter(states,mask,sender=Representation('input','v2',12,'last'),receiver=receiver)
        with self.assertRaises(ValueError):adapter(states,torch.zeros_like(mask),sender=sender,receiver=receiver)

if __name__=='__main__':unittest.main()
