"""Complete a predeclared feedback ablation after the reasoning capability pair."""
import json
from pathlib import Path
import subprocess
import sys
import time
from group_regressions import compare

root=Path(__file__).resolve().parent
paths=[root/'reasoning-pair-20261031'/f'{mode}-ft09/result.json' for mode in ('on','off')]
deadline=time.monotonic()+2700
while not all(p.exists() for p in paths):
    if time.monotonic()>deadline:raise TimeoutError('Reasoning pair did not finish')
    time.sleep(2)
on,off=[json.loads(p.read_text()) for p in paths]
if any(r.get('error') or not r.get('valid_model_run') for r in (on,off)):
    raise RuntimeError('Inspect failed capability trial before changing policy')
# Prefer completions. The predeclared tie-break retains reasoning, closer to
# the competition configuration. Never select by mere action count.
mode='off' if off['levels_completed']>on['levels_completed'] else 'on'
baseline=off if mode=='off' else on
out=root/'inspection-feedback-20261031'
subprocess.run([sys.executable,str(root/'run_duck_loop.py'),'--source',
    str(root/'duck-loop-20261031/v13/ARC3-Inference'),'--game','ft09','--variant','control',
    '--out',str(out),'--thinking',mode,'--inspection-feedback',
    '--token-budget','2048','--request-tokens','1024','--seconds','1200'],check=True,timeout=1260)
candidate=json.loads((out/'result.json').read_text())
report=compare([baseline],[candidate])
report['thinking']=mode
report['promotion']='Not established by this single-family capability probe'
(out/'comparison.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report),flush=True)
