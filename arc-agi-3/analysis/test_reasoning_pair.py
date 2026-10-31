"""Paired capability diagnosis before choosing another agent modification."""
from pathlib import Path
import subprocess
import sys

root=Path(__file__).resolve().parent
for thinking in ('on','off'):
    out=root/('reasoning-pair-20261031/'+thinking+'-ft09')
    if out.exists():raise FileExistsError(out)
    cmd=[sys.executable,str(root/'run_duck_loop.py'),'--source',
         str(root/'duck-loop-20261031/v13/ARC3-Inference'),
         '--game','ft09','--variant','control','--out',str(out),
         '--thinking',thinking,'--token-budget','2048','--request-tokens','1024','--seconds','1200']
    subprocess.run(cmd,check=True,timeout=1260)
