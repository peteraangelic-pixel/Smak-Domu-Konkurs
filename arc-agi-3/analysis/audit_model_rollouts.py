"""Audit frozen models on recorded multi-step sequences; no fitting or actions.

This adapter uses the model-repair lab's encoded b/d/a state schema. It does
not generalize the fixed fixture model or turn this audit into an ARC agent.
"""
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import argparse
import copy
import hashlib
import json
import os
import repair_model_constants as codec


def input_key(row):
    return json.dumps([row['before'], row['action']], sort_keys=True)


def evaluate_episode(job):
    label, code, episode, eligible_starts, horizons = job
    namespace = {}
    exec(compile(code, '<frozen-rollout-model>', 'exec'), namespace)
    rows = episode['rows']
    out = []
    for horizon in horizons:
        exact = eligible = errors = changed_exact = changed = 0
        for start in range(len(rows) - horizon + 1):
            window = rows[start:start + horizon]
            if (episode['seed'], window[0]['index']) not in eligible_starts:
                continue
            # A sequence may never bridge an excluded/terminal transition.
            if any(window[i + 1]['index'] != window[i]['index'] + 1 or
                   window[i + 1]['before'] != window[i]['after']
                   for i in range(len(window) - 1)):
                continue
            eligible += 1
            initial = codec.state(window[0]['before'])
            actual = codec.canonical(codec.state(window[-1]['after']))
            did_change = actual != codec.canonical(initial)
            changed += int(did_change)
            predicted = copy.deepcopy(initial)
            try:
                for row in window:
                    next_state = namespace['model_step'](
                        copy.deepcopy(predicted), row['action'])
                    if next_state is not None:
                        predicted = next_state
                correct = codec.canonical(predicted) == actual
                exact += int(correct)
                changed_exact += int(correct and did_change)
            except Exception:
                errors += 1
        out.append(dict(model=label, seed=episode['seed'], horizon=horizon,
                        samples=eligible, exact=exact, errors=errors,
                        changed=changed, changed_exact=changed_exact))
    return out


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--lab', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
                 'RAYON_NUM_THREADS'):
        os.environ[name] = '1'
    args.out.mkdir(exist_ok=False)
    episodes_path = args.lab / 'contact-merge/final-episodes.json'
    episodes = json.loads(episodes_path.read_text())
    prior = json.loads((args.lab / 'composed/training.json').read_text())
    prior += json.loads((args.lab / 'holdout.json').read_text())
    for stage in ('point-motion', 'composed'):
        prior += [row for ep in json.loads(
            (args.lab / stage / 'final-episodes.json').read_text())
                  for row in ep['rows']]
    previous_inputs = set(map(input_key, prior))
    eligible_starts = set()
    for episode in episodes:
        for row in episode['rows']:
            key = input_key(row)
            if key not in previous_inputs:
                previous_inputs.add(key)
                eligible_starts.add((episode['seed'], row['index']))
    models = {stage: (args.lab / stage / 'selected-model.py').read_text()
              for stage in ('composed', 'contact-merge')}
    horizons = (1, 2, 4, 8)
    manifest = dict(workers=16, horizons=horizons,
                    unique_novel_start_inputs=len(eligible_starts),
                    model_sha256_lf={name: hashlib.sha256(code.encode()).hexdigest()
                                     for name, code in models.items()},
                    episodes_sha256=hashlib.sha256(episodes_path.read_bytes()).hexdigest(),
                    fitting=False, new_environment_actions=0,
                    qualification='Recorded-sequence prediction audit on one fixture; '
                                  'not a planner, new completions, or Kaggle score.')
    (args.out / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    jobs = [(name, code, ep, eligible_starts, horizons)
            for name, code in models.items() for ep in episodes]
    with ProcessPoolExecutor(max_workers=16) as pool:
        detail = [row for result in pool.map(evaluate_episode, jobs) for row in result]
    totals = []
    for name in models:
        for horizon in horizons:
            selected = [r for r in detail if r['model'] == name and r['horizon'] == horizon]
            total = {key: sum(r[key] for r in selected)
                     for key in ('samples', 'exact', 'errors', 'changed', 'changed_exact')}
            total.update(model=name, horizon=horizon)
            totals.append(total)
    (args.out / 'episode-results.json').write_text(json.dumps(detail, indent=2))
    (args.out / 'report.json').write_text(json.dumps(totals, indent=2))
    print(json.dumps(totals))
