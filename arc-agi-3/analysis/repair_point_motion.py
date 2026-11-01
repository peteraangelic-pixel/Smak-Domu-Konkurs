"""Add a missing point-motion branch suggested by TRAINING counterexamples.

The first generated model merges dots or moves blocks, but cannot move a dot
to a nearby click. This experiment learns that branch's bounded parameters.
It is a model-specific program-repair prototype, not a general ARC agent.
"""
from concurrent.futures import ProcessPoolExecutor,ThreadPoolExecutor,as_completed
import ast
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import repair_model_constants as constants
import model_repair_dataset as dataset
LAB=constants.LAB;OUT=LAB/'point-motion'


def build(base,radius,speed,eating,fast,distance):
    tree=ast.parse(base)
    next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='model_step').name='_base_model_step'
    metric={'chebyshev':'max(abs(r-R),abs(c-C))','manhattan':'abs(r-R)+abs(c-C)','euclidean':'((r-R)**2+(c-C)**2)**0.5'}[distance]
    suffix='''
def model_step(state,act):
    if isinstance(act,dict) and act.get('row') is not None and state['d']:
        R,C=act['row'],act['col']
        def distance(point):
            r,c=point
            return METRIC
        old=min(state['d'],key=lambda p:(distance(p),p))
        if distance(old)<=RADIUS:
            point=(old[0]+max(-SPEED,min(SPEED,R-old[0])),old[1]+max(-SPEED,min(SPEED,C-old[1])))
            if point!=tuple(old):
                st={'b':list(state['b']),'d':[d for d in state['d'] if d!=old]+[point],'a':state['a']}
                moved=(1,point[0],point[1]) if FAST else None
                st['a']=arrow_step(st['a'],st['b'],st['d'],moved)
                if EATING:
                    eaten=eats(st['a'],st['b'],st['d'])
                    st['b']=[b for b in st['b'] if b not in eaten]
                    st['d']=[d for d in st['d'] if (1,d[0],d[1]) not in eaten]
                return st
    return _base_model_step(state,act)
'''
    for name,value in [('METRIC',metric),('RADIUS',repr(radius)),('SPEED',repr(speed)),('EATING',repr(eating)),('FAST',repr(fast))]:suffix=suffix.replace(name,value)
    return ast.unparse(tree)+'\n'+suffix


def key(row):return json.dumps([row['before'],row['action']],sort_keys=True)


if __name__=='__main__':
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','RAYON_NUM_THREADS'):os.environ[name]='1'
    if OUT.exists():raise FileExistsError(OUT)
    OUT.mkdir();base=(LAB/'base_model.py').read_text();train=json.loads((LAB/'train.json').read_text())
    examples=[]
    for row in train:
        before={tuple(p) for p in row['before']['d']};after={tuple(p) for p in row['after']['d']}
        removed=before-after;added=after-before
        if len(removed)==len(added)==1:
            new=next(iter(added))
            if new==(row['action']['row'],row['action']['col']):examples.append({'removed':list(removed),'new':new,'action':row['action']})
    assert examples,'No observed training support for point-to-click motion'
    manifest={'workers':16,'training_evidence_examples':examples[:5],'training_evidence_count':len(examples),
              'final_test_seeds':list(range(9220,9236)),'base_sha256':hashlib.sha256(base.encode()).hexdigest(),
              'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'scope':'Missing branch induced from training only; parameters selected on train; old holdout=validation; fresh final episodes after freezing. One public fixture, not completions/Kaggle.'}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    configs={};jobs=[(base,[])]
    for radius,speed,eating,fast,distance in itertools.product((2,4,6,8),(2,4,6,8),(False,True),(False,True),('chebyshev','manhattan','euclidean')):
        config=dict(radius=radius,speed=speed,eating=eating,fast=fast,distance=distance)
        code=build(base,**config);configs[hashlib.sha256(code.encode()).hexdigest()]=config;jobs.append((code,[config]))
    print(str(len(jobs))+' point-motion programs,16processes',flush=True)
    with ProcessPoolExecutor(max_workers=16,initializer=constants.initialize) as pool:rows=list(pool.map(constants.score,jobs,chunksize=8))
    best=max(rows,key=constants.rank);(OUT/'selected-model.py').write_text(best['code'],encoding='utf8')
    (OUT/'selection.json').write_text(json.dumps({k:v for k,v in best.items() if k!='code'},indent=2),encoding='utf8')
    (OUT/'trials.jsonl').write_text(''.join(json.dumps({k:v for k,v in r.items() if k!='code'})+'\n' for r in rows),encoding='utf8')
    validation=json.loads((LAB/'holdout.json').read_text())
    report={'candidates':len(rows),'baseline_training':constants.evaluate(base,train),'selected_training':best['training'],
            'baseline_validation':constants.evaluate(base,validation),'selected_validation':constants.evaluate(best['code'],validation),
            'selected_config':configs.get(best['sha256']), 'selected_sha256':best['sha256']}
    improved=report['selected_training']['balanced_exact']>report['baseline_training']['balanced_exact'] and report['selected_validation']['balanced_exact']>report['baseline_validation']['balanced_exact']
    if improved:
        games=json.loads((dataset.PROMPTS/'benchmark.json').read_text())['game_runs']
        history=next(g['history'] for g in games if g['game_id'].startswith('su15-'))
        path=next((dataset.ROOT/'games/environment_files').rglob('su15.py'));cls=re.search(r'^class (\w+)\(ARCBaseGame\)',path.read_text(),re.M)[1]
        jobs=[(str(path.resolve()),cls,history,s,'final_test') for s in manifest['final_test_seeds']]
        with ThreadPoolExecutor(max_workers=16) as pool:episodes=list(pool.map(dataset.isolated,jobs))
        (OUT/'final-episodes.json').write_text(json.dumps(episodes,indent=2),encoding='utf8')
        final=[r for e in episodes for r in e['rows']];seen={key(r) for r in train+validation};novel=[]
        for r in final:
            k=key(r)
            if k not in seen:novel.append(r);seen.add(k)
        report.update(final_episode_errors=[e for e in episodes if e.get('error')],final_samples_total=len(final),novel_final_samples=len(novel),
                      baseline_final=constants.evaluate(base,novel),selected_final=constants.evaluate(best['code'],novel))
    else:report['final_test']='Not opened: no training+validation advantage.'
    report['qualification']=manifest['scope']
    (OUT/'report.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report),flush=True)
