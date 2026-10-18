"""Streaming helpers; partial text is never presented as validated JSON."""
import json,re,threading

def partial_text(raw):
    decoder=json.JSONDecoder();i=0;raw=raw.lstrip()
    if not raw.startswith('{'):return None
    i=1
    while i<len(raw):
        while i<len(raw) and raw[i].isspace():i+=1
        try:key,end=decoder.raw_decode(raw,i)
        except ValueError:return None
        if not isinstance(key,str):return None
        i=end
        while i<len(raw) and raw[i].isspace():i+=1
        if i>=len(raw) or raw[i]!=':':return None
        i+=1
        while i<len(raw) and raw[i].isspace():i+=1
        if key=='texte':
            if i>=len(raw) or raw[i]!='"':return None
            j=i+1;safe=j
            while j<len(raw):
                if raw[j]=='"':
                    try:return json.loads(raw[i:j+1])
                    except ValueError:return None
                if raw[j]=='\\':
                    if j+1>=len(raw):break
                    length=6 if raw[j+1]=='u' else 2
                    if j+length>len(raw):break
                    j+=length
                else:j+=1
                safe=j
            try:
                value=json.loads(raw[i:safe]+'"')
                return value.encode('utf-8',errors='ignore').decode('utf-8')
            except ValueError:return None
        try:_,i=decoder.raw_decode(raw,i)
        except ValueError:return None
        while i<len(raw) and raw[i].isspace():i+=1
        if i>=len(raw) or raw[i]!=',':return None
        i+=1
    return None

class StreamRequests:
    def __init__(self):self.requests={};self.lock=threading.Lock()
    def register(self,key):
        if not isinstance(key,str) or not re.fullmatch(r'[a-zA-Z0-9_-]{8,64}',key):raise ValueError('Identifiant de requête invalide')
        with self.lock:
            if key in self.requests:raise ValueError('Cette requête existe déjà')
            event=threading.Event();self.requests[key]=event;return event
    def stop(self,key):
        if not isinstance(key,str):raise ValueError('Identifiant invalide')
        with self.lock:
            event=self.requests.get(key)
            if event is not None:event.set()
            return event is not None
    def remove(self,key):
        with self.lock:self.requests.pop(key,None)
