"""Compose object motion, input activation, autonomous dynamics and contact.

Hypotheses come from TRAINING residuals. A small active probe resolves a
training activation-boundary ambiguity. A fresh final bank is sealed until
the composed program has been selected. This remains one-fixture research.
"""
from concurrent.futures import ProcessPoolExecutor,ThreadPoolExecutor
import ast
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import sys
import repair_model_constants as constants
import model_repair_dataset as dataset
LAB=constants.LAB;OUT=LAB/'composed'


def active_region(train):
    labelled=[(r['action']['row'],constants.canonical(r['before'])!=constants.canonical(r['after'])) for r in train]
    intervals=[(lo,hi) for lo in range(64) for hi in range(lo,64) if all((lo<=r<=hi)==changed for r,changed in labelled)]
    assert intervals,'Simple row interval unsupported by TRAINING observations'
    initial=list(intervals)
    # Evaluation-only public fixture API. This is not shipped in a policy.
    from arcengine import ActionInput,GameAction
    from sweep2 import load_game,frame_of
    from types import SimpleNamespace
    sys.path.insert(0,str(dataset.SOURCE))
    from inference.utils.segmentation import segment_layer
    from inference.utils.grid_utils import ARC_COLOR_CHARS
    games=json.loads((dataset.PROMPTS/'benchmark.json').read_text())['game_runs']
    history=next(g['history'] for g in games if g['game_id'].startswith('su15-'))
    path=next((dataset.ROOT/'games/environment_files').rglob('su15.py'));cls=re.search(r'^class (\w+)\(ARCBaseGame\)',path.read_text(),re.M)[1]
    engine=load_game(str(path),cls);fd=engine.perform_action(ActionInput(id=GameAction.RESET))
    for row in history:
        if int(fd.levels_completed)==3:break
        a=row['action'];fd=engine.perform_action(ActionInput(id=getattr(GameAction,a['id']),data=a.get('data') or {}))
    ns={};exec((LAB/'base_model.py').read_text(),ns)
    def encode(fd):return ns['model_state'](SimpleNamespace(segmentation=segment_layer(frame_of(fd).tolist(),ARC_COLOR_CHARS)))
    extra=[];trace=[]
    for index in range(4):
        if len(intervals)==1:break
        def uncertainty(r):
            n=sum(lo<=r<=hi for lo,hi in intervals)
            return (n*(len(intervals)-n),r)
        row=max(range(64),key=uncertainty)
        if uncertainty(row)[0]==0:break
        col=int(frame_of(fd).shape[1]//2);before=encode(fd)
        fd=engine.perform_action(ActionInput(id=GameAction.from_id(6),data={'x':col,'y':row}))
        assert int(fd.levels_completed)==3 and not str(fd.state).endswith(('WIN','GAME_OVER'))
        after=encode(fd);changed=constants.canonical(before)!=constants.canonical(after)
        survivors=[v for v in intervals if (v[0]<=row<=v[1])==changed]
        trace.append({'candidate_intervals':intervals,'chosen_row':row,'col':col,'observed_change':changed,'survivors':survivors})
        extra.append({'episode':'active-boundary','index':index,'split':'train','before':before,'action':{'action':'MOUSE','row':row,'col':col},'after':after})
        assert survivors,'Active observation falsified all proposed activation models'
        intervals=survivors
    assert len(intervals)==1,'Ambiguity remains; do not pretend a unique rule was learned'
    return intervals[0],extra,{'initial_hypotheses':initial,'actual_discriminating_probes':trace}


def build(base,lo,hi,dr,dc,metric,rounding,pool,fast,eating):
    tree=ast.parse(base)
    renames={'arrow_step':'_prior_arrow','eats':'_contact','model_step':'_object_stage'}
    for node in tree.body:
        if isinstance(node,ast.FunctionDef) and node.name in renames:node.name=renames[node.name]
    distance={'chebyshev':'max(abs(v[0]),abs(v[1]))','manhattan':'abs(v[0])+abs(v[1])','euclidean':'v[0]*v[0]+v[1]*v[1]'}[metric]
    code='''
def arrow_step(ar,blocks,dots,moved): return ar
def eats(ar,blocks,dots): return set()
def model_step(state,act):
    if not isinstance(act,dict) or act.get('row') is None or not LO<=act['row']<=HI: return None
    result=_object_stage(state,act)
    st=result if result is not None else {'b':list(state['b']),'d':list(state['d']),'a':state['a']}
    objects=[tuple(x) for x in POOL['b']]+[(1,r,c) for r,c in POOL['d']]
    ar=state['a']
    if ar is not None and objects:
        def vector(o):
            center=cen_of(o)
            return (ROUND(center[0]-DR)-ar[0],ROUND(center[1]-DC)-ar[1])
        def distance(o):
            v=vector(o)
            return DISTANCE
        target=min(objects,key=lambda o:(distance(o),o));r,c=vector(target)
        old=set(tuple(x) for x in state['b'])|{(1,r,c) for r,c in state['d']}
        added=(set(tuple(x) for x in st['b'])|{(1,r,c) for r,c in st['d']})-old
        boosted=FAST and target in added
        k,limit=(2,12) if boosted else (1,4)
        st['a']=(ar[0]+max(-limit,min(limit,k*r)),ar[1]+max(-limit,min(limit,k*c)))
        if EATING:
            eaten=_contact(st['a'],st['b'],st['d'])
            st['b']=[b for b in st['b'] if b not in eaten]
            st['d']=[d for d in st['d'] if (1,d[0],d[1]) not in eaten]
    return st
'''
    replacements={'LO':repr(lo),'HI':repr(hi),'DR':repr(dr),'DC':repr(dc),'ROUND':rounding,'DISTANCE':distance,
                  'POOL':'st' if pool=='after' else 'state','FAST':repr(fast),'EATING':repr(eating)}
    for a,b in replacements.items():code=code.replace(a,b)
    return ast.unparse(tree)+'\n'+code


TRAIN=[]
def initialize():
    global TRAIN
    TRAIN=json.loads((OUT/'training.json').read_text())
def score(job):
    code,config=job
    return {'code':code,'config':config,'sha256':hashlib.sha256(code.encode()).hexdigest(),
            'training':constants.evaluate(code,TRAIN),'edits':[config]}


if __name__=='__main__':
    for n in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','RAYON_NUM_THREADS'):os.environ[n]='1'
    if OUT.exists():raise FileExistsError(OUT)
    OUT.mkdir();base=(LAB/'point-motion/selected-model.py').read_text();train=json.loads((LAB/'train.json').read_text())
    manifest={'workers':16,'base_sha256_lf':hashlib.sha256(base.encode()).hexdigest(),'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'final_seeds':list(range(9300,9316)),'hypothesis':'TRAINING residuals show autonomous actor motion even when clicked point did not move; coordinate activation gate separates HUD/border noops.',
              'scope':'Compositional prediction model at one public fixture, not general agent/completions/Kaggle score.'}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    (lo,hi),extra,probes=active_region(train)
    (OUT/'active-region.json').write_text(json.dumps(probes,indent=2),encoding='utf8')
    train+=extra;(OUT/'training.json').write_text(json.dumps(train,indent=2),encoding='utf8')
    jobs=[]
    for dr,dc,metric,rounding,pool,fast,eating in itertools.product((1.,1.5,2.,2.5),(1.,1.5,2.,2.5),('chebyshev','manhattan','euclidean'),('round','int'),('before','after'),(False,True),(False,True)):
        cfg=dict(lo=lo,hi=hi,dr=dr,dc=dc,metric=metric,rounding=rounding,pool=pool,fast=fast,eating=eating)
        jobs.append((build(base,**cfg),cfg))
    print(str(len(jobs))+' composed programs,16processes;'+str(len(extra))+' real discriminating probes',flush=True)
    with ProcessPoolExecutor(max_workers=16,initializer=initialize) as p:rows=list(p.map(score,jobs,chunksize=8))
    selected=max(rows,key=constants.rank);(OUT/'selected-model.py').write_bytes(selected['code'].encode())
    (OUT/'selection.json').write_text(json.dumps({k:v for k,v in selected.items() if k!='code'},indent=2),encoding='utf8')
    (OUT/'trials.jsonl').write_text(''.join(json.dumps({k:v for k,v in r.items() if k!='code'})+'\n' for r in rows),encoding='utf8')
    validation=json.loads((LAB/'holdout.json').read_text())
    report={'candidates':len(rows),'baseline_training':constants.evaluate(base,train),'selected_training':selected['training'],
            'baseline_validation':constants.evaluate(base,validation),'selected_validation':constants.evaluate(selected['code'],validation),
            'selected_config':selected['config'],'selected_sha256':selected['sha256'],'region':probes}
    if report['selected_validation']['balanced_exact']>report['baseline_validation']['balanced_exact']:
        games=json.loads((dataset.PROMPTS/'benchmark.json').read_text())['game_runs'];history=next(g['history'] for g in games if g['game_id'].startswith('su15-'))
        path=next((dataset.ROOT/'games/environment_files').rglob('su15.py'));cls=re.search(r'^class (\w+)\(ARCBaseGame\)',path.read_text(),re.M)[1]
        with ThreadPoolExecutor(max_workers=16) as p:episodes=list(p.map(dataset.isolated,[(str(path.resolve()),cls,history,s,'final-composed') for s in manifest['final_seeds']]))
        (OUT/'final-episodes.json').write_text(json.dumps(episodes,indent=2),encoding='utf8')
        prior=json.loads((LAB/'point-motion/final-episodes.json').read_text());prior_rows=[r for e in prior for r in e['rows']]
        key=lambda r:json.dumps([r['before'],r['action']],sort_keys=True)
        seen={key(r) for r in train+validation+prior_rows};novel=[]
        for e in episodes:
            for r in e['rows']:
                k=key(r)
                if k not in seen:seen.add(k);novel.append(r)
        report.update(final_episode_errors=[e for e in episodes if e.get('error')],novel_final_samples=len(novel),
                      baseline_final=constants.evaluate(base,novel),selected_final=constants.evaluate(selected['code'],novel))
    else:report['final_test']='Not opened: no validation advantage.'
    report['qualification']=manifest['scope'];(OUT/'report.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report),flush=True)
