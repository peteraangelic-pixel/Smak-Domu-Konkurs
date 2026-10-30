"""Bounded evolution of offline search settings on pinned public ARC games.

This evaluates the engine search, with no language model. Completion coverage
is an objective for this lab and is not a prediction of the Kaggle score.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import random
import re
import time
import subprocess
import sys
import site

from sweep2 import Args, play_game
from native_kernels import native_kernels

GENES = {
    'bfs_branch': [0, 4, 8],
    'beam': [32, 120],
    'max_clicks': [8, 16, 40],
    'click_candidates': [12, 28],
    'min_moves': [1, 3],
    'calib_step': [4, 8],
}
CONTROL = dict(bfs_branch=8, beam=120, max_clicks=40,
               click_candidates=28, min_moves=3, calib_step=4)


def identity(genome):
    return hashlib.sha256(json.dumps(genome, sort_keys=True).encode()).hexdigest()[:12]


def breed(parents, population, rng):
    children = {identity(CONTROL): dict(CONTROL)}
    for parent in parents:
        children[identity(parent)] = dict(parent)
    while len(children) < population:
        a, b = rng.choice(parents), rng.choice(parents)
        child = {name: rng.choice((a[name], b[name])) for name in GENES}
        for name, values in GENES.items():
            if rng.random() < 0.35:
                child[name] = rng.choice(values)
        children[identity(child)] = child
    return list(children.values())[:population]


def worker(job):
    genome, path, cls, budget = job
    args = Args(**dict(
        backend='rust', node_cap=budget['node_cap'], sec_cap=budget['sec_cap'],
        max_levels=budget['max_levels'], max_depth=80, frontier_cap=256,
        calib_time=0.75, **genome))
    result = play_game((path, cls, args))
    result['genome'] = identity(genome)
    result['weighted_completion'] = 0.0
    solved = sum(level['solved'] for level in result.get('levels', []))
    total = result.get('win_levels', 0)
    if not result.get('error') and total:
        result['weighted_completion'] = 100 * solved * (solved + 1) / (total * (total + 1))
    return result


def isolated_worker(job):
    genome, path, cls, budget = job
    try:
        # Windows venv python.exe may launch another interpreter process.
        # Run that interpreter directly so the timeout owns the game process.
        environment = os.environ.copy()
        environment['PYTHONPATH'] = os.pathsep.join(site.getsitepackages())
        process = subprocess.run(
            [sys._base_executable, str(Path(__file__).resolve()), '--worker'],
            input=json.dumps(job), capture_output=True, text=True,
            env=environment,
            timeout=(budget['sec_cap'] + 10) * budget['max_levels'])
        if process.returncode:
            raise RuntimeError(process.stderr[-1000:])
        return json.loads(process.stdout.strip().splitlines()[-1])
    except (subprocess.TimeoutExpired, RuntimeError, ValueError) as exc:
        return {'game': Path(path).stem, 'genome': identity(genome),
                'error': f'{type(exc).__name__}: {str(exc)[:1000]}',
                'levels': [], 'weighted_completion': 0.0}


def summary(genome, games, cache):
    rows = [cache[identity(genome), path] for path, _ in games]
    return {
        'genome': genome, 'id': identity(genome), 'games': len(rows),
        'errors': sum(bool(row.get('error')) for row in rows),
        'mean_weighted_completion': sum(row['weighted_completion'] for row in rows) / len(rows),
        'solved_levels': sum(level['solved'] for row in rows for level in row.get('levels', [])),
        'nodes': sum(level['nodes'] for row in rows for level in row.get('levels', [])),
    }


def rank(row):
    return (-row['errors'], row['mean_weighted_completion'], row['solved_levels'], -row['nodes'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--population', type=int, default=6)
    parser.add_argument('--generations', type=int, default=2)
    parser.add_argument('--screen-games', type=int, default=4)
    parser.add_argument('--node-cap', type=int, default=300)
    parser.add_argument('--sec-cap', type=float, default=5)
    parser.add_argument('--max-levels', type=int, default=1)
    parser.add_argument('--seed', type=int, default=20261030)
    parser.add_argument('--reuse', type=Path, help='Reuse completed matching trials from an earlier run')
    args = parser.parse_args()
    if not 4 <= args.population <= 144 or args.generations < 1 or not 1 <= args.screen_games <= 17:
        parser.error('Population 4..144, generations >=1 and screen-games 1..17 required')
    if args.node_cap < 1 or args.sec_cap < 1 or not 1 <= args.max_levels <= 6:
        parser.error('Positive budgets and max-levels 1..6 required')
    if args.out.exists():
        parser.error('Choose a new output directory to preserve previous evidence')
    native_kernels()
    root = Path(__file__).resolve().parents[1]
    files = sorted((root / 'games/environment_files').rglob('*.py'))
    games = []
    for path in files:
        match = re.search(r'^class (\w+)\(ARCBaseGame\)', path.read_text(encoding='utf8'), re.M)
        if match:
            games.append((str(path.resolve()), match[1]))
    if len(games) != 25:
        raise ValueError('Expected the pinned 25-game corpus')
    # Stable game-family split. The breeding seed never creates new environments.
    games.sort(key=lambda pair: hashlib.sha256(Path(pair[0]).stem.encode()).hexdigest())
    train, holdout = games[:17], games[17:]
    args.out.mkdir(parents=True)
    manifest = {
        'seed': args.seed, 'workers': 16,
        'budget': {'node_cap': args.node_cap, 'sec_cap': args.sec_cap, 'max_levels': args.max_levels},
        'train': [Path(path).stem for path, _ in train],
        'holdout': [Path(path).stem for path, _ in holdout],
        'game_sha256': {Path(path).stem: hashlib.sha256(Path(path).read_bytes()).hexdigest() for path, _ in games},
        'implementation_sha256': {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                                  for name in ('sweep2.py', 'native_kernels.py', 'evolve_search.py')},
        'objective': 'weighted completion, then completed levels, then fewer nodes',
        'qualification': 'Exploratory public holdout. All public games were inspected earlier. No hidden-game claim.',
    }
    (args.out / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf8')
    rng = random.Random(args.seed)
    initial = [dict(CONTROL)]
    initial.extend({key: rng.choice(values) for key, values in GENES.items()} for _ in range(2))
    population = breed(initial, args.population, rng)
    cache = {}
    if args.reuse:
        previous = json.loads((args.reuse / 'manifest.json').read_text(encoding='utf8'))
        for key in ('budget', 'game_sha256'):
            if previous[key] != manifest[key]:
                raise ValueError(f'Reuse mismatch: {key}')
        for name in ('sweep2.py', 'native_kernels.py'):
            if previous['implementation_sha256'][name] != manifest['implementation_sha256'][name]:
                raise ValueError(f'Reuse implementation mismatch: {name}')
        by_name = {Path(path).stem: path for path, _ in games}
        for line in (args.reuse / 'trials.jsonl').read_text(encoding='utf8').splitlines():
            row = json.loads(line)
            cache[row['genome'], by_name[row['game']]] = row
        manifest['reused_directory'] = str(args.reuse)
        manifest['reused_trials'] = len(cache)
        (args.out / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf8')
    start = time.monotonic()
    with (args.out / 'trials.jsonl').open('w', encoding='utf8') as log, ThreadPoolExecutor(max_workers=16) as pool:
        for row in cache.values():
            log.write(json.dumps(row) + '\n')
        log.flush()
        def evaluate(genomes, subset, phase):
            tasks = {}
            for genome in genomes:
                for path, cls in subset:
                    key = identity(genome), path
                    if key not in cache and key not in tasks.values():
                        future = pool.submit(isolated_worker, (genome, path, cls, manifest['budget']))
                        tasks[future] = key
            print(f'{phase}: {len(tasks)} new game/configuration trials, 16 workers', flush=True)
            for index, future in enumerate(as_completed(tasks), 1):
                result = future.result()
                cache[tasks[future]] = result
                log.write(json.dumps(result) + '\n')
                log.flush()
                if index % 16 == 0 or index == len(tasks):
                    print(f'{phase}: {index}/{len(tasks)} completed', flush=True)
            return sorted([summary(g, subset, cache) for g in genomes], key=rank, reverse=True)

        history = []
        for generation in range(args.generations):
            ranked = evaluate(population, train[:args.screen_games], f'generation {generation}')
            history.append(ranked)
            print('screen best', ranked[0], flush=True)
            population = breed([r['genome'] for r in ranked[:2]], args.population, rng)
        finalists = {r['id']: r['genome'] for r in history[-1][:2]}
        finalists[identity(CONTROL)] = dict(CONTROL)
        ranking = evaluate(list(finalists.values()), train, 'full training confirmation')
        baseline = next(row for row in ranking if row['id'] == identity(CONTROL))
        winner = ranking[0]
        train_gain = (winner['errors'] == 0 and
                      winner['mean_weighted_completion'] > baseline['mean_weighted_completion'])
        if not train_gain:
            winner = baseline
        selected = {winner['id']: winner['genome'], identity(CONTROL): CONTROL}
        held = evaluate(list(selected.values()), holdout, 'single holdout evaluation')
    report = {'training_history': history, 'training_finalists': ranking,
              'selected': winner, 'strict_train_gain': train_gain,
              'holdout': held, 'trials': len(cache), 'seconds': time.monotonic() - start,
              'promotion': 'pending independent full-agent evaluation'}
    (args.out / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps({key: report[key] for key in ('strict_train_gain', 'trials', 'seconds', 'holdout')}), flush=True)


if __name__ == '__main__':
    for variable in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'RAYON_NUM_THREADS'):
        os.environ[variable] = '1'
    if sys.argv[1:] == ['--worker']:
        print(json.dumps(worker(json.load(sys.stdin))))
    else:
        main()
