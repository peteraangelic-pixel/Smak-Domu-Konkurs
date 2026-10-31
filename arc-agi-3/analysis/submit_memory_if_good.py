"""User-authorized, one-attempt conditional submission, not before02:10 Warsaw.

Fixed notebook/version and explicit gates; never pushes a new kernel.
"""
import csv
from datetime import datetime,timezone
import hashlib
import io
import json
import math
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'analysis/memory-v3-scheduled-submit-20261101'
SLUG='petersharps/arc3-codex-memory-v3-lab'
TAG='Codex memory-v3 v1 scheduled20261101'
NOT_BEFORE=datetime(2026,11,1,1,10,tzinfo=timezone.utc)


def gate(control,candidate):
    a={r['game_id']:r for r in control['game_runs']}
    b={r['game_id']:r for r in candidate['game_runs']}
    if len(a)!=10 or len(b)!=10 or a.keys()!=b.keys():return False,{'reason':'roster_mismatch'}
    if any(a[g]['number_of_levels']!=b[g]['number_of_levels'] or
           a[g]['base_actions_per_level']!=b[g]['base_actions_per_level'] for g in a):
        return False,{'reason':'different_environment_metadata'}
    scores=[float(r['final_score']) for r in b.values()]
    levels=sum(int(r['levels_completed']) for r in b.values())
    mean=sum(scores)/10
    control_mean=sum(float(r['final_score']) for r in a.values())/10
    checks={'all_scores_finite':all(math.isfinite(x) and 0<=x<=100 for x in scores),
            'more_than33_completions':levels>33,'score_above_control':mean>control_mean,
            'no_new_zero_games':all(int(b[g]['levels_completed'])>0 for g in a),
            'no_crashed_games':all(str(r['state']).lower() in ('gave_up','win','won','completed','finished') for r in b.values())}
    return all(checks.values()),{'checks':checks,'mean_score':mean,'control_mean':control_mean,'levels':levels}


def main():
    OUT.mkdir(exist_ok=True,parents=True)
    config=json.loads((ROOT/'duck-lab-candidates/memory-v3/SUBMISSION-CANDIDATE.json').read_text(encoding='utf8'))
    assert config['kernel']==SLUG
    version=int(config['version']);assert version>=1
    source=(ROOT/config['source']).resolve()
    assert (ROOT/'duck-lab-candidates').resolve() in source.parents
    assert len(config['sha256'])==64
    version_ref=SLUG+'/'+str(version)
    decision={'notebook':SLUG,'version':version,'sha256':config['sha256'],'utc':datetime.now(timezone.utc).isoformat(),'submitted':False}
    def save(): (OUT/'decision.json').write_text(json.dumps(decision,indent=2),encoding='utf8')
    def command(label,args):
        p=subprocess.run(['kaggle',*args],capture_output=True,text=True,timeout=180)
        raw=p.stdout+'\n'+p.stderr
        secret=os.environ.get('KAGGLE_API_TOKEN','')
        if secret:raw=raw.replace(secret,'[REDACTED]')
        (OUT/(label+'.txt')).write_text(raw,encoding='utf8')
        if p.returncode:raise RuntimeError(label+' failed; no fallback submission')
        return p.stdout
    try:
        if datetime.now(timezone.utc)<NOT_BEFORE:
            decision['reason']='too_early';save();return
        # Do not spend a slot on a later day after a stale scheduled wakeup.
        if datetime.now(timezone.utc).date()!=NOT_BEFORE.date():
            decision['reason']='outside_authorized_date';save();return
        if (OUT/'attempted.json').exists():
            decision['reason']='previous_attempt_requires_review';save();return
        status=command('kernel-status',['kernels','status',version_ref])
        if 'KernelWorkerStatus.COMPLETE' not in status:
            decision['reason']='kernel_not_complete';save();return
        pulled=OUT/'pulled'
        command('kernel-pull',['kernels','pull',version_ref,'-p',str(pulled),'-m'])
        assert hashlib.sha256(source.read_bytes()).hexdigest()==config['sha256']
        actual=next(pulled.glob('*.ipynb'))
        def code(p):return [''.join(c['source']).rstrip('\n') for c in json.loads(p.read_text(encoding='utf8'))['cells'] if c['cell_type']=='code']
        if code(source)!=code(actual):
            decision['reason']='published_code_mismatch';save();return
        output=OUT/'kernel-output'
        command('kernel-output',['kernels','output',version_ref,'-p',str(output),
                                 '--file-pattern',r'(benchmark\.json|.*\.log|submission\.parquet)$'])
        control=json.loads((ROOT/'analysis/v3-target-result-20261031/v3-output/benchmark.json').read_text(encoding='utf8'))
        candidate=json.loads(next(output.rglob('benchmark.json')).read_text(encoding='utf8'))
        ok,details=gate(control,candidate);decision.update(details)
        log=output/'arc3-codex-memory-v3-lab.log'
        text=log.read_text(encoding='utf8')
        try:text=''.join(row.get('data','') for row in json.loads(text) if isinstance(row,dict))
        except (ValueError,TypeError):pass
        import re
        decision['smoke_ok']=bool(re.search(r'^ARC3_SMOKE_OK\s*$',text,re.M))
        decision['memory_captured']=bool(re.search(r'^SLM_V3_CAPTURE levels=\d+ current=\d+\s*$',text,re.M))
        decision['memory_pinned']=bool(re.search(r'^SOLVED_LEVEL_MEMORY pinned: \d+ level\(s\), \d+ chars\s*$',text,re.M))
        decision['memory_errors']=bool(re.search(r'^(SLM_V3_REFRESH_ERROR |SOLVED_LEVEL_MEMORY error \()',text,re.M))
        ok=ok and decision['smoke_ok'] and decision['memory_captured'] and decision['memory_pinned'] and not decision['memory_errors']
        if not ok:
            decision['reason']='quality_or_activation_gate_failed';save();return
        if not list(output.rglob('submission.parquet')):
            decision['reason']='missing_submission_output';save();return
        submissions=command('submissions-before',['competitions','submissions','arc-prize-2026-arc-agi-3','--csv'])
        rows=list(csv.DictReader(io.StringIO(submissions)))
        if not rows or 'ref' not in rows[0]:raise RuntimeError('Unrecognized submission inventory; no submission')
        if any(('memory-v3' in str(r) and 'scheduled20261101' in str(r)) or
               'arc3-codex-memory-v3-lab' in str(r) for r in rows):
            decision['reason']='already_submitted';save();return
        # Durable attempt marker is written BEFORE the irreversible API call.
        (OUT/'attempted.json').write_text(json.dumps({'tag':TAG,'utc':datetime.now(timezone.utc).isoformat()}),encoding='utf8')
        response=command('competition-submit',['competitions','submit','arc-prize-2026-arc-agi-3',
                                              '-k',SLUG,'-v',str(version),'-f','submission.parquet','-m',TAG.replace(' v1 ',f' v{version} ')])
        decision.update(submitted=True,reason='gates_passed_submission_accepted',response=response)
        save()
    except Exception as exc:
        decision['reason']='error_no_automatic_retry';decision['error']=str(exc);save();raise


if __name__=='__main__':main()
