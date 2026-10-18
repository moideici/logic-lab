from pathlib import Path
import shutil
R=Path(r'C:\Users\gabor\code\text-comprehension');S=Path(__file__).parent
for f in ('json_output.py','serve.py','OUTPUT.md'):shutil.copyfile(S/f,R/f)
shutil.copyfile(S/'test_json_output.py',R/'tests/test_json_output.py')
p=R/'README.md';t=p.read_text(encoding='utf-8');t+='\n## Sorties et vocabulaire\n\nLe contrat prioritaire est une [sortie JSON stricte avec clés simples et valeurs typées](OUTPUT.md). Le [premier corpus de dictionnaire français](LEXICON.md) prépare le cycle suivant, sans modifier les tests de la comparaison initiale.\n';p.write_text(t,encoding='utf-8')
