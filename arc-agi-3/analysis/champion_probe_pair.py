"""Resumable, serial inference A/B of recovered v3 and packaged feedback.

The engine remains Python; these are genuine ToolAgent inference trials, not
Rust search benchmarks. One server request stream avoids oversubscription.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from group_regressions import compare

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'analysis/champion-probe-pair-20261031'
ARMS={
    'control':(ROOT/'analysis/champion-recovery-20261031/materialized-clean/ARC3-Inference',
               ROOT/'analysis/champion-recovery-20261031/champion-v3/arc3-duck.ipynb'),
    'probe':(ROOT/'analysis/duck-loop-20261031/packaged-probe/ARC3-Inference',
             ROOT/'duck-lab-candidates/probe/agent.ipynb'),
}

def main():
    OUT.mkdir(exist_ok=True)
    # Fail rather than run another copy of this same matrix. An interrupted
    # process leaves its lock for inspection; completed rows are immutable.
    lock=OUT/'running.lock'
    with lock.open('x',encoding='utf8') as f:
        import os
        f.write(str(os.getpid()))
    try:
        manifest={'games':['ft09','ls20'],'seed':731,'model':'arc-lab-27b',
                  'thinking':'off','generated_tokens':8192,'request_tokens':4096,
                  'seconds':3600,'inference_concurrency':1,
                  'notebooks':{arm:hashlib.sha256(nb.read_bytes()).hexdigest() for arm,(_,nb) in ARMS.items()},
                  'qualification':'Local Qwen3.8-27B Q4,16k context; not Kaggle Flash-Next or a score forecast.'}
        (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
        for game in manifest['games']:
            for arm,(source,notebook) in ARMS.items():
                out=OUT/f'{arm}-{game}'
                if (out/'result.json').exists():
                    row=json.loads((out/'result.json').read_text())
                    if row.get('notebook_sha256')!=manifest['notebooks'][arm]:
                        raise ValueError('Existing row has different notebook; refuse reuse')
                    continue
                if out.exists() and any(out.iterdir()):
                    raise RuntimeError(f'Interrupted trial requires inspection: {out}')
                command=[sys.executable,'-X','utf8',str(ROOT/'analysis/run_duck_loop.py'),
                         '--source',str(source),'--notebook',str(notebook),'--game',game,
                         '--variant',arm,'--out',str(out),'--thinking','off',
                         '--token-budget','8192','--request-tokens','4096','--seconds','3600']
                with (OUT/f'{arm}-{game}.log').open('w',encoding='utf8') as f:
                    subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=3720)
                print(f'Completed {arm}/{game}',flush=True)
        rows={arm:[json.loads((OUT/f'{arm}-{g}/result.json').read_text()) for g in manifest['games']] for arm in ARMS}
        report=compare(rows['control'],rows['probe'])
        report['completed_levels']={arm:sum(r['levels_completed'] for r in rr) for arm,rr in rows.items()}
        report['feedback_activations']=sum(r.get('inspection_feedback_count',0) for r in rows['probe'])
        report['local_candidate_advantage']=bool(report['error_free'] and report['no_level_regressions']
            and report['no_group_score_regressions'] and report['completed_levels']['probe']>report['completed_levels']['control'])
        report['promotion']='No Kaggle recommendation from this two-game local test alone'
        (OUT/'comparison.json').write_text(json.dumps(report,indent=2),encoding='utf8')
        print(json.dumps(report),flush=True)
    finally:
        lock.unlink(missing_ok=True)

if __name__=='__main__':main()
