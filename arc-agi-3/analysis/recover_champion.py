"""Read-only recovery of the exact Kaggle version behind submission 57247568."""
import hashlib
import json
from pathlib import Path
import subprocess

OUT = Path('research')
OUT.mkdir(exist_ok=True)
commands = [
    (['kernels', 'pull', 'petersharps/arc3-duck/3', '--metadata', '--path', str(OUT/'champion-v3')], 'champion-pull.log'),
    (['competitions', 'submissions', '-c', 'arc-prize-2026-arc-agi-3', '--csv'], 'own-submissions.csv'),
    (['competitions', 'leaderboard', '-c', 'arc-prize-2026-arc-agi-3', '--show'], 'leaderboard.txt'),
]
manifest = {'submission_ref': 57247568, 'kernel': 'petersharps/arc3-duck', 'kernel_version': 3, 'commands': []}
for args, name in commands:
    result = subprocess.run(['kaggle', *args], capture_output=True, text=True, timeout=180)
    (OUT/name).write_text(result.stdout+'\n'+result.stderr, encoding='utf8')
    manifest['commands'].append({'args': args, 'returncode': result.returncode})
manifest['files'] = {str(p.relative_to(OUT)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in (OUT/'champion-v3').glob('*') if p.is_file()}
(OUT/'recovery-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf8')
print(json.dumps(manifest, indent=2))
if manifest['commands'][0]['returncode']:
    raise RuntimeError('Version 3 recovery failed; do not substitute latest kernel source')
