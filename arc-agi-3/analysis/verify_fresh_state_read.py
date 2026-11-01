"""Real isolated sandbox protocol fixtures; no LLM quality claim."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('--source',type=Path,default=ROOT/'analysis/champion-recovery-20261031/materialized-clean/ARC3-Inference')
p.add_argument('--out',type=Path,default=ROOT/'analysis/fresh-state-read-20261101/verification.json')
args=p.parse_args();sys.path.insert(0,str(args.source.resolve()))
from inference.agent import python_tool_sandbox as sb
if (args.source/'inference/utils/fresh_state_read.py').exists():
    from inference.utils.fresh_state_read import install
else:
    from fresh_state_read import install
install(sb);saved=sb._SANDBOX_BOOTSTRAP;install(sb);assert saved==sb._SANDBOX_BOOTSTRAP
original_popen=sb.subprocess.Popen
def popen(command,**kwargs):
    if os.name=='nt' and '-c' in command and len(command[-1])>16000:
        path=Path(kwargs['cwd'])/'bootstrap.py';path.write_text(command[-1],encoding='utf8');command=command[:-2]+[str(path)]
    return original_popen(command,**kwargs)
sb.subprocess.Popen=popen


def exercise(code,mode='normal'):
    messages=[]
    def state(step):
        frame={'ascii':'BB\nBB','step':step,'level':1,'shape':[2,2],'grid':[[0,0],[0,0]]}
        return {'current_frame':frame,'history':[{'action':'UP','frame':dict(frame)}],'valid_actions':['UP','RIGHT']}
    def action(actions,*,stale_after=None):
        message={'actions':actions,'stale_after':stale_after}
        messages.append(message)
        result={'executed':True,'executed_actions':['UP'],'gameplay_changed':False}
        if message.get('stale_after'):
            result={'executed':False,'stop_reason':'stale_state','stop_detail':'fixture stale warning'}
        elif mode=='death' and len(messages)==2:
            result={'executed':False,'stop_reason':'known_death','stop_detail':'fixture known death'}
        elif mode=='known_noop' and len(messages)==2:
            result={'executed':False,'stop_reason':'known_noop','stop_detail':'fixture known noop'}
        elif mode=='repeated' and len(messages)==2:
            result={'executed':False,'stop_reason':'repeated_action_in_state','stop_detail':'fixture repeated state'}
        elif mode=='terminal':result['game_over']=True
        return {'state':state(len(messages)),'action_result':result}
    result=sb.run_sandboxed_python(code=code,timeout_seconds=10,initial_state=state(0),action_handler=action)
    return result,messages


blocked={
 'blind':"action(['UP']);action(['RIGHT'])",
 'read_before_noop':"a=current_frame.ascii;action(['UP']);action(['RIGHT'])",
 'old_alias':"old=current_frame;action(['UP']);a=old.ascii;action(['RIGHT'])",
 'history':"action(['UP']);a=history[-1].frame.ascii;action(['RIGHT'])",
 'metadata':"action(['UP']);a=current_frame.step;action(['RIGHT'])",
}
for label,code in blocked.items():
    result,messages=exercise(code)
    assert len(messages)==2 and messages[1]['stale_after'],(label,result,messages)
    assert 'StaleStateActionError' in str(result),(label,result)
for attr in ('ascii','segmentation'):
    result,messages=exercise("action(['UP']);a=current_frame."+attr+";action(['RIGHT'])")
    assert not result.get('error'),result
    assert len(messages)==2 and messages[1]['stale_after'] is None,messages
    assert 'FRESH_STATE_READ reobserved=1' in result['stdout'],result
for mode,error in [('death','KnownDeathActionError'),('known_noop','KnownNoOpActionError'),('repeated','RepeatedActionInStateError')]:
    result,messages=exercise("action(['UP']);a=current_frame.ascii;action(['RIGHT'])",mode)
    assert error in str(result),(mode,result)
result,messages=exercise("action(['UP']);a=current_frame.ascii;action(['RIGHT'])",'terminal')
assert len(messages)==1 and 'TerminalStateActionError' in str(result),(result,messages)
from inference.agent import tool_agent as ta
from inference.agent.runtime_state import Frame,HistoryEntry,write_runtime_state
with tempfile.TemporaryDirectory() as tmp:
    for idx,code in enumerate(("action(['UP']);action(['RIGHT'])","action(['UP']);a=current_frame.ascii;action(['RIGHT'])")):
        path=Path(tmp)/str(idx)/'state.json';path.parent.mkdir()
        history=[];messages=[]
        def update(step):
            frame=Frame(grid=((0,0),(0,0)),step=step,level=1)
            history.append(HistoryEntry(action='UP' if step else '',frame=frame))
            write_runtime_state(path,current_frame=frame,history=history)
        update(0)
        def callback(arguments):
            messages.append(arguments)
            if arguments.get('stale_after'):
                return {'executed':False,'stop_reason':'stale_state','stop_detail':'fixture stale','valid_actions':['UP','RIGHT']}
            update(len(messages))
            return {'executed':True,'executed_count':1,'executed_actions':['UP'],
                    'gameplay_changed':False,'gameplay_changed_per_action':[False],
                    'valid_actions':['UP','RIGHT'],'level':1,'action_num':len(messages)}
        agent=ta.ToolAgent(model='verification-only',provider='lmstudio');agent._ensure_session(path)
        agent._step_env_callback=callback;agent._current_valid_actions=['UP','RIGHT']
        result=json.loads(agent._run_python_tool(path,{'code':code}).content)
        assert len(messages)==2,(idx,result,messages)
        assert bool(messages[1].get('stale_after'))==(idx==0),(idx,result,messages)
        assert ('StaleStateActionError' in str(result))==(idx==0),(idx,result)
report={'actual_isolated_sandbox':True,'install_idempotent':True,'blind_and_stale_aliases_still_blocked':list(blocked),
        'current_ascii_and_segmentation_read_clear_stale':True,'internal_action_reads_do_not_clear_stale':True,
        'known_death_noop_repeated_and_terminal_preserved':True,'actual_toolagent_callback_protocol':True,
        'marker_observed':True,'source':str(args.source.resolve()),
        'scope':'Synthetic protocol fixtures on actual sandbox; not an engine/LLM quality result.'}
args.out.parent.mkdir(exist_ok=True,parents=True);args.out.write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))
