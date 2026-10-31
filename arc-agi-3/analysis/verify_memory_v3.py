"""Exercise shipped memory hooks: real solved state, turn eviction and isolation.

No LLM quality claim; the state fixture was produced by verify_memory_hook.py
through actual arcengine actions, never packaged in the competition agent.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    p.add_argument('--state',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();sys.path.insert(0,str(a.source.resolve()))
    os.environ.update(ARC3_LEVEL_NOTES='1',ARC3_HISTORY_ASSISTANT_TURNS='1',ARC3_HISTORY_TURN_DRAIN='0')
    from inference.agent import tool_agent as ta
    agent=ta.ToolAgent(model='arc-lab-27b',provider='lmstudio')
    agent._ensure_session(a.state)
    agent._last_step_summary={'level':2}
    ta._slm_before_turn(agent,a.state)
    assert len(agent._slm_levels)==1
    messages=[{'role':'system','content':agent._system_prompt}]
    for i in range(6):
        messages += [{'role':'user','content':f'observation {i}'},{'role':'assistant','content':f'hypothesis {i}'}]
    agent._context_budget_tokens=1000000
    direct=agent._trim_messages_for_context(messages,tools=None)
    assert len(direct)==len(messages),'Token trimmer must not be responsible for this eviction'
    before=agent._system_prompt
    kept=agent._persistent_history_messages(messages,tools=None)
    assert len(kept)<len(messages)-1
    assert ta._SLM_HEADER in agent._system_prompt
    assert agent._system_prompt!=before
    assert agent._slm_v3_evictions>0
    pinned=agent._system_prompt
    agent._persistent_history_messages([{'role':'system','content':pinned},*kept],tools=None)
    assert agent._system_prompt==pinned,'Stable history must not rewrite cached memory'
    second=ta.ToolAgent(model='arc-lab-27b',provider='lmstudio')
    second._ensure_session(a.state)
    assert second._slm_levels==[]
    agent._ensure_session(a.state.with_name('different-game.json'))
    assert agent._slm_levels==[] and agent._slm_block_text==''
    assert ta._SLM_HEADER not in agent._system_prompt
    assert agent._last_step_summary is None
    report={'actual_level_state_recorded':True,'turn_cap_eviction_without_token_trim':True,
            'memory_pinned_after_turn_eviction':True,'stable_history_does_not_rewrite':True,
            'separate_agent_isolated':True,'different_state_path_clears_memory':True,
            'source_sha256':hashlib.sha256(Path(ta.__file__).read_bytes()).hexdigest(),
            'qualification':'Real shipped ToolAgent hooks, scripted solved-state fixture, no model-quality measurement.'}
    a.out.write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
