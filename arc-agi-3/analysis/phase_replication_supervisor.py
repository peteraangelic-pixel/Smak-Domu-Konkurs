"""Bounded pipeline for this authorized PRIVATE experiment, never submission.

Wait for the existing collector, analyze its immutable output, and start at
most one prepared identical-source replication only if explicit gates pass.
No writes to Kaggle competition endpoints; no retries of ambiguous dispatch.
"""
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from compare_target_runs import compare

ROOT=Path(__file__).resolve().parents[1]
LAB=ROOT/'analysis/phase-lesson-20261101'
OUT=LAB/'auto-replication'
REPO='peteraangelic-pixel/Smak-Domu-Konkurs'
REF='codex/arc-local-lab-v18-20261030'
SHA='b6140e3400ae7f33c83413128db33fda24b4a8fec12bd60b1aa1b7a434626f62'
CUTOFF=datetime(2026,11,2,23,59,tzinfo=timezone.utc)


def atomic_json(path,data):
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(data,indent=2),encoding='utf8');temp.replace(path)


def write(name,data):
    atomic_json(OUT/name,data)


def alive_time():
    if datetime.now(timezone.utc)>=CUTOFF:raise RuntimeError('Authorized experiment cutoff reached')


def gh(*args):
    return subprocess.run(['gh',*args],check=True,text=True,encoding='utf8',capture_output=True,timeout=180).stdout


def wait_run(run):
    while True:
        alive_time();status=json.loads(gh('run','view',str(run),'--repo',REPO,'--json','status,conclusion'))
        write('status.json',{'pid':os.getpid(),'run':run,'utc':datetime.now(timezone.utc).isoformat(),**status})
        if status['status']=='completed':
            if status['conclusion']!='success':raise RuntimeError('Workflow did not succeed: '+str(status))
            return
        time.sleep(30)


def download(run,label):
    target=OUT/label
    gh('run','download',str(run),'--repo',REPO,'--name','arc-submission-access-57811453','--dir',str(target))
    return target/'submission-access-20261031'


def dispatch(mode,label):
    assert mode in ('phase-lesson-watch','phase-lesson-retest-smoke','phase-lesson-retest-watch')
    alive_time()
    # Create the attempt receipt BEFORE making a write. Never repeat a label,
    # including after an interrupted or ambiguous HTTP response.
    receipt=OUT/(label+'-attempt.json')
    with receipt.open('x',encoding='utf8') as f:json.dump({'mode':mode,'utc':datetime.now(timezone.utc).isoformat()},f)
    output=gh('workflow','run','arc3-ops.yml','--repo',REPO,'--ref',REF,'-f','mode='+mode)
    match=re.search(r'/actions/runs/(\d+)',output)
    if not match:raise RuntimeError('Ambiguous dispatch receipt; inspect runs, DO NOT retry')
    run=int(match[1]);write(label+'-dispatch.json',{'run':run,'mode':mode,'receipt':output})
    return run


if __name__=='__main__':
    OUT.mkdir(exist_ok=False)  # single owner; repeated starts fail closed
    write('OWNER.json',{'pid':os.getpid(),'scope':'Bounded private replication only','status':'running'})
    try:
        source=ROOT/'duck-lab-candidates/v3-phase-lesson/agent.ipynb'
        replica=ROOT/'duck-lab-candidates/v3-phase-lesson-retest/agent.ipynb'
        assert hashlib.sha256(source.read_bytes()).hexdigest()==SHA
        assert source.read_bytes()==replica.read_bytes()
        run=json.loads((LAB/'RUN.json').read_text())['watch_run']
        folder=None
        for attempt in range(3):
            wait_run(run);downloaded=download(run,'phase-watch-'+str(run))
            status=(downloaded/'phase-lesson-status.txt').read_text()
            if 'KernelWorkerStatus.COMPLETE' in status:folder=downloaded/'phase-lesson-output';break
            if not re.search(r'KernelWorkerStatus\.(RUNNING|QUEUED)',status):raise RuntimeError('Kernel not complete/running/queued')
            if attempt==2:break
            run=dispatch('phase-lesson-watch','renew-watch-'+str(attempt))
            record=json.loads((LAB/'RUN.json').read_text());record['watch_run']=run
            atomic_json(LAB/'RUN.json',record)
        if folder is None:raise RuntimeError('Collector windows expired; kernel preserved, no new GPU launch')
        controls=[ROOT/'analysis/v3-target-result-20261031/v3-output',ROOT/'analysis/v3-control-retest-20261101/result-download/submission-access-20261031/control-retest-output']
        report=compare(folder,controls);write('comparison.json',report)
        logs=json.loads(next(folder.glob('arc3*.log')).read_text())
        log=''.join(e.get('data','') for e in logs)
        instruction=json.loads((source.parent/'MANIFEST.json').read_text())['instruction']
        activation=sum(' '.join(instruction.split()) in ' '.join(p.read_text().split()) for p in (folder/'prompts').glob('*.log'))
        gates={'source_pinned':True,'complete':True,'same_corpus':report['same_corpus_verified'],
               'all_ten_games':report['candidate_summary']['games']==10,
               'at_least_best_control_completions':report['candidate_summary']['levels']>=38,
               'score_above_best_control':report['candidate_summary']['score_mean']>36.09038984237083,
               'no_new_zeros':all(not x['new_zeros'] for x in report['comparisons']),
               'no_crashes':'crashed=[]' in log and 'ARC3_SMOKE_OK' in log,
               'instruction_delivered_all_ten':activation==10}
        decision={'gates':gates,'replication_qualified':all(gates.values()),
                  'levels':report['candidate_summary']['levels'],'score':report['candidate_summary']['score_mean'],
                  'qualification':'Single public private-test observation, not proven superiority or competition score.'}
        write('decision.json',decision)
        if all(gates.values()):
            launched=dispatch('phase-lesson-retest-smoke','replication-launch');wait_run(launched)
            pushed=download(launched,'replication-launch-'+str(launched))
            response=(pushed/'phase-lesson-retest-push.txt').read_text()
            expected='https://www.kaggle.com/code/petersharps/arc3-duck-codex-v3-phase-retest-1101'
            if 'Kernel version 1 successfully pushed.' not in response or expected not in response:
                raise RuntimeError('Replication acceptance not confirmed; preserve receipt and do not retry')
            record={'kernel':'petersharps/arc3-duck-codex-v3-phase-retest-1101','version':1,'sha256':SHA,
                    'source':'duck-lab-candidates/v3-phase-lesson-retest/agent.ipynb','launch_run':launched,
                    'status':'version1 accepted;collector pending','owner':'phase_replication_supervisor.py'}
            target=ROOT/'analysis/phase-lesson-retest-20261101';target.mkdir(exist_ok=True)
            atomic_json(target/'RUN.json',record)
            watch=dispatch('phase-lesson-retest-watch','replication-watch')
            record.update(watch_run=watch,status='version1 accepted;result pending')
            atomic_json(target/'RUN.json',record)
            decision['replication']=record;write('decision.json',decision)
        write('DONE.json',{'status':'complete','replication_started':all(gates.values()),'utc':datetime.now(timezone.utc).isoformat()})
    except Exception as exc:
        write('FAILED.json',{'error':repr(exc),'utc':datetime.now(timezone.utc).isoformat(),
                             'instruction':'Inspect durable dispatch receipts and current runs before any retry.'})
        raise
