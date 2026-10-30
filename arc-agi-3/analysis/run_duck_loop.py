"""Run the SHIPPED Duck ToolAgent + HarnessGameSession against real local games.

Local adapters: arcengine-backed TAAF Game, Windows bootstrap file, LM Studio
request compatibility. Agent tools, observations, guards and action callbacks
are the notebook's code. No replacement JSON policy and no search of engine
state. Baselines are hidden from the agent and used only after the run to score.
"""
import argparse
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import threading
import time
import types

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--game', required=True)
    p.add_argument('--variant', choices=['control', 'v18', 'memory', 'router'], required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--token-budget', type=int, default=1024)
    p.add_argument('--request-tokens', type=int, default=512)
    p.add_argument('--seconds', type=int, default=600)
    p.add_argument('--seed', type=int, default=731)
    p.add_argument('--model', default='arc-lab-27b')
    p.add_argument('--image-scale',type=int,default=4)
    args = p.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        raise FileExistsError(args.out)
    args.out.mkdir(parents=True, exist_ok=True)
    # Apply notebook environment using literal data only; no notebook execution.
    nb = json.loads((ROOT/'duck-v18-experiment/base-v13-7.ipynb').read_text(encoding='utf8'))
    def safe_value(node):
        if isinstance(node,ast.Constant): return node.value
        if isinstance(node,ast.Name) and node.id in ('SERVER_BASE_URL','SERVED_MODEL_NAME'):
            return 'http://127.0.0.1:1234/v1' if node.id=='SERVER_BASE_URL' else args.model
        if isinstance(node,ast.BinOp) and isinstance(node.op,(ast.Add,ast.Mult)):
            left,right=safe_value(node.left),safe_value(node.right)
            return left+right if isinstance(node.op,ast.Add) else left*right
        raise ValueError(f'Unsupported setup expression: {ast.dump(node)}')
    # The variant dictionary is only a delta. Recover the notebook's complete
    # policy setup as well (guards, UNDO, animations, function retention, etc.).
    setup_cell=''.join(nb['cells'][17]['source'])
    start=setup_cell.index('setup_env =')
    setup_assignment=setup_cell[start:setup_cell.index('\n}',start)+2]
    for node in ast.walk(ast.parse(setup_assignment)):
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='setup_env' for t in node.targets):
            assert isinstance(node.value,ast.Dict)
            os.environ.update({str(safe_value(k)):str(safe_value(v)) for k,v in zip(node.value.keys,node.value.values)})
    for node in ast.walk(ast.parse(''.join(nb['cells'][1]['source']))):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'ARC3_VARIANT' for t in node.targets):
            variant = ast.literal_eval(node.value)
            os.environ.update(variant['env'])
    os.environ.update(ARC3_PLAN_COMMIT='1', ARC3_ESCALATE_ACTIONS='20', ARC3_LEVEL_TOKEN_CAP='0',
        LOCAL_ANALYZER_MODEL_ID=args.model, LOCAL_ANALYZER_PROVIDER='lmstudio',
        LOCAL_ANALYZER_BASE_URL='http://127.0.0.1:1234/v1', LOCAL_ANALYZER_CONTEXT_WINDOW='16384',
        LOCAL_ANALYZER_MAX_OUTPUT=str(args.request_tokens), LOCAL_ANALYZER_ENABLE_THINKING='0',
        LOCAL_ANALYZER_TEMPERATURE='0', LOCAL_ANALYZER_SEED=str(args.seed),
        ONLY_RESET_LEVELS='true', ARC3_MAX_ACTIVE_STREAMS='1',
        MULTIMODAL_UPSCALE=str(args.image_scale),
        ARC3_WINPATH_DIR=str((args.out/'winpath').resolve()),
        ARC3_WINPATH_LOG='0', MPLBACKEND='Agg')
    sys.path.insert(0, str(args.source.resolve()))
    # TAAF's top-level __init__ eagerly imports cloud deployment/notebook
    # packages. Load the actual game/solver modules without that orchestration.
    package = types.ModuleType('taaf')
    package.__path__ = [str((ROOT/'kaggle/ops/results/r033-recon-bundle/bundle/src/tufa-arc-agi-framework/src/taaf').resolve())]
    sys.modules['taaf'] = package
    import arcengine
    import numpy as np
    import requests
    import taaf.game as tg
    from inference.framework.solver import HarnessSolver, _HarnessGameSession
    from inference.agent import tool_agent as ta
    from inference.agent import python_tool_sandbox as sandbox
    from observation_router import families, install

    # Same request semantics for every arm. Do not flatten chat history or tools.
    original_post = requests.post
    api_rows = []
    def post(url, **kwargs):
        payload = kwargs.get('json', {})
        if str(url).endswith('/chat/completions'):
            payload.pop('chat_template_kwargs', None)
            payload.pop('top_k', None)
            payload.pop('priority', None)
            payload['reasoning_effort'] = 'none'
            payload['seed'] = args.seed
            # Respect exact total generated-token budget instead of overshooting
            # by one whole request at the end of a game.
            remaining = args.token_budget - sum(r.get('completion_tokens', 0) for r in api_rows)
            if remaining <= 0:
                raise RuntimeError('Generated token budget exhausted')
            payload['max_tokens'] = min(int(payload.get('max_tokens') or args.request_tokens), remaining)
            (args.out/'last-request.json').write_text(json.dumps(payload), encoding='utf8')
        t = time.monotonic()
        try:
            response = original_post(url, **kwargs)
        except requests.RequestException as exc:
            row={'seconds':time.monotonic()-t,'status':0,'transport_error':str(exc)}
            api_rows.append(row)
            with (args.out/'api.jsonl').open('a',encoding='utf8') as f:f.write(json.dumps(row)+'\n')
            raise
        data = response.json()
        usage = data.get('usage', {})
        row = {'seconds': time.monotonic()-t, 'status': response.status_code, **usage,
               'finish_reason': (data.get('choices') or [{}])[0].get('finish_reason')}
        api_rows.append(row)
        with (args.out/'api.jsonl').open('a', encoding='utf8') as f:
            f.write(json.dumps(dict(row, response=data))+'\n')
        print(f"{args.variant}/{args.game}: API {len(api_rows)} {row}", flush=True)
        return response
    requests.post = post

    # Preserve the exact shipped sandbox bootstrap bytes on Windows.
    original_popen = sandbox.subprocess.Popen
    def popen(command, **kwargs):
        if os.name == 'nt' and isinstance(command, list) and '-c' in command and len(command[-1]) > 16000:
            path = Path(kwargs['cwd'])/'bootstrap.py'
            path.write_text(command[-1], encoding='utf8')
            command = command[:-2] + [str(path)]
        return original_popen(command, **kwargs)
    sandbox.subprocess.Popen = popen
    if args.variant == 'router' and ta.ToolAgent._build_user_prompt.__name__ != 'routed':
        install(ta.ToolAgent)
    if args.variant == 'memory' and ta.ToolAgent.analyze.__name__ != '_slm_analyze':
        from lalalia_compat import install as install_memory
        install_memory()

    path = next((ROOT/'games/environment_files').rglob(args.game+'.py'))
    game_text = path.read_text(encoding='utf8')
    import re
    cls_name = re.search(r'^class (\w+)\(ARCBaseGame\)', game_text, re.M)[1]
    spec = importlib.util.spec_from_file_location('local_game', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    engine = getattr(module, cls_name)()
    baseline = json.loads(path.with_name('metadata.json').read_text(encoding='utf8'))['baseline_actions']

    def raw_action(action):
        observed = engine.perform_action(action)
        raw = arcengine.FrameDataRaw(**observed.model_dump(exclude={'frame'}))
        raw.frame = [np.asarray(frame, dtype=np.int8) for frame in observed.frame]
        return raw

    class LocalGame(tg.Game):
        def _start_game(self, session):
            self.game_id = args.game
            self.number_of_levels = len(baseline)
            self.base_actions_per_level = None  # hidden from model and scheduler
            return tg.GameState(raw=raw_action(arcengine.ActionInput(id=arcengine.GameAction.RESET)))
        def _execute_action(self, action):
            return tg.GameState(raw=raw_action(action), previous_action=action)

    game = LocalGame()
    game.start_game()
    initial_actions = list(game.current_state.available_actions)
    solver = HarnessSolver(model=args.model, max_runtime_s_per_game=args.seconds,
                           max_generated_tokens_per_game=args.token_budget, max_actions_per_game=100, concurrency=1)
    analyzer = ta.ToolAgent(model=args.model, base_url='http://127.0.0.1:1234/v1', provider='lmstudio',
                            timeout=args.seconds, save_request_logs=True)
    session = _HarnessGameSession(solver=solver, game=game, analyzer=analyzer,
        game_index=0, pass_index=0, state_path=args.out/'tool_runtime_state.json',
        transcript_path=args.out/'transcript.txt', analysis_html_relpath='analysis.html',
        stop_event=threading.Event(), viewer_data_path=args.out/'viewer.json')
    manifest = {'variant': args.variant, 'game': args.game, 'model': args.model, 'seed': args.seed,
        'budget': {'generated_tokens': args.token_budget, 'request_tokens': args.request_tokens, 'seconds': args.seconds},
        'environment': {k:v for k,v in os.environ.items() if k.startswith(('ARC3_', 'LOCAL_ANALYZER_', 'MULTIMODAL_')) and 'KEY' not in k},
        'game_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'source_manifest': json.loads((args.source.parent/'source-manifest.json').read_text(encoding='utf8')),
        'qualification': 'Full local Duck loop with notebook policy env, Qwen3.8-27B Q4, 16k context; not target Flash-Next/SGLang or Kaggle score.',
        'driver_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (args.out/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf8')
    start, error = time.monotonic(), None
    try:
        session.play()
    except Exception as exc:
        import traceback
        error = traceback.format_exc()
        print(error, flush=True)
    if game.game_run.final_score is None:
        game.finish_game()
    run = game.game_run
    # Official scoring only after the agent has finished; no baseline leakage.
    from arc_agi.scorecard import EnvironmentScoreCalculator
    calc = EnvironmentScoreCalculator(id=args.game, state=game.current_state.raw.state)
    for i, human in enumerate(baseline):
        calc.add_level(level_index=i+1, completed=i<run.levels_completed,
                       actions_taken=run.actions_per_level[i], baseline_actions=int(human))
    score = calc.to_score()
    result = {'variant': args.variant, 'game': args.game, 'seed': args.seed, 'model': args.model,
              'budget': manifest['budget'], 'game_sha256': manifest['game_sha256'],
              'families': families(initial_actions), 'levels_completed': run.levels_completed,
              'actions': len(run.history), 'actions_per_level': run.actions_per_level,
              'rhae_score_pct': float(score.score), 'generated_tokens': analyzer.generated_tokens,
              'api_calls': len(api_rows), 'api_errors': sum(r['status'] != 200 for r in api_rows),
              'reasoning_tokens': sum(r.get('completion_tokens_details',{}).get('reasoning_tokens',0) for r in api_rows),
              'routes': getattr(analyzer,'_lab_routes',[]), 'memory_levels': len(getattr(analyzer,'_slm_levels',[])),
              'memory_pinned_chars': len(getattr(analyzer,'_slm_block_text','')),
              'note': run.solver_note, 'error': error, 'seconds': time.monotonic()-start}
    result['image_scale']=args.image_scale
    result['valid_model_run']=bool(api_rows) and not result['api_errors']
    result['time_limit_binding']=result['seconds']>=args.seconds-1
    (args.out/'result.json').write_text(json.dumps(result, indent=2), encoding='utf8')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','RAYON_NUM_THREADS'):
        os.environ[name] = '1'
    main()
