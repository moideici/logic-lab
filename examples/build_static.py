"""Produit dist/ à partir des sources web pour l'hébergement statique."""
from pathlib import Path
import shutil

root=Path(__file__).resolve().parents[1]
shutil.copytree(root/"web",root/"dist",dirs_exist_ok=True)
print(root/"dist")
