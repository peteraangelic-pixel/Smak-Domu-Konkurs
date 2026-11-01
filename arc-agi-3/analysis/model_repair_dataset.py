"""Offline observed-transition dataset for generic model-repair experiments.

The evaluator replays a public trace to obtain a fixture state. The proposed
repairer receives only encoded observations and model code, never engine state,
environment source, game IDs or replay paths. Not a submission policy.
"""
from concurrent.futures import ThreadPoolExecutor,as_completed
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import site
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
LAB=ROOT/'analysis/model-repair-lab-20261101'
SOURCE=ROOT/'analysis/champion-recovery-20261031/materialized-clean/ARC3-Inference'
PROMPTS=ROOT/'analysis/v3-validation-retest-20261101/result-download/submission-access-20261031/validation-retest-output'


def extract_model():
    sys.path.insert(0,str(ROOT/'analysis'))
    from analyze_prompt_snapshots import HEAD
    path=next((PROMPTS/'prompts').glob('su15*.log'))
    text=path.read_text(encoding='utf8');heads=list(HEAD.finditer(text));definitions={};literal={}
    for i,h in enumerate(heads):
        if h.group(1)!='ASSISTANT TOOL CALL: python':continue
        block=text[h.end():heads[i+1].start() if i+1<len(heads) else len(text)]
        match=re.search(r'<parameter=code>\s*\n(.*?)</parameter>',block,re.S)
        if not match:continue
        try:tree=ast.parse(match[1])
        except SyntaxError:continue
        for node in tree.body:
            if isinstance(node,ast.FunctionDef):definitions[node.name]=node
            elif isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
                try:ast.literal_eval(node.value)
                except Exception:continue
                literal[node.targets[0].id]=node
        # Freeze FIRST complete model, before later source repairs. New probe
        # episodes below are generated after freezing; no claim that old trace
        # transitions were held out from this LLM's original observations.
        if all(n in definitions for n in ('enc2','model_state','model_step','model_goal')):break
    names=('enc2','model_state','desired','cen_of','arrow_step','eats','model_step','model_goal')
    assert all(n in definitions for n in names)
    module=ast.Module(body=list(literal.values())+[definitions[n] for n in names],type_ignores=[])
    code=ast.unparse(module)+'\n';compile(code,'<observed-model>','exec')
    (LAB/'base_model.py').write_text(code,encoding='utf8')
    return code


def worker(job):
    path,cls,history,seed,split=job
    import random
    import numpy as np
    from types import SimpleNamespace
    from arcengine import ActionInput,GameAction
    from sweep2 import load_game,frame_of
    from native_kernels import NativeKernels
    sys.path.insert(0,str(SOURCE))
    from inference.utils.segmentation import segment_layer
    from inference.utils.grid_utils import ARC_COLOR_CHARS,format_grid_ascii
    namespace={};exec(compile((LAB/'base_model.py').read_text(),'<base-model>','exec'),namespace)
    encoder=namespace['model_state'];engine=load_game(path,cls)
    frame=engine.perform_action(ActionInput(id=GameAction.RESET));prefix_actions=0
    for record in history:
        if int(frame.levels_completed)>=3:break
        action=record['action'];frame=engine.perform_action(ActionInput(id=getattr(GameAction,action['id']),data=action.get('data') or {}));prefix_actions+=1
    assert int(frame.levels_completed)==3,'public replay did not reach the fixture level'
    rng=random.Random(seed);native=NativeKernels();rows=[];excluded_terminal=0
    def encode(fd):
        grid=frame_of(fd)
        view=SimpleNamespace(ascii=format_grid_ascii(grid.tolist()),
            segmentation=segment_layer(grid.tolist(),ARC_COLOR_CHARS))
        return encoder(view),grid
    before,grid=encode(frame)
    for index in range(12):
        # Rust connected-component click candidates plus deterministic spatial
        # offsets; proposals use pixels alone, never internals or goal feedback.
        candidates=native.blob_candidates(grid.astype(np.uint8),limit=64)
        if candidates:
            y,x=rng.choice(candidates);y=max(0,min(grid.shape[0]-1,y+rng.choice((-6,0,6))));x=max(0,min(grid.shape[1]-1,x+rng.choice((-6,0,6))))
        else:y=rng.randrange(grid.shape[0]);x=rng.randrange(grid.shape[1])
        action={'action':'MOUSE','row':int(y),'col':int(x)}
        frame=engine.perform_action(ActionInput(id=GameAction.from_id(6),data={'x':int(x),'y':int(y)}))
        if str(frame.state).endswith(('WIN','GAME_OVER')) or int(frame.levels_completed)!=3:
            excluded_terminal+=1;break
        after,grid=encode(frame)
        rows.append({'episode':seed,'index':index,'split':split,'before':before,'action':action,'after':after})
        before=after
    return {'seed':seed,'split':split,'rows':rows,'prefix_actions':prefix_actions,'terminal_transitions_excluded':excluded_terminal,
            'backend':'16process-cap; Rust ctypes click proposals; official Python segmentation for exact encoder compatibility'}


