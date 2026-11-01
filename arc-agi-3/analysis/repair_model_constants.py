"""Bounded train-only AST repair; one frozen evaluation on new probe holdout.

This repairs predictions, not complete ARC games. The repairer reads only model
source and encoded observed transitions. It never loads the game engine.
"""
from concurrent.futures import ProcessPoolExecutor
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import random

LAB=Path(__file__).resolve().parent/'model-repair-lab-20261101'
TRAIN=[]


def state(value):
    return {'b':[tuple(x) for x in value['b']],'d':[tuple(x) for x in value['d']],
            'a':tuple(value['a']) if value['a'] is not None else None}


def canonical(value):
    return {'b':sorted(tuple(x) for x in value['b']),'d':sorted(tuple(x) for x in value['d']),
            'a':tuple(value['a']) if value['a'] is not None else None}


def evaluate(code,rows):
    ns={};exec(compile(code,'<model-repair-candidate>','exec'),ns)
    counts={'changed':0,'noop':0};correct=dict.fromkeys(counts,0);fields=dict.fromkeys(counts,0);errors=0
    for row in rows:
        before=state(row['before']);after=canonical(row['after'])
        category='noop' if canonical(before)==after else 'changed';counts[category]+=1
        try:
            predicted=ns['model_step'](copy.deepcopy(before),row['action'])
            predicted=canonical(before if predicted is None else predicted)
            correct[category]+=predicted==after
            fields[category]+=sum(predicted[k]==after[k] for k in ('b','d','a'))/3
        except Exception:errors+=1
    available=[k for k,v in counts.items() if v]
    return {'samples':len(rows),'counts':counts,'correct':correct,'errors':errors,
            'balanced_exact':sum(correct[k]/counts[k] for k in available)/len(available),
            'balanced_fields':sum(fields[k]/counts[k] for k in available)/len(available)}


def initialize():
    global TRAIN
    TRAIN=json.loads((LAB/'train.json').read_text())


def score(job):
    code,edits=job
    return {'sha256':hashlib.sha256(code.encode()).hexdigest(),'code':code,'edits':edits,'training':evaluate(code,TRAIN)}


def mutations(code):
    tree=ast.parse(code);eligible=[]
    for fn in tree.body:
        if isinstance(fn,ast.FunctionDef) and fn.name in ('desired','cen_of','arrow_step','eats','model_step'):
            for node in ast.walk(fn):
                if isinstance(node,ast.Constant) and type(node.value) in (int,float) and abs(node.value)<=16:
                    eligible.append(node)
    values=(0,1,2,3,4,5,6,7,8,10,12,14,16,.5,1.5,2.5,3.5)
    for index,node in enumerate(eligible):
        old=node.value
        for value in values:
            if value==old:continue
            node.value=value
            yield ast.unparse(tree)+'\n',{'kind':'numeric_literal','site':index,'old':old,'new':value}
        node.value=old
    # Change repeated literals together inside one function (e.g. clamping
    # limits need symmetric lower/upper changes). This is generic AST search.
    for fn in tree.body:
        if not isinstance(fn,ast.FunctionDef) or fn.name not in ('arrow_step','model_step'):continue
        sites=[n for n in ast.walk(fn) if isinstance(n,ast.Constant) and type(n.value) in (int,float)]
        for old in (4,6,7,8,12):
            matching=[n for n in sites if n.value==old]
            if len(matching)<2:continue
            for value in (3,4,5,6,7,8,10,12,14):
                if value==old:continue
                for n in matching:n.value=value
                yield ast.unparse(tree)+'\n',{'kind':'coupled_literal','function':fn.name,'old':old,'new':value}
            for n in matching:n.value=old


def rank(row):
    s=row['training']
    return (s['balanced_exact'],s['balanced_fields'],-s['errors'],-len(row['edits']))


if __name__=='__main__':
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','RAYON_NUM_THREADS'):os.environ[name]='1'
    if (LAB/'repair-report.json').exists():raise FileExistsError('Preserve completed experiment')
    base=(LAB/'base_model.py').read_text();rng=random.Random(20261101);seen=set();parents=[{'code':base,'edits':[]}]
    trials=[]
    manifest={'workers':16,'max_generations':3,'max_candidates_per_generation':1024,'parent_beam':4,
              'base_sha256':hashlib.sha256(base.encode()).hexdigest(),'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'selection':'Training balanced exact-transition accuracy, then field accuracy, then errors/edit count. Holdout not read until finalist frozen.',
              'scope':'AST numeric repair of one frozen LLM model on new observed transitions; not an agent or Kaggle result.'}
    (LAB/'repair-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    with (LAB/'repair-trials.jsonl').open('x',encoding='utf8') as log,ProcessPoolExecutor(max_workers=16,initializer=initialize) as pool:
        for generation in range(3):
            proposals=[]
            if generation==0:proposals.append((base,[]))
            for parent in parents:
                for code,edit in mutations(parent['code']):
                    sha=hashlib.sha256(code.encode()).hexdigest()
                    if sha not in seen:seen.add(sha);proposals.append((code,parent['edits']+[edit]))
            # Freeze the bounded sample before scoring; no holdout feedback.
            if len(proposals)>1024:
                if generation==0:proposals=[proposals[0]]+rng.sample(proposals[1:],1023)
                else:proposals=rng.sample(proposals,1024)
            print('generation '+str(generation)+': '+str(len(proposals))+' candidates',flush=True)
            for row in pool.map(score,proposals,chunksize=8):
                row['generation']=generation;trials.append(row)
                log.write(json.dumps({k:v for k,v in row.items() if k!='code'})+'\n');log.flush()
            parents=sorted(trials,key=rank,reverse=True)[:4]
            print(json.dumps({'generation':generation,'best':parents[0]['training'],'edits':parents[0]['edits']}),flush=True)
    selected=parents[0]
    (LAB/'selected-model.py').write_text(selected['code'],encoding='utf8')
    (LAB/'selection.json').write_text(json.dumps({k:v for k,v in selected.items() if k!='code'},indent=2),encoding='utf8')
    # Deliberately load held-out labels ONLY after writing frozen selection.
    holdout=json.loads((LAB/'holdout.json').read_text());train=json.loads((LAB/'train.json').read_text())
    report={'trials':len(trials),'baseline_training':evaluate(base,train),'selected_training':selected['training'],
            'baseline_holdout':evaluate(base,holdout),'selected_holdout':evaluate(selected['code'],holdout),
            'selected_sha256':selected['sha256'],'selected_edits':selected['edits'],'qualification':manifest['scope']}
    (LAB/'repair-report.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report),flush=True)
