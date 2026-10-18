import unittest
from streaming import partial_text,StreamRequests

class StreamingTests(unittest.TestCase):
    def test_partial_json_string_escaping_and_root_field(self):
        cases=[('{"texte":"Bonjour','Bonjour'),('{"texte":"Une \\"citation','Une "citation'),('{"texte":"a\\nb','a\nb'),('{"texte":"caf\\u00e9','café'),('{"texte":"abc\\u00','abc'),('{"valeurs":{"texte":"autre"},"texte":"bon','bon'),('{"valeurs":{"texte":"autre',''),('{"texte":"fin", "valeurs":{}}','fin')]
        for raw,expected in cases:
            with self.subTest(raw=raw):self.assertEqual(partial_text(raw) or '',expected)
    def test_cancellation_is_scoped_and_cleanup_allows_next_request(self):
        streams=StreamRequests();a=streams.register('request_a');b=streams.register('request_b')
        self.assertTrue(streams.stop('request_a'));self.assertTrue(a.is_set());self.assertFalse(b.is_set())
        self.assertFalse(streams.stop('unknown_id'))
        with self.assertRaises(ValueError):streams.register('request_b')
        streams.remove('request_a');self.assertFalse(streams.register('request_a').is_set())
