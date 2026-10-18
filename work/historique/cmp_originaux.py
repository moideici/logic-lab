"""Compare les originaux sous code\\ au manifeste de copie : fichiers modifiés, absents ou ajoutés depuis."""
import json, os

m = json.load(open(r'C:\Users\gabor\code\logic-lab\docs\regroupement\REGROUPEMENT.json', encoding='utf-8'))
for p in m['projects']:
    src = p['source']
    listed = {f['path']: f['bytes'] for f in p['files']}
    diff, missing = [], []
    for rel, size in listed.items():
        f = os.path.join(src, rel)
        if not os.path.exists(f):
            missing.append(rel)
        elif os.path.getsize(f) != size:
            diff.append(rel)
    extra = []
    for d, ds, fs in os.walk(src):
        for x in fs:
            rel = os.path.relpath(os.path.join(d, x), src)
            if rel not in listed:
                extra.append(rel)
    print(src, '| copiés', len(listed), '| modifiés depuis', len(diff), '| absents', len(missing), '| nouveaux', len(extra))
    for lab, l in (('modifié', diff), ('nouveau', extra)):
        for r in l[:8]:
            print('   ', lab, r)
