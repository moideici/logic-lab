from pathlib import Path
import shutil
R=Path(r'C:\Users\gabor\code\playi');S=Path(__file__).parent
p=R/'logic_arena/continuous.py';t=p.read_text(encoding='utf-8').replace("champion.for_game(game).choose(obs,legal,10).action","champion.for_game(game).choose(obs,legal,10)");t=t.replace('os.replace(temporary,path)','''
 for attempt in range(12):
  try:os.replace(temporary,path);break
  except PermissionError:
   if attempt==11:raise
   time.sleep(.01*(attempt+1))''');p.write_text(t,encoding='utf-8')
shutil.copyfile(S/'strategic_styles.py',R/'logic_arena/strategic_styles.py');shutil.copyfile(S/'strategic-styles.js',R/'web/strategic-styles.js')
p=R/'web/planner.js';t=p.read_text(encoding='utf-8');t="import {applyStrategicStyles} from './strategic-styles.js';\n"+t;t=t.replace('const {selected,info}=selectQuality(result.action_values,level,tieLogits,o.game),best=info.selected_is_best;',"const styled=applyStrategicStyles(o,result.action_values,decision.info.style??'balanced',result.info.analysis_exact);result.action_values=styled.values;result.info.style_effect=styled.changed?'strategic_evaluation':'equal_quality_tiebreak';const {selected,info}=selectQuality(result.action_values,level,tieLogits,o.game),best=info.selected_is_best;");p.write_text(t,encoding='utf-8')
p=R/'logic_arena/planner.py';t=p.read_text(encoding='utf-8').replace('time_ms=None, logits=None):',"time_ms=None, logits=None, style='balanced'):");t=t.replace('    selected,ranking=select_quality(values,level,logits,game)',"    from .strategic_styles import apply_styles\n    values,changed=apply_styles(obs,values,style,info.get('analysis_exact',False));info['style_effect']='strategic_evaluation' if changed else 'equal_quality_tiebreak'\n    selected,ranking=select_quality(values,level,logits,game)");p.write_text(t,encoding='utf-8')
p=R/'logic_arena/neural.py';t=p.read_text(encoding='utf-8').replace('self.time_ms, logits=logits)','self.time_ms, logits=logits, style=self.style)');p.write_text(t,encoding='utf-8')
p=R/'logic_arena/agents.py';t=p.read_text(encoding='utf-8').replace('legal_actions[0],self.time_ms)','legal_actions[0],self.time_ms,style=self.style)');p.write_text(t,encoding='utf-8')
# Keep errors visible after a dead process or stale heartbeat, including server restarts.
p=R/'logic_arena/continuous_service.py';t=p.read_text(encoding='utf-8').replace("d=json.loads(p.read_text(encoding='utf-8'));d['id']=p.parent.name;out.append(d)","d=json.loads(p.read_text(encoding='utf-8'));d['id']=p.parent.name\n    process=self.processes.get(p.parent.name)\n    if d['state']=='running' and ((process is not None and process.poll() is not None) or time.time()-p.stat().st_mtime>60):d.update(state='error',error='Le processus d’apprentissage s’est arrêté ; le dernier modèle accepté est conservé.')\n    out.append(d)");p.write_text(t,encoding='utf-8')
print('Live process recovery and strategic styles fixed')
