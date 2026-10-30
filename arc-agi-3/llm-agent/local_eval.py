"""Ewaluator lokalny (v6.8): multiprocessing Pool po grach, bez wrappera Kaggle.

Odpowiednik ich FFI+MP w skali ARC: silnik wołamy BEZPOŚREDNIO przez arcengine
(CPU), gry są niezależnymi procesami (Pool), decyzje pobiera LM Studio (jedno
wspólne; LM Studio kolejkowuje żądania — włącz równoległość w ustawieniach
servera, jeśli jest). Ten sam plik działa w dwóch trybach:

  --real  (domyślny): arcengine + LM Studio, prawdziwe gry demo
  --mock:              atrapy klatek, zero zależności (test okablowania, CI)

Ewaluator jest fitnessem dla evolve_knobs.py:
  --fitness local_eval:make_fitness  (env GAMES_DIR, EVAL_GAMES, EVAL_ACTIONS)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import types as _types
_pkg = _types.ModuleType("llmagent")  # katalog ma myślnik — alias pakietu
_pkg.__path__ = [str(Path(__file__).resolve().parent)]
sys.modules.setdefault("llmagent", _pkg)

RESET = "0"


# ---------------------------------------------------------------------------
# tryb mock: deterministyczne atrapy (bez arcengine, bez sieci)
# ---------------------------------------------------------------------------

_MOCK_SCRIPT = [
    ((0, 0, 0, 0), "PLAYING", 0),
    ((0, 1, 0, 0), "PLAYING", 0),
    ((0, 1, 1, 0), "PLAYING", 0),
    ((0, 1, 1, 2), "PLAYING", 0),
    ((0, 1, 1, 2), "WIN", 1),
]


class _MockGame:
    """Mini-gra: określona sekwencja klatek; liczy wywołania Reset jako śmierć."""

    def __init__(self) -> None:
        self.step = 0

    def frame(self):
        if self.step >= len(_MOCK_SCRIPT):
            self.step = len(_MOCK_SCRIPT) - 1
        grid, state, level = _MOCK_SCRIPT[self.step]
        return grid, state, level


def play_mock(gid: str, max_actions: int = 32) -> dict:
    """Pętla polityki na atrapach — weryfikuje parser/temperatury/notes bez sieci."""
    from llmagent.llm_policy import FrameInfo

    class _StubClient:
        total_tokens = 0

        def chat(self, messages, temperature=None):
            self.total_tokens += 42
            return {"content": '{"action": "UP", "reasoning": "mock"}'}

    from llmagent.llm_policy import LLMPolicy
    policy = LLMPolicy.__new__(LLMPolicy)
    policy.config = None
    policy.client = _StubClient()
    policy.tracker = lp_StateTracker()
    _init_fields(policy)

    game = _MockGame()
    ok = True
    for _ in range(max_actions):
        grid, state, levels = game.frame()
        if state == "WIN":
            break
        frame = FrameInfo(grid=(grid, grid), step=game.step, level=0,
                          state_name=state, levels_completed=levels,
                          available_actions=["ACTION1", "ACTION2", "ACTION6"])
        proposal = policy.choose_action(frame)
        game.step += 1
    final_state = game.frame()[1]
    return {"game": gid, "mode": "mock", "ok": ok, "steps": game.step,
            "total_tokens": policy.client.total_tokens,
            "levels_completed": final_state == "WIN",
            "won": final_state == "WIN",
            "final_state": final_state}


def lp_StateTracker():  # krótszy alias dla czytelności powyżej
    from llmagent.llm_policy import StateTracker
    return StateTracker()


def _init_fields(policy) -> None:
    """Pola, które __init__ ustawia poza atrybutami zależnymi od sieci."""
    policy.tracker = lp_StateTracker()
    policy._messages = []
    policy._action_queue = []
    policy._actions_since_last_llm = 0
    policy._max_actions_per_plan = 15
    policy._last_level = 0
    policy._game_notes = []
    policy._actions_on_level = 0
    p_ = policy
    p_._last_audit_at = 0
    p_._probe_level = None
    p_._noop_recent = []
    p_._last_exec = None
    p_._last_grid = None
    p_._run_lessons = []
    p_._level_start_tokens = 0
    p_._audit_level_tokens = 0
    p_._pending_notes = None
    p_._level_notes = {}
    p_._game_overs = []
    p_._audits_on_level = 0
    p_.value_gate = None


# ---------------------------------------------------------------------------
# tryb real: arcengine (bezpośrednio, bez wrappera) + LM Studio
# ---------------------------------------------------------------------------

def _engine_names(raw) -> list[str]:
    import re
    names = []
    for item in raw or []:
        match = re.search(r"ACTION(\d+)", str(item))
        if match:
            names.append(f"ACTION{match.group(1)}")
    return names


def play_one(games_dir: str, gid: str, max_actions: int = 40,
             knobs_json: str = "", png_last: str | None = None) -> dict:
    """Jedna gra: arcengine CPU + nasza polityka na LM Studio."""
    from llmagent.knobs import DEFAULTS, KNOBS, reset_to_defaults
    reset_to_defaults()
    if knobs_json:
        from llmagent.knobs import apply_overrides
        apply_overrides(knobs_json)

    from llmagent.llm_policy import FrameInfo, LLMPolicy
    policy = LLMPolicy()  # klient z env (LLM_BASE_URL / LLM_MODEL_ID)

    from arcengine import ActionInput, GameAction
    from arc_agi.scorecard import EnvironmentScoreCalculator

    src = Path(games_dir) / gid / gid / f"{gid}.py"
    if not src.exists():
        return {"game": gid, "ok": False, "error": f"brak pliku gry: {src}"}
    import importlib.util
    spec = importlib.util.spec_from_file_location(f"game_{gid}", src)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    cls = next(v for v in vars(mod).values()
               if isinstance(v, type) and issubclass(v, ARCBaseGame := _arc_base())
               and v is not _arc_base())
    game = cls()

    def send(name: str, data: dict | None = None):
        if name in ("RESET", RESET):
            return game.perform_action(ActionInput(id=GameAction.RESET))
        return game.perform_action(
            ActionInput(id=GameAction[name], data=data or {}))

    fd = send(RESET)
    last_png = None
    result = {"game": gid, "mode": "real", "ok": True, "steps": 0,
              "levels_completed": 0, "level_actions": [], "partial_level_actions": 0,
              "bad_actions": 0, "won": False, "final_state": "UNKNOWN"}
    level_action_count = 0
    for _ in range(max_actions):
        rendered = game.camera.render(game.current_level.get_sprites())
        grid = tuple(tuple(int(c) for c in row) for row in rendered)
        state = str(fd.state)
        if "WIN" in state.upper():
            result["won"] = True
            result["final_state"] = state
            break
        if "GAME_OVER" in state.upper():
            result["final_state"] = state
            break
        frame = FrameInfo(grid=grid, step=result["steps"], level=int(fd.levels_completed or 0),
                          state_name=state,
                          levels_completed=int(fd.levels_completed or 0),
                          available_actions=_engine_names(fd.available_actions))
        proposal = policy.choose_action(frame)
        action_name = str(proposal.get("name", "RESET"))
        action_data = {}
        if action_name == "ACTION6":
            rows, cols = frame.shape
            x = int(proposal.get("x", cols // 2))
            y = int(proposal.get("y", rows // 2))
            action_data = {"x": max(0, min(max(cols - 1, 0), x)),
                           "y": max(0, min(max(rows - 1, 0), y))}
        try:
            fd = send(action_name, action_data)
        except Exception as exc:  # nieprawidłowa akcja w tej grze — nie kończ
            result["bad_actions"] += 1
            result[f"bad_action_{result['steps']}"] = str(exc)[:120]
            fd = send("RESET")
        result["steps"] += 1
        level_action_count += 1
        completed = int(fd.levels_completed or 0)
        while len(result["level_actions"]) < completed:
            result["level_actions"].append(level_action_count)
            level_action_count = 0
        result["levels_completed"] = int(fd.levels_completed or 0)
        if png_last:
            last_png = _save_png(rendered, png_last)
    result["final_state"] = str(fd.state)
    result["won"] = "WIN" in result["final_state"].upper()
    result["partial_level_actions"] = level_action_count
    result["total_tokens"] = int(policy.total_tokens)
    result["llm_calls"] = int(policy.total_calls)
    result["llm_seconds"] = round(float(policy.client.total_time), 2)
    result["reasoning_tokens"] = int(getattr(policy.client, "reasoning_tokens", 0))
    result["failed_llm_calls"] = int(getattr(policy.client, "failed_calls", 0))
    metadata = Path(games_dir) / gid / gid / "metadata.json"
    try:
        baseline_actions = json.loads(metadata.read_text(encoding="utf-8"))["baseline_actions"]
        calculator = EnvironmentScoreCalculator(id=gid, state=fd.state)
        for index, baseline in enumerate(baseline_actions):
            completed_level = index < len(result["level_actions"])
            actions = (result["level_actions"][index] if completed_level else
                       result["partial_level_actions"] if index == len(result["level_actions"]) else 0)
            calculator.add_level(level_index=index + 1, completed=completed_level,
                                 actions_taken=actions, baseline_actions=int(baseline))
        score = calculator.to_score()
        result["rhae_score_pct"] = round(float(score.score), 4)
        result["level_scores_pct"] = [round(float(x), 4) for x in score.level_scores]
        result["baseline_actions"] = baseline_actions
    except (OSError, KeyError, TypeError, ValueError):
        result["rhae_score_pct"] = None
    if last_png:
        result["png"] = last_png
    return result


def _arc_base():
    from arcengine import ARCBaseGame
    return ARCBaseGame


def _save_png(rendered, path: str) -> str | None:
    try:
        import numpy as np
        from PIL import Image
        PALETTE = [(255, 255, 255), (204, 204, 204), (153, 153, 153), (102, 102, 102),
                   (51, 51, 51), (0, 0, 0), (229, 58, 163), (255, 123, 204),
                   (249, 60, 49), (30, 147, 255), (136, 216, 241), (255, 220, 0),
                   (255, 133, 27), (146, 18, 49), (79, 204, 48), (163, 86, 208)]
        a = np.asarray(rendered, dtype=np.int64)
        rgb = np.array(PALETTE, dtype=np.uint8)[a % 16]
        Image.fromarray(rgb).resize((a.shape[1] * 8, a.shape[0] * 8),
                                    Image.NEAREST).save(path)
        return path
    except Exception:
        return None


# ---------------------------------------------------------------------------
# multiprocessing: worker na (gra × zestaw knobów)
# ---------------------------------------------------------------------------

_JOBS: dict[str, Any] = {}


def _worker_init(games_dir: str, mode: str, max_actions: int) -> None:
    _JOBS["games_dir"] = games_dir
    _JOBS["mode"] = mode
    _JOBS["max_actions"] = max_actions


def _run_job(job: dict) -> dict:
    gid, knobs_json = job["game"], job.get("knobs_json", "")
    mode = _JOBS.get("mode", "mock")
    games_dir = _JOBS.get("games_dir", "")
    max_actions = _JOBS.get("max_actions", 40)
    t0 = time.time()
    try:
        if mode == "mock":
            from llmagent.knobs import reset_to_defaults, apply_overrides
            reset_to_defaults()
            if knobs_json:
                apply_overrides(knobs_json)
            result = play_mock(gid, max_actions=max_actions)
        else:
            result = play_one(games_dir, gid, max_actions=max_actions,
                              knobs_json=knobs_json)
    except Exception as exc:  # błąd jednej gry nie zabija ewaluacji
        result = {"game": gid, "ok": False, "error": str(exc)[:200]}
    result["seconds"] = round(time.time() - t0, 1)
    result["knobs_id"] = job.get("knobs_id", "")
    return result


def evaluate(knobs_sets: list[dict], games: list[str], games_dir: str = "",
             mode: str = "mock", max_actions: int = 40, workers: int | None = None
             ) -> list[dict]:
    """Równoległa ewaluacja: |knobs_sets| × |games| zadań w Pool."""
    jobs = []
    items = (knobs_sets.items() if isinstance(knobs_sets, dict)
             else enumerate(knobs_sets))
    for knobs_id, blob in items:
        for gid in games:
            jobs.append({"game": gid, "knobs_id": str(knobs_id),
                         "knobs_json": json.dumps(blob) if blob else ""})
    if workers is None:
        if mode == "mock":
            workers = max(1, min(len(jobs), os.cpu_count() or 1))
        else:
            # One local model server is shared by all workers. Default to one
            # request stream on small-VRAM PCs; parallelism remains explicit.
            try:
                limit = max(1, int(os.environ.get("LLM_MAX_PARALLEL", "1")))
            except ValueError:
                limit = 1
            workers = max(1, min(len(jobs), limit))
    if mode == "mock":
        ctx_workers = workers
        with Pool(processes=ctx_workers, initializer=_worker_init,
                  initargs=("", "mock", max_actions)) as pool:
            return pool.map(_run_job, jobs, chunksize=1)
    with Pool(processes=workers, initializer=_worker_init,
              initargs=(games_dir, "real", max_actions)) as pool:
        return pool.map(_run_job, jobs, chunksize=1)


def summarize(results: list[dict]) -> str:
    by_knobs: dict[str, list[dict]] = {}
    for r in results:
        by_knobs.setdefault(r.get("knobs_id", ""), []).append(r)
    lines = []
    for knobs_id, rows in sorted(by_knobs.items()):
        ok_rows = [r for r in rows if r.get("ok")]
        levels = sum(r.get("levels_completed", 0) for r in ok_rows)
        wins = sum(1 for r in ok_rows if r.get("won"))
        tokens = sum(r.get("total_tokens", 0) for r in ok_rows)
        scores = [float(r.get("rhae_score_pct") or 0.0) for r in rows]
        mean_score = sum(scores) / len(rows) if rows else 0.0
        lines.append(f"{knobs_id or 'default':<16} ok={len(ok_rows)}/{len(rows)} "
                     f"RHAE={mean_score:.2f}% poziomy={levels} "
                     f"wygrane={wins} tokeny={tokens}")
    return "\n".join(lines)


def make_fitness(games_dir: str = "", games: list[str] | None = None,
                 mode: str = "mock", max_actions: int = 40, workers: int | None = None):
    """Adapter dla evolve_knobs.py: fitness(knobs) -> float (wyżej = lepiej)."""
    games = games or ["ft09", "ls20", "ka59"]

    def fitness(knobs: dict[str, float]) -> float:
        results = evaluate({"cand": {k: v for k, v in knobs.items()}}, games,
                           games_dir=games_dir, mode=mode,
                           max_actions=max_actions, workers=workers)
        ok_rows = [r for r in results if r.get("ok")]
        if not ok_rows:
            return float("-inf")
        if mode == "real":
            # Failed games and games without an official score count as zero;
            # optimize the same mean-per-game score used by the competition.
            return sum(float(r.get("rhae_score_pct") or 0.0) for r in results) / max(1, len(results))
        levels = sum(r.get("levels_completed", 0) for r in ok_rows)
        wins = sum(1 for r in ok_rows if r.get("won"))
        errors = len(results) - len(ok_rows)
        return levels + 2.0 * wins - 3.0 * errors

    return fitness


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("games_dir", nargs="?", default="")
    parser.add_argument("--games", default="ft09,ls20,ka59")
    parser.add_argument("--mode", choices=["mock", "real"], default="mock")
    parser.add_argument("--knobs-file", default=None,
                        help="JSON: {\"nazwa\": {KNOBS...}, ...} albo jeden zestaw")
    parser.add_argument("--max-actions", type=int, default=40)
    parser.add_argument("--workers", type=int, default=None)
    args = parser.parse_args(argv)

    games = [g.strip() for g in args.games.split(",") if g.strip()]
    if args.knobs_file:
        blob = json.loads(Path(args.knobs_file).read_text(encoding="utf-8"))
        knob_sets = blob if all(isinstance(v, dict) for v in blob.values()) else {"default": blob}
    else:
        knob_sets = {"default": {}}

    results = evaluate(knob_sets, games, games_dir=args.games_dir,
                       mode=args.mode, max_actions=args.max_actions,
                       workers=args.workers)
    print(summarize(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
