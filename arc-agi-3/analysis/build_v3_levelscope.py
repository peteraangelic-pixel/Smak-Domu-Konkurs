"""One environment-variable ablation on exact recovered v3; no extra patches."""
import ast
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]


def main():
    base=ROOT/'analysis/champion-recovery-20261031/champion-v3'
    source=base/'arc3-duck.ipynb'
    assert hashlib.sha256(source.read_bytes()).hexdigest()=='8d0195f92c5518a41d14edbfca596b72c27690f269f681bbaa9af0bc3d257bcc'
    nb=json.loads(source.read_text(encoding='utf8'))
    before=[''.join(c.get('source',[])) for c in nb['cells']]
    idx=next(i for i,s in enumerate(before) if re.search(r'^ARC3_VARIANT = ',s,re.M))
    match=re.search(r'^ARC3_VARIANT = (.*)$',before[idx],re.M)
    variant=ast.literal_eval(match.group(1))
    assert variant['env']=={'ARC3_WORLD_MODEL':'1'}
    variant['env']['ARC3_PERSISTENT_FUNCTIONS_SCOPE']='levelup'
    variant['name']='codex-v3-levelscope'
    nb['cells'][idx]['source']=(before[idx][:match.start(1)]+json.dumps(variant,sort_keys=True)+before[idx][match.end(1):]).splitlines(keepends=True)
    after=[''.join(c.get('source',[])) for c in nb['cells']]
    assert [i for i,(a,b) in enumerate(zip(before,after)) if a!=b]==[idx]
    compiled=0
    for i,c in enumerate(nb['cells']):
        s=after[i]
        if c['cell_type']=='code' and not s.lstrip().startswith('%%'):
            s='\n'.join('pass' if l.lstrip().startswith('!') else l for l in s.splitlines())
            compile(s,f'cell{i}','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT);compiled+=1
    out=ROOT/'duck-lab-candidates/v3-levelscope';out.mkdir(exist_ok=True)
    payload=json.dumps(nb,ensure_ascii=False,indent=1).encode('utf8');(out/'agent.ipynb').write_bytes(payload)
    meta=json.loads((base/'kernel-metadata.json').read_text(encoding='utf8'));meta.pop('id_no',None)
    meta.update(id='petersharps/arc3-duck-codex-v3-levelscope-1101',title='arc3-duck-codex-v3-levelscope-1101',code_file='agent.ipynb')
    (out/'kernel-metadata.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
    record={'base_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'sha256':hashlib.sha256(payload).hexdigest(),
            'changed_cell':idx,'compiled_code_cells':compiled,'env_delta':{'ARC3_PERSISTENT_FUNCTIONS_SCOPE':['game','levelup']},
            'extra_patches':0,'score_measured':False,'model_budget_roster_unchanged':True}
    (out/'MANIFEST.json').write_text(json.dumps(record,indent=2),encoding='utf8');print(json.dumps(record,indent=2))


if __name__=='__main__':main()
