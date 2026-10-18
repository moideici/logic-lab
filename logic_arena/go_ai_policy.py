"""AI procedure: play board moves, then pass and agree; never negotiate at random."""
from .go_rules import group,neighbors,play_candidate
def go_ai_actions(o,legal):
 s=o['go_state'];n=len(o['board']);p=o['current_player'];b=o['board']
 if s['phase']=='scoring':
  disputed=any(b[i//n][i%n]==p and len(group(b,i//n,i%n)[1])>=2 for i in s['dead'])
  return [a for a in legal if a.get('resume')] if disputed else [a for a in legal if a.get('accept')]
 placements=[a for a in legal if 'row'in a];passing=next((a for a in legal if a.get('pass')),None)
 if o['moves']>=2*n*n or not placements:return [passing] if passing else placements
 seen=set(s['seen']);useful=False
 for a in placements:
  r,c=a['row'],a['col'];after,captured,_=play_candidate(b,p,r,c,seen)
  if captured:useful=True;break
  if all(b[y][x]==p for y,x in neighbors(n,r,c)):continue
  if len(group(after,r,c)[1])>=2:useful=True;break
 return placements if useful else [passing] if passing else placements
