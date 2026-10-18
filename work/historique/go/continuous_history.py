"""Exclude every earlier continuous-training state from subsequent new trials."""
import json
from pathlib import Path
from .continuous import atomic_json

def historical_case_ids(directory,current):
    directory=Path(directory);current=Path(current).resolve();identifiers=set();sources=[]
    if not directory.exists():return identifiers,sources
    for folder in sorted(directory.iterdir()):
        path=folder/'cases.jsonl'
        if folder.resolve()==current or not path.is_file():continue
        stat=path.stat();signature={'size':stat.st_size,'mtime_ns':stat.st_mtime_ns};cache=folder/'case-index.json'
        try:
            data=json.loads(cache.read_text(encoding='utf-8'))
            if data.get('source')!=signature or not isinstance(data.get('ids'),list) or any(not isinstance(key,str) for key in data['ids']):raise ValueError('Index périmé')
            keys=set(data['ids'])
        except (OSError,ValueError,TypeError):
            keys=set()
            with path.open(encoding='utf-8') as stream:
                for number,line in enumerate(stream,1):
                    try:
                        case=json.loads(line);key=case['id']
                        if not isinstance(key,str) or case['split'] not in ('train','validation','test'):raise ValueError('Cas invalide')
                        keys.add(key)
                    except (ValueError,KeyError,TypeError) as error:
                        raise ValueError(f'Historique incomplet : {path.name}, ligne {number}') from error
            if path.stat().st_size!=signature['size'] or path.stat().st_mtime_ns!=signature['mtime_ns']:raise ValueError('L’historique a changé pendant sa lecture')
            atomic_json(cache,{'source':signature,'ids':sorted(keys)})
        identifiers.update(keys);sources.append({'job':folder.name,'unique_states':len(keys),**signature})
    return identifiers,sources
