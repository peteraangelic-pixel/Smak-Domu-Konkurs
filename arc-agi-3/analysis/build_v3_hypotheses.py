"""Package the isolated hypothesis tools on exact v3; no quality claim."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import re
from install_hypothesis_tools import GUIDANCE

ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'duck-lab-candidates/v3-target-control'
raw=(base/'arc3-duck.ipynb').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='8d0195f92c5518a41d14edbfca596b72c27690f269f681bbaa9af0bc3d257bcc'
nb=json.loads(raw)
src=ROOT/'analysis/champion-recovery-20261031/materialized-clean/ARC3-Inference'
module=(ROOT/'analysis/hypothesis_probes.py').read_text(encoding='utf8')
changes={
 'inference/utils/hypothesis_probes.py':module,
 'inference/agent/python_tool_sandbox.py':(src/'inference/agent/python_tool_sandbox.py').read_text(encoding='utf8')+'''
# Experimental hypotheses: helpers execute inside the existing isolated process.
from inference.utils import hypothesis_probes as _hypothesis_module
_hp_source = inspect.getsource(_hypothesis_module)
assert _SANDBOX_BOOTSTRAP.count('HOST_STDOUT = sys.stdout') == 1
_SANDBOX_BOOTSTRAP = _SANDBOX_BOOTSTRAP.replace('HOST_STDOUT = sys.stdout', _hp_source + '\\nHOST_STDOUT = sys.stdout')
_hp_anchor = '        runtime_globals["plan"] = plan'
assert _SANDBOX_BOOTSTRAP.count(_hp_anchor) == 1
_SANDBOX_BOOTSTRAP = _SANDBOX_BOOTSTRAP.replace(_hp_anchor, _hp_anchor + '\\n        runtime_globals["choose_probe"] = choose_probe\\n        runtime_globals["validate_hypotheses"] = validate')
_hypothesis_tools_installed = True
''',
 'inference/agent/tool_agent.py':(src/'inference/agent/tool_agent.py').read_text(encoding='utf8')+'\n_PYTHON_TOOL_DESCRIPTION += '+repr('\n'+GUIDANCE)+'\n_hypothesis_guidance_installed = True\n',
}
patch=''
for path,new in changes.items():
    old=(src/path).read_text(encoding='utf8') if (src/path).exists() else ''
    patch+=''.join(difflib.unified_diff(old.splitlines(keepends=True),new.splitlines(keepends=True),fromfile='a/ARC3-Inference/'+path if old else '/dev/null',tofile='b/ARC3-Inference/'+path))
s=''.join(nb['cells'][1]['source']);m=re.search(r'^ARC3_VARIANT = (.*)$',s,re.M)
v=ast.literal_eval(m[1]);v['name']='codex-v3-hypotheses';v['patch_files'].append('/kaggle/duck-hypotheses.patch')
nb['cells'][1]['source']=(s[:m.start(1)]+json.dumps(v)+s[m.end(1):]).splitlines(keepends=True)
cell="from pathlib import Path as _P\n_P('/kaggle/duck-hypotheses.patch').write_text("+repr(patch)+", encoding='utf8')\n"
nb['cells'].insert(7,{'cell_type':'code','metadata':{},'outputs':[],'execution_count':None,'source':cell.splitlines(keepends=True)})
for i,c in enumerate(nb['cells']):
    code=''.join(c.get('source',[]))
    if c['cell_type']=='code' and not code.startswith('%%'):
        code='\n'.join('pass' if l.lstrip().startswith('!') else l for l in code.splitlines())
        compile(code,f'cell{i}','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
out=ROOT/'duck-lab-candidates/v3-hypotheses';out.mkdir(exist_ok=True)
payload=json.dumps(nb,ensure_ascii=False,indent=1).encode('utf8');(out/'agent.ipynb').write_bytes(payload)
meta=json.loads((base/'kernel-metadata.json').read_text());meta.update(id='petersharps/arc3-duck-codex-v3-hypotheses-1101',title='arc3-duck-codex-v3-hypotheses-1101',code_file='agent.ipynb')
(out/'kernel-metadata.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
manifest={'sha256':hashlib.sha256(payload).hexdigest(),'base_sha256':hashlib.sha256(raw).hexdigest(),'extra_patches':1,'env_unchanged':True,'scope':'Package only; no LLM activation or quality measurement.'}
(out/'MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf8');print(json.dumps(manifest))
