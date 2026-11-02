"""Small bounded local screen; evaluator alone accesses the engine.

No cloning/search/oracle or game IDs are passed to the policy.
"""
from pathlib import Path
import json
import re
import time
import argparse
from arcengine import ActionInput, GameAction
from sweep2 import load_game, frame_of
from small_reactive_agent import ReactivePolicy

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'analysis/small-reactive-20261102'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=OUT)
    parser.add_argument('--decisions', type=int, default=12)
    args = parser.parse_args()
    OUT = args.out
    OUT.mkdir(exist_ok=False)
    manifest = dict(model='arc-small-reactive', games=['ft09', 'ls20'],
                    max_decisions_per_game=args.decisions, max_seconds_per_game=120,
                    training=False, qualification='Bounded local feasibility screen, not Kaggle score or paired quality comparison.')
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    summaries = []
    for game in manifest['games']:
        path = next((ROOT / 'games/environment_files').rglob(game + '.py'))
        cls = re.search(r'^class (\w+)\(ARCBaseGame\)', path.read_text(), re.M)[1]
        engine = load_game(str(path), cls)
        frame = engine.perform_action(ActionInput(id=GameAction.RESET))
        policy = ReactivePolicy()
        started = time.perf_counter()
        errors = []
        count = 0
        for turn in range(args.decisions):
            if time.perf_counter() - started > 120:
                break
            grid = frame_of(frame).tolist()
            names = {1: 'UP', 2: 'DOWN', 3: 'LEFT', 4: 'RIGHT', 5: 'ACTION5', 6: 'MOUSE', 7: 'UNDO'}
            valid = [names[int(a)] for a in frame.available_actions if int(a) in names]
            try:
                choice, record = policy.choose(grid, valid, int(frame.levels_completed))
                record['turn'] = turn
                with (OUT / (game + '.jsonl')).open('a', encoding='utf-8') as f:
                    f.write(json.dumps(record) + '\n')
                action_id = next(k for k, v in names.items() if v == choice['action'])
                data = {'x': choice['col'], 'y': choice['row']} if action_id == 6 else {}
                frame = engine.perform_action(ActionInput(id=GameAction.from_id(action_id), data=data))
                count += 1
                if str(frame.state).endswith(('WIN', 'GAME_OVER')):
                    break
            except Exception as exc:
                error = dict(turn=turn, error=repr(exc), response=getattr(policy, 'last_response', None))
                errors.append(error)
                break
        summaries.append(dict(game=game, levels=int(frame.levels_completed), actions=count,
                              seconds=time.perf_counter() - started, errors=errors,
                              history=policy.history))
        (OUT / 'result.json').write_text(json.dumps(summaries, indent=2), encoding='utf-8')
        print(json.dumps(summaries[-1]), flush=True)
