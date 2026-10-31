"""Reconstruct shipped agent sources from notebook patches without executing cells."""
import ast
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def materialize(notebook, output):
    notebook, output = Path(notebook), Path(output)
    if output.exists():
        raise FileExistsError(output)
    source = output / 'ARC3-Inference'
    shutil.copytree(ROOT / 'kaggle/ops/results/r033-recon-bundle/bundle/src/ARC3-Inference', source)
    nb = json.loads(notebook.read_text(encoding='utf8'))
    hashes = []
    for i, item in enumerate(nb['cells']):
        if item.get('cell_type') != 'code':
            continue
        cell = ''.join(nb['cells'][i]['source'])
        if not any(marker in cell for marker in ('diff --git', '--- a/', '--- /dev/null')):
            continue
        if cell.startswith('%%') and not cell.startswith('%%writefile /kaggle/harness-changes.patch'):
            continue
        patches = [cell.split('\n', 1)[1]] if cell.startswith('%%writefile /kaggle/harness-changes.patch') else [
            n.value for n in ast.walk(ast.parse(cell))
            if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and n.value.startswith(('diff --git', '--- a/', '--- /dev/null'))]
        for patch in patches:
            subprocess.run(['git', 'apply', '--include=ARC3-Inference/*', '--whitespace=nowarn', '-'],
                           input=(patch.rstrip('\n') + '\n').encode(), cwd=output, check=True)
            hashes.append(hashlib.sha256(patch.encode()).hexdigest())
    for path in (source / 'inference').rglob('*.py'):
        compile(path.read_text(encoding='utf8'), str(path), 'exec')
    record = {'notebook': str(notebook.resolve()),
              'notebook_sha256': hashlib.sha256(notebook.read_bytes()).hexdigest(),
              'patch_sha256': hashes,
              'source_sha256': {str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in (source / 'inference').rglob('*.py')}}
    (output / 'source-manifest.json').write_text(json.dumps(record, indent=2), encoding='utf8')
    return source


if __name__ == '__main__':
    import sys
    print(materialize(sys.argv[1], sys.argv[2]))
