from pathlib import Path
import json
ROOT=Path(r'C:\Users\gabor\code\playi');p=ROOT/'tools/real-games';p.mkdir(parents=True,exist_ok=True)
(p/'package.json').write_text(json.dumps({'name':'garry-real-games','private':True,'type':'module','dependencies':{'playwright':'1.62.1'}},indent=2)+'\n',encoding='utf-8')
q=ROOT/'web/fast-search.js';s=q.read_text(encoding='utf-8');old='((row>>>shift)&15)>=11';assert old in s;s=s.replace(old,'((row>>>shift)&15)>=(budget.goalRank??11)');q.write_text(s,encoding='utf-8')
print('External adapter dependencies declared; score mode can continue beyond tile 2048.')
