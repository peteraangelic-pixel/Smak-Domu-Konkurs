"""Target only quarantined clone backends; restore their original heuristic.

Offline laboratory only. Environment names select infrastructure regression
fixtures, never a submission policy. No new full-corpus sweep.
"""
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib
import inspect
import json
import os
from pathlib import Path
import random
import re
import site
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
BUDGET={'node_cap':50000,'sec_cap':120,'max_levels':6}


def worker(job):
    import extended_search_experiment as runner
    import fast_sweep
    module=fast_sweep._module
    runner.BUDGET.update(BUDGET)
    path,cls,arm,genome,replica=job
    original_search=module.search_level
    source=inspect.getsource(original_search)
    old='nov = float((frame != cf).sum()) if frame.shape == cf.shape else 1.0'
    new='nov = (float((frame != cf).sum()) / max(1,frame.size) if frame.shape == cf.shape else 1.0) + .001 * (len(seq)+1)'
    assert source.count(old)==1
    namespace=dict(vars(module))
    exec(compile(source.replace(old,new),'<target-fallback-priority>','exec'),namespace)
    priority_search=namespace['search_level']
    observed=[]
    def guarded(game,*args,**kwargs):
        approved=type(game) in fast_sweep._approved
        if arm=='original_control' or not approved:
            kwargs['beam_width']=min(kwargs['beam_width'],120)
            observed.append('original')
            return original_search(game,*args,**kwargs)
        observed.append('priority')
        return priority_search(game,*args,**kwargs)
    module.search_level=guarded
    result=runner.worker((path,cls,'fast_selected',dict(genome,beam=120 if arm=='original_control' else 512)))
    result.update(arm=arm,replica=replica,selected_heuristics=sorted(set(observed)))
    # These are specifically the three backend fallback regression fixtures.
    assert set(observed)<= {'original'},'quarantined fixture unexpectedly approved'
    return result


def isolated(job):
    env=os.environ.copy();env['PYTHONPATH']=os.pathsep.join(site.getsitepackages())
    try:
        p=subprocess.run([sys._base_executable,str(Path(__file__).resolve()),'--worker'],input=json.dumps(job),capture_output=True,text=True,encoding='utf8',env=env,timeout=240)
        if p.returncode:raise RuntimeError(p.stderr[-1200:])
        return json.loads(p.stdout.strip().splitlines()[-1])
    except Exception as exc:return {'game':Path(job[0]).stem,'arm':job[2],'replica':job[4],'error':repr(exc),'levels':[]}


if __name__=='__main__':
    for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','RAYON_NUM_THREADS'):os.environ[key]='1'
    if sys.argv[1:]==['--worker']:
        print(json.dumps(worker(json.load(sys.stdin))));sys.exit()
    lab=ROOT/'analysis/target-fallback-cpu-20261101'
    if lab.exists():raise FileExistsError(lab)
    lab.mkdir()
    source=json.loads((ROOT/'analysis/resource-gated-cpu-20261101/manifest.json').read_text())
    paths=[p for p in (ROOT/'games/environment_files').rglob('*.py') if p.stem in ('bp35','lf52','tn36')]
    assert len(paths)==3
    jobs=[(str(p.resolve()),re.search(r'^class (\w+)\(ARCBaseGame\)',p.read_text(encoding='utf8'),re.M)[1],arm,source['genome'],rep)
          for rep in range(2) for arm in ('original_control','full_fallback_guard') for p in paths]
    random.Random(20261101).shuffle(jobs)
    manifest={'workers':16,'jobs':len(jobs),'budget':BUDGET,'replicas':2,'genome':source['genome'],
              'change':'Unsupported clone type uses original priority and beam120, rather than only beam120.',
              'scope':'Targeted offline infrastructure regression; no LLM quality or competition score claim.',
              'source_sha256':{n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in
                               ('target_fallback_cpu.py','extended_search_experiment.py','fast_sweep.py','fast_state_clone.py','sweep2.py','native_kernels.py','fast-clone-certificate-20261101.json')}}
    (lab/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8');rows=[]
    with (lab/'trials.jsonl').open('x',encoding='utf8') as log,ThreadPoolExecutor(max_workers=16) as pool:
        for future in as_completed([pool.submit(isolated,j) for j in jobs]):
            row=future.result();rows.append(row);log.write(json.dumps(row)+'\n');log.flush()
            print(str(len(rows))+'/'+str(len(jobs))+' '+row['game']+' '+row['arm'],flush=True)
    report={arm:{'games':sum(r['arm']==arm for r in rows),'errors':sum(bool(r.get('error')) for r in rows if r['arm']==arm),
                 'verified_levels':sum(r.get('independent_replay_levels',0) for r in rows if r['arm']==arm)} for arm in ('original_control','full_fallback_guard')}
    (lab/'report.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report),flush=True)
