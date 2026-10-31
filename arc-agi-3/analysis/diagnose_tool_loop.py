"""Count unique native tool calls/results, rather than duplicated chat history.

The transcript includes old messages again after each analyzer turn. Counting
tracebacks or feedback strings there overcounts. Use native tool-call IDs.
"""
import argparse
import ast
from collections import Counter
import json
from pathlib import Path


def diagnose(request_rows, api_rows=()):
    calls, results = {}, {}
    for row in request_rows:
        for msg in row.get('messages', []):
            for call in msg.get('tool_calls', []):
                calls[call['id']] = call
            if msg.get('role') == 'tool' and msg.get('tool_call_id'):
                results[msg['tool_call_id']] = msg.get('content', '')
    for row in api_rows:
        for choice in row.get('response', {}).get('choices', []):
            for call in choice.get('message', {}).get('tool_calls', []):
                calls[call['id']] = call
    errors, error_kinds, action_calls, feedback = [], Counter(), [], []
    for call_id, call in calls.items():
        if call.get('function', {}).get('name') != 'python':
            continue
        try:
            args=json.loads(call['function']['arguments'])
            tree=ast.parse(args['code'])
        except (ValueError, KeyError, SyntaxError, TypeError):
            continue
        if any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id=='action'
               for n in ast.walk(tree)):
            action_calls.append(call_id)
    for call_id, content in results.items():
        if not isinstance(content, str):
            continue
        if 'EXPERIMENT FEEDBACK:' in content:
            feedback.append(call_id)
        try:
            obj, _ = json.JSONDecoder().raw_decode(content)
        except (ValueError, TypeError):
            continue
        error=obj.get('error')
        if error or obj.get('returncode', 0):
            error=str(error or obj.get('stderr', 'nonzero returncode'))
            last=error.strip().splitlines()[-1]
            kind=last.split(':', 1)[0]
            error_kinds[kind]+=1
            errors.append({'tool_call_id':call_id,'error':last})
    return {'unique_tool_calls':len(calls),'unique_observed_tool_results':len(results),
            'calls_without_observed_result':sorted(set(calls)-set(results)),
            'tool_errors':len(errors),'tool_error_kinds':dict(error_kinds),'errors':errors,
            'calls_containing_action_code':len(action_calls),'unique_feedback_results':len(feedback),
            'qualification':'Action code is intent, not proof of executed engine actions. Missing tool outputs are unobserved, not assumed failures. API errors and tool errors are separate.'}


def read_jsonl(path):
    if not path.exists():return []
    return [json.loads(line) for line in path.read_text(encoding='utf8').splitlines() if line.strip()]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('run',type=Path)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    report=diagnose(read_jsonl(args.run/'requests.jsonl'),read_jsonl(args.run/'api.jsonl'))
    result=args.run/'result.json'
    report['finished']=result.exists()
    if result.exists():
        r=json.loads(result.read_text(encoding='utf8'))
        report['engine_actions']=r['actions']
        report['levels_completed']=r['levels_completed']
    args.out.write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
