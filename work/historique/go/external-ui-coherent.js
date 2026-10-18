const $=id=>document.getElementById(id);let active=null,busy=false,lastBoard='',runningJob=null;
const labels={starting:'Ouverture du site…',running:'Garry joue sur le site',finished:'Partie terminée',truncated:'Limite de coups atteinte',stopped:'Partie arrêtée',error:'Partie interrompue'};
async function api(path,body){const response=await fetch('/api/external'+path,{method:body?'POST':'GET',headers:body?{'Content-Type':'application/json'}:{},body:body?JSON.stringify(body):undefined});const data=await response.json();if(!response.ok||!data.ok)throw Error(data.error??'Passerelle indisponible');return data.result;}
function configure(){const go=$('external-game').value==='go';$('external-go-options').hidden=!go;for(const id of ['external-game','external-mode','external-go-size'])$(id).disabled=!!runningJob;$('external-start').disabled=!!runningJob;$('external-start').title=runningJob?'Une partie est déjà en cours. Arrêtez-la avant un nouveau lancement.':'';$('external-start').textContent=go?'Lancer le Go sur COSUMI ↗':'Lancer le vrai 2048 ↗';}
function renderLive(s){const el=$('external-live-board'),key=JSON.stringify([s.game,s.board,s.last_action]);el.hidden=!s.board;if(!s.board||key===lastBoard)return;lastBoard=key;const n=s.board.length;el.innerHTML='';el.className=s.game==='go'?'external-live-go continuous-board':'external-live-tiles';el.style.gridTemplateColumns=`repeat(${n},1fr)`;s.board.forEach((row,r)=>row.forEach((v,c)=>{const cell=document.createElement('span');if(s.game==='go'){cell.className='continuous-cell'+(v?' stone-'+v:'');if(s.last_action?.row===r&&s.last_action?.col===c)cell.classList.add('continuous-last');}else{cell.className='live-tile';cell.textContent=v||'';if(v){const rank=Math.log2(v);cell.style.background=`hsl(${Math.max(25,80-rank*4)} 45% ${Math.max(35,94-rank*5)}%)`;if(rank>5)cell.style.color='#fff';}}el.append(cell);}));}
function display(s){
 active=s.id;const go=s.game==='go';
 $('external-title').textContent=go?`Go ${s.size} × ${s.size} · COSUMI`:'2048 original';
 $('external-description').textContent=go?'Garry pose les pierres avec les commandes du site.':'Garry joue avec les flèches du clavier sur le site original.';
 $('external-site-link').href=go?'https://www.cosumi.net/en/':'https://classic.play2048.co/';$('external-site-link').textContent=go?'Ouvrir COSUMI ↗':'Ouvrir 2048 original ↗';
 $('external-status').textContent=s.error??s.result_text??labels[s.state]??s.state;
 $('external-score-label').textContent=go?'RÉSULTAT DU SITE':'SCORE DU SITE';$('external-score').textContent=go?(s.result_text??'Résultat non établi'):s.score??0;$('external-score').style.fontSize=go?'18px':'';
 $('external-tile-label').textContent=go?'COUPS DE GARRY':'MEILLEURE TUILE';$('external-tile').textContent=go?s.garry_moves??0:s.best_tile??0;$('external-steps').textContent=s.steps??0;$('external-verified').textContent=`${s.transition_checks??0} transitions vérifiées`;
 $('external-probes').hidden=go;$('external-agreement').textContent=s.probe_agreement==null?'—':`${(100*s.probe_agreement).toFixed(0)} %`;$('external-regret').textContent=s.estimated_regret_mean==null?'—':s.estimated_regret_mean.toFixed(1);
 $('external-stop').disabled=!['starting','running'].includes(s.state);$('external-stop').title=$('external-stop').disabled?'Sélectionnez une partie en cours pour l’arrêter.':'';
 renderLive(s);$('external-image').hidden=!s.transition_checks;$('external-image').alt=go?'Capture du plateau de Go sur COSUMI':'Capture du vrai plateau 2048';if(s.transition_checks)$('external-image').src=`/api/external/image?id=${encodeURIComponent(s.id)}&step=${s.steps}`;
 $('external-record').hidden=!s.steps;$('external-record').href=`/api/external/trace?id=${encodeURIComponent(s.id)}`;
 $('external-rules-note').textContent=go?'COSUMI joue avec un comptage japonais et un komi de 6,5. Son résultat final fait foi. Une partie arrêtée ou limitée n’a pas de résultat établi.':'Garry continue après 2048. Chaque fusion, son score et l’apparition d’une tuile sont vérifiés. Le plateau ci-dessus suit les coups confirmés sur le site.';
 configure();
}
async function refresh(){if(busy)return;busy=true;try{
 const all=await api('/list');runningJob=all.find(s=>['starting','running'].includes(s.state))?.id??null;configure();if(!all.length)return;
 const selected=all.find(s=>s.id===active)??all[0];display(selected);const rows=$('external-history');rows.innerHTML='';
 for(const s of all.slice(0,12)){const row=document.createElement('button');row.className='external-history-row';row.setAttribute('aria-pressed',String(s.id===active));row.textContent=s.game==='go'?`${labels[s.state]??s.state} · Go ${s.size} × ${s.size} · ${s.steps} coups · ${s.result_text??'résultat non établi'}`:`${labels[s.state]??s.state} · ${s.mode??'garry'} · score ${s.score??0} · tuile ${s.best_tile??0}`;row.onclick=()=>display(s);rows.append(row);}
 }catch(error){$('external-status').textContent=error.message;}finally{busy=false;}}
 $('external-start').onclick=async()=>{try{$('external-start').disabled=true;const game=$('external-game').value;const result=await api('/start',{game,mode:$('external-mode').value,max_steps:game==='go'?1000:10000,...(game==='go'?{size:+$('external-go-size').value}:{})});runningJob=result.id;display(result);}catch(error){$('external-status').textContent=error.message;await refresh();}};
 $('external-game').onchange=configure;
 $('external-stop').onclick=async()=>{if(active)try{$('external-stop').disabled=true;await api('/stop',{id:active});$('external-status').textContent='Arrêt demandé…';}catch(error){$('external-status').textContent=error.message;}};
 setInterval(()=>{if(!$('external-tab').hidden)refresh();},250);document.querySelector('[data-tab="external"]').addEventListener('click',refresh);configure();
