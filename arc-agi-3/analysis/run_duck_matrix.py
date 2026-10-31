"""Resume a bounded Duck matrix from an explicit, reviewable job plan."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--run',default='duck-loop-pilot-20261031')
parser.add_argument('--tokens',type=int,default=1024)
parser.add_argument('--request-tokens',type=int,default=512)
parser.add_argument('--seconds',type=int,default=600)
parser.add_argument('--variants',default='control,v18,memory,router')
args=parser.parse_args()
RUN=ROOT/args.run
SOURCE=ROOT/'duck-loop-20261031'
RUN.mkdir(exist_ok=True)
plan=RUN/'matrix-plan.json'
if not plan.exists():
    plan.write_text(json.dumps([{'game':g,'variant':v} for g in ('vc33','ls20')
                               for v in args.variants.split(',')],indent=2))
while True:
    jobs=json.loads(plan.read_text())
    pending=[]
    for job in jobs:
        target=RUN/(job['variant']+'-'+job['game']+'-paired')
        result=target/'result.json'
        if result.exists():
            record=json.loads(result.read_text())
            assert record['model']=='arc-lab-27b' and record['seed']==731
            assert record['budget']=={'generated_tokens':args.tokens,'request_tokens':args.request_tokens,'seconds':args.seconds}
            assert record['variant']==job['variant'] and record['game']==job['game']
            if record.get('error'):
                raise RuntimeError('Failed trial requires inspection: '+str(result))
        else:
            pending.append((job,target))
    if not pending:
        break
    job,target=pending[0]
    game,variant=job['game'],job['variant']
    if target.exists() and any(target.iterdir()):
        print('WAITING FOR EXISTING CHILD',variant,game,flush=True)
        limit=time.monotonic()+args.seconds+60
        while not (target/'result.json').exists() and time.monotonic()<limit:
            time.sleep(1)
        if not (target/'result.json').exists():
            raise TimeoutError(target)
        continue
    source=SOURCE/('v18' if variant=='v18' else 'packaged-'+variant if variant in ('memory','router') else 'v13')/'ARC3-Inference'
    command=[sys.executable,str(ROOT/'run_duck_loop.py'),'--source',str(source),'--game',game,
             '--variant',variant,'--out',str(target),'--token-budget',str(args.tokens),'--request-tokens',str(args.request_tokens),'--seconds',str(args.seconds)]
    print('START',variant,game,flush=True)
    process=subprocess.run(command,timeout=args.seconds+60)
    if process.returncode or not (target/'result.json').exists():
        raise RuntimeError(f'Incomplete {variant}/{game}: {process.returncode}')
    print('FINISH',variant,game,flush=True)
print('DUCK MATRIX COMPLETE',flush=True)
