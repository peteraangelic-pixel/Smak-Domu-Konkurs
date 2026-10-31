"""Package the peer gate on the reproduced Gemma v17, retaining its guard.

Input lineage: Codex v3-template + Gemma c4/acb2a95 guard packaging;
single-mismatch gate proposed by Gemma 6d/004769ec.
No competition upload or score prediction.
"""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = ROOT/'analysis/peer-refresh-20261031/ARC3/duck-v17/arc3-duck-v17.ipynb'
    assert hashlib.sha256(source.read_bytes()).hexdigest() == '76b57100dbac44a27990bc63702cf5516b9d418e3c7db2ab68d0edd13b519795'
    nb = json.loads(source.read_text(encoding='utf8'))
    body = (ROOT/'analysis/template_gated_transfer.py').read_text(encoding='utf8').rstrip('\n')+'\n'
    path = 'ARC3-Inference/inference/utils/codex_template_transfer.py'
    segment = (f'diff --git a/{path} b/{path}\nnew file mode 100644\n'
               f'index 0000000..1111111\n--- /dev/null\n+++ b/{path}\n'
               f'@@ -0,0 +1,{len(body.splitlines())} @@\n'
               + ''.join('+'+line+'\n' for line in body.splitlines()))
    changed = 0
    for cell in nb['cells']:
        text = ''.join(cell.get('source',[]))
        if cell.get('cell_type')!='code' or text.startswith('%%') or 'codex_template_transfer.py' not in text:
            continue
        literals = [n for n in ast.walk(ast.parse(text)) if isinstance(n,ast.Constant)
                    and isinstance(n.value,str) and n.value.startswith('diff --git')
                    and f'diff --git a/{path}' in n.value]
        assert len(literals)==1
        node = literals[0]
        patch = node.value
        start = patch.index(f'diff --git a/{path}')
        end = patch.index('\ndiff --git ',start)+1
        patch = patch[:start]+segment+patch[end:]
        text = text.replace(ast.get_source_segment(text,node),json.dumps(patch,ensure_ascii=False),1)
        text = text.replace('v17-champion-template','codex-v3-guarded-gated')
        cell['source'] = text.splitlines(keepends=True)
        changed += 1
    assert changed==1
    out = ROOT/'duck-lab-candidates/guarded-gated'
    out.mkdir(exist_ok=True)
    payload = (json.dumps(nb,indent=1,ensure_ascii=False)+'\n').encode('utf8')
    (out/'agent.ipynb').write_bytes(payload)
    meta = json.loads((source.parent/'kernel-metadata.json').read_text(encoding='utf8'))
    meta.update(id='petersharps/arc3-duck-codex-guarded-gated',title='arc3-duck-codex-guarded-gated',code_file='agent.ipynb')
    (out/'kernel-metadata.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
    print(hashlib.sha256(payload).hexdigest(),out/'agent.ipynb')


if __name__=='__main__':main()
