import os
os.chdir(r'C:\Users\gabor\code\logic-lab')
bs = chr(92)
old = bs.join(['C:', 'Users', 'gabor', 'Documents', 'Codex', '2026-10-16', 'tra'])
new = bs.join(['C:', 'Users', 'gabor', 'code', 'logic-lab'])


def sub(p, pairs):
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        s = s.replace(a, b)
    open(p, 'w', encoding='utf-8', newline='').write(s)


sub('README.md', [(old, new), ('[LIRE-MOI.md](docs/LIRE-MOI.md)', '[docs/LIRE-MOI.md](docs/LIRE-MOI.md)')])
sub('docs/EXPLOITATION.md', [(old, new),
    ('`REGROUPEMENT.json`', '`docs/regroupement/REGROUPEMENT.json`'),
    ('`VERIFICATION-REGROUPEMENT.json`', '`docs/regroupement/VERIFICATION-REGROUPEMENT.json`')])
sub('PLAN-GLOBAL.md', [('`REGROUPEMENT.json` et `LIRE-MOI.md`', '`docs/regroupement/REGROUPEMENT.json` et `docs/LIRE-MOI.md`')])
sub('docs/INVENTAIRE-JUSTIFIE.md', [
    ('`README.md`, `LIRE-MOI.md`', '`README.md`, `docs/LIRE-MOI.md`'),
    ('| `REGROUPEMENT.json`', '| `docs/regroupement/REGROUPEMENT.json`'),
    ('| `VERIFICATION-REGROUPEMENT.json`', '| `docs/regroupement/VERIFICATION-REGROUPEMENT.json`'),
    ('| `CATALOGUE-FICHIERS.csv`', '| `docs/regroupement/CATALOGUE-FICHIERS.csv`')])
sub('docs/LIRE-MOI.md', [(old, new),
    ('(PLAN-GLOBAL.md)', '(../PLAN-GLOBAL.md)'), ('(projets/', '(../projets/'), ('(recherche/', '(../recherche/'),
    ('(outputs)', '(../outputs)'), ('(work)', '(../work)'),
    ('[REGROUPEMENT.json](REGROUPEMENT.json)', '[REGROUPEMENT.json](regroupement/REGROUPEMENT.json)'),
    ('`VERIFICATION-REGROUPEMENT.json`', '`regroupement/VERIFICATION-REGROUPEMENT.json`'),
    ('Depuis PowerShell, dans ce dossier :', 'Depuis PowerShell, à la racine du projet (' + new + ') :'),
    ('Les fichiers sont copiés dans ce dossier, sans effacer ou déplacer les originaux dans `C:' + bs + 'Users' + bs + 'gabor' + bs + 'code`',
     'Les fichiers ont été copiés dans ce dossier, puis déplacés le 18 octobre 2026 de `Documents' + bs + 'Codex' + bs + '2026-10-16' + bs + 'tra` vers `code' + bs + 'logic-lab`, sans effacer les originaux sous `C:' + bs + 'Users' + bs + 'gabor' + bs + 'code`')])

import re
bad = 0
for p in ['README.md', 'PLAN-GLOBAL.md'] + ['docs/' + f for f in os.listdir('docs') if f.endswith('.md')]:
    s = open(p, encoding='utf-8').read()
    for m in re.finditer(r'\]\(([^)#\s]+)', s):
        t = m.group(1)
        if ':' in t:
            continue
        if not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(p), t))):
            print('CASSE', p, t); bad += 1
print('liens cassés :', bad)
