from pathlib import Path
import shutil
R=Path(r'C:\Users\gabor\code\text-comprehension');S=Path(__file__).parent
(R/'web').mkdir(exist_ok=True)
for f in ('input.html','input.css','input.js'):shutil.copyfile(S/f,R/'web'/f)
shutil.copyfile(S/'chat.py',R/'chat.py')
(R/'web/input.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#183c35"/><text x="32" y="43" text-anchor="middle" font-size="38" fill="#d6e9af">✳</text></svg>',encoding='utf-8')
p=R/'serve.py';t=p.read_text(encoding='utf-8');start=t.index(' def do_GET(self):');end=t.index(' def do_POST(self):',start)
t=t[:start]+''' def do_GET(self):
  static={'/':('input.html','text/html'),'/input.html':('input.html','text/html'),'/input.css':('input.css','text/css'),'/input.js':('input.js','text/javascript'),'/input.svg':('input.svg','image/svg+xml')}
  if self.path in static:
   name,mime=static[self.path];data=(ROOT/'web'/name).read_bytes();self.send_response(200);self.send_header('Content-Type',mime+'; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
  elif self.path=='/api/progres':
   def state(name):
    p=ROOT/'results'/name
    try:return loads(p.read_text(encoding='utf-8')) if p.exists() else {}
    except (OSError,ValueError):return {}
   self.send({'chat_pret':(ROOT/'models/chat_base.json').exists(),'corpus':state('corpus_status.json'),'entrainement':state('language_status.json')})
  elif self.path=='/etat':
   path=ROOT/'results/status.json';self.send(loads(path.read_text(encoding='utf-8')) if path.exists() else {'etat':'preparation'})
  else:self.send({'etat':'erreur','texte':'Adresse inconnue'},404)
''' +t[end:]
t=t.replace("if self.path!='/analyse':", "if self.path not in ('/analyse','/api/chat'):")
t=t.replace("req=loads(self.rfile.read(n).decode('utf-8'));self.send(analyse(req))", "req=loads(self.rfile.read(n).decode('utf-8'))\n   if self.path=='/api/chat':\n    from chat import respond\n    self.send(respond(req))\n   else:self.send(analyse(req))")
t=t.replace("except Exception:self.send", "except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError):return\n  except Exception:\n   import traceback;traceback.print_exc()\n   self.send")
p.write_text(t,encoding='utf-8')
print('Logic Lab Input page and contextual chat API installed')
