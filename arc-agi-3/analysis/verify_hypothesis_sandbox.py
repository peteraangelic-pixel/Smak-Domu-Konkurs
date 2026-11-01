"""Verify the experimental helpers inside the real isolated Duck process."""
import json
import os
from pathlib import Path
import sys
import argparse
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=ROOT/'analysis/champion-recovery-20261031/materialized-clean/ARC3-Inference')
args=p.parse_args()
sys.path.insert(0,str(args.source.resolve()))
os.environ['ARC3_WORLD_MODEL']='1'
from inference.agent import python_tool_sandbox as sandbox
from inference.agent import tool_agent as ta
from install_hypothesis_tools import install,install_agent,GUIDANCE
original_description=ta._PYTHON_TOOL_DESCRIPTION
install_agent(ta,sandbox)
description=ta._PYTHON_TOOL_DESCRIPTION
install_agent(ta,sandbox)
assert ta._PYTHON_TOOL_DESCRIPTION==description
assert description.startswith(original_description) and description.count(GUIDANCE)==1
agent=ta.ToolAgent(model='verification-only',provider='lmstudio')
spec=agent._tools(ROOT/'analysis/hypothesis-fixture/state.json')
assert 'choose_probe' in json.dumps(spec),spec
before=sandbox._SANDBOX_BOOTSTRAP
install(sandbox)
assert before==sandbox._SANDBOX_BOOTSTRAP
# Same Windows command-length adapter as run_duck_loop.py; bytes unchanged.
original_popen=sandbox.subprocess.Popen
def popen(command, **kwargs):
    if os.name=='nt' and isinstance(command,list) and '-c' in command and len(command[-1])>16000:
        path=Path(kwargs['cwd'])/'bootstrap.py'
        path.write_text(command[-1],encoding='utf8')
        command=command[:-2]+[str(path)]
    return original_popen(command,**kwargs)
sandbox.subprocess.Popen=popen
code='''
def encode(f): return f['position']
def wall(s,a): return min(2,s+1) if a=='RIGHT' else max(0,s-1)
def wrap(s,a): return (s+1)%3 if a=='RIGHT' else (s-1)%3
models=[{'name':'wall','encode':encode,'step':wall}, {'name':'wrap','encode':encode,'step':wrap}]
p=choose_probe(models,{'position':2},['LEFT','RIGHT'])
assert p['action']=='RIGHT'
r=validate_hypotheses(models,[({'position':2},'RIGHT',{'position':0})])
assert not r[0]['validated'] and r[1]['validated']
print('HYPOTHESIS_SANDBOX_OK')
'''
def no_action(*args,**kwargs):raise AssertionError('Verification must not execute game actions')
r=sandbox.run_sandboxed_python(code=code,timeout_seconds=10,initial_state={},action_handler=no_action)
assert not r.get('error'),r
assert 'HYPOTHESIS_SANDBOX_OK' in r['stdout'],r
assert 'HYPOTHESIS_PROBE models=2 actions=2' in r['stdout'],r
assert 'HYPOTHESIS_VALIDATE models=2 transitions=1' in r['stdout'],r
print(json.dumps({'real_isolated_sandbox':True,'idempotent_install':True,'probe_and_evidence_validation':True,'game_actions':len(r.get('action_results',[])),'scope':'Synthetic mechanics; no LLM or ARC quality measurement.'}))
