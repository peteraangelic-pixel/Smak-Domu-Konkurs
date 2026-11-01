"""One policy instruction on exact v3; no extra tools, memory or guard changes."""
import ast
import hashlib
import json
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
LESSON=(
    'Before searching a handwritten simulator, test its causal order against actual observations. '
    'Separate input activation, object movement, autonomous effects, and contact or merging. '
    'An input that leaves the selected object stationary may still advance other mechanics; '
    'test rather than assume this. Check whether targets are chosen before or after movement. '
    'Use your own functions or check_model with explicit adapters to compare compact predicted '
    'and observed states on recorded transitions. Repair a counterexample before increasing search depth. '
    'If two rules still fit, choose one inexpensive action where their predictions disagree. '
    'Avoid another inspection that cannot distinguish those rules.'
)
base=ROOT/'duck-lab-candidates/v3-target-control';raw=(base/'arc3-duck.ipynb').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='8d0195f92c5518a41d14edbfca596b72c27690f269f681bbaa9af0bc3d257bcc'
nb=json.loads(raw);original=json.loads(raw)
s=''.join(nb['cells'][1]['source']);m=re.search(r'^ARC3_VARIANT = (.*)$',s,re.M)
variant=ast.literal_eval(m[1]);assert variant['env']=={'ARC3_WORLD_MODEL':'1'}
variant['name']='codex-v3-phase-lesson';variant['env']['ARC3_SYSTEM_PROMPT_PREFIX']=LESSON
nb['cells'][1]['source']=(s[:m.start(1)]+json.dumps(variant)+s[m.end(1):]).splitlines(keepends=True)
assert len(nb['cells'])==len(original['cells'])
assert [i for i,(a,b) in enumerate(zip(nb['cells'],original['cells'])) if a!=b]==[1]
for i,c in enumerate(nb['cells']):
    code=''.join(c.get('source',[]))
    if c['cell_type']=='code' and not code.startswith('%%'):
        compile('\n'.join('pass' if line.lstrip().startswith('!') else line for line in code.splitlines()),f'cell{i}','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
out=ROOT/'duck-lab-candidates/v3-phase-lesson';out.mkdir(exist_ok=True)
payload=json.dumps(nb,ensure_ascii=False,indent=1).encode('utf8');(out/'agent.ipynb').write_bytes(payload)
metadata=json.loads((base/'kernel-metadata.json').read_text())
metadata.update(id='petersharps/arc3-duck-codex-v3-phase-lesson-1101',title='arc3-duck-codex-v3-phase-lesson-1101',code_file='agent.ipynb')
(out/'kernel-metadata.json').write_text(json.dumps(metadata,indent=2),encoding='utf8')
manifest={'sha256':hashlib.sha256(payload).hexdigest(),'base_sha256':hashlib.sha256(raw).hexdigest(),
          'changed_cells':[1],'extra_patches':0,'only_policy_change':'ARC3_SYSTEM_PROMPT_PREFIX',
          'instruction':LESSON,'qualification':'General causal-model validation instruction; no game-specific model, route, ID or prediction of score.'}
(out/'MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf8');print(json.dumps(manifest))
