"""Fresh equal-budget repetitions of a frozen priority-search finalist."""
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib
import json
import os
from pathlib import Path
import random
import re
from resource_gated_cpu_search import ROOT,BUDGET,CONTROL,isolated,rank


if __name__=='__main__':
    for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','RAYON_NUM_THREADS'):os.environ[key]='1'
    lab=ROOT/'analysis/resource-cpu-confirmation-20261101'
    if lab.exists():raise FileExistsError(lab)
    lab.mkdir()
    source_lab=ROOT/'analysis/resource-gated-cpu-20261101'
    report=json.loads((source_lab/'report.json').read_text())
    finalist=report['training'][0]['config']
    manifest=json.loads((source_lab/'manifest.json').read_text())
    genome=manifest['genome'];paths=sorted((ROOT/'games/environment_files').rglob('*.py'))
    jobs=[(str(p.resolve()),re.search(r'^class (\w+)\(ARCBaseGame\)',p.read_text(encoding='utf8'),re.M)[1],config,genome,'replica'+str(replica))
          for replica in range(2) for config in (CONTROL,finalist) for p in paths]
    random.Random(20261101).shuffle(jobs)
    record={'budget':BUDGET,'workers':16,'jobs':len(jobs),'control':CONTROL,'frozen_finalist':finalist,
            'replicas':2,'holdout':manifest['holdout'],'source_manifest':manifest,
            'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'qualification':'Fresh shuffled CPU replications; public offline search, not LLM/Kaggle prediction.'}
    (lab/'manifest.json').write_text(json.dumps(record,indent=2),encoding='utf8');rows=[]
    with (lab/'trials.jsonl').open('x',encoding='utf8') as log,ThreadPoolExecutor(max_workers=16) as pool:
        for future in as_completed([pool.submit(isolated,job) for job in jobs]):
            row=future.result();rows.append(row);log.write(json.dumps(row)+'\n');log.flush()
            if len(rows)%8==0 or len(rows)==len(jobs):print(str(len(rows))+'/'+str(len(jobs)),flush=True)
    results={}
    for replica in range(2):
        sub=[r for r in rows if r['phase']=='replica'+str(replica)]
        held=[r for r in sub if r['game'] in manifest['holdout']]
        results[str(replica)]={'all':[rank(c,sub) for c in (CONTROL,finalist)],'holdout':[rank(c,held) for c in (CONTROL,finalist)]}
    (lab/'report.json').write_text(json.dumps(results,indent=2),encoding='utf8');print('RESOURCE_CPU_CONFIRMATION_COMPLETE',flush=True)
