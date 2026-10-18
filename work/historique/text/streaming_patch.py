from pathlib import Path
import shutil
R=Path(r'C:\Users\gabor\code\text-comprehension');S=Path(__file__).parent
for name in ('streaming.py','test_streaming.py'):
    dest=R/('tests/'+name if name.startswith('test_') else name);shutil.copyfile(S/name,dest)
p=R/'decoding.py';s=p.read_text(encoding='utf-8')
s=s.replace('def __init__(self,tokenizer,prompt_length):self.tokenizer=tokenizer;self.prompt_length=prompt_length;self.first=None','def __init__(self,tokenizer,prompt_length,on_progress=None,cancel=None):self.tokenizer=tokenizer;self.prompt_length=prompt_length;self.first=None;self.on_progress=on_progress;self.cancel=cancel;self.last_update=0')
s=s.replace("  if self.first is None:self.first=time.perf_counter()", "  if self.cancel is not None and self.cancel.is_set():return True\n  if self.first is None:self.first=time.perf_counter()")
s=s.replace("  if not text.endswith('}'):return False", "  if self.on_progress and time.perf_counter()-self.last_update>.08:\n   from streaming import partial_text\n   self.on_progress({'phase':'generation','texte':partial_text(text) or ''});self.last_update=time.perf_counter()\n  if not text.endswith('}'):return False")
s=s.replace('max_tokens=320,max_seconds=35):','max_tokens=320,max_seconds=35,on_progress=None,cancel=None):')
s=s.replace("stop=CompleteObject(tokenizer,inputs['input_ids'].shape[1]);", "stop=CompleteObject(tokenizer,inputs['input_ids'].shape[1],on_progress,cancel);")
s=s.replace(" elapsed=time.perf_counter()-began;", " if cancel is not None and cancel.is_set():raise InterruptedError('Génération arrêtée')\n elapsed=time.perf_counter()-began;")
p.write_text(s,encoding='utf-8')
p=R/'chat.py';s=p.read_text(encoding='utf-8').replace('def respond(req):','def respond(req,on_progress=None,cancel=None):')
s=s.replace(' with LOCK:\n  began='," if on_progress:on_progress({'phase':'attente'})\n with LOCK:\n  if cancel is not None and cancel.is_set():raise InterruptedError('Génération arrêtée')\n  if on_progress:on_progress({'phase':'preparation'})\n  began=")
s=s.replace('inputs,SCHEMA,sample=True);','inputs,SCHEMA,sample=True,on_progress=on_progress,cancel=cancel);')
s=s.replace("'base':'Qwen3-0.6B','adapte'", "'base':'Qwen3-0.6B','verification':'non_verifiee','adapte'")
p.write_text(s,encoding='utf-8')
p=R/'serve.py';s=p.read_text(encoding='utf-8')
s=s.replace("ROOT=Path(__file__).resolve().parent;LOCK=threading.Lock();CACHE={}","ROOT=Path(__file__).resolve().parent;LOCK=threading.Lock();CACHE={}\nfrom streaming import StreamRequests\nSTREAMS=StreamRequests()")
s=s.replace("if self.path not in ('/analyse','/api/chat'):","if self.path not in ('/analyse','/api/chat','/api/chat/stream','/api/chat/stop'):")
s=s.replace("256000 if self.path=='/api/chat'", "256000 if self.path.startswith('/api/chat')")
s=s.replace("   if self.path=='/api/chat':", "   if self.path=='/api/chat/stop':\n    if not isinstance(req,dict) or set(req)!={'id'}:raise ValueError('Identifiant requis')\n    self.send({'arrete':STREAMS.stop(req['id'])});return\n   if self.path=='/api/chat/stream':\n    from chat import respond,validate_messages\n    validate_messages(req);request_id=self.headers.get('X-Request-ID','');cancel=STREAMS.register(request_id)\n    self.send_response(200);self.send_header('Content-Type','text/event-stream; charset=utf-8');self.send_header('Cache-Control','no-store');self.end_headers()\n    def event(kind,payload):\n     try:self.wfile.write(('event: '+kind+'\\ndata: '+dumps(payload)+'\\n\\n').encode('utf-8'));self.wfile.flush()\n     except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError):cancel.set();raise InterruptedError('Client déconnecté')\n    try:\n     result=respond(req,on_progress=lambda payload:event('progress',payload),cancel=cancel);event('result',result)\n    except InterruptedError:pass\n    except Exception:\n     import traceback;traceback.print_exc()\n     try:event('error',{'texte':'La réponse n’a pas pu être terminée. Vous pouvez réessayer.'})\n     except InterruptedError:pass\n    finally:STREAMS.remove(request_id)\n    return\n   if self.path=='/api/chat':")
p.write_text(s,encoding='utf-8')
for name in ('input.html','input.js'):
    shutil.copyfile(S/('redesign-'+name),R/'web'/name)
p=R/'web/input.css';s=p.read_text(encoding='utf-8');marker='/* Input conversation workspace */'
if marker in s:s=s[:s.index(marker)]
p.write_text(s+'\n'+(S/'redesign.css').read_text(encoding='utf-8'),encoding='utf-8')
print('Streaming, cancellation and conversation interface installed')
