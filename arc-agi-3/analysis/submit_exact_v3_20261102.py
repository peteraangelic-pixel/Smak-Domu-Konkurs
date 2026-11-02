"""Explicit user authorization: submit pinned recovered v3 once on Nov 2 UTC."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import io
import json
import os
import subprocess

OUT = Path('arc-agi-3/analysis/v3-submit-20261102')
SLUG = 'petersharps/arc3-duck-codex-v3-control-1031'
SHA = '8d0195f92c5518a41d14edbfca596b72c27690f269f681bbaa9af0bc3d257bcc'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    decision = dict(kernel=SLUG, version=1, sha256=SHA, submitted=False,
                    utc=datetime.now(timezone.utc).isoformat())
    def run(label, args):
        result = subprocess.run(['kaggle', *args], capture_output=True, text=True, timeout=180)
        text = result.stdout + '\n' + result.stderr
        secret = os.environ.get('KAGGLE_API_TOKEN', '')
        if secret:
            text = text.replace(secret, '[REDACTED]')
        (OUT / (label + '.txt')).write_text(text, encoding='utf-8')
        if result.returncode:
            raise RuntimeError(label + ' failed; no automatic retry')
        return result.stdout
    try:
        assert datetime.now(timezone.utc).date().isoformat() == '2026-11-02', 'Outside authorized UTC date'
        assert not (OUT / 'attempted.json').exists(), 'Prior attempt requires review'
        source = Path('arc-agi-3/duck-lab-candidates/v3-target-control/arc3-duck.ipynb')
        assert hashlib.sha256(source.read_bytes()).hexdigest() == SHA, 'Local source hash mismatch'
        run('cli-version', ['--version'])
        status = run('kernel-status', ['kernels', 'status', SLUG + '/1'])
        assert 'KernelWorkerStatus.COMPLETE' in status, 'Kernel not COMPLETE'
        run('kernel-pull', ['kernels', 'pull', SLUG + '/1', '-p', str(OUT / 'pulled'), '-m'])
        actual = next((OUT / 'pulled').glob('*.ipynb'))
        def cells(p):
            return [''.join(c['source']).rstrip('\n') for c in json.loads(p.read_text())['cells']
                    if c['cell_type'] == 'code']
        assert cells(actual) == cells(source), 'Published code mismatch'
        decision['published_code_matches'] = True
        run('kernel-output', ['kernels', 'output', SLUG + '/1', '-p', str(OUT / 'output'),
                              '--file-pattern', r'(submission\.parquet|benchmark\.json)$'])
        assert list((OUT / 'output').rglob('submission.parquet')), 'Missing submission.parquet'
        benchmark = json.loads(next((OUT / 'output').rglob('benchmark.json')).read_text())
        decision['public_test_levels'] = sum(int(g['levels_completed']) for g in benchmark['game_runs'])
        assert len(benchmark['game_runs']) == 10 and decision['public_test_levels'] == 33, 'Unexpected control output'
        listing = run('submissions-before', ['competitions', 'submissions', 'arc-prize-2026-arc-agi-3', '--csv'])
        rows = list(csv.DictReader(io.StringIO(listing)))
        assert rows and 'ref' in rows[0] and 'date' in rows[0], 'Unrecognized submission inventory'
        today = datetime.now(timezone.utc).date()
        for row in rows:
            date = datetime.fromisoformat(row['date'].replace('Z', '+00:00'))
            if date.date() == today:
                decision.update(reason='Existing submission today; preserve daily quota', existing=row)
                return
        (OUT / 'attempted.json').write_text(json.dumps(decision, indent=2))
        reply = run('competition-submit', ['competitions', 'submit', 'arc-prize-2026-arc-agi-3',
                    '-k', SLUG, '-v', '1', '-f', 'submission.parquet',
                    '-m', 'Exact recovered v3; user authorized 2026-11-02'])
        decision.update(submitted=True, reason='API accepted submission', response=reply)
        run('submissions-after', ['competitions', 'submissions', 'arc-prize-2026-arc-agi-3', '--csv'])
    except Exception as exc:
        decision.update(reason='Stopped; no automatic retry', error=str(exc))
        raise
    finally:
        (OUT / 'decision.json').write_text(json.dumps(decision, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
