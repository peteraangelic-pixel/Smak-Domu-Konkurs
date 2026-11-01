"""Read-only discovery of artifacts for scored ARC submission57811453.

Never submits, reruns, edits kernels or exports credentials. Kernel outputs
and competition rerun artifacts must not be conflated.
"""
import json
import os
from pathlib import Path
import re
import subprocess
import time

OUT=Path('arc-agi-3/analysis/submission-access-20261031')
OUT.mkdir(parents=True,exist_ok=True)


def run(label,args):
    try:
        p=subprocess.run(['kaggle',*args],capture_output=True,text=True,timeout=150)
        raw=p.stdout+'\n'+p.stderr
        secret=os.environ.get('KAGGLE_API_TOKEN','')
        if secret:raw=raw.replace(secret,'[REDACTED]')
        raw=re.sub(r'(?i)([?&](?:token|key|signature|credential)=[^\s&]*)','[REDACTED]',raw)
        (OUT/(label+'.txt')).write_text(raw,encoding='utf8')
        return {'label':label,'args':args,'returncode':p.returncode,'output_file':label+'.txt'}
    except subprocess.TimeoutExpired:
        return {'label':label,'args':args,'timeout':150}


records=[]
for label,args in [
    ('cli-version',['--version']),
    ('submission-v137',['competitions','submission','57811453']),
    ('submission-v3',['competitions','submission','57247568']),
    ('episodes-v137',['competitions','episodes','57811453']),
    ('download-v137',['competitions','submission-download','57811453','-p',str(OUT/'submitted-file')]),
    ('competition-help',['competitions','--help']),
]:
    record=run(label,args);records.append(record)
    print(label,record.get('returncode','timeout'),flush=True)
    if label=='cli-version' and record.get('returncode')!=0:
        raise RuntimeError('Kaggle CLI failed before API access; no push or status polling performed')

inventory=[]
for p in (OUT/'submitted-file').glob('**/*'):
    if p.is_file():
        entry={'path':str(p.relative_to(OUT)),'bytes':p.stat().st_size}
        if p.suffix=='.parquet':
            try:
                import pandas as pd
                frame=pd.read_parquet(p)
                entry.update(rows=len(frame),columns=list(frame.columns))
                frame.head(20).to_json(OUT/'submitted-preview.json',orient='records',indent=2)
            except Exception as exc:entry['inspection_error']=type(exc).__name__
        inventory.append(entry)
(OUT/'access-audit.json').write_text(json.dumps({'operations':records,'download_inventory':inventory},indent=2),encoding='utf8')

mode=os.environ.get('ARC_AUDIT_MODE')
if mode in ('v3-smoke','memory-smoke','slim-smoke','levelscope-smoke','control-retest-smoke','hypotheses-smoke','validation-smoke','validation-retest-smoke','observation-cache-smoke','fresh-read-smoke','phase-lesson-smoke','phase-lesson-retest-smoke','transition-schema-smoke'):
    # Explicitly authorized private save-run. No competition submit command.
    slug='petersharps/arc3-codex-memory-v3-lab' if mode=='memory-smoke' else 'petersharps/arc3-duck-codex-v3-control-1031'
    label='memory-target' if mode=='memory-smoke' else 'v3-target'
    package='arc-agi-3/duck-lab-candidates/memory-v3' if mode=='memory-smoke' else 'arc-agi-3/duck-lab-candidates/v3-target-control'
    if mode=='slim-smoke':
        slug='petersharps/arc3-duck-codex-v3-slim-1101';label='slim-target';package='arc-agi-3/duck-lab-candidates/v3-slim'
    if mode=='levelscope-smoke':
        slug='petersharps/arc3-duck-codex-v3-levelscope-1101';label='levelscope-target';package='arc-agi-3/duck-lab-candidates/v3-levelscope'
    if mode=='control-retest-smoke':
        slug='petersharps/arc3-duck-codex-v3-retest-1101';label='control-retest';package='arc-agi-3/duck-lab-candidates/v3-control-retest'
    if mode=='hypotheses-smoke':
        slug='petersharps/arc3-duck-codex-v3-hypotheses-1101';label='hypotheses-target';package='arc-agi-3/duck-lab-candidates/v3-hypotheses'
    if mode=='validation-smoke':
        slug='petersharps/arc3-duck-codex-v3-validation-1101';label='validation-target';package='arc-agi-3/duck-lab-candidates/v3-validation'
    if mode=='validation-retest-smoke':
        slug='petersharps/arc3-duck-codex-v3-validation-retest-1101';label='validation-retest';package='arc-agi-3/duck-lab-candidates/v3-validation-retest'
    if mode=='observation-cache-smoke':
        slug='petersharps/arc3-duck-codex-v3-observation-cache-1101';label='observation-cache';package='arc-agi-3/duck-lab-candidates/v3-observation-cache'
    if mode=='fresh-read-smoke':
        slug='petersharps/arc3-duck-codex-v3-fresh-read-1101';label='fresh-read';package='arc-agi-3/duck-lab-candidates/v3-fresh-read'
    if mode=='phase-lesson-smoke':
        slug='petersharps/arc3-duck-codex-v3-phase-lesson-1101';label='phase-lesson';package='arc-agi-3/duck-lab-candidates/v3-phase-lesson'
    if mode=='phase-lesson-retest-smoke':
        slug='petersharps/arc3-duck-codex-v3-phase-retest-1101';label='phase-lesson-retest';package='arc-agi-3/duck-lab-candidates/v3-phase-lesson-retest'
    if mode=='transition-schema-smoke':
        slug='petersharps/arc3-duck-codex-v3-transition-schema-1101';label='transition-schema';package='arc-agi-3/duck-lab-candidates/v3-transition-schema'
    existing=run(label+'-preflight',['kernels','list','--mine','--search',slug.split('/')[1],'--csv'])
    status=(OUT/(label+'-preflight.txt')).read_text(encoding='utf8')
    if existing.get('returncode')==0 and slug in status:
        print('Existing target kernel: preserve it, no duplicate push.',flush=True)
    elif existing.get('returncode')==0:
        record=run(label+'-push',['kernels','push','-p',package])
        print('Authorized private save-run push result:',record.get('returncode'),flush=True)
    else:
        print('Preflight inconclusive: no push.',flush=True)

