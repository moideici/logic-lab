import json,urllib.request,urllib.error
from pathlib import Path
rows=[]
for text in ('Quelle est ta phrase préférée ? Réponds en une phrase courte.','J’achète 4 cahiers à 3,25 € chacun. Donne quantite, prix et total dans valeurs.'):
    request=urllib.request.Request('http://127.0.0.1:8766/api/chat',data=json.dumps({'messages':[{'role':'user','content':text}]},ensure_ascii=False).encode(),headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(request,timeout=100) as response:value=json.load(response)
    except urllib.error.HTTPError as error:value=json.load(error)
    rows.append({'demande':text,**value});print(json.dumps(rows[-1],ensure_ascii=False),flush=True)
Path(r'C:\Users\gabor\code\logic-lab\outputs\input-adaptation-focus-active.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
