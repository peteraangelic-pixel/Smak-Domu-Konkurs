"""TRAINING-supported merge and swept-contact hypotheses on a frozen model.

One-fixture prediction research. No engine/source access in the repairer;
new forward probe episodes are generated only after freezing selection.
"""
from concurrent.futures import ProcessPoolExecutor,ThreadPoolExecutor
import ast
import hashlib
import itertools
import json
import os
import re
import copy
import repair_model_constants as constants
import model_repair_dataset as dataset

LAB=constants.LAB;OUT=LAB/'contact-merge';TRAIN=[]


def build(base,radius,speed,merge_radius,anchor,offset,motion,include_start,pool):
    tree=ast.parse(base)
    object_stage=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_object_stage')
    for node in ast.walk(object_stage):
        if isinstance(node,ast.Compare) and isinstance(node.left,ast.Call) and isinstance(node.left.func,ast.Name) and node.left.func.id=='distance':
            for v in node.comparators:
                if isinstance(v,ast.Constant) and v.value==8:v.value=radius
        elif isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in ('min','max'):
            for v in node.args:
                if isinstance(v,ast.Constant) and v.value==8:v.value=speed
                elif isinstance(v,ast.UnaryOp) and isinstance(v.operand,ast.Constant) and v.operand.value==8:v.operand.value=speed
    model=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='model_step')
    anchors={'moved':'p','click':"(act['row'],act['col'])",'partner':'q','midpoint':'(int(round((p[0]+q[0])/2)),int(round((p[1]+q[1])/2)))'}
    snippet='''
if MERGE_RADIUS>0:
    added=set(st['d'])-set(state['d'])
    for p in sorted(added):
        others=[q for q in st['d'] if q!=p]
        if not others:continue
        q=min(others,key=lambda q:(max(abs(q[0]-p[0]),abs(q[1]-p[1])),q))
        if max(abs(q[0]-p[0]),abs(q[1]-p[1]))<=MERGE_RADIUS:
            center=ANCHOR
            st['d']=[d for d in st['d'] if d not in (p,q)]
            st['b'].append((2,center[0]-OFFSET,center[1]-OFFSET))
            break
'''.replace('MERGE_RADIUS',repr(merge_radius)).replace('ANCHOR',anchors[anchor]).replace('OFFSET',repr(offset))
    index=next(i for i,n in enumerate(model.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='st' for t in n.targets))
    model.body[index+1:index+1]=ast.parse(snippet).body
    assignments=[n for n in ast.walk(model) if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Subscript)
                 and isinstance(n.targets[0].value,ast.Name) and n.targets[0].value.id=='st' and isinstance(n.targets[0].slice,ast.Constant)
                 and n.targets[0].slice.value=='a']
    assert len(assignments)==1
    node=assignments[0];objects='st' if pool=='after' else 'state'
    node.value=ast.Call(func=ast.Name(id='_swept_contact',ctx=ast.Load()),args=[ast.parse("state['a']",mode='eval').body,node.value,
                  ast.parse(objects+"['b']",mode='eval').body,ast.parse(objects+"['d']",mode='eval').body],keywords=[])
    helper='''
def _swept_contact(origin,target,blocks,dots):
    if MODE=='none' or origin is None or target is None:return target
    dr=target[0]-origin[0];dc=target[1]-origin[1];steps=max(abs(dr),abs(dc))
    if not steps:return target
    for i in range(START,int(steps)+1):
        if MODE=='axis_clamp':
            p=(origin[0]+(1 if dr>=0 else -1)*min(i,abs(dr)),origin[1]+(1 if dc>=0 else -1)*min(i,abs(dc)))
        else:p=(origin[0]+int(round(dr*i/steps)),origin[1]+int(round(dc*i/steps)))
        if _contact(p,blocks,dots):return p
    return target
'''.replace('MODE',repr(motion)).replace('START','0' if include_start else '1')
    tree.body.extend(ast.parse(helper).body);ast.fix_missing_locations(tree)
    return ast.unparse(tree)+'\n'


def initialize():
    global TRAIN
    TRAIN=json.loads((LAB/'composed/training.json').read_text())


def score(job):
    code,config=job;metrics=constants.evaluate(code,TRAIN);ns={};exec(code,ns);phenotype=hashlib.sha256()
    for r in TRAIN:
        before=constants.state(r['before'])
        try:
            p=ns['model_step'](copy.deepcopy(before),r['action']);p=constants.canonical(before if p is None else p)
            phenotype.update(json.dumps(p,sort_keys=True,separators=(',',':')).encode())
        except Exception as exc:phenotype.update(type(exc).__name__.encode())
    return {'sha256':hashlib.sha256(code.encode()).hexdigest(),'code':code,'config':config,'edits':[] if config=={'identity':True} else [config],
            'training':metrics,'training_prediction_fingerprint':phenotype.hexdigest()}


