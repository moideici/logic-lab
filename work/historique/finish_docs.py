import os, re, shutil
os.chdir(r'C:\Users\gabor\code\logic-lab')
for f in ('LIRE-MOI', 'EXPLOITATION', 'VALIDATION', 'REPRISE'):
    os.remove(f'docs/{f}.md')
shutil.move('docs/INVENTAIRE-JUSTIFIE.md', 'docs/regroupement/INVENTAIRE-JUSTIFIE.md')

g = open('docs/GUIDE.md', encoding='utf-8').read()
g = g.replace('| HRM | 3 tests réussis ; `smoke_hrm.py` : 1 grille publique résolue sur 2 (la seconde échoue déjà dans l\'état de référence). |',
              '| HRM | Non remesuré après déplacement. Mesure du regroupement : 3 tests réussis ; `smoke_hrm.py` : 1 grille publique résolue sur 2 (la seconde échoue déjà dans l\'état de référence). |')
g = g.replace('Mesuré le 18 octobre 2026 après déplacement :', 'Mesuré le 18 octobre 2026 après déplacement (Garry, Input) :')
open('docs/GUIDE.md', 'w', encoding='utf-8', newline='').write(g)

r = open('README.md', encoding='utf-8').read()
start = r.index('## Lire dans cet ordre')
end = r.index('## Points d’entrée')
new = '''## Lire dans cet ordre

1. [PLAN-GLOBAL.md](PLAN-GLOBAL.md) — objectifs, bilan, périmètre actif des modèles, prochaines étapes. Fait autorité sur les anciens rapports.
2. [docs/GUIDE.md](docs/GUIDE.md) — arborescence, lancement, vérifications, sauvegardes, reprise.
3. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — composants et circulation des informations.
4. [docs/DECISIONS.md](docs/DECISIONS.md) — décisions, raisons et sujets ouverts.

Provenance du regroupement (manifeste, empreintes, catalogue fichier par fichier, inventaire justifié) : [docs/regroupement/](docs/regroupement/).

'''
r = r[:start] + new + r[end:]
open('README.md', 'w', encoding='utf-8', newline='').write(r)

for p in ['PLAN-GLOBAL.md', 'docs/ARCHITECTURE.md', 'docs/DECISIONS.md', 'docs/regroupement/INVENTAIRE-JUSTIFIE.md']:
    s = open(p, encoding='utf-8').read()
    s = s.replace('`docs/LIRE-MOI.md`', '`docs/GUIDE.md`').replace('`LIRE-MOI.md`', '`docs/GUIDE.md`')
    s = s.replace('`README.md`, `docs/GUIDE.md`', '`README.md`, `docs/GUIDE.md`')
    for old in ('LIRE-MOI', 'EXPLOITATION', 'VALIDATION', 'REPRISE'):
        s = re.sub(r'\[([^\]]*)\]\((?:\.\./|\.\./\.\./)?(?:docs/)?' + old + r'\.md\)', r'[\1](' + ('../GUIDE.md' if 'regroupement' in p else ('docs/GUIDE.md' if p == 'PLAN-GLOBAL.md' else 'GUIDE.md')) + ')', s)
    if p.endswith('INVENTAIRE-JUSTIFIE.md'):
        s = s.replace('(regroupement/CATALOGUE-FICHIERS.csv)', '(CATALOGUE-FICHIERS.csv)')
    open(p, 'w', encoding='utf-8', newline='').write(s)

bad = 0
for p in ['README.md', 'PLAN-GLOBAL.md'] + [os.path.join(d, f) for d, _, fs in os.walk('docs') for f in fs if f.endswith('.md')]:
    s = open(p, encoding='utf-8').read()
    for m in re.finditer(r'\]\(([^)#\s]+)', s):
        t = m.group(1)
        if ':' not in t and not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(p), t))):
            print('CASSE', p, t); bad += 1
    for old in ('LIRE-MOI', 'EXPLOITATION', 'VALIDATION.md', 'REPRISE'):
        if old in s:
            print('mention', old, 'dans', p)
print('liens cassés :', bad)
