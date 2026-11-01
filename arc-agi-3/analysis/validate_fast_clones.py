"""Differential clone verification on the original public engine, 16 workers."""
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import sys
import time


def worker(path):
    import numpy as np
    from arcengine import ARCBaseGame,ActionInput,GameAction
    from fast_state_clone import clone,dumps
    from sweep2 import frame_of
    try:
        spec=importlib.util.spec_from_file_location('clone_fixture_'+Path(path).stem,path)
        mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
        cls=next(v for v in vars(mod).values() if isinstance(v,type) and v.__module__==mod.__name__ and issubclass(v,ARCBaseGame))
        parent=cls();initial=parent.perform_action(ActionInput(id=GameAction.RESET))
        compared=0;states=set();transitions=0
        for seed in range(6):
            rng=random.Random(731+seed)
            reference=copy.deepcopy(parent);candidate=clone(parent)
            parent_before=hashlib.sha256(dumps(parent)).hexdigest()
            fd=initial
            for step in range(24):
                legal=list(fd.available_actions);aid=0 if step in (7,19) else int(rng.choice(legal))
                data={'x':rng.randrange(64),'y':rng.randrange(64)} if aid==6 else {}
                a=ActionInput(id=GameAction.from_id(aid),data=data)
                left=reference.perform_action(a);right=candidate.perform_action(a)
                assert np.array_equal(frame_of(left),frame_of(right)),'frame divergence'
                for field in ('state','levels_completed','available_actions','win_levels'):
                    assert getattr(left,field)==getattr(right,field),field+' divergence'
                compared+=1;states.add(str(right.state));transitions+=int(right.levels_completed>fd.levels_completed)
                # Mutate a sibling; it must not affect this candidate or parent.
                before=hashlib.sha256(dumps(candidate)).hexdigest()
                sibling=clone(candidate);sibling.perform_action(ActionInput(id=GameAction.RESET))
                assert hashlib.sha256(dumps(candidate)).hexdigest()==before,'sibling changed candidate'
                assert hashlib.sha256(dumps(parent)).hexdigest()==parent_before,'child changed parent'
                if str(right.state).endswith(('WIN','GAME_OVER')):break
                fd=right
        # Existing solved traces are infrastructure fixtures only, never policy.
        fixture=Path(__file__).with_name('sweep-rust-ffi.jsonl')
        if fixture.exists():
            found=next((json.loads(line) for line in fixture.read_text(encoding='utf8').splitlines()
                        if json.loads(line).get('game')==Path(path).stem),None)
            if found:
                reference=copy.deepcopy(parent);candidate=clone(parent);previous=0
                for level in found.get('levels',[]):
                    if not level.get('solved'):break
                    for move in level.get('seq',[]):
                        data={k:v for k,v in move.items() if k in ('x','y')}
                        a=ActionInput(id=GameAction.from_id(move['a']),data=data)
                        left=reference.perform_action(a);right=candidate.perform_action(a)
                        assert np.array_equal(frame_of(left),frame_of(right)),'fixture frame divergence'
                        for field in ('state','levels_completed','available_actions','win_levels'):
                            assert getattr(left,field)==getattr(right,field),'fixture '+field
                        compared+=1;states.add(str(right.state))
                        transitions+=int(right.levels_completed>previous);previous=right.levels_completed
                    # Clone after a real level transition and compare RESET effects.
                    sibling_a=copy.deepcopy(reference);sibling_b=clone(candidate)
                    fa=sibling_a.perform_action(ActionInput(id=GameAction.RESET))
                    fb=sibling_b.perform_action(ActionInput(id=GameAction.RESET))
                    assert np.array_equal(frame_of(fa),frame_of(fb)),'post-transition RESET divergence'
                assert hashlib.sha256(dumps(parent)).hexdigest()==parent_before,'fixture changed parent'
        times={}
        for name,fn in [('deepcopy',copy.deepcopy),('pickle5',clone)]:
            t=time.perf_counter()
            for _ in range(16):fn(parent)
            times[name]=(time.perf_counter()-t)/16
        return {'game':Path(path).stem,'comparisons':compared,'states_seen':sorted(states),'level_transitions_observed':transitions,'clone_seconds':times,'speedup':times['deepcopy']/times['pickle5'],'ok':True}
    except Exception as exc:return {'game':Path(path).stem,'ok':False,'error':repr(exc)}


if __name__=='__main__':
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','RAYON_NUM_THREADS'):os.environ[name]='1'
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--games',nargs='*');p.add_argument('--workers',type=int,default=16)
    a=p.parse_args();root=Path(__file__).resolve().parents[1]
    paths=[str(p.resolve()) for p in (root/'games/environment_files').rglob('*.py') if not a.games or p.stem in a.games]
    if a.out.exists():raise FileExistsError(a.out)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('x',encoding='utf8') as log,ProcessPoolExecutor(max_workers=a.workers) as pool:
        for row in pool.map(worker,paths):
            log.write(json.dumps(row)+'\n');log.flush();print(json.dumps(row),flush=True)
