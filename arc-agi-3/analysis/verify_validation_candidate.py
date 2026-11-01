"""Verify actual shipped ToolAgent hook; no model calls."""
import json
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
os.environ.update(ARC3_PERSISTENT_FUNCTIONS='1',ARC3_PERSISTENT_FUNCTIONS_SCOPE='game',ARC3_MEMORY_SECTIONS='off')
sys.path.insert(0,str(ROOT/'analysis/v3-validation-20261101/materialized/ARC3-Inference'))
from inference.agent.tool_agent import ToolAgent
from inference.agent.runtime_state import Frame,HistoryEntry

def prompt(agent,level):
    frame=Frame(grid=((0,0),(0,0)),step=1,level=level)
    return agent._build_user_prompt(1,current_frame=frame,history_entries=[HistoryEntry(action='',frame=frame)],valid_actions=['UP'])

a=ToolAgent(model='verification-only',provider='lmstudio');a._ensure_session(ROOT/'analysis/fixture-a/state.json')
assert 'MODEL_VALIDATION_REQUEST' not in prompt(a,1)
a._kept_functions={'helper':'def l3_step(s,a):\n return s'}
assert 'MODEL_VALIDATION_REQUEST' in prompt(a,1)
assert 'MODEL_VALIDATION_REQUEST' not in prompt(a,1)
assert 'MODEL_VALIDATION_REQUEST' in prompt(a,2)
a._ensure_session(ROOT/'analysis/fixture-b/state.json')
assert not a._kept_functions
a._kept_functions={'helper':'def l3_step(s,a):\n return s'}
assert 'MODEL_VALIDATION_REQUEST' in prompt(a,1)
b=ToolAgent(model='verification-only',provider='lmstudio');b._ensure_session(ROOT/'analysis/fixture-c/state.json')
assert 'MODEL_VALIDATION_REQUEST' not in prompt(b,1)
report={'shipped_hook_active':True,'no_simulator_no_nudge':True,'once_per_level':True,'new_level_rearms':True,'new_game_rearms':True,'agents_isolated':True,'qualification':'Synthetic retained helper fixture on actual shipped ToolAgent;no LLM quality measurement.'}
(ROOT/'analysis/v3-validation-20261101/verification.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))
