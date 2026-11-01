"""Bounded unattended train/select/holdout pipeline, always <=16 game workers."""
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib
import inspect
import itertools
import json
import os
from pathlib import Path
import re
import site
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
BUDGET={'node_cap':50000,'sec_cap':120,'max_levels':6}
CONTROL={'depth_weight':0.0,'beam':120}


def identity(config):return json.dumps(config,sort_keys=True)


def worker(job):
    import extended_search_experiment as runner
    from fast_sweep import _module
    runner.BUDGET.update(BUDGET)
    path,cls,config,genome,phase=job
    source=inspect.getsource(_module.search_level)
    old='nov = float((frame != cf).sum()) if frame.shape == cf.shape else 1.0'
    new='nov = (float((frame != cf).sum()) / max(1,frame.size) if frame.shape == cf.shape else 1.0) + '+repr(config['depth_weight'])+' * (len(seq)+1)'
    assert source.count(old)==1
    exec(compile(source.replace(old,new),'<cpu-search-priority>','exec'),vars(_module))
    genome=dict(genome,beam=config['beam'])
    # Fast cloning is unavailable for some environments. Bound the cost of
    # their wide frontiers by implementation capability, never by game ID.
    import fast_sweep
    search=_module.search_level
    def resource_search(game,*args,**kwargs):
        if type(game) not in fast_sweep._approved:
            kwargs['beam_width']=min(kwargs['beam_width'],120)
        return search(game,*args,**kwargs)
    _module.search_level=resource_search
    row=runner.worker((path,cls,'cpu_priority',genome))
    row.update(config=config,config_id=identity(config),phase=phase)
    return row


def isolated(job):
    env=os.environ.copy();env['PYTHONPATH']=os.pathsep.join(site.getsitepackages())
    try:
        p=subprocess.run([sys._base_executable,str(Path(__file__).resolve()),'--worker'],input=json.dumps(job),capture_output=True,text=True,encoding='utf8',env=env,timeout=240)
        if p.returncode:raise RuntimeError(p.stderr[-1200:])
        return json.loads(p.stdout.strip().splitlines()[-1])
    except Exception as exc:return {'game':Path(job[0]).stem,'config':job[2],'config_id':identity(job[2]),'phase':job[4],'error':repr(exc),'levels':[]}


def rank(config,rows):
    sub=[r for r in rows if r['config_id']==identity(config)]
    errors=sum(bool(r.get('error')) for r in sub)
    solved=sum(r.get('independent_replay_levels',0) for r in sub)
    coverage=sum(100*r.get('independent_replay_levels',0)*(r.get('independent_replay_levels',0)+1)/(r['win_levels']*(r['win_levels']+1)) for r in sub if not r.get('error') and r.get('win_levels'))/len(sub)
    return {'config':config,'games':len(sub),'errors':errors,'verified_levels':solved,'mean_weighted_completion':coverage}


if __name__=='__main__':
    for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','RAYON_NUM_THREADS'):os.environ[k]='1'
    if sys.argv[1:]==['--worker']:
        print(json.dumps(worker(json.load(sys.stdin))));sys.exit()
    lab=ROOT/'analysis/resource-gated-cpu-20261101'
    if lab.exists():raise FileExistsError(lab)
    lab.mkdir()
    split=json.loads((ROOT/'analysis/cpu-search-20261101/manifest.json').read_text())
    genome=json.loads((ROOT/'analysis/cpu-search-20261101/finalized-report.json').read_text())['selected']['genome']
    paths={p.stem:p for p in (ROOT/'games/environment_files').rglob('*.py')}
    configs=[CONTROL,{'depth_weight':.001,'beam':512}]
    sources=('resource_gated_cpu_search.py','extended_search_experiment.py','fast_sweep.py','fast_state_clone.py','sweep2.py','fast-clone-certificate-20261101.json','native_kernels.py')
    manifest={'budget':BUDGET,'workers':16,'configs':configs,'train':split['train'],'holdout':split['holdout'],'genome':genome,
              'source_sha256':{n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in sources},
              'game_sha256':{n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p in paths.items()},
              'scope':'Original-engine offline priority-search experiment, independently replayed; no LLM or hidden-score claim.'}
    (lab/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    with (lab/'trials.jsonl').open('x',encoding='utf8') as log,ThreadPoolExecutor(max_workers=16) as pool:
        def evaluate(options,names,phase):
            jobs=[(str(paths[n].resolve()),re.search(r'^class (\w+)\(ARCBaseGame\)',paths[n].read_text(encoding='utf8'),re.M)[1],c,genome,phase) for c in options for n in names]
            print(phase+': '+str(len(jobs))+' trials,16workers',flush=True);rows=[]
            for f in as_completed([pool.submit(isolated,j) for j in jobs]):
                row=f.result();rows.append(row);log.write(json.dumps(row)+'\n');log.flush()
                if len(rows)%8==0 or len(rows)==len(jobs):print(phase+': '+str(len(rows))+'/'+str(len(jobs)),flush=True)
            return rows
        training=evaluate(configs,split['train'],'training')
        ranked=sorted([rank(c,training) for c in configs],key=lambda x:(-x['errors'],x['mean_weighted_completion'],x['verified_levels']),reverse=True)
        selected={identity(CONTROL):CONTROL,identity(ranked[0]['config']):ranked[0]['config']}
        (lab/'selection.json').write_text(json.dumps(ranked,indent=2),encoding='utf8')
        held=evaluate(list(selected.values()),split['holdout'],'holdout')
    (lab/'report.json').write_text(json.dumps({'training':ranked,'holdout':[rank(c,held) for c in selected.values()],'qualification':manifest['scope']},indent=2),encoding='utf8')
    print('CONTINUOUS_CPU_COMPLETE',flush=True)
