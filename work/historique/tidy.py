"""Range outputs/, work/ et la racine ; met à jour les liens Markdown. Passe sèche avec --dry."""
import os, re, shutil, sys

root = r'C:\Users\gabor\code\logic-lab'
dry = '--dry' in sys.argv
moves = {}  # ancien chemin relatif (/) -> nouveau


def add(old, new):
    moves[old.replace('\\', '/')] = new.replace('\\', '/')


# --- outputs/ : par type puis par projet
out = os.path.join(root, 'outputs')
for f in sorted(os.listdir(out)):
    if not os.path.isfile(os.path.join(out, f)):
        continue
    l = f.lower()
    if l.endswith('.png'):
        sub = 'captures'
    elif l.endswith(('.log', '.id')):
        sub = 'journaux'
    elif 'verification' in l or l.startswith('audit-'):
        sub = 'verifications'
    elif l.startswith(('garry', 'session-')):
        sub = 'rapports/garry'
    elif l.startswith(('input', 'logic-lab', 'logiclab', 'francais')):
        sub = 'rapports/input'
    elif l.startswith('hrm'):
        sub = 'rapports/hrm'
    else:
        sub = 'rapports/autres'
    add('outputs/' + f, f'outputs/{sub}/{f}')

# --- work/ : environnement vs scripts historiques
keep = {'text-env', 'python-deps', 'browsers', 'compiler', 'historique'}
w = os.path.join(root, 'work')
for f in sorted(os.listdir(w)):
    if f in keep:
        continue
    add('work/' + f, 'work/historique/' + f)

# --- racine
add('LIRE-MOI.md', 'docs/LIRE-MOI.md')
for f in ('REGROUPEMENT.json', 'VERIFICATION-REGROUPEMENT.json', 'CATALOGUE-FICHIERS.csv'):
    add(f, 'docs/regroupement/' + f)

if dry:
    for o, n in list(moves.items())[:400]:
        print(o, '->', n)
    sys.exit()

for o, n in moves.items():
    src, dst = os.path.join(root, o), os.path.join(root, n)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.move(src, dst)

# --- mise à jour des liens dans les .md de la racine, docs/ et outputs/rapports
def rewrite(path):
    s = open(path, encoding='utf-8').read()
    t = s
    here = os.path.dirname(path)
    # liens relatifs ](chemin) et ](../chemin)
    def fix(m):
        target = m.group(1)
        frag = ''
        if '#' in target:
            target, frag = target.split('#', 1)
            frag = '#' + frag
        if re.match(r'^[a-z]+:', target) or not target:
            return m.group(0)
        # résout par rapport à l'ancien emplacement du fichier
        old_here = reverse_loc.get(path, here)
        absold = os.path.normpath(os.path.join(old_here, target))
        rel = os.path.relpath(absold, root).replace('\\', '/')
        if rel in moves:
            newabs = os.path.join(root, moves[rel])
            newrel = os.path.relpath(newabs, here).replace('\\', '/')
            return f']({newrel}{frag})'
        # fichier non déplacé mais le .md lui-même a bougé
        if here != old_here and os.path.exists(absold):
            newrel = os.path.relpath(absold, here).replace('\\', '/')
            return f']({newrel}{frag})'
        return m.group(0)
    t = re.sub(r'\]\(([^)\s]+)\)', fix, t)
    if t != s:
        open(path, 'w', encoding='utf-8', newline='').write(t)
        print('liens mis à jour :', os.path.relpath(path, root))


reverse_loc = {}
for o, n in moves.items():
    reverse_loc[os.path.join(root, n)] = os.path.dirname(os.path.join(root, o))

targets = [os.path.join(root, 'README.md'), os.path.join(root, 'PLAN-GLOBAL.md')]
for d, _, fs in os.walk(os.path.join(root, 'docs')):
    targets += [os.path.join(d, f) for f in fs if f.endswith('.md')]
for d, _, fs in os.walk(os.path.join(root, 'outputs')):
    targets += [os.path.join(d, f) for f in fs if f.endswith('.md')]
for p in targets:
    rewrite(p)
print(len(moves), 'éléments déplacés')
