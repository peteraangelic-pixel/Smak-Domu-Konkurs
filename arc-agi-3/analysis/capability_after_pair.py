"""One conditional capability diagnostic after the active A/B releases LM Studio.

Earlier thinking-ON requests ended with length while still in reasoning. If
the entire current pair has zero completions, test whether a single longer
response can produce useful reasoning and actions. Total token cap stays8192;
this is a capability probe, not an A/B score claim or a parameter sweep.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
PAIR=ROOT/'analysis/champion-probe-pair-20261031'
OUT=ROOT/'analysis/capability-on-8192-20261031'


def main():
    lock=PAIR/'capability-followup.lock'
    with lock.open('x',encoding='utf8') as f:f.write(str(os.getpid()))
    try:
        deadline=time.monotonic()+4*3600
        # Wait for completed results AND release of the matrix's server lock.
        while not (PAIR/'comparison.json').exists() or (PAIR/'running.lock').exists():
            if time.monotonic()>deadline:raise TimeoutError('Pair did not finish; do not infer with another active stream')
            time.sleep(2)
        report=json.loads((PAIR/'comparison.json').read_text(encoding='utf8'))
        if not report['error_free']:
            print('No capability follow-up: inspect errors in the paired trial first',flush=True)
            return
        if any(report['completed_levels'].values()):
            print('No zero-control follow-up: paired trial contains completions; assess those first',flush=True)
            return
        if OUT.exists():raise FileExistsError(f'Do not duplicate or overwrite {OUT}')
        command=[sys.executable,'-X','utf8',str(ROOT/'analysis/run_duck_loop.py'),
                 '--source',str(ROOT/'analysis/champion-recovery-20261031/materialized-clean/ARC3-Inference'),
                 '--notebook',str(ROOT/'analysis/champion-recovery-20261031/champion-v3/arc3-duck.ipynb'),
                 '--game','ft09','--variant','control','--out',str(OUT),
                 '--thinking','on','--token-budget','8192','--request-tokens','8192','--seconds','3600']
        (PAIR/'capability-command.json').write_text(json.dumps(command,indent=2),encoding='utf8')
        with (PAIR/'capability-followup.log').open('w',encoding='utf8') as f:
            subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=3720)
        row=json.loads((OUT/'result.json').read_text(encoding='utf8'))
        row['interpretation']='Single capability diagnostic of reasoning truncation; not evidence that a submission candidate outperforms its control.'
        (OUT/'capability-summary.json').write_text(json.dumps(row,indent=2),encoding='utf8')
        print(json.dumps(row),flush=True)
    finally:
        lock.unlink(missing_ok=True)


if __name__=='__main__':main()
