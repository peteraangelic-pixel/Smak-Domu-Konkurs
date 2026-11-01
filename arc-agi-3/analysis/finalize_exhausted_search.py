"""Finalize an exhausted finite search without repeated costly surrogate fits."""
from concurrent.futures import ThreadPoolExecutor
import itertools
import json
import os
from pathlib import Path
import re
from evolve_search import GENES,CONTROL,identity,summary,rank,isolated_worker


if __name__=='__main__':
    for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','RAYON_NUM_THREADS'):os.environ[k]='1'
    root=Path(__file__).resolve().parents[1];lab=root/'analysis/cpu-search-20261101'
    out=lab/'finalized-report.json'
    if out.exists():raise FileExistsError(out)
    manifest=json.loads((lab/'manifest.json').read_text())
    genomes=[dict(zip(GENES,v)) for v in itertools.product(*GENES.values())]
    games={}
    for p in (root/'games/environment_files').rglob('*.py'):
        cls=re.search(r'^class (\w+)\(ARCBaseGame\)',p.read_text(encoding='utf8'),re.M)[1]
        games[p.stem]=(str(p.resolve()),cls)
    train=[games[g] for g in manifest['train']];holdout=[games[g] for g in manifest['holdout']]
    rows=[json.loads(l) for l in (lab/'trials.jsonl').read_text().splitlines()]
    cache={(r['genome'],games[r['game']][0]):r for r in rows}
    assert all((identity(g),path) in cache for g in genomes for path,_ in train),'Training space not exhausted'
    ranked=sorted([summary(g,train,cache) for g in genomes],key=rank,reverse=True)
    best=ranked[0];selected={best['id']:best['genome'],identity(CONTROL):CONTROL}
    jobs=[(g,path,cls,manifest['budget']) for g in selected.values() for path,cls in holdout]
    with (lab/'final-holdout.jsonl').open('x',encoding='utf8') as log,ThreadPoolExecutor(max_workers=16) as pool:
        for row in pool.map(isolated_worker,jobs):
            cache[row['genome'],games[row['game']][0]]=row
            log.write(json.dumps(row)+'\n');log.flush()
    held=[summary(g,holdout,cache) for g in selected.values()]
    report={'reason':'All 144 configurations x 17 training games already evaluated; stop redundant surrogate refits.',
            'training_trials':len(rows),'training_errors':sum(bool(r.get('error')) for r in rows),
            'selected':best,'control_training':summary(CONTROL,train,cache),'holdout':held,
            'qualification':'Finite offline search, not LLM quality or Kaggle prediction; no hidden-game generalization claim.'}
    out.write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report),flush=True)
