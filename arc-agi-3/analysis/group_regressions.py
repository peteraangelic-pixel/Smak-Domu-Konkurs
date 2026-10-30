"""Paired full-loop regression gates, including groups hidden by the mean."""
import argparse
import json
from pathlib import Path


def compare(control, candidate, score_field='rhae_score_pct'):
    def keyed(rows):
        result = {}
        for row in rows:
            key = row['game'], row['seed']
            if key in result:
                raise ValueError(f'Duplicate trial {key}')
            result[key] = row
        return result
    a, b = keyed(control), keyed(candidate)
    if set(a) != set(b) or not a:
        raise ValueError('Require the same nonempty game/seed corpus')
    paired = []
    for key, baseline in a.items():
        trial = b[key]
        for field in ('model', 'budget', 'game_sha256', 'families'):
            if baseline[field] != trial[field]:
                raise ValueError(f'{key}: mismatch in {field}')
        if baseline.get('image_scale') != trial.get('image_scale'):
            raise ValueError(f'{key}: mismatch in image scale')
        paired.append({'game': key[0], 'seed': key[1], 'families': baseline['families'],
                       'level_delta': trial['levels_completed']-baseline['levels_completed'],
                       'score_delta': trial[score_field]-baseline[score_field],
                       'error': bool(trial.get('error') or trial.get('api_errors') or baseline.get('error') or baseline.get('api_errors')
                                     or trial.get('valid_model_run') is False or baseline.get('valid_model_run') is False
                                     or trial.get('time_limit_binding') or baseline.get('time_limit_binding'))})
    groups = {}
    for group in sorted({g for r in paired for g in r['families']}):
        rows = [r for r in paired if group in r['families']]
        groups[group] = {'trials': len(rows), 'games': len({r['game'] for r in rows}),
                         'level_delta': sum(r['level_delta'] for r in rows),
                         'mean_score_delta': sum(r['score_delta'] for r in rows)/len(rows),
                         'regressed_games': sorted({r['game'] for r in rows if r['level_delta']<0 or r['score_delta'] < -1e-9})}
    return {'metric':score_field, 'pairs': paired, 'groups': groups,
            'no_level_regressions': all(r['level_delta']>=0 for r in paired),
            'no_group_score_regressions': all(g['mean_score_delta'] >= -1e-9 for g in groups.values()),
            'error_free': not any(r['error'] for r in paired),
            'qualification': 'Descriptive paired public-game gate; no significance or hidden-score claim.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('run', type=Path)
    p.add_argument('--control', default='control')
    p.add_argument('--candidate', required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    rows = [json.loads(path.read_text()) for path in args.run.glob('*/result.json')]
    report = compare([r for r in rows if r['variant']==args.control],
                     [r for r in rows if r['variant']==args.candidate])
    args.out.write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps(report, indent=2))
