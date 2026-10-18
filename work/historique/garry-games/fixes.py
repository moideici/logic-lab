exec((__import__('pathlib').Path(__file__).parent/'integrate.py').read_text(encoding='utf-8').split('# Freeze the last')[0])
edit('web/migration.js',[("games=Object.keys(specs)","games=[...LEGACY_GAMES,...Object.keys(specs).filter(g=>!LEGACY_GAMES.includes(g))]")])
edit('web/teachers.js',[("selectQuality(result.action_values,10,null,o.game)","selectQuality(result.action_values,10,Array(925).fill(0),o.game)")])
edit('logic_arena/diversity.py',[
("if game in ('tictactoe','connect4'):","if game in ('tictactoe','connect4','reversi'):"),
("elif game in ('2048','minesweeper'):variants", "elif game in ('2048','minesweeper','reversi','lightsout'):variants"),
("    else:raise ValueError('Unknown game')", "    elif game in ('reversi','nim','lightsout'):\n        from .extra_planner import extra_values\n        values,info=extra_values(obs,legal,Budget(nodes,10000),max_depth=3 if game=='reversi' else None)\n        info['category']=('pass' if legal[0].get('pass') else 'endgame' if sum(v==0 for row in obs['board'] for v in row)<=10 else 'opening' if obs['moves']<10 else 'middle') if game=='reversi' else ('winning' if max(v['quality'][0] for v in values)>0 else 'losing') if game=='nim' else ('short' if min(v['remaining_moves'] for v in values)<=8 else 'long')\n    else:raise ValueError('Unknown game')"),
("if game=='sliding_puzzle':return", "if game in ('sliding_puzzle','nim'):return"),
("('tictactoe','minesweeper','2048') else", "('tictactoe','minesweeper','2048','reversi','lightsout') else"),
("if a.get('undo'):return dict(a)","if a.get('undo') or a.get('pass'):return dict(a)")])
edit('examples/build_garry_repertoire.py',[
("            else:\n                env=make_game('2048'", "            elif game in ('reversi','nim','lightsout'):\n                env=make_game(game,runseed)\n                if game=='nim':\n                    heaps=[rng.randrange(16) for _ in range(3)]\n                    if not any(heaps):heaps[0]=1\n                    env.board=[[1]*n+[0]*(15-n) for n in heaps]\n                for step in range(36 if game=='reversi' else 12):\n                    if env.done:break\n                    add(env,family,'public_varied_play',nodes=3000)\n                    env.step(rng.choice(env.legal_actions()))\n            else:\n                env=make_game('2048'")])
# Historical model tests stay historical, while the general model tests use all nine games.
edit('tests/test_garry.py',[
('from logic_arena.games import make_game','from logic_arena.games import make_game\nfrom logic_arena.migration import LEGACY_GAMES'),
('for g in SPECS}', 'for g in LEGACY_GAMES}'),('for g in SPECS:', 'for g in LEGACY_GAMES:'),('(1912,818)','(2060,925)')])
edit('tests/garry.test.mjs',[
("import test from", "import {LEGACY_GAMES} from '../web/migration.js';\nimport test from"),
("m.input,1912", "m.input,2060"),("m.output,818", "m.output,925"),
("GarryModel.fuse(GARRY_GAMES.map", "GarryModel.fuse(LEGACY_GAMES.map"),
("for(const g of GARRY_GAMES){const old", "for(const g of LEGACY_GAMES){const old"),
("encodeGeneral(o).length,1912", "encodeGeneral(o).length,2060"),("'3.2.0'","'4.0.0'")])
edit('tests/web.test.mjs',[("import test from", "import {LEGACY_GAMES} from '../web/migration.js';\nimport test from"),("Object.keys(NAMES).map(k=>[k,new Network", "LEGACY_GAMES.map(k=>[k,new Network")])
edit('tests/test_versions.py',[("identity['version'],'3.2.0'", "identity['version'],'4.0.0'")])
edit('tests/test_certified.py',[("self.assertEqual(GarryPolicy.from_dict(old).export()['w1'],old['w1'])", "new=GarryPolicy.from_dict(old);h=new.hidden\n        np=__import__('numpy');np.testing.assert_array_equal(new.w1[:1906],np.asarray(old['w1'],dtype=np.float32).reshape(1912,h)[:1906])\n        np.testing.assert_array_equal(new.w1[2051:2057],np.asarray(old['w1'],dtype=np.float32).reshape(1912,h)[1906:])")])
edit('tests/levels.test.mjs',[
("migrated.export().version,'3.2.0'", "migrated.export().version,'4.0.0'"),
("assert.deepEqual(Array.from(migrated.w1),old.w1);", "assert.deepEqual(Array.from(migrated.w1.slice(0,1906*48)),old.w1.slice(0,1906*48));assert.deepEqual(Array.from(migrated.w1.slice(2051*48,2057*48)),old.w1.slice(1906*48));")])
edit('tests/test_diversity.py',[("self.assertEqual(len(first),18)","self.assertEqual(len(first),27)")])
print('Legacy compatibility, new teachers, curriculum and architecture tests updated.')
