import unittest
import torch
from decoding import CompleteObject

class Tokenizer:
    def __init__(self,text):self.text=text
    def decode(self,*args,**kwargs):return self.text

class DecodingTests(unittest.TestCase):
    def test_stop_only_after_a_complete_json_object(self):
        ids=torch.tensor([[1,2]])
        for raw,expected in [('{"texte":"une accolade }", "valeurs":{}',False),('{"texte":"une accolade }", "valeurs":{}}',True),('{"texte":"réponse',False),('[]',False),('{"texte":"ok","valeurs":{}}  ',True)]:
            with self.subTest(raw=raw):
                stop=CompleteObject(Tokenizer(raw),1)
                self.assertEqual(stop(ids,None),expected)
                self.assertIsNotNone(stop.first)
