from pathlib import Path
import shutil
R=Path(r'C:\Users\gabor\code\text-comprehension');S=Path(__file__).parent
shutil.copyfile(S/'decoding.py',R/'decoding.py')
p=R/'chat.py';t=p.read_text(encoding='utf-8');a=t.index("SYSTEM='''");b=t.index("'''",a+10)+3;t=t[:a]+'''SYSTEM='''+"'''Réponds directement à la dernière demande en français en utilisant le contexte. Ne répète pas une présentation à chaque message. Si une information manque, indique-le. Réponds uniquement en JSON : texte contient une réponse courte et pertinente ; valeurs contient les données demandées avec des clés simples et des nombres, booléens ou null. Sans données demandées, valeurs vaut {}.'''"+t[b:]
t=t.replace("key=json.dumps([selected,training],sort_keys=True)","key=json.dumps(selected,sort_keys=True)")
t=t.replace("device='cuda' if torch.cuda.is_available() and not training else 'cpu'","device='cuda' if torch.cuda.is_available() else 'cpu'")
t=t.replace("began=time.perf_counter();m=model();tokenizer", "began=time.perf_counter();loading=time.perf_counter();m=model();load_ms=round((time.perf_counter()-loading)*1000);tokenizer")
start=t.index('  parser=JsonSchemaParser(SCHEMA);prefix=');end=t.index(";return {'etat':'ok'",start)
t=t[:start]+"  from decoding import generate_json\n  raw,timing=generate_json(m['net'],tokenizer,m['tokens'],inputs,SCHEMA,sample=True);answer=validate_response(loads(raw))"+t[end:]
t=t.replace("'adapte':m['adapted'],'temps_ms'", "'adapte':m['adapted'],'materiel':m['device'],'chargement_ms':load_ms,**timing,'temps_ms'")
p.write_text(t,encoding='utf-8')
p=R/'web/input.js';t=p.read_text(encoding='utf-8');t=t.replace("${(result.temps_ms/1000).toFixed(1).replace('.',',')} s ·", "${(result.temps_ms/1000).toFixed(1).replace('.',',')} s · ${result.tokens_par_seconde??'—'} tokens/s · ${result.materiel==='cuda'?'GPU':'CPU'}${result.chargement_ms>1000?' · chargement '+(result.chargement_ms/1000).toFixed(1)+' s':''} ·");p.write_text(t,encoding='utf-8')
print('Short relevant prompt, bounded decoding, no repeated introductions and measured token speed installed')
