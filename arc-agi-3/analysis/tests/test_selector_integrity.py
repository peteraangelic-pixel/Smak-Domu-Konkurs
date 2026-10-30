"""Check evidence isolation and equal budgets before expensive engine runs."""
import json
from pathlib import Path
import shutil
import sys

ANALYSIS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ANALYSIS))
from compare_search_selectors import make_plans
from evolve_search import identity


def test_validation_outcomes_cannot_change_proposals_or_parents(tmp_path):
    source = ANALYSIS / 'evolution-watchdog-20261030'
    run = tmp_path / 'warm'
    run.mkdir()
    for name in ('manifest.json', 'report.json', 'trials.jsonl'):
        shutil.copyfile(source / name, run / name)
    expected = make_plans(run, [731], 4)
    manifest = json.loads((run / 'manifest.json').read_text())
    report = json.loads((run / 'report.json').read_text())
    report['holdout'] = [{'genome': {}, 'solved_levels': 100000}]
    report['selected'] = {'genome': {'DO_NOT_USE_VALIDATION': True}}
    (run / 'report.json').write_text(json.dumps(report))
    rows = [json.loads(line) for line in (run / 'trials.jsonl').read_text().splitlines()]
    for row in rows:
        if row['game'] in manifest['holdout']:
            row['weighted_completion'] = 99999
            row['genome'] = 'unknown-validation-only-genome'
    (run / 'trials.jsonl').write_text('\n'.join(json.dumps(r) for r in rows))
    assert make_plans(run, [731], 4) == expected


def test_equal_novel_genome_slots_and_reproducibility():
    source = ANALYSIS / 'evolution-watchdog-20261030'
    report = json.loads((source / 'report.json').read_text())
    known = {r['id'] for generation in report['training_history'] for r in generation}
    known.update(r['id'] for r in report['training_finalists'])
    first = make_plans(source, [731], 4)
    assert make_plans(source, [731], 4) == first
    for genomes in first[0][0]['arms'].values():
        ids = {identity(g) for g in genomes}
        assert len(ids) == 4
        assert not ids.intersection(known)
