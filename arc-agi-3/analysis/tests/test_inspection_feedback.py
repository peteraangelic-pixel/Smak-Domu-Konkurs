from dataclasses import dataclass
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from inspection_feedback import install

@dataclass(frozen=True)
class Result:
    content:str
    step_executed:bool=False
    made_progress:bool=False

def test_different_inspections_count_and_results_are_retained():
    class Agent:
        def _run_python_tool(self,text):return Result(text)
    install(Agent)
    a=Agent()
    assert a._run_python_tool('crop A').content=='crop A'
    assert a._run_python_tool('crop B').content=='crop B'
    r=a._run_python_tool('crop C')
    assert r.content.startswith('crop C') and 'EXPERIMENT FEEDBACK' in r.content
    assert not r.step_executed and a._inspection_feedback_count==1

def test_executed_action_resets_feedback_even_without_progress():
    class Agent:
        def _run_python_tool(self,action=False):return Result('actual output',action,False)
    install(Agent)
    a=Agent();a._run_python_tool();a._run_python_tool()
    r=a._run_python_tool(True)
    assert r.step_executed and r.content=='actual output'
    assert a._inspection_idle_count==0
