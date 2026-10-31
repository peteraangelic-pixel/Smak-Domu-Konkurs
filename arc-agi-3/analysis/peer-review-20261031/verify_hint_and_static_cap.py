"""Check the two peer proposals without GPU inference or competition submission.

Run after materialize_duck.py reconstructs v11-hint-source-check.
The prompt check executes the actual helper and conditional AST fragment only;
it is not a complete ToolAgent or LLM quality test.
"""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE.parent
ROOT = ANALYSIS.parent


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    v11 = HERE / 'v11-hint-source-check/ARC3-Inference/inference'
    v13 = ANALYSIS / 'champion-recovery-20261031/v137-rematerialized/ARC3-Inference/inference'
    agent_path = v11 / 'agent/tool_agent.py'
    tree = ast.parse(agent_path.read_text(encoding='utf-8'))
    helpers = [n for n in tree.body if isinstance(n, ast.FunctionDef)
               and n.name in {'_get_env_bool', '_opener_commit_hint'}]
    branches = [n for n in ast.walk(tree) if isinstance(n, ast.If)
                and ast.unparse(n.test) == '_opener_commit_hint()']
    assert len(helpers) == 2 and len(branches) == 1
    namespace = {'os': os}
    exec(compile(ast.Module(body=helpers, type_ignores=[]), str(agent_path), 'exec'), namespace)
    branch = compile(ast.Module(body=branches, type_ignores=[]), str(agent_path), 'exec')

    old_env = os.environ.copy()
    try:
        prompts = {}
        for switch in ('0', '1'):
            os.environ['ARC3_OPENER_COMMIT_HINT'] = switch
            namespace['lines'] = []
            exec(branch, namespace)
            prompts[switch] = namespace['lines'][:]
        assert prompts['0'] == [] and len(prompts['1']) == 1
        assert 'action(actions)' in prompts['1'][0]

        os.environ.update(ARC3_LEVEL_TOKEN_CAP='45000', ARC3_LEVEL_RESETS_MAX='1',
                          ARC3_LEVEL_MIN_DONE='0', ARC3_DYN_CAP='0')
        modules = [load_module(p, name) for p, name in (
            (v11 / 'framework/arc3_level_budget.py', 'peer_v11_budget'),
            (v13 / 'framework/arc3_level_budget.py', 'peer_v13_budget'))]
        rng = random.Random(731)
        decision_counts = {}
        comparisons = 0
        for _ in range(100):
            policies = [m.LevelBudget.from_env() for m in modules]
            tokens, levels = 0, 0
            for _ in range(100):
                tokens += rng.choice((0, 4096, 12000, 45000, 90000))
                levels += int(rng.random() < .08)
                peeks = [p.peek(tokens, levels) for p in policies]
                assert peeks[0] == peeks[1], (tokens, levels, peeks)
                steps = [p.step(tokens, levels) for p in policies]
                assert steps[0] == steps[1], (tokens, levels, steps)
                decision_counts[steps[0]] = decision_counts.get(steps[0], 0) + 1
                comparisons += 1
        assert set(decision_counts) == {'keep_going', 'reset_level', 'abandon'}
    finally:
        os.environ.clear()
        os.environ.update(old_env)

    notebook = ROOT / 'duck-v18-experiment/base-v13-7.ipynb'
    cells = json.loads(notebook.read_text(encoding='utf-8'))['cells']
    sources = [''.join(c.get('source', [])) for c in cells]
    probe_cell = next(i for i, s in enumerate(sources) if 'budget_probe.json' in s)
    swap_cell = next(i for i, s in enumerate(sources) if 'bm.games = _competition_games()' in s)
    assert probe_cell < swap_cell
    record = {
        'scope': 'Source/policy verification, no engine games or LLM quality evaluation',
        'v11_notebook_sha256': hashlib.sha256((ROOT / 'duck-v11-c45/arc3-duck-v11.ipynb').read_bytes()).hexdigest(),
        'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in (agent_path, v11 / 'framework/arc3_level_budget.py',
                                    v13 / 'framework/arc3_level_budget.py')},
        'hint_ast_fragment_output': prompts,
        'static_budget_sampled_comparisons': comparisons,
        'static_budget_decisions': decision_counts,
        'v13_probe_cell_zero_based': probe_cell,
        'v13_live_roster_swap_cell_zero_based': swap_cell,
        'caveats': [
            'Hint activation is not evidence of more completed levels.',
            'Sampled static policy agreement is not full solver equivalence.',
            '45000 is a per-level token cap; it does not replace 532 minutes per game.',
            'No expected Kaggle score or top-five ceiling is established by these checks.'
        ]
    }
    (HERE / 'hint-and-static-cap-verification.json').write_text(
        json.dumps(record, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(record, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
