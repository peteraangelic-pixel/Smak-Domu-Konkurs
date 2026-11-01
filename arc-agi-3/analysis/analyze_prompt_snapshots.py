"""Deduplicate tool errors in retained prompt snapshots by native call ID.

Snapshots contain retained context, not every call of the full run. Counts
are observed lower bounds; action intent is not proof of game execution.
"""
import argparse
import ast
from collections import Counter
import json
from pathlib import Path
import re

HEAD=re.compile(r'^\[(SYSTEM|USER|ASSISTANT|REASONING|THINKING|ASSISTANT TOOL CALL: [^\]]+|TOOL RESULT: [^\]]+|TURN TRANSCRIPT SO FAR|SYSTEM PROMPT|USER PROMPT|MODEL RESPONSE META|TOOL CALL: [^\]]+|ANALYZER STATUS)\]\s*$',re.M)


def analyze(path):
    text=path.read_text(encoding='utf8')
    markers=list(HEAD.finditer(text));calls={};results={}
    for i,m in enumerate(markers):
        block=text[m.end():markers[i+1].start() if i+1<len(markers) else len(text)]
        kind=m.group(1)
        if kind=='ASSISTANT TOOL CALL: python':
            cid=re.search(r'^id: (call_\w+)',block,re.M)
            code=re.search(r'<parameter=code>\s*\n(.*?)</parameter>',block,re.S)
            if cid and code:calls[cid.group(1)]=code.group(1)
        elif kind.startswith('TOOL RESULT: call_'):
            results[kind.split(': ',1)[1]]=block
    errors=[]
    for cid,result in results.items():
        if 'Traceback (most recent call last)' not in result:continue
        lines=re.findall(r'^(?:\w*Error|Exception):[^\n]*',result,re.M)
        if lines:errors.append({'call_id':cid,'error':lines[-1],'code':calls.get(cid)})
    return {'snapshot':str(path),'observed_unique_calls':len(calls),'observed_unique_results':len(results),
            'errors':errors,'bool_as_mapping_errors':sum("'bool' object" in e['error'] and
              ('subscriptable' in e['error'] or "attribute 'get'" in e['error']) for e in errors),
            'scope':'Retained context snapshot only; deduplicated by native tool-call ID.'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prompts',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();rows=[analyze(p) for p in sorted(a.prompts.glob('*.log'))]
    record={'games':rows,'observed_errors':sum(len(r['errors']) for r in rows),
            'bool_as_mapping_errors':sum(r['bool_as_mapping_errors'] for r in rows)}
    a.out.parent.mkdir(exist_ok=True,parents=True);a.out.write_text(json.dumps(record,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in record.items() if k!='games'}))
    print(json.dumps({Path(r['snapshot']).name.split('-')[0]:[e['error'] for e in r['errors']] for r in rows},indent=2))
