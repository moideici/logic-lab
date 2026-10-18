from pathlib import Path
root=Path(r'C:\Users\gabor\code\playi')
def edit(name,old,new):
 p=root/name;t=p.read_text(encoding='utf-8')
 if old not in t:raise RuntimeError(f'Absent {name}')
 p.write_text(t.replace(old,new),encoding='utf-8')
edit('web/go-ui.js',"game.done?(s.final_score?","game.done?(game.winner===0?'Égalité au comptage':s.final_score?")
edit('web/go-ui.js',"$('go-komi').value=String(game.goState.komi);","const komi=String(game.goState.komi);if(![...$('go-komi').options].some(o=>o.value===komi)){const option=document.createElement('option');option.value=komi;option.textContent=komi.replace('.',',')+' · personnalisé';$('go-komi').append(option);} $('go-komi').value=komi;")
edit('web/app.js',"game.name==='lightsout'?'Lampes éteintes sur 25':","game.name==='lightsout'?'Lampes éteintes sur 25':game.name==='go'?'Écart final Noir − Blanc, komi compris':")
edit('web/puzzle-ui.js',"$('sudoku-options').hidden=!sudoku;",'''document.querySelector('label[for="sudoku-difficulty"]').textContent=sudoku&&!info?'DIFFICULTÉ DE LA PROCHAINE GRILLE':'DIFFICULTÉ DE LA GRILLE';document.querySelector('label[for="sliding-difficulty"]').textContent=sliding&&!info?'DIFFICULTÉ DE LA PROCHAINE GRILLE':'DIFFICULTÉ DE LA GRILLE'; $('sudoku-options').hidden=!sudoku;''')
print('Affichage des résultats et paramètres personnalisés cohérent.')
