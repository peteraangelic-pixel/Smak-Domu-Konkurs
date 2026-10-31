"""Read-only discovery of artifacts for scored ARC submission57811453.

Never submits, reruns, edits kernels or exports credentials. Kernel outputs
and competition rerun artifacts must not be conflated.
"""
import json
import os
from pathlib import Path
import re
import subprocess

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
