"""Forward-only real public-game evaluation,16 worker processes, no LLM.

The policy sees only pixels, public level count and legal controls. Environment
source is imported by the evaluator, never supplied to or inspected by policy.
No clone/search/reset oracle, no baseline actions, no stored solution replay.
"""
import argparse
import hashlib
from concurrent.futures import ProcessPoolExecutor,as_completed
import importlib.util
import json
import os
from pathlib import Path
import re
import time

ROOT=Path(__file__).resolve().parents[1]


def run(job):
    path,variant,cap,backend=job
    import numpy as np
    from arcengine import ActionInput,GameAction
    from causal_explorer import CausalExplorer
    from template_transfer import TemplateTransfer
    spec=importlib.util.spec_from_file_location('public_environment',path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    # Discover the exported game class; do not inspect its implementation.
    from arcengine import ARCBaseGame
    cls=next(v for v in vars(mod).values() if isinstance(v,type) and v.__module__==mod.__name__ and issubclass(v,ARCBaseGame))
    engine=cls(); fd=engine.perform_action(ActionInput(id=GameAction.RESET))
    if variant=='gated':
        from template_gated_guarded import GuardedTemplateTransfer
        if backend=='rust':
            from native_rectangles import NativeRectangles
            agent=GuardedTemplateTransfer(extract_rectangles=NativeRectangles())
        else:agent=GuardedTemplateTransfer()
    elif variant=='navigation':
        from motion_navigator import MotionNavigator
        if backend=='rust':
            from native_rectangles import NativeRectangles
            agent=MotionNavigator(extract_rectangles=NativeRectangles())
        else:agent=MotionNavigator()
    elif variant=='guarded':
        from template_guarded import GuardedTemplateTransfer
        if backend=='rust':
            from native_rectangles import NativeRectangles
            agent=GuardedTemplateTransfer(extract_rectangles=NativeRectangles())
        else:agent=GuardedTemplateTransfer()
    elif variant=='template' and backend=='rust':
        from native_rectangles import NativeRectangles
        agent=TemplateTransfer(extract_rectangles=NativeRectangles())
    else:agent=TemplateTransfer() if variant=='template' else CausalExplorer(responsive=variant=='causal')
    records=[];t=time.perf_counter()
    for i in range(cap):
        grid=np.asarray(fd.frame,dtype=np.uint8)
        while grid.ndim>2:grid=grid[-1]
        controls=[int(x.value[0]) if hasattr(x,'value') else int(x) for x in fd.available_actions]
        action=agent.act(grid,controls,int(fd.levels_completed))
        if action is None:break
        command=ActionInput(id=GameAction.from_id(action[0]),data={'x':action[1],'y':action[2]} if action[0]==6 else {})
        before=int(fd.levels_completed);fd=engine.perform_action(command)
        records.append({'action':action,'completed':int(fd.levels_completed),'state':str(fd.state)})
        if str(fd.state).endswith(('WIN','GAME_OVER')):break
    return {'game':Path(path).stem,'variant':variant,'backend':backend,'levels_completed':int(fd.levels_completed),
            'actions':len(records),'seconds':time.perf_counter()-t,'state':str(fd.state),
            'policy_sha256':hashlib.sha256(Path(__file__).with_name('template_gated_guarded.py' if variant=='gated' else 'motion_navigator.py' if variant=='navigation' else 'template_guarded.py' if variant=='guarded' else 'template_transfer.py' if variant=='template' else 'causal_explorer.py').read_bytes()).hexdigest(),
            'base_template_sha256':hashlib.sha256(Path(__file__).with_name('template_gated_transfer.py' if variant=='gated' else 'template_transfer.py').read_bytes()).hexdigest() if variant in ('guarded','gated') else None,
            'evaluator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'trace':records,'template_hits':getattr(agent,'hits',0),'prediction_mismatches':getattr(agent,'mismatches',0),
            'qualification':'Forward-only observation policy,public games,no Kaggle score forecast.'}


if __name__=='__main__':
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','RAYON_NUM_THREADS'):os.environ[name]='1'
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--games',nargs='*')
    p.add_argument('--workers',type=int,default=16)
    p.add_argument('--variants',nargs='+',choices=['uniform','causal','template','guarded','gated','navigation'],default=['uniform','causal','template'])
    p.add_argument('--rect-backend',choices=['numpy','rust'],default='numpy')
    p.add_argument('--actions',type=int,default=256)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if args.out.exists():raise FileExistsError(args.out)
    paths=[x for x in (ROOT/'games/environment_files').rglob('*.py') if not args.games or x.stem in args.games]
    jobs=[(str(path),v,args.actions,args.rect_backend) for path in paths for v in args.variants]
    args.out.parent.mkdir(exist_ok=True,parents=True)
    with args.out.open('x',encoding='utf8') as f,ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures={pool.submit(run,j):j for j in jobs}
        for future in as_completed(futures):
            try:row=future.result()
            except Exception as e:row={'job':futures[future],'error':repr(e)}
            f.write(json.dumps(row)+'\n');f.flush()
            print({k:v for k,v in row.items() if k!='trace'},flush=True)
