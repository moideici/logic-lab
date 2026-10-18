from pathlib import Path
import urllib.request,urllib.error,json,time
req=urllib.request.Request('http://127.0.0.1:8766/api/chat',data=json.dumps({'messages':[{'role':'user','content':'Bonjour ! Présente-toi en une phrase.'}]}).encode(),headers={'Content-Type':'application/json'})
try:
 with urllib.request.urlopen(req,timeout=100)as r:raw=r.read().decode();print(raw);Path('outputs/input-premiere-reponse.json').write_text(raw,encoding='utf-8')
except urllib.error.HTTPError as e:print(e.code,e.read().decode());raise
