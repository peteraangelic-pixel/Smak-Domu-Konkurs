"""Compare saved target-model runs and retained tool evidence, without forecasting."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
from analyze_prompt_snapshots import HEAD,analyze
from analyze_v137_smoke import summarize


def evidence(folder):
    games=[]
    for path in sorted((folder/'prompts').glob('*.log')):
        raw=path.read_text(encoding='utf8');heads=list(HEAD.finditer(raw))
        calls={};results={};requests=0
        for i,h in enumerate(heads):
            block=raw[h.end():heads[i+1].start() if i+1<len(heads) else len(raw)]
            kind=h.group(1)
            if kind=='ASSISTANT TOOL CALL: python':
                cid=re.search(r'^id: (call_\w+)',block,re.M)
                code=re.search(r'<parameter=code>\s*\n(.*?)</parameter>',block,re.S)
                if cid and code:calls[cid[1]]=code[1]
            elif kind.startswith('TOOL RESULT: call_'):
                results[kind.split(': ',1)[1]]=block
            elif kind in ('USER','USER PROMPT'):
                requests+=block.count('MODEL_VALIDATION_REQUEST')
        syntax=[]
        for cid,code in calls.items():
            try:tree=ast.parse(code)
            except SyntaxError:continue
            if any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='check_model' for n in ast.walk(tree)):
                syntax.append(cid)
        restored={cid:[int(n) for n in re.findall(r'OBSERVATION_CACHE restored=(\d+)',text)] for cid,text in results.items() if re.search(r'OBSERVATION_CACHE restored=\d+',text)}
        diagnostics=analyze(path)
        games.append({'snapshot':path.name,'snapshot_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                      'observed_unique_calls':len(calls),'validation_request_occurrences':requests,
                      'syntactic_check_model_call_ids':syntax,'cache_restore_tool_results':restored,
                      'observed_tool_errors':[{k:v for k,v in e.items() if k!='code'} for e in diagnostics['errors']]})
    return {'games':games,'scope':'Retained snapshots only, deduplicated by native call ID within a game. Syntactic check_model calls need not execute. Missing evidence does not establish whole-run absence.'}


def compare(candidate,controls):
    raw=json.loads((candidate/'benchmark.json').read_text(encoding='utf8'))
    def corpus(d):
        runs=d['game_runs'];ids=[g['game_id'] for g in runs]
        if len(ids)!=len(set(ids)):raise ValueError('Duplicate game ID in run')
        return {g['game_id']:(g['number_of_levels'],g['base_actions_per_level']) for g in runs}
    summary=summarize(candidate/'benchmark.json')
    left={r['game_id']:r for r in summary['rows']};comparisons=[]
    for folder in controls:
        other=json.loads((folder/'benchmark.json').read_text(encoding='utf8'))
        if corpus(raw)!=corpus(other):raise ValueError('Different corpus/level definitions: '+str(folder))
        baseline=summarize(folder/'benchmark.json');right={r['game_id']:r for r in baseline['rows']}
        rows=[{'game_id':gid,'candidate_levels':left[gid]['completed'],'control_levels':right[gid]['completed'],
               'level_delta':left[gid]['completed']-right[gid]['completed'],
               'candidate_score':left[gid]['score'],'control_score':right[gid]['score'],
               'candidate_tokens':left[gid]['final_generated_tokens'],'control_tokens':right[gid]['final_generated_tokens']}
              for gid in sorted(left)]
        comparisons.append({'control':str(folder),'control_summary':baseline,'rows':rows,
                            'new_zeros':[r['game_id'] for r in rows if r['candidate_levels']==0<r['control_levels']],
                            'wins':sum(r['level_delta']>0 for r in rows),'losses':sum(r['level_delta']<0 for r in rows),
                            'ties':sum(r['level_delta']==0 for r in rows)})
    return {'candidate_summary':summary,'candidate_benchmark_sha256':hashlib.sha256((candidate/'benchmark.json').read_bytes()).hexdigest(),
            'candidate_states':{g['game_id']:g['state'] for g in raw['game_runs']},
            'candidate_total_tokens':sum(g['final_generated_tokens'] for g in raw['game_runs']),
            'same_corpus_verified':True,'comparisons':comparisons,'activation':evidence(candidate),
            'limitations':['Public save-run; not a competition score or forecast.',
                           'Benchmark corpus checked here; model, code hash, and configured budgets must be checked against pinned notebook/RUN separately.',
                           'One result does not prove a policy improvement under control variation.']}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--control',type=Path,action='append',required=True);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();report=compare(args.candidate,args.control)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'levels':report['candidate_summary']['levels'],'score':report['candidate_summary']['score_mean'],
                      'comparisons':[{'control':c['control'],'wins':c['wins'],'losses':c['losses'],'ties':c['ties'],'new_zeros':c['new_zeros']} for c in report['comparisons']]}))
