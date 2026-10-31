import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from diagnose_tool_loop import diagnose


def test_repeated_history_counts_native_id_once_and_error_without_returncode():
    call={'id':'call1','function':{'name':'python','arguments':json.dumps({'code':'action(["LEFT"])'})}}
    messages=[{'role':'assistant','tool_calls':[call]},
              {'role':'tool','tool_call_id':'call1','content':json.dumps({'tool':'python','error':"KeyError: 'steps'"})}]
    r=diagnose([{'messages':messages},{'messages':messages}])
    assert r['unique_tool_calls']==r['unique_observed_tool_results']==r['tool_errors']==1
    assert r['calls_containing_action_code']==1
    assert r['tool_error_kinds']=={'KeyError':1}


def test_feedback_after_json_and_action_text_in_comment_are_not_engine_actions():
    call={'id':'call1','function':{'name':'python','arguments':json.dumps({'code':'# action(["LEFT"])\nprint("NameError: example")'})}}
    r=diagnose([{'messages':[{'role':'assistant','tool_calls':[call]},
        {'role':'tool','tool_call_id':'call1','content':json.dumps({'tool':'python','stdout':'NameError: example'})+'\nEXPERIMENT FEEDBACK: probe'}]}])
    assert r['tool_errors']==r['calls_containing_action_code']==0
    assert r['unique_feedback_results']==1
