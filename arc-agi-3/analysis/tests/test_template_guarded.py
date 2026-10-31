from pathlib import Path
import sys
from types import SimpleNamespace

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from template_guarded import GuardedTemplateTransfer,install
import json
import numpy as np

def observed_grid():
    return np.array(json.loads((Path(__file__).resolve().parents[1]/'causal-agent-20261031/ft09-initial-grid.json').read_text()),dtype=np.uint8)


def test_observed_oscillation_stops_at_cap_and_rearms_on_level_change():
    a=observed_grid();agent=GuardedTemplateTransfer();previous=None;count=0
    for _ in range(60):
        out=agent.act(a,[6],1)
        if out is None:break
        _,x,y=out;a[y-3:y+3,x-3:x+3]=agent.prediction['expected_color']
        if previous is not None:
            xx,yy=previous;a[yy-3:yy+3,xx-3:xx+3]=9
        previous=x,y;count+=1
    assert count==32
    assert agent.act(a,[6],1) is None
    assert agent.act(observed_grid(),[6],2) is not None
    assert agent.level_actions==1


def test_install_is_idempotent_and_kill_switch_delegates_exactly(monkeypatch):
    class Agent:
        def analyze(self,*args,**kwargs):return ('baseline',args,kwargs)
    ta=SimpleNamespace(ToolAgent=Agent)
    install(ta);first=ta.ToolAgent.analyze
    install(ta);assert ta.ToolAgent.analyze is first
    monkeypatch.setenv('ARC3_TEMPLATE_ENABLED','0')
    assert Agent().analyze(11,flag=True)==('baseline',(11,),{'flag':True})
