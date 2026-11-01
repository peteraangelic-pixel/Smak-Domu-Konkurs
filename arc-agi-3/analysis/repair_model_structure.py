"""Small structural program-repair experiment, selected only on training.

The old holdout is now validation because a prior numeric experiment used it.
An untouched final seed bank is opened only for a frozen promising candidate.
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

LAB=constants.LAB
OUT=LAB/'structural'


def candidate(base,mask,distance,rounding,radius):
    tree=ast.parse(base);step=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='model_step')
    sites=[]
    for parent in ast.walk(step):
        for field,value in ast.iter_fields(parent):
            if not isinstance(value,list):continue
            for index,node in enumerate(value):
                if (isinstance(node,ast.If) and not node.orelse and len(node.body)==1
                    and isinstance(node.body[0],ast.Return) and isinstance(node.body[0].value,ast.Constant)
                    and node.body[0].value.value is None and index+1<len(value)):
                    sites.append((parent,field,index))
    for i,(parent,field,index) in reversed(list(enumerate(sites))):
        if mask&(1<<i):
            body=getattr(parent,field);guard=body[index]
            # Keep the rest of this branch conditional, but allow subsequent
            # world dynamics outside it to run when the proposed move is inert.
            replacement=ast.If(test=ast.UnaryOp(op=ast.Not(),operand=guard.test),body=body[index+1:],orelse=[])
            setattr(parent,field,body[:index]+[replacement])
    class Rewrite(ast.NodeTransformer):
        def visit_Call(self,node):
            self.generic_visit(node)
            if isinstance(node.func,ast.Name) and node.func.id=='round' and rounding=='truncate':node.func.id='int'
            if (distance!='chebyshev' and isinstance(node.func,ast.Name) and node.func.id=='max' and len(node.args)==2
                and all(isinstance(a,ast.Call) and isinstance(a.func,ast.Name) and a.func.id=='abs' and len(a.args)==1 for a in node.args)):
                if distance=='manhattan':return ast.BinOp(left=node.args[0],op=ast.Add(),right=node.args[1])
                return ast.BinOp(left=ast.BinOp(left=node.args[0],op=ast.Pow(),right=ast.Constant(2)),op=ast.Add(),
                                 right=ast.BinOp(left=node.args[1],op=ast.Pow(),right=ast.Constant(2)))
            return node
    for fn in tree.body:
        if not isinstance(fn,ast.FunctionDef) or fn.name not in ('desired','cen_of','arrow_step','eats','model_step'):continue
        Rewrite().visit(fn)
        if fn.name=='model_step':
            for node in ast.walk(fn):
                if isinstance(node,ast.Constant) and type(node.value)is int and node.value==6:node.value=radius
    ast.fix_missing_locations(tree)
    return ast.unparse(tree)+'\n',len(sites)


if __name__=='__main__':
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','RAYON_NUM_THREADS'):os.environ[key]='1'
    if OUT.exists():raise FileExistsError(OUT)
    OUT.mkdir();base=(LAB/'base_model.py').read_text();_,sites=candidate(base,0,'chebyshev','round',6)
    manifest={'workers':16,'guard_sites':sites,'final_test_seeds':list(range(9220,9236)),
              'selection':'Training only; existing holdout renamed validation; independent final episodes only after selection.',
              'hypotheses':['inert input may still advance world dynamics','distance metric','rounding convention','coupled movement radius'],
              'base_sha256':hashlib.sha256(base.encode()).hexdigest(),'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'scope':'One public fixture prediction repair; not unseen games, completions, or Kaggle score.'}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    configs={};jobs=[]
    for mask,distance,rounding,radius in itertools.product(range(1<<sites),('chebyshev','manhattan','euclidean'),('round','truncate'),(4,6,8,10)):
        code,_=candidate(base,mask,distance,rounding,radius);sha=hashlib.sha256(code.encode()).hexdigest()
        if sha in configs:continue
        edit={'mask':mask,'distance':distance,'rounding':rounding,'radius':radius};configs[sha]=edit
        jobs.append((code,[] if code==base else [edit]))
    print(str(len(jobs))+' structural candidates,16processes',flush=True)
    with ProcessPoolExecutor(max_workers=16,initializer=constants.initialize) as pool:rows=list(pool.map(constants.score,jobs,chunksize=8))
    best=max(rows,key=constants.rank);(OUT/'selected-model.py').write_text(best['code'],encoding='utf8')
    (OUT/'selection.json').write_text(json.dumps({k:v for k,v in best.items() if k!='code'},indent=2),encoding='utf8')
    (OUT/'trials.jsonl').write_text(''.join(json.dumps({k:v for k,v in r.items() if k!='code'})+'\n' for r in rows),encoding='utf8')
    train=json.loads((LAB/'train.json').read_text());validation=json.loads((LAB/'holdout.json').read_text())
    report={'candidates':len(rows),'baseline_training':constants.evaluate(base,train),'selected_training':best['training'],
            'baseline_validation':constants.evaluate(base,validation),'selected_validation':constants.evaluate(best['code'],validation),
            'selected_sha256':best['sha256'],'selected_config':configs[best['sha256']]}
    improved=report['selected_training']['balanced_exact']>report['baseline_training']['balanced_exact'] and report['selected_validation']['balanced_exact']>report['baseline_validation']['balanced_exact']
    if improved:
        # Evaluation-only oracle wrapper; not imported by the program repairer.
        game=json.loads((dataset.PROMPTS/'benchmark.json').read_text())['game_runs']
        history=next(g['history'] for g in game if g['game_id'].startswith('su15-'))
        path=next((dataset.ROOT/'games/environment_files').rglob('su15.py'))
        cls=re.search(r'^class (\w+)\(ARCBaseGame\)',path.read_text(),re.M)[1]
        jobs=[(str(path.resolve()),cls,history,seed,'final_test') for seed in manifest['final_test_seeds']]
        episodes=[]
        with ThreadPoolExecutor(max_workers=16) as pool:
            for f in as_completed([pool.submit(dataset.isolated,j) for j in jobs]):episodes.append(f.result())
        (OUT/'final-episodes.json').write_text(json.dumps(episodes,indent=2),encoding='utf8')
        final=[r for e in episodes for r in e['rows']]
        report.update(final_episode_errors=[e for e in episodes if e.get('error')],
                      baseline_final=constants.evaluate(base,final),selected_final=constants.evaluate(best['code'],final))
    else:report['final_test']='Not opened: no training+validation advantage.'
    report['qualification']=manifest['scope']
    (OUT/'report.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report),flush=True)