if mode=='memory-correction':
    slug='petersharps/arc3-codex-memory-v3-lab'
    pulled=OUT/'latest-memory'
    result=run('memory-correction-preflight',['kernels','pull',slug,'-p',str(pulled)])
    if result.get('returncode')==0:
        old=Path('arc-agi-3/duck-lab-candidates/memory-v3/agent.ipynb')
        actual=next(pulled.glob('*.ipynb'))
        def codes(p):return [''.join(c['source']).rstrip('\n') for c in json.loads(p.read_text(encoding='utf8'))['cells'] if c['cell_type']=='code']
        if codes(old)==codes(actual):
            record=run('memory-correction-push',['kernels','push','-p','arc-agi-3/duck-lab-candidates/memory-v3-recovery'])
            print('Correction push:',record.get('returncode'),flush=True)
        else:print('Latest memory code differs; do not overwrite or duplicate correction.',flush=True)

if mode in ('v3-watch','memory-watch','memory-correction-watch','slim-watch','levelscope-watch','control-retest-watch','hypotheses-watch','validation-watch','validation-retest-watch','observation-cache-watch','fresh-read-watch','phase-lesson-watch','phase-lesson-retest-watch','transition-schema-watch'):
    slug='petersharps/arc3-codex-memory-v3-lab' if mode in ('memory-watch','memory-correction-watch') else 'petersharps/arc3-duck-codex-v3-control-1031'
    if mode=='memory-correction-watch':slug='petersharps/arc3-codex-memory-v3-recovery'
    label='memory-correction' if mode=='memory-correction-watch' else 'memory-target' if mode=='memory-watch' else 'v3-target'
    version='2' if mode=='memory-correction-watch' else '1'
    if mode=='slim-watch':slug='petersharps/arc3-duck-codex-v3-slim-1101';label='slim-target'
    if mode=='levelscope-watch':slug='petersharps/arc3-duck-codex-v3-levelscope-1101';label='levelscope-target'
    if mode=='control-retest-watch':slug='petersharps/arc3-duck-codex-v3-retest-1101';label='control-retest'
    if mode=='hypotheses-watch':slug='petersharps/arc3-duck-codex-v3-hypotheses-1101';label='hypotheses-target'
    if mode=='validation-watch':slug='petersharps/arc3-duck-codex-v3-validation-1101';label='validation-target'
    if mode=='validation-retest-watch':slug='petersharps/arc3-duck-codex-v3-validation-retest-1101';label='validation-retest'
    if mode=='observation-cache-watch':slug='petersharps/arc3-duck-codex-v3-observation-cache-1101';label='observation-cache'
    if mode=='fresh-read-watch':slug='petersharps/arc3-duck-codex-v3-fresh-read-1101';label='fresh-read'
    if mode=='phase-lesson-watch':slug='petersharps/arc3-duck-codex-v3-phase-lesson-1101';label='phase-lesson'
    if mode=='phase-lesson-retest-watch':slug='petersharps/arc3-duck-codex-v3-phase-retest-1101';label='phase-lesson-retest'
    if mode=='transition-schema-watch':slug='petersharps/arc3-duck-codex-v3-transition-schema-1101';label='transition-schema'
    deadline=time.monotonic()+6000
    events=[]
    while time.monotonic()<deadline:
        record=run(label+'-status',['kernels','status',slug+'/'+version])
        status=(OUT/(label+'-status.txt')).read_text(encoding='utf8')
        match=re.search(r'KernelWorkerStatus\.(\w+)',status)
        state=match.group(1).upper() if match else 'UNRESOLVED'
        events.append({'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'state':state,'returncode':record.get('returncode')})
        (OUT/(label+'-watch-events.json')).write_text(json.dumps(events,indent=2),encoding='utf8')
        print(label+' status:',state,flush=True)
        if state in ('COMPLETE','ERROR','CANCELLED','CANCELED'):
            run(label+'-output',['kernels','output',slug+'/'+version,'-p',str(OUT/(label+'-output')),
                                  '--file-pattern',r'(benchmark\.json|.*\.log|.*metrics.*\.json|budget_probe\.json)$'])
            break
        if len(events)>=3 and all(e['state']=='UNRESOLVED' for e in events[-3:]):
            break
        time.sleep(60)
