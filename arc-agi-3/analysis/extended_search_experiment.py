"""Three-arm, equal-budget offline experiment with independent solution replay."""
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib
import json
import os
from pathlib import Path
import re
import site
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
BUDGET={'node_cap':20000,'sec_cap':60,'max_levels':6}


def worker(job):
    from sweep2 import Args,play_game as original,load_game
    from fast_sweep import play_game as fast
    from arcengine import ActionInput,GameAction
    path,cls,arm,genome=job
    args=Args(backend='rust',max_depth=80,frontier_cap=512,calib_time=.75,**BUDGET,**genome)
    result=(original if arm=='original_control' else fast)((path,cls,args))
    # Re-run any claimed solution on a fresh ORIGINAL engine, without fast clone.
    replay=load_game(path,cls);fd=replay.perform_action(ActionInput(id=GameAction.RESET))
    verified=0
    for level in result.get('levels',[]):
        if not level['solved']:break
        for move in level.get('seq',[]):
            fd=replay.perform_action(ActionInput(id=GameAction.from_id(move['a']),data={k:v for k,v in move.items() if k in ('x','y')}))
        if int(fd.levels_completed)<=level['level']:
            result['error']='Independent original-engine solution replay diverged';break
        verified+=1
    result.update(arm=arm,genome=genome,independent_replay_levels=verified)
    return result


def isolated(job):
    environment=os.environ.copy();environment['PYTHONPATH']=os.pathsep.join(site.getsitepackages())
    try:
        p=subprocess.run([sys._base_executable,str(Path(__file__).resolve()),'--worker'],input=json.dumps(job),
                         text=True,encoding='utf8',capture_output=True,env=environment,timeout=180)
        if p.returncode:raise RuntimeError(p.stderr[-1200:])
        return json.loads(p.stdout.strip().splitlines()[-1])
    except Exception as exc:return {'game':Path(job[0]).stem,'arm':job[2],'error':repr(exc),'levels':[]}


if __name__=='__main__':
    for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','RAYON_NUM_THREADS'):os.environ[key]='1'
    if sys.argv[1:]==['--worker']:
        print(json.dumps(worker(json.load(sys.stdin))));sys.exit()
    from evolve_search import CONTROL
    lab=ROOT/'analysis/extended-search-20261101'
    if lab.exists():raise FileExistsError(lab)
    lab.mkdir()
    selected=json.loads((ROOT/'analysis/cpu-search-20261101/finalized-report.json').read_text())['selected']['genome']
    arms={'original_control':CONTROL,'fast_selected':selected}
    paths=sorted((ROOT/'games/environment_files').rglob('*.py'))
    jobs=[(str(path.resolve()),re.search(r'^class (\w+)\(ARCBaseGame\)',path.read_text(encoding='utf8'),re.M)[1],arm,genome)
          for path in paths for arm,genome in arms.items()]
    manifest={'budget':BUDGET,'workers':16,'arms':arms,'jobs':len(jobs),
              'source_sha256':{name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in
                              ('extended_search_experiment.py','sweep2.py','fast_sweep.py','fast_state_clone.py','fast-clone-certificate-20261101.json','native_kernels.py')},
              'game_sha256':{p.stem:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
              'qualification':'Exploratory public original-engine search; no LLM/Kaggle forecast; finite clone validation only.'}
    (lab/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    rows=[]
    with (lab/'trials.jsonl').open('x',encoding='utf8') as log,ThreadPoolExecutor(max_workers=16) as pool:
        futures=[pool.submit(isolated,j) for j in jobs]
        for future in as_completed(futures):
            row=future.result();rows.append(row);log.write(json.dumps(row)+'\n');log.flush()
            print(str(len(rows))+'/'+str(len(jobs))+' '+row['arm']+' '+row['game'],flush=True)
    report={arm:{'games':sum(r['arm']==arm for r in rows),'errors':sum(bool(r.get('error')) for r in rows if r['arm']==arm),
                 'solved_levels':sum(sum(bool(l['solved']) for l in r.get('levels',[])) for r in rows if r['arm']==arm),
                 'verified_levels':sum(r.get('independent_replay_levels',0) for r in rows if r['arm']==arm)} for arm in arms}
    (lab/'report.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report),flush=True)
