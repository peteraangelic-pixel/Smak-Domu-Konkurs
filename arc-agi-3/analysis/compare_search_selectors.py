"""Equal-trial-budget, frozen-warm-start comparison of surrogate vs evolution.

This tests the NEXT batch selector, not a full adaptive optimization campaign.
All selectors receive the same historical training evidence. Evaluation jobs
are interleaved and shared across arms when identical. Public validation is
consulted only after each training winner is frozen. Neither metric predicts
hidden Kaggle score. Repeated seeds share environments and are not independent
replications of game generalization.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import itertools
import json
import os
from pathlib import Path
import random
import re
import time

from evolve_search import CONTROL, GENES, breed, identity, isolated_worker, rank, summary
from native_kernels import native_kernels
from propose_search import recommend


def make_plans(run, seeds, count):
    report = json.loads((run / 'report.json').read_text())
    known = {r['id']: r['genome'] for generation in report['training_history'] for r in generation}
    known.update({r['id']: r['genome'] for r in report['training_finalists']})
    parents = [r['genome'] for r in sorted(report['training_finalists'], key=rank, reverse=True)[:2]]
    incumbent = parents[0]
    options = [dict(zip(GENES, values)) for values in itertools.product(*GENES.values())]
    novel = {identity(g): g for g in options if identity(g) not in known}
    if count > len(novel):
        raise ValueError('Not enough unseen genotypes for the trial budget')
    plans = []
    for seed in seeds:
        rng = random.Random(seed)
        # Same crossover/mutation operator as evolve_search. Historical parents
        # are free warm-start evidence, not charged again as new trial slots.
        children = {}
        for _ in range(1000):
            for genome in breed(parents, max(4, count + len(parents) + 1), rng):
                gid = identity(genome)
                if gid in novel:
                    children[gid] = genome
                if len(children) == count:
                    break
            if len(children) == count:
                break
        if len(children) != count:
            raise RuntimeError('Evolution could not fill novel trial slots')
        guided = recommend(run, seed=seed, count=count)['recommendations']
        plans.append({'seed': seed, 'arms': {
            'surrogate': [r['genome'] for r in guided],
            'evolution': list(children.values()),
        }})
    return plans, incumbent


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('run', type=Path)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--seeds', default='20261031,20261032,20261033')
    p.add_argument('--count', type=int, default=8)
    args = p.parse_args()
    if args.out.exists():
        p.error('Use a fresh output directory')
    previous = json.loads((args.run / 'manifest.json').read_text())
    root = Path(__file__).resolve().parents[1]
    game_map = {}
    for path in (root / 'games/environment_files').rglob('*.py'):
        match = re.search(r'^class (\w+)\(ARCBaseGame\)', path.read_text(encoding='utf8'), re.M)
        if match:
            game_map[path.stem] = (str(path.resolve()), match[1])
    for name, digest in previous['game_sha256'].items():
        if hashlib.sha256(Path(game_map[name][0]).read_bytes()).hexdigest() != digest:
            raise ValueError(f'Corpus changed: {name}')
    for name in ('sweep2.py', 'native_kernels.py'):
        if hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() != previous['implementation_sha256'][name]:
            raise ValueError(f'Worker changed: {name}')
    native_kernels()
    plans, incumbent = make_plans(args.run, [int(s) for s in args.seeds.split(',')], args.count)
    train = [game_map[name] for name in previous['train']]
    held = [game_map[name] for name in previous['holdout']]
    args.out.mkdir(parents=True)
    manifest = dict(previous, source_run=str(args.run.resolve()), plans=plans,
                    comparison='Frozen warm start; equal number of new genomes x 17 training games per arm',
                    repeated_seed_limit='Same public families and shared trials; descriptive comparison only')
    manifest['implementation_sha256'] = dict(previous['implementation_sha256'])
    for name in ('compare_search_selectors.py', 'propose_search.py'):
        manifest['implementation_sha256'][name] = hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
    (args.out / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf8')
    cache = {}
    start = time.monotonic()
    with ThreadPoolExecutor(max_workers=16) as pool, (args.out / 'trials.jsonl').open('w', encoding='utf8') as log:
        def evaluate(genomes, games, phase):
            jobs = {(identity(g), path): (g, path, cls, previous['budget'])
                    for g in genomes for path, cls in games if (identity(g), path) not in cache}
            # Interleave configurations to avoid giving the first arm a quieter CPU.
            keys = sorted(jobs)
            random.Random(731).shuffle(keys)
            futures = {pool.submit(isolated_worker, jobs[key]): key for key in keys}
            print(f'{phase}: {len(futures)} new jobs; 16 processes; Rust FFI', flush=True)
            for index, future in enumerate(as_completed(futures), 1):
                row = future.result()
                cache[futures[future]] = row
                log.write(json.dumps(row) + '\n')
                log.flush()
                if index % 32 == 0 or index == len(futures):
                    print(f'{phase}: {index}/{len(futures)}', flush=True)
        all_genomes = {identity(CONTROL): CONTROL, identity(incumbent): incumbent}
        for plan in plans:
            for genomes in plan['arms'].values():
                all_genomes.update({identity(g): g for g in genomes})
        evaluate(list(all_genomes.values()), train, 'training')
        selected = {identity(CONTROL): CONTROL, identity(incumbent): incumbent}
        results = []
        for plan in plans:
            arms = {}
            for name, genomes in plan['arms'].items():
                ranking = sorted([summary(g, train, cache) for g in [incumbent, *genomes]], key=rank, reverse=True)
                best = ranking[0]
                selected[best['id']] = best['genome']
                arms[name] = {'new_genomes': len(genomes), 'charged_training_trials': len(genomes) * len(train),
                              'best_training': best, 'ranking': ranking}
            results.append({'seed': plan['seed'], 'arms': arms})
        # Persist frozen selection BEFORE consulting validation.
        (args.out / 'frozen-selection.json').write_text(json.dumps(results, indent=2), encoding='utf8')
        evaluate(list(selected.values()), held, 'validation after selection')
        for result in results:
            for arm in result['arms'].values():
                arm['validation'] = summary(arm['best_training']['genome'], held, cache)
    def phenotype(genome):
        # An outcome/solution signature is a lower bound on behavioral diversity,
        # not a complete search trace. Node counts/timings deliberately excluded.
        rows = [cache[identity(genome), path] for path, _ in train]
        return json.dumps([[(lv['solved'], lv.get('seq')) for lv in row['levels']] for row in rows], sort_keys=True)
    report = {'seeds': results, 'control_training': summary(CONTROL, train, cache),
              'incumbent_training': summary(incumbent, train, cache),
              'control_validation': summary(CONTROL, held, cache),
              'incumbent_validation': summary(incumbent, held, cache),
              'unique_training_genotypes': len(all_genomes),
              'unique_outcome_solution_signatures': len({phenotype(g) for g in all_genomes.values()}),
              'physical_trials': len(cache), 'errors': sum(bool(row.get('error')) for row in cache.values()),
              'seconds': time.monotonic() - start,
              'qualification': 'Next-batch selector ablation on previously inspected public games; not independent hidden-game evidence.'}
    (args.out / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps({k: v for k, v in report.items() if k != 'seeds'}), flush=True)


if __name__ == '__main__':
    for variable in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'RAYON_NUM_THREADS'):
        os.environ[variable] = '1'
    main()
