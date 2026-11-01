"""Observe world-model API use in retained snapshots; never infer whole-run absence."""
import ast
import argparse
import json
from pathlib import Path
import re
from analyze_prompt_snapshots import HEAD


def inspect(path):
    text=path.read_text(encoding='utf8');markers=list(HEAD.finditer(text));calls={}
    for i,m in enumerate(markers):
        if m.group(1)!='ASSISTANT TOOL CALL: python':continue
        block=text[m.end():markers[i+1].start() if i+1<len(markers) else len(text)]
        cid=re.search(r'^id: (call_\w+)',block,re.M)
        code=re.search(r'<parameter=code>\s*\n(.*?)</parameter>',block,re.S)
        if cid and code:calls[cid.group(1)]=code.group(1)
    names=('model_state','model_step','model_goal','check_model','plan','commit')
    definitions={k:0 for k in names};uses={k:0 for k in names};details=[]
    parsed=0;syntax_errors=0;all_helpers=set()
    for cid,code in calls.items():
        try:tree=ast.parse(code)
        except SyntaxError:
            syntax_errors+=1;continue
        parsed+=1
        defs=[n.name for n in ast.walk(tree) if isinstance(n,ast.FunctionDef)]
        all_helpers.update(defs)
        invoked=[n.func.id for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)]
        for k in names:
            definitions[k]+=defs.count(k);uses[k]+=invoked.count(k)
        if any(k in defs or k in invoked for k in names):
            details.append({'call_id':cid,'definitions':[k for k in defs if k in names],
                            'calls':[k for k in invoked if k in names]})
    return {'snapshot':path.name,'unique_native_tool_calls':len(calls),
            'parsed_snippets':parsed,'syntax_errors':syntax_errors,'helper_names':sorted(all_helpers),'definitions':definitions,
            'syntactic_calls':uses,'details':details,
            'scope':'Retained snippets only; syntactic calls may be inside unused functions or fail before execution.'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prompts',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();rows=[inspect(f) for f in sorted(a.prompts.glob('*.log'))]
    a.out.write_text(json.dumps(rows,indent=2),encoding='utf8')
    print(json.dumps([{k:v for k,v in r.items() if k not in ('details','scope')} for r in rows],indent=2))
