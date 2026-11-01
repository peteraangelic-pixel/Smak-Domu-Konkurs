"""Exercise real ToolAgent and isolated snippets; no LLM or engine oracle."""
import json
import os
from pathlib import Path
import sys
import tempfile
import argparse
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--source',type=Path,default=ROOT/'analysis/champion-recovery-20261031/materialized-clean/ARC3-Inference')
parser.add_argument('--out',type=Path,default=ROOT/'analysis/observation-cache-20261101/verification.json')
args=parser.parse_args()
sys.path.insert(0,str(args.source.resolve()))
os.environ.update(ARC3_PERSISTENT_FUNCTIONS='1',ARC3_PERSISTENT_FUNCTIONS_SCOPE='game')
from inference.agent import tool_agent as ta,python_tool_sandbox as sb
from inference.agent.runtime_state import Frame,HistoryEntry,write_runtime_state
if (args.source/'inference/utils/install_observation_cache.py').exists():
    from inference.utils.install_observation_cache import install
else:
    from install_observation_cache import install
install(ta,sb);hook=ta.run_sandboxed_python;install(ta,sb);assert hook is ta.run_sandboxed_python
assert 'Small literal scratch variables' in ta._PYTHON_TOOL_DESCRIPTION
rendered=ta._build_system_prompt(tool_output_tokens=4096)
assert 'Small literal scratch variables' in rendered
assert 'Python variables reset between tool calls.' not in rendered
original=sb.subprocess.Popen
def popen(command,**kw):
    if os.name=='nt' and '-c' in command and len(command[-1])>16000:
        path=Path(kw['cwd'])/'bootstrap.py';path.write_text(command[-1],encoding='utf8');command=command[:-2]+[str(path)]
    return original(command,**kw)
sb.subprocess.Popen=popen


with tempfile.TemporaryDirectory() as folder:
    root=Path(folder)
    def state(game='a',step=0,level=1,grid=((0,0),(0,0))):
        p=root/game/'state.json';p.parent.mkdir(exist_ok=True)
        f=Frame(grid=grid,step=step,level=level)
        write_runtime_state(p,current_frame=f,history=[HistoryEntry(action='',frame=f)])
        return p
    p=state();a=ta.ToolAgent(model='verification-only',provider='lmstudio');a._ensure_session(p)
    def run(code,agent=a,path=None):return json.loads(agent._run_python_tool(path or p,{'code':code}).content)
    assert run("BLK={'R':[(1,2)]}; RING={(3,4)}")['returncode']==0
    restored=run("print(BLK['R'])")
    assert '[(1, 2)]' in restored['stdout']
    assert 'OBSERVATION_CACHE restored=' in restored['stdout']
    assert '(3, 4)' in run('print(RING)')['stdout']
    state(step=1);error=run('print(BLK)');assert 'NameError' in str(error)
    run('value=17');other=state('b');a._ensure_session(other)
    assert 'NameError' in str(run('print(value)',path=other))
    a._ensure_session(p);run('value=18')
    b=ta.ToolAgent(model='verification-only',provider='lmstudio');b._ensure_session(p)
    assert 'NameError' in str(run('print(value)',agent=b))
    run("value=19\ntry: action(['INVALID'])\nexcept Exception: pass")
    assert 'NameError' in str(run('print(value)'))
    calls=[]
    def callback(arguments):
        assert a._observation_literal_cache.payload=='{}','cache must clear before host callback'
        calls.append(arguments)
        raise RuntimeError('synthetic host failure after invalidation')
    a._step_env_callback=callback;a._current_valid_actions=['UP']
    run("value=19\ntry: action(['UP'])\nexcept Exception: pass")
    assert calls,'actual action host callback was not reached'
    assert 'NameError' in str(run('print(value)'))
    run('value=20');run("raise ValueError('fixture error')")
    assert 'NameError' in str(run('print(value)'))
    run("current_frame='overwritten'; value=21")
    assert '1' in run('print(current_frame.step)')['stdout']
    state(step=1,level=2)
    assert 'NameError' in str(run('print(value)'))
    run('value=22')
    state(step=1,level=2,grid=((1,0),(0,0)))
    assert 'NameError' in str(run('print(value)'))
report={'same_observation_restores_literals':True,'step_change_invalidates':True,
        'new_game_isolated':True,'agents_isolated':True,'caught_invalid_action_invalidates':True,
        'snippet_error_invalidates':True,'protected_frame_not_persisted':True,'level_change_invalidates':True,
        'install_idempotent':True,'cache_cleared_before_action_callback':True,
        'restore_marker_observed':True,'tool_description_updated':True,
        'system_prompt_updated':True,'frame_change_without_step_change_invalidates':True,
        'source':str(args.source.resolve()),
        'scope':'Actual ToolAgent and isolated Python processes; synthetic observations, no LLM quality claim.'}
args.out.parent.mkdir(exist_ok=True,parents=True)
args.out.write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))
