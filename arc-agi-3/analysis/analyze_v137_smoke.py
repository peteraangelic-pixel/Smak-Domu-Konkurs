"""Read the public smoke traces; never label them competition-rerun logs."""
import argparse
import json
from pathlib import Path
import statistics


def summarize(path):
    d=json.loads(path.read_text(encoding='utf8'))
    rows=[]
    for g in d['game_runs']:
        n=g['levels_completed'];ac=g['actions_per_level']
        rows.append({'game_id':g['game_id'],'completed':n,'actions':sum(ac),
                     'closed_actions':sum(ac[:n]),'unfinished_actions':sum(ac[n:]),
                     'actions_per_level':ac,'score':g['final_score'],
                     'wall_seconds':g['final_wallclock_seconds'],
                     'first_action_s':g['history'][0]['wallclock_seconds'] if g['history'] else None,
                     'final_generated_tokens':g['final_generated_tokens']})
    total=sum(r['actions'] for r in rows);closed=sum(r['closed_actions'] for r in rows)
    completed=sum(r['completed'] for r in rows)
    return {'source':str(path),'scope':'PUBLIC_SAVE_RUN_NOT_SCORED_RERUN',
            'games':len(rows),'levels':completed,'score_mean':statistics.mean(r['score'] for r in rows),
            'actions':total,'closed_actions':closed,'unfinished_actions':total-closed,
            'unfinished_action_share':(total-closed)/total,
            'closed_actions_per_completion':closed/completed,
            'all_actions_per_completion':total/completed,'rows':rows}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--results',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    records={label:summarize(next(a.results.glob(label+'-*/output-pick/benchmark.json'))) for label in ('r085','r121')}
    left={r['game_id'] for r in records['r085']['rows']};right={r['game_id'] for r in records['r121']['rows']}
    assert left==right,'Different roster'
    output={'same_game_ids':True,'runs':records,'limitations':[
        'Historical non-randomized traces; multiple patches and dates differ.',
        'Completed levels select different populations; lower closed cost does not prove improved efficiency.',
        'A ratio using all actions conflates finished and unfinished levels.',
        'final_generated_tokens=0 is present in these exports; do not treat it as zero inference.',
        'These files cannot prove the cause of scored submission57811453.'
    ]}
    a.out.parent.mkdir(exist_ok=True,parents=True);a.out.write_text(json.dumps(output,indent=2),encoding='utf8')
    print(json.dumps({k:{x:y for x,y in v.items() if x!='rows'} for k,v in records.items()},indent=2))
