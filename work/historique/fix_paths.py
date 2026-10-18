"""Remplace l'ancien chemin absolu du dossier de conversation par le chemin actuel."""
import os

root = r'C:\Users\gabor\code\logic-lab'
old = r'C:\Users\gabor\Documents\Codex\2026-10-16\tra'
bs = chr(92)
variants = [
    (old, root),
    (old.replace(bs, bs * 2), root.replace(bs, bs * 2)),
    (old.replace(bs, '/'), root.replace(bs, '/')),
]
skipdirs = {'.git', 'node_modules', '__pycache__', 'Lib', 'Include', 'site-packages', 'python-deps'}
exts = {'.json', '.py', '.mjs', '.cjs', '.js', '.cfg', '.yaml', '.yml', '.toml', '.txt', '.bat', '.ps1', '.cmd', '.html', '.sh', ''}
skipfiles = {'REGROUPEMENT.json', 'VERIFICATION-REGROUPEMENT.json', 'CATALOGUE-FICHIERS.csv'}
changed = []
for d, ds, fs in os.walk(root):
    ds[:] = [x for x in ds if x not in skipdirs and not (d == root and x == 'outputs')]
    for f in fs:
        if f in skipfiles or f == 'fix_paths.py':
            continue
        p = os.path.join(d, f)
        if os.path.splitext(f)[1].lower() not in exts:
            continue
        try:
            if os.path.getsize(p) > 8_000_000:
                continue
            b = open(p, 'rb').read()
        except OSError:
            continue
        if b'\x00' in b[:2000]:
            continue
        try:
            s = b.decode('utf-8')
        except UnicodeDecodeError:
            continue
        t = s
        for o, n in variants:
            t = t.replace(o, n)
        if t != s:
            open(p, 'wb').write(t.encode('utf-8'))
            changed.append(os.path.relpath(p, root))
print(len(changed))
print('\n'.join(changed))