def key(r):return json.dumps([r['before'],r['action']],sort_keys=True)


if __name__=='__main__':
    for n in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','RAYON_NUM_THREADS'):os.environ[n]='1'
    if OUT.exists():raise FileExistsError(OUT)
    OUT.mkdir();base=(LAB/'composed/selected-model.py').read_text()
    manifest={'workers':16,'base_sha256_lf':hashlib.sha256(base.encode()).hexdigest(),'runner_sha256':hashlib.sha256(__import__('pathlib').Path(__file__).read_bytes()).hexdigest(),
              'final_seeds':list(range(9400,9416)),'hypotheses':['move then merge near point','merge placement','first-contact stop along motion'],
              'evidence':'composed/training-residuals.json; no final labels used for design/fitting',
              'scope':'One public fixture/level prediction repair; not agent completions or competition score.'}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    jobs=[(base,{'identity':True})];seen={hashlib.sha256(base.encode()).hexdigest()}
    for radius,speed,merge_radius,anchor,offset,motion,include_start,pool in itertools.product((6,8,10),(6,8),(0,2,4,6,8),('moved','click','partner','midpoint'),(0,1),('none','linear_round','axis_clamp'),(False,True),('before','after')):
        if merge_radius==0 and (anchor!='moved' or offset!=1):continue
        if motion=='none' and (include_start or pool!='after'):continue
        config=dict(radius=radius,speed=speed,merge_radius=merge_radius,anchor=anchor,offset=offset,motion=motion,include_start=include_start,pool=pool)
        code=build(base,**config);sha=hashlib.sha256(code.encode()).hexdigest()
        if sha in seen:continue
        seen.add(sha);jobs.append((code,config))
    print(str(len(jobs))+' contact/merge programs,16processes',flush=True)
    with ProcessPoolExecutor(max_workers=16,initializer=initialize) as p:rows=list(p.map(score,jobs,chunksize=8))
    selected=max(rows,key=constants.rank)
    (OUT/'selected-model.py').write_bytes(selected['code'].encode())
    (OUT/'selection.json').write_text(json.dumps({k:v for k,v in selected.items() if k!='code'},indent=2),encoding='utf8')
    (OUT/'trials.jsonl').write_text(''.join(json.dumps({k:v for k,v in r.items() if k!='code'})+'\n' for r in rows),encoding='utf8')
    train=json.loads((LAB/'composed/training.json').read_text());validation=json.loads((LAB/'holdout.json').read_text())
    report={'source_variants':len(rows),'distinct_training_prediction_phenotypes':len({r['training_prediction_fingerprint'] for r in rows}),
            'baseline_training':constants.evaluate(base,train),'selected_training':selected['training'],
            'baseline_validation':constants.evaluate(base,validation),'selected_validation':constants.evaluate(selected['code'],validation),
            'selected_sha256':selected['sha256'],'selected_config':selected['config']}
    if report['selected_validation']['balanced_exact']>report['baseline_validation']['balanced_exact']:
        games=json.loads((dataset.PROMPTS/'benchmark.json').read_text())['game_runs'];history=next(g['history'] for g in games if g['game_id'].startswith('su15-'))
        path=next((dataset.ROOT/'games/environment_files').rglob('su15.py'));cls=re.search(r'^class (\w+)\(ARCBaseGame\)',path.read_text(),re.M)[1]
        with ThreadPoolExecutor(max_workers=16) as p:episodes=list(p.map(dataset.isolated,[(str(path.resolve()),cls,history,s,'final-contact') for s in manifest['final_seeds']]))
        (OUT/'final-episodes.json').write_text(json.dumps(episodes,indent=2),encoding='utf8')
        prior=[]
        for old in ('point-motion','composed'):
            prior.extend(r for e in json.loads((LAB/old/'final-episodes.json').read_text()) for r in e['rows'])
        seen={key(r) for r in train+validation+prior};novel=[]
        for e in episodes:
            for r in e['rows']:
                k=key(r)
                if k not in seen:seen.add(k);novel.append(r)
        report.update(final_episode_errors=[e for e in episodes if e.get('error')],novel_final_samples=len(novel),
                      baseline_final=constants.evaluate(base,novel),selected_final=constants.evaluate(selected['code'],novel))
    else:report['final_test']='Not opened: no validation advantage.'
    report['qualification']=manifest['scope'];(OUT/'report.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report),flush=True)
