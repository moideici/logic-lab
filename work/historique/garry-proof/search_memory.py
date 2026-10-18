"""Validated public opening experience, stored inside the general model."""
def empty_memory():return {'format':'garry-search-memory-v1','game':'connect4','entries':[]}
def _mirror(key):
    out=0
    for _ in range(7):out=(out<<7)|(key&127);key>>=7
    return out
def memory_key(obs):
    position=mask=0
    for r,row in enumerate(obs['board']):
        for c,p in enumerate(row):
            if p:
                bit=1<<(c*7+5-r);mask|=bit
                if p==obs['current_player']:position|=bit
    raw=position+mask;other=_mirror(raw);flip=other<raw
    return f'{min(raw,other):013x}',flip
def validate_memory(data):
    if not isinstance(data,dict) or data.get('format')!='garry-search-memory-v1' or data.get('game')!='connect4' or not isinstance(data.get('entries'),list) or len(data['entries'])>100000:raise ValueError('Mémoire de recherche invalide')
    seen=set();entries=[]
    for e in data['entries']:
        if not isinstance(e,dict) or not isinstance(e.get('key'),str) or len(e['key'])!=13 or any(c not in '0123456789abcdef' for c in e['key']) or type(e.get('column')) is not int or not 0<=e['column']<7 or e.get('guarantee') not in ('experience','non_loss','win','draw') or e['key'] in seen:raise ValueError('Position de mémoire invalide')
        key=int(e['key'],16);copy=key
        if key>=1<<49 or _mirror(key)<key:raise ValueError('Clé de mémoire invalide')
        for c in range(7):
            chunk=copy&127
            if chunk==127 or (c==e['column'] and chunk>=63):raise ValueError('Colonne de mémoire illégale')
            copy>>=7
        seen.add(e['key']);entries.append({k:e[k] for k in ('key','column','guarantee')})
    return {'format':data['format'],'game':data['game'],'entries':entries}
def lookup_memory(obs,legal,memory):
    if not memory:return None
    key,flip=memory_key(obs)
    entry=next((e for e in memory['entries'] if e['key']==key),None)
    if entry is None:return None
    column=6-entry['column'] if flip else entry['column']
    return {**entry,'column':column} if {'column':column} in legal else None
def memory_decision(entry,remaining):
    proof=None if entry['guarantee']=='experience' else entry['guarantee'];complete=proof in ('win','draw');column=entry['column']
    return {'column':column},{'method':'solved_opening' if proof else 'self_play_opening','runtime':'opening_memory','nodes':0,'depth':0,'value':1000000-remaining if proof=='win' else 0,'proof':proof,'search_complete':complete,'outcome_proven':complete,'certified_non_loss':bool(proof),'certificate_nodes':0,'solved_horizon':remaining if complete else None,'mate_distance_known':False,'principal_variation':[column],'learned_value':False,'evaluation_scope':'offline_certified_move' if proof else 'adversarial_self_play','forced_win':proof=='win','forced_loss':False,'optimal':proof=='draw','outcome_optimal':complete,'opening_memory':True}
