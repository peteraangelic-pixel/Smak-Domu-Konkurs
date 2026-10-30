"""Replay an actual solved public level, then exercise Duck's real trim hook.

The scripted solve is test data, never an embedded game strategy in the agent.
Rule text below tests capture only; it is not a claim that an LLM learned it.
"""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--mode',choices=['original','compatible','packaged'],required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    os.environ.update(ARC3_LEVEL_NOTES='1',LOCAL_ANALYZER_MODEL_ID='arc-lab-27b',LOCAL_ANALYZER_PROVIDER='lmstudio')
    sys.path.insert(0,str(args.source.resolve()))
    from inference.agent.tool_agent import ToolAgent
    from inference.agent.runtime_state import Frame,HistoryEntry,write_runtime_state
    from sweep2 import load_game,frame_of
    from arcengine import ActionInput,GameAction
    from lalalia_compat import install
    if args.mode=='packaged':
        from inference.agent import tool_agent
        ns=vars(tool_agent)
    else:
        ns=install(compatible=args.mode=='compatible')
    rows=[json.loads(x) for x in (ROOT/'analysis/sweep-rust-ffi.jsonl').read_text().splitlines()]
    solve=next(r for r in rows if r['game']=='ft09')['levels'][0]['seq']
    path=next((ROOT/'games/environment_files').rglob('ft09.py'))
    engine=load_game(str(path),'Ft09')
    fd=engine.perform_action(ActionInput(id=GameAction.RESET))
    def frame(step):
        return Frame(grid=tuple(tuple(map(int,row)) for row in frame_of(fd)),step=step,level=fd.levels_completed+1)
    history=[HistoryEntry(action='',frame=frame(0))]
    for i,act in enumerate(solve):
        fd=engine.perform_action(ActionInput(id=GameAction.from_id(act['a']),data={k:v for k,v in act.items() if k!='a'}))
        label=f"MOUSE(row={act['y']}, col={act['x']})" if act['a']==6 else GameAction.from_id(act['a']).name
        history.append(HistoryEntry(action=label,frame=frame(i+1)))
    assert fd.levels_completed==1
    state=args.out/'state.json'
    write_runtime_state(state,current_frame=history[-1].frame,history=history)
    agent=ToolAgent(model='arc-lab-27b',provider='lmstudio')
    agent._ensure_session(state)
    agent._last_step_summary={'level':2}
    original_system=agent._system_prompt
    ns['_slm_before_turn'](agent,state)
    no_early_rewrite=agent._system_prompt==original_system
    prompt=agent._build_user_prompt(len(solve),current_frame=history[-1].frame,history_entries=history,valid_actions=['MOUSE'])
    asked='Rule for level 1:' in prompt
    agent._history_messages.append({'role':'assistant','content':'Rule for level 1: TEST RULE ONLY; use observed control effects and recheck the next board.'})
    ns['_slm_before_turn'](agent,state)
    messages=[{'role':'system','content':agent._system_prompt},{'role':'user','content':'old '*30000},
              {'role':'assistant','content':'old response'}, {'role':'user','content':'new board'}]
    agent._context_budget_tokens=1000000
    kept=agent._trim_messages_for_context(messages,tools=None)
    no_trim_unchanged=kept[0]['content']==original_system
    agent._context_budget_tokens=6000
    trimmed=agent._trim_messages_for_context(messages,tools=None)
    present=ns['_SLM_HEADER'] in trimmed[0]['content']
    prefix_preserved=trimmed[0]['content'].startswith(agent._arc3_base_system_prompt)
    # A second trim used to lose an already-cached block even with a naive fix.
    again=agent._trim_messages_for_context([{**messages[0],'content':agent._system_prompt},*messages[1:]],tools=None)
    second_present=ns['_SLM_HEADER'] in again[0]['content']
    record={'mode':args.mode,'real_level_completed':fd.levels_completed,'winning_actions':len(solve),
            'recorded_actions':agent._slm_levels[0]['n_actions'],'rule_requested':asked,
            'no_early_system_rewrite':no_early_rewrite,'no_trim_system_unchanged':no_trim_unchanged,
            'history_was_trimmed':len(trimmed)<len(messages),'memory_in_actual_request':present,
            'memory_survives_second_trim':second_present,'base_prefix_preserved':prefix_preserved,
            'qualification':'Actual engine level and real Duck trim hooks; scripted rule text; no LLM quality claim.'}
    (args.out/'result.json').write_text(json.dumps(record,indent=2),encoding='utf8')
    print(json.dumps(record),flush=True)
    if args.mode in ('compatible','packaged'):
        assert all((asked,no_early_rewrite,no_trim_unchanged,present,second_present,prefix_preserved))


if __name__=='__main__':main()
