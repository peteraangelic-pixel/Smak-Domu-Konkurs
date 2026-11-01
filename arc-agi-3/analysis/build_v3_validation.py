"""Package one targeted validation hook on exact v3, preserving env/budgets."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'duck-lab-candidates/v3-target-control'
raw=(base/'arc3-duck.ipynb').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='8d0195f92c5518a41d14edbfca596b72c27690f269f681bbaa9af0bc3d257bcc'
nb=json.loads(raw)
src=ROOT/'analysis/champion-recovery-20261031/materialized-clean/ARC3-Inference'
path='inference/agent/tool_agent.py';old=(src/path).read_text(encoding='utf8')
changes={path:old+'\nfrom inference.utils.model_validation_nudge import install as _install_validation_nudge\n_install_validation_nudge(ToolAgent)\n',
         'inference/utils/model_validation_nudge.py':Path(__file__).with_name('model_validation_nudge.py').read_text(encoding='utf8')}
patch=''
for path,new in changes.items():
    old=(src/path).read_text(encoding='utf8') if (src/path).exists() else ''
    patch+=''.join(difflib.unified_diff(old.splitlines(keepends=True),new.splitlines(keepends=True),
                  fromfile='a/ARC3-Inference/'+path if old else '/dev/null',tofile='b/ARC3-Inference/'+path))
s=''.join(nb['cells'][1]['source']);m=re.search(r'^ARC3_VARIANT = (.*)$',s,re.M)
v=ast.literal_eval(m[1]);assert v['env']=={'ARC3_WORLD_MODEL':'1'}
v['name']='codex-v3-validation';v['patch_files'].append('/kaggle/duck-validation.patch')
nb['cells'][1]['source']=(s[:m.start(1)]+json.dumps(v)+s[m.end(1):]).splitlines(keepends=True)
cell="from pathlib import Path as _P\n_P('/kaggle/duck-validation.patch').write_text("+repr(patch)+",encoding='utf8')\n"
nb['cells'].insert(7,{'cell_type':'code','metadata':{},'outputs':[],'execution_count':None,'source':cell.splitlines(keepends=True)})
for i,c in enumerate(nb['cells']):
    code=''.join(c.get('source',[]))
    if c['cell_type']=='code' and not code.startswith('%%'):
        compile('\n'.join('pass' if l.lstrip().startswith('!') else l for l in code.splitlines()),f'cell{i}','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
out=ROOT/'duck-lab-candidates/v3-validation';out.mkdir(exist_ok=True)
payload=json.dumps(nb,ensure_ascii=False,indent=1).encode('utf8');(out/'agent.ipynb').write_bytes(payload)
meta=json.loads((base/'kernel-metadata.json').read_text());meta.update(id='petersharps/arc3-duck-codex-v3-validation-1101',title='arc3-duck-codex-v3-validation-1101',code_file='agent.ipynb')
(out/'kernel-metadata.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
manifest={'sha256':hashlib.sha256(payload).hexdigest(),'base_sha256':hashlib.sha256(raw).hexdigest(),'extra_patches':1,'env_unchanged':True,'scope':'One prompt hook for existing simulator validation; no quality measurement.'}
(out/'MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf8');print(json.dumps(manifest))
