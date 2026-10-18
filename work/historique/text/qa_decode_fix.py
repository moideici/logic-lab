import json,urllib.request,urllib.error,time
from pathlib import Path
rows=[];history=[]
for text in ('bonjour ! tu fonctionne','hey ! ça va ??','quelle est ta phrase préférée ?','Je m’appelle Élodie et j’ai 17 ans. Retiens-le.','Quel est mon prénom et mon âge ? Mets les données dans valeurs.'):
    history.append({'role':'user','content':text});req=urllib.request.Request('http://127.0.0.1:8766/api/chat',data=json.dumps({'messages':history},ensure_ascii=False).encode(),headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=100) as res:value=json.load(res)
    except urllib.error.HTTPError as error:
        value=json.load(error)
    if value.get('etat')=='ok':history.append({'role':'assistant','content':json.dumps(value['reponse'],ensure_ascii=False)})
    else:history.pop()
    rows.append({'demande':text,**value});print(json.dumps(rows[-1],ensure_ascii=False),flush=True)
Path(r'C:\Users\gabor\code\logic-lab\outputs\input-decodage-apres.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