def isolated(job):
    env=os.environ.copy();env['PYTHONPATH']=os.pathsep.join(site.getsitepackages())
    try:
        result=subprocess.run([sys._base_executable,str(Path(__file__).resolve()),'--worker'],input=json.dumps(job),capture_output=True,text=True,encoding='utf8',env=env,timeout=120)
        if result.returncode:raise RuntimeError(result.stderr[-1500:])
        return json.loads(result.stdout.strip().splitlines()[-1])
    except Exception as exc:return {'seed':job[3],'split':job[4],'error':repr(exc),'rows':[]}


if __name__=='__main__':
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','RAYON_NUM_THREADS'):os.environ[name]='1'
    if sys.argv[1:]==['--worker']:
        print(json.dumps(worker(json.load(sys.stdin))));sys.exit()
    LAB.mkdir(exist_ok=True)
    if (LAB/'dataset-manifest.json').exists():raise FileExistsError('Preserve existing dataset')
    model=extract_model();benchmark=json.loads((PROMPTS/'benchmark.json').read_text())
    game=next(g for g in benchmark['game_runs'] if g['game_id'].startswith('su15-'))
    path=next((ROOT/'games/environment_files').rglob('su15.py'))
    cls=re.search(r'^class (\w+)\(ARCBaseGame\)',path.read_text(),re.M)[1]
    jobs=[(str(path.resolve()),cls,game['history'],9100+i,'train' if i<8 else 'holdout') for i in range(16)]
    manifest={'workers':16,'episodes':16,'train_seeds':list(range(9100,9108)),'holdout_seeds':list(range(9108,9116)),
              'probes_per_episode':12,'base_model_sha256':hashlib.sha256(model.encode()).hexdigest(),
              'evaluator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'game_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
              'qualification':'New public forward probe episodes at one fixture; frozen model and seed split before evaluation. No game-completion or Kaggle score claim. Not unseen-game generalization.'}
    (LAB/'dataset-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    reports=[]
    with (LAB/'episode-reports.jsonl').open('x',encoding='utf8') as log,ThreadPoolExecutor(max_workers=16) as pool:
        for future in as_completed([pool.submit(isolated,j) for j in jobs]):
            row=future.result();reports.append(row);log.write(json.dumps(row)+'\n');log.flush();print(str(len(reports))+'/16 '+str(row['seed'])+' '+str(len(row['rows']))+' transitions',flush=True)
    for split in ('train','holdout'):
        rows=[r for e in reports if e['split']==split for r in e['rows']]
        (LAB/(split+'.json')).write_text(json.dumps(rows,indent=2),encoding='utf8')
    summary={'episodes':len(reports),'errors':[e for e in reports if e.get('error')],
             'train':sum(len(e['rows']) for e in reports if e['split']=='train'),
             'holdout':sum(len(e['rows']) for e in reports if e['split']=='holdout')}
    (LAB/'dataset-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf8');print(json.dumps(summary))
