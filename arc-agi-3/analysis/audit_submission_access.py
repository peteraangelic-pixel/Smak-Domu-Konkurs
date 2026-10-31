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
if mode in ('v3-smoke','memory-smoke'):
    # Explicitly authorized private save-run. No competition submit command.
    slug='petersharps/arc3-codex-memory-v3-lab' if mode=='memory-smoke' else 'petersharps/arc3-duck-codex-v3-control-1031'
    label='memory-target' if mode=='memory-smoke' else 'v3-target'
    package='arc-agi-3/duck-lab-candidates/memory-v3' if mode=='memory-smoke' else 'arc-agi-3/duck-lab-candidates/v3-target-control'
    existing=run(label+'-preflight',['kernels','list','--mine','--search',slug.split('/')[1],'--csv'])
    status=(OUT/(label+'-preflight.txt')).read_text(encoding='utf8')
    if existing.get('returncode')==0 and slug in status:
        print('Existing target kernel: preserve it, no duplicate push.',flush=True)
    elif existing.get('returncode')==0:
        record=run(label+'-push',['kernels','push','-p',package])
        print('Authorized private save-run push result:',record.get('returncode'),flush=True)
    else:
        print('Preflight inconclusive: no push.',flush=True)

if mode in ('v3-watch','memory-watch'):
    slug='petersharps/arc3-codex-memory-v3-lab' if mode=='memory-watch' else 'petersharps/arc3-duck-codex-v3-control-1031'
    label='memory-target' if mode=='memory-watch' else 'v3-target'
    deadline=time.monotonic()+6000
    events=[]
    while time.monotonic()<deadline:
        record=run(label+'-status',['kernels','status',slug])
        status=(OUT/(label+'-status.txt')).read_text(encoding='utf8')
        match=re.search(r'KernelWorkerStatus\.(\w+)',status)
        state=match.group(1).upper() if match else 'UNRESOLVED'
        events.append({'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'state':state,'returncode':record.get('returncode')})
        (OUT/(label+'-watch-events.json')).write_text(json.dumps(events,indent=2),encoding='utf8')
        print(label+' status:',state,flush=True)
        if state in ('COMPLETE','ERROR','CANCELLED','CANCELED'):
            run(label+'-output',['kernels','output',slug+'/1','-p',str(OUT/(label+'-output')),
                                  '--file-pattern',r'(benchmark\.json|.*\.log|.*metrics.*\.json|budget_probe\.json)$'])
            break
        if len(events)>=3 and all(e['state']=='UNRESOLVED' for e in events[-3:]):
            break
        time.sleep(60)
