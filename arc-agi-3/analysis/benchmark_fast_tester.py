"""Paired node-limited real-engine search: original vs full-state fast clone."""
from concurrent.futures import ProcessPoolExecutor
import json
import os
from pathlib import Path
import re
import time


def run(path):
    from sweep2 import Args,play_game as baseline
    from fast_sweep import play_game as candidate
    from evolve_search import CONTROL
    cls=re.search(r'^class (\w+)\(ARCBaseGame\)',Path(path).read_text(encoding='utf8'),re.M)[1]
    args=Args(backend='rust',node_cap=120,sec_cap=60,max_levels=1,max_depth=80,
              frontier_cap=256,calib_time=60,**CONTROL)
    rows={}
    # Deterministic per-game order alternation reduces one-sided warmup bias.
    order=[('baseline',baseline),('candidate',candidate)]
    if sum(Path(path).stem.encode())%2:order.reverse()
    for name,fn in order:
        t=time.perf_counter();r=fn((path,cls,args));r['measured_seconds']=time.perf_counter()-t;rows[name]=r
    a,b=rows['baseline'],rows['candidate']
    keys=lambda r:[(l['solved'],l['nodes'],l.get('seq')) for l in r.get('levels',[])]
    return {'game':Path(path).stem,'equivalent_node_search':not a.get('error') and not b.get('error') and keys(a)==keys(b),
            'speedup':a['measured_seconds']/b['measured_seconds'],'runs':rows,
            'qualification':'Original public engine, offline search; no LLM or Kaggle prediction.'}


if __name__=='__main__':
    for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','RAYON_NUM_THREADS'):os.environ[k]='1'
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--games',nargs='*');p.add_argument('--workers',type=int,default=16)
    a=p.parse_args();root=Path(__file__).resolve().parents[1]
    paths=[str(f.resolve()) for f in (root/'games/environment_files').rglob('*.py') if not a.games or f.stem in a.games]
    if a.out.exists():raise FileExistsError(a.out)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('x',encoding='utf8') as log,ProcessPoolExecutor(max_workers=a.workers) as pool:
        for row in pool.map(run,paths):
            log.write(json.dumps(row)+'\n');log.flush()
            print(json.dumps({k:v for k,v in row.items() if k!='runs'}),flush=True)
