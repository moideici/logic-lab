exec((__import__('pathlib').Path(__file__).parent/'integrate.py').read_text(encoding='utf-8').split('# Freeze the last')[0])
import shutil,hashlib
# Keep the reproducible full-game benchmark alongside the other examples.
src=ROOT/'benchmark-strategy.mjs';dst=ROOT/'examples/benchmark_strategy.mjs'
if src.exists():
    src.rename(dst);s=dst.read_text(encoding='utf-8').replace("from './web/","from '../web/");dst.write_text(s,encoding='utf-8')
p=ROOT/'tests/test_strategy.py';s=p.read_text(encoding='utf-8');marker='    def test_all_nine_prior_modes_are_preserved_after_strategy_training(self):'
addition='''    def test_python_protocol_creates_suggests_and_plays_both_strategy_games(self):
        from logic_arena.harness import Arena,catalog
        self.assertEqual(len(catalog()['games']),11)
        arena=Arena()
        for name in ('draughts','breakthrough'):
            result=arena.dispatch({'op':'create','game':name,'seed':1710711});self.assertTrue(result['ok']);session=result['result']['session_id']
            before=arena.dispatch({'op':'observe','session_id':session})['result']
            decision=arena.dispatch({'op':'suggest','session_id':session,'agent':{'level':10,'time_ms':30}})
            self.assertTrue(decision['ok']);self.assertIn(decision['result']['action'],before['legal_actions'])
            step=arena.dispatch({'op':'step','session_id':session,'expected_revision':0,'action':decision['result']['action']});self.assertTrue(step['ok']);self.assertEqual(step['result']['revision'],1)
            rejected=arena.dispatch({'op':'step','session_id':session,'expected_revision':0,'action':decision['result']['action']});self.assertFalse(rejected['ok'])

'''
assert marker in s;s=s.replace(marker,addition+marker);p.write_text(s,encoding='utf-8')
old=ROOT/'versions/3.2.0';assert hashlib.sha256((old/'connect4-search.wasm').read_bytes()).digest()==hashlib.sha256((ROOT/'web/connect4-search.wasm').read_bytes()).digest()
print('Benchmark stored, Python protocol regression added, original search engine preserved.')
