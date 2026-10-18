from pathlib import Path
import shutil
R=Path(r'C:\Users\gabor\code\playi');S=Path(__file__).parent
for f in ('game-regressions.test.mjs','test_game_regressions.py'):shutil.copyfile(S/f,R/'tests'/f)
p=R/'tools/real-games/external-go.mjs';t=p.read_text(encoding='utf-8');needle='export function inferGoMove'
t=t.replace(needle,"export async function submitGoPass(page){await page.locator('#pass-2').click();await page.locator('#yes').waitFor();await sleep(650);if(!/Are You Sure to Pass/.test(await page.locator('#message').innerText()))throw Error('Confirmation de passe inattendue');await page.locator('#yes').click();await page.locator('#yes').waitFor({state:'detached'});}\n"+needle)
t=t.replace("if(a.pass)await page.locator('#pass-2').click();","if(a.pass)await submitGoPass(page);")
p.write_text(t,encoding='utf-8')
print('Regression tests and real-site pass confirmation installed')
