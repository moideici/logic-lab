exec((__import__('pathlib').Path(__file__).parent/'integrate.py').read_text(encoding='utf-8').split('# Freeze the last')[0])
edit('web/engine.js',[(" positionValue(o){",''' adoptAddedModes(source,knownGames){
  if(this.hidden!==source.hidden)return;
  for(const game of GARRY_GAMES){if(knownGames.includes(game))continue;
   const [ni,no]=SPECS[game],a=GARRY_INPUT_OFFSETS[game],b=GARRY_OUTPUT_OFFSETS[game],tag=GARRY_FEATURES+GARRY_GAMES.indexOf(game);
   this.w1.set(source.w1.slice(a*this.hidden,(a+ni)*this.hidden),a*this.hidden);
   this.w1.set(source.w1.slice(tag*this.hidden,(tag+1)*this.hidden),tag*this.hidden);
   for(let j=0;j<this.hidden;j++)this.w2.set(source.w2.slice(j*this.output+b,j*this.output+b+no),j*this.output+b);
   this.b2.set(source.b2.slice(b,b+no),b);this.steps+=source.gameSteps[game]-this.gameSteps[game];this.gameSteps[game]=source.gameSteps[game];
  }
 }
 positionValue(o){''')])
edit('web/app.js',[
("let general=null,selectedPiece=null;", "let general=null,selectedPiece=null,packagedModel=null;"),
("function useGarry(data){const next=data instanceof GarryModel?data:new GarryModel(data);general=next;", "function useGarry(data,knownGames=data?.games){const next=data instanceof GarryModel?data:new GarryModel(data);if(packagedModel&&Array.isArray(knownGames)&&knownGames.length<11)next.adoptAddedModes(packagedModel,knownGames);general=next;"),
("if(response.ok)shipped=await response.json();", "if(response.ok){shipped=await response.json();packagedModel=new GarryModel(shipped);}"),
("if(stored.version!==AGENT_VERSION)await persistModels();", "if(stored.version!==AGENT_VERSION||stored.input!==general.input)await persistModels();"),
("useGarry(data.format==='logic-arena-suite-v1'?GarryModel.fuse(data.models):data);", "useGarry(data.format==='logic-arena-suite-v1'?GarryModel.fuse(data.models):data,data.format==='logic-arena-suite-v1'?data.models.map(m=>m.game):data.games);")])
edit('web/planner.js',[("limit:o.game==='connect4'?CONNECT_LIMITS[9]:LIMITS[9]", "limit:o.game==='connect4'?CONNECT_LIMITS[9]:['draughts','breakthrough'].includes(o.game)?30000:LIMITS[9]")])
edit('web/index.html',[("expectimax à 2048 contraintes", "expectimax à 2048, contraintes"),("3617 actions", "3 617 actions")])
edit('logic_arena/__main__.py',[("six jeux et un réseau partagé", "onze jeux et un réseau partagé")])
edit('examples/train_new_games.py',[
("model=GarryPolicy.load(ROOT/'versions/3.2.0/garry.json')", "model=GarryPolicy.load(ROOT/'web/models/garry.json')"),
("'architecture':[2060,48,48,925]", "'architecture':[2494,48,48,3617]")])
edit('examples/train_garry_repertoire.py',[
("    for game in GAMES:\n        model=", "    for game in GAMES:\n        if not any(c['observation']['game']==game for c in train):continue\n        if not any(c['observation']['game']==game for c in val) or not any(c['observation']['game']==game for c in test):raise ValueError('Missing validation or test split: '+game)\n        model="),
("retention_before=metrics(base,retention,game) if retention else None", "retention_before=metrics(base,retention,game) if any(c['observation']['game']==game for c in retention) else None"),
("retained=metrics(model,retention,game) if retention else None", "retained=metrics(model,retention,game) if retention_before is not None else None"),
("metrics(candidate,retention,game) if retention else None", "metrics(candidate,retention,game) if retention_before is not None else None"),
("'software_version':'3.1.0'", "'software_version':'4.0.0'"),
("data['summary']", "data.get('summary',{})")])
# Validate the additional public turn state before accepting browser replay.
edit('web/repertoire.js',[("  const env=Object.assign",'''  if(![1,2].includes(o.current_player))throw Error('Joueur invalide');
  if(o.game==='draughts'){
   const s=o.draughts_state,coordinate=p=>Array.isArray(p)&&p.length===2&&p.every(v=>Number.isInteger(v)&&v>=0&&v<10)&&(p[0]+p[1])%2===1;
   if(!s||Object.keys(s).some(k=>!['forced_piece','pending_captures','quiet_plies','endgame_16','endgame_5','repetitions'].includes(k))||s.forced_piece!==null&&!coordinate(s.forced_piece)||!Array.isArray(s.pending_captures)||s.pending_captures.length>20||s.pending_captures.some(p=>!coordinate(p))||new Set(s.pending_captures.map(p=>p.join(','))).size!==s.pending_captures.length||!Number.isInteger(s.quiet_plies)||s.quiet_plies<0||s.quiet_plies>50||['endgame_16','endgame_5'].some(k=>s[k]!==null&&(!Number.isInteger(s[k])||s[k]<0||s[k]>32))||!s.repetitions||typeof s.repetitions!=='object'||Array.isArray(s.repetitions)||Object.entries(s.repetitions).some(([k,v])=>!/^[12]:[0-4]{100}$/.test(k)||!Number.isInteger(v)||v<1||v>3)||o.board.some((row,r)=>row.some((v,c)=>v&&(r+c)%2!==1)))throw Error('État public des dames invalide');
  }
  const env=Object.assign''')])
print('Old personal models keep their learned parameters and receive trained added modes.')
