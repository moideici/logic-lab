from pathlib import Path
R=Path(r'C:\Users\gabor\code\playi')
p=R/'logic_arena/continuous.py';t=p.read_text(encoding='utf-8').replace('def run(output,seconds=3600):','def run(output,seconds=3600,resume=False):')
t=t.replace("champion.save(output/'initial.json');expected_hash", "saved=json.loads((output/'status.json').read_text(encoding='utf-8')) if resume else None;elapsed_before=saved['elapsed_seconds'] if saved else 0;deadline=start+max(0,seconds-elapsed_before);\n if not resume:champion.save(output/'initial.json')\n expected_hash")
needle=";last_write=0.;episode=0"
t=t.replace(needle,";last_write=0.;episode=0\n if saved:\n  if saved['model_sha256']!=expected_hash:raise RuntimeError('Le modèle a changé depuis le dernier point de reprise')\n  state.update(saved);state.update(state='running',phase='resuming',pid=os.getpid(),resumes=saved.get('resumes',0)+1);episode=saved.get('episode',0)\n  for line in (output/'cases.jsonl').read_text(encoding='utf-8').splitlines():\n   c=json.loads(line);history.add(c['id']);g=c['observation']['game']\n   if c['split']=='train':training.append(c)\n   elif c['split']=='validation':fresh_valid[g].append(c)\n   else:fresh_test.append(c)\n  rng.seed(171601+episode)\n state['ends_at']=datetime.fromtimestamp(time.time()+max(0,seconds-elapsed_before),timezone.utc).isoformat()")
t=t.replace('elapsed_seconds=round(now-start,2)','elapsed_seconds=round(elapsed_before+now-start,2)')
t=t.replace("args=p.parse_args();run(args.output,args.seconds)","p.add_argument('--resume',action='store_true');args=p.parse_args();run(args.output,args.seconds,args.resume)")
p.write_text(t,encoding='utf-8')
p=R/'logic_arena/continuous_service.py';t=p.read_text(encoding='utf-8').replace("creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)","creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)|getattr(subprocess,'CREATE_NEW_PROCESS_GROUP',0)");p.write_text(t,encoding='utf-8')
print('Checkpoint resume and independent process group installed')
