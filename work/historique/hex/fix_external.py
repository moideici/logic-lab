from pathlib import Path
p=Path(r'C:\Users\gabor\code\playi\tools\real-games\external-2048.mjs');s=p.read_text(encoding='utf-8')
s=s.replace("  let state=await readVisible(page);status.state='running';", "  const consent=async()=>{const essential=page.locator('#ez-accept-necessary');if(await essential.isVisible()){await essential.click();status.cookie_choice='necessary_only';}};\n  let state=await readVisible(page);status.state='running';")
s=s.replace("   if(state.game_over){", "   if(step%10===0||state.won)await consent();\n   if(state.game_over){")
s=s.replace("fs.renameSync(tmp,path.join(jobDir,'board.png'));", "await renameImage(tmp,path.join(jobDir,'board.png'));" )
marker='export async function readVisible(page)'
s=s.replace(marker,"async function renameImage(tmp,target){for(let i=0;i<8;i++)try{fs.renameSync(tmp,target);return;}catch(e){if(!['EPERM','EACCES','EBUSY'].includes(e.code)||i===7)throw e;await new Promise(r=>setTimeout(r,20*(i+1)));}}\n"+marker)
p.write_text(s,encoding='utf-8')
