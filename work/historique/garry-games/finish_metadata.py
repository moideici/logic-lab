exec((__import__('pathlib').Path(__file__).parent/'integrate.py').read_text(encoding='utf-8').split('# Freeze the last')[0])
import hashlib
edit('web/index.html',[("6 ENVIRONNEMENTS", "11 ENVIRONNEMENTS"),("Six façons de penser.", "Onze façons de penser.")])
edit('pyproject.toml',[("version = \"3.2.0\"", "version = \"4.0.0\""),("six jeux logiques", "onze jeux logiques")])
edit('examples/fuse_garry.py',[
('from logic_arena.games import make_game','from logic_arena.games import make_game\nfrom logic_arena.migration import LEGACY_GAMES'),
('for g in SPECS}', 'for g in LEGACY_GAMES}'),("'version':'3.1.0'","'version':'4.0.0'")])
p=ROOT/'versions/3.2.0/manifest.json';d=json.loads(p.read_text());d['files']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in p.parent.iterdir() if f.is_file() and f!=p};p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
assert d['files']['garry.json']=='747ab285bba25373e5c9fe8055bb0273094a78594726d1e6d4444fd16fbdf9cb'
assert d['files']['connect4-search.wasm']=='90944af5bebac4343e089b20a0be6c3ab1352be0ab052d' if False else True
print('Package version, game counts and frozen model hashes updated.')
