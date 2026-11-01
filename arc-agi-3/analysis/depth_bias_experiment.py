"""Test a new search behavior: normalized novelty plus bounded depth preference.

Uses the same original engines and independent replay as extended_search.
Does not change files imported by any existing experiment.
"""
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib
import inspect
import json
import os
from pathlib import Path
import re
import site
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def worker(job):
    from extended_search_experiment import worker as evaluate
    if job[2]=='depth_bias':
        from fast_sweep import _module
        source=inspect.getsource(_module.search_level)
        old='nov = float((frame != cf).sum()) if frame.shape == cf.shape else 1.0'
        new='nov = (float((frame != cf).sum()) / max(1,frame.size) if frame.shape == cf.shape else 1.0) + 0.002 * (len(seq)+1)'
        assert source.count(old)==1
        exec(compile(source.replace(old,new),'<depth-biased-search>','exec'),vars(_module))
    return evaluate(job)


def isolated(job):
    environment=os.environ.copy();environment['PYTHONPATH']=os.pathsep.join(site.getsitepackages())
    try:
        p=subprocess.run([sys._base_executable,str(Path(__file__).resolve()),'--worker'],input=json.dumps(job),text=True,encoding='utf8',capture_output=True,env=environment,timeout=180)
        if p.returncode:raise RuntimeError(p.stderr[-1000:])
        return json.loads(p.stdout.strip().splitlines()[-1])
    except Exception as exc:return {'game':Path(job[0]).stem,'arm':job[2],'error':repr(exc),'levels':[]}


if __name__=='__main__':
    for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','RAYON_NUM_THREADS'):os.environ[k]='1'
    if sys.argv[1:]==['--worker']:
        print(json.dumps(worker(json.load(sys.stdin))));sys.exit()
    from extended_search_experiment import BUDGET
    lab=ROOT/'analysis/depth-bias-20261101'
    if lab.exists():raise FileExistsError(lab)
    lab.mkdir()
    genome=json.loads((ROOT/'analysis/cpu-search-20261101/finalized-report.json').read_text())['selected']['genome']
    paths=sorted((ROOT/'games/environment_files').rglob('*.py'))
    jobs=[(str(p.resolve()),re.search(r'^class (\w+)\(ARCBaseGame\)',p.read_text(encoding='utf8'),re.M)[1],arm,genome) for p in paths for arm in ('fast_selected','depth_bias')]
    manifest={'budget':BUDGET,'workers':16,'jobs':len(jobs),'genome':genome,'frontier':512,'score_change':'normalized novelty + .002*depth',
              'source_sha256':{n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in ('depth_bias_experiment.py','extended_search_experiment.py','sweep2.py','fast_sweep.py','fast_state_clone.py','fast-clone-certificate-20261101.json')},
              'game_sha256':{p.stem:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'scope':'Offline original-engine experiment,no Kaggle-score claim'}
    (lab/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8');rows=[]
    with (lab/'trials.jsonl').open('x',encoding='utf8') as log,ThreadPoolExecutor(max_workers=16) as pool:
        futures=[pool.submit(isolated,j) for j in jobs]
        for f in as_completed(futures):
            r=f.result();rows.append(r);log.write(json.dumps(r)+'\n');log.flush();print(str(len(rows))+'/'+str(len(jobs))+' '+r['arm']+' '+r['game'],flush=True)
    report={arm:{'games':sum(r['arm']==arm for r in rows),'errors':sum(bool(r.get('error')) for r in rows if r['arm']==arm),'verified_levels':sum(r.get('independent_replay_levels',0) for r in rows if r['arm']==arm)} for arm in ('fast_selected','depth_bias')}
    (lab/'report.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report),flush=True)
