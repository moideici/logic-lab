"""Local, allowlisted browser jobs for actual game websites."""
import json,os,subprocess,threading,uuid,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ACTIVE={'starting','running'}
class ExternalArena:
    def __init__(self,directory=None):self.directory=Path(directory or ROOT/'training/external');self.lock=threading.RLock();self.processes={}
    def _path(self,identifier):
        if not isinstance(identifier,str) or not identifier or len(identifier)>80 or not all(c.isalnum() or c in '-_' for c in identifier):raise ValueError('Partie externe inconnue')
        p=self.directory/identifier
        if not p.is_dir():raise ValueError('Partie externe inconnue')
        return p
    def get(self,identifier):
        p=self._path(identifier)
        try:result=json.loads((p/'status.json').read_text(encoding='utf-8'))
        except (FileNotFoundError,json.JSONDecodeError):result={'state':'starting','steps':0,'score':0,'best_tile':0}
        result['id']=identifier;process=self.processes.get(identifier)
        if result['state'] in ACTIVE and process is None and (p/'status.json').is_file() and time.time()-(p/'status.json').stat().st_mtime>180:
            result.update(state='error',error='Cette partie ne publie plus de coups depuis trois minutes. Relancez une nouvelle partie.')
        if result['state'] in ACTIVE and process is not None and process.poll() is not None:
            result['state']='error';result['error']='Le navigateur s’est arrêté. Consultez le journal local.'
        return result
    def list(self):
        if not self.directory.exists():return []
        results=[]
        for path in self.directory.iterdir():
            if path.is_dir() and (path/'status.json').exists():
                try:results.append(self.get(path.name))
                except (ValueError,OSError):continue
        return sorted(results,key=lambda s:s.get('started_at',''),reverse=True)[:100]
    def start(self,config):
        if not isinstance(config,dict) or set(config)-{'game','mode','max_steps','size','opponent_level'}:raise ValueError('Paramètres externes invalides')
        game=config.get('game','2048')
        if game not in ('go','2048'):raise ValueError('Jeu externe inconnu')
        size=config.get('size',19);opponent=config.get('opponent_level',1)
        if game=='go' and (type(size)is not int or size not in (9,13,19) or type(opponent)is not int or not 1<=opponent<=9):raise ValueError('Taille ou adversaire Go invalide')
        mode=config.get('mode','garry');steps=config.get('max_steps',1000 if game=='go' else 10000)
        if mode not in ('garry','network','random') or type(steps) is not int or not 1<=steps<=(1000 if game=='go' else 10000):raise ValueError('Mode ou limite invalide')
        with self.lock:
            if any(self.get(k)['state'] in ACTIVE for k,p in self.processes.items() if p.poll() is None):raise ValueError('Une partie externe est déjà en cours')
            identifier=uuid.uuid4().hex;folder=self.directory/identifier;folder.mkdir(parents=True)
            (folder/'status.json').write_text(json.dumps({'state':'starting','steps':0,'score':0,'best_tile':0,'mode':mode,'game':game,'size':size if game=='go' else None,'site':'https://www.cosumi.net/en/' if game=='go' else 'https://classic.play2048.co/','started_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}),encoding='utf-8')
            command=['node',str(ROOT/('tools/real-games/external-go.mjs' if game=='go' else 'tools/real-games/external-2048.mjs')),'--job-dir',str(folder),'--max-steps',str(steps),'--mode',mode]
            if game=='go':command+=['--size',str(size),'--opponent-level',str(opponent)]
            try:
                with (folder/'process.log').open('wb') as stream:self.processes[identifier]=subprocess.Popen(command,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            except OSError as error:raise ValueError('Impossible de lancer le navigateur : '+str(error)) from error
            return self.get(identifier)
    def stop(self,identifier):
        p=self._path(identifier);(p/'stop.json').write_text('{}',encoding='utf-8');return self.get(identifier)
    def image(self,identifier):return self._path(identifier)/'board.png'
