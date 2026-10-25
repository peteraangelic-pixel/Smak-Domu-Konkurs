#!/usr/bin/env python3
"""Build `arc3-duck-v9.ipynb` from the accepted c45 notebook.

Input : src/base-c45.ipynb   (byte copy of arc-agi-3/kaggle/duck-c45/arc3-duck-c45.ipynb)
Output: arc3-duck-v9.ipynb

The build does exactly four things, all of them reversible and greppable:

1. adds a `V9` profile cell (one switch per lever; default = c45 as accepted);
2. wires three values through it: LOCAL_ANALYZER_MAX_OUTPUT,
   ARC3_SYSTEM_PROMPT_PREFIX, ARC3_MAX_ACTIVE_STREAMS;
3. makes the sglang launcher's MAXREQ / CTX overridable from the same cell;
4. appends a read-only metering cell that prints the numbers a slot is
   supposed to buy (actions/game, calls/game, tok/action) and writes
   v9_metrics.json for the ops channel.

Nothing else is touched: the 498 KB harness patch, the three extra patches,
the model paths, TRUE_SUBMISSION logic and the smoke/submit switch stay
byte-identical to c45.

Usage:  python3 tools/build_v9.py [--base src/base-c45.ipynb] [--out arc3-duck-v9.ipynb]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

MARK_BASE_CELLS = 30  # c45 has exactly 30 cells; a different base is a different notebook

V9_CELL = '''# === v9 profile: one switch, one measured lever ===========================
# Base is duck-c45 as accepted on 24.10 (Franzen fast engine: INT4 + MTP +
# sglang, Tufa duck harness, patches 0000-0004, level token cap 45k).
# Change ONE profile at a time; anything else is a confounded slot.
#
#   c45   faithful re-run of c45. First measurement of the fast line; the
#         metadata in this package is what makes it runnable at all.
#   deep  c45 + route-batching directive: aim 8-15 actions per model call with
#         an in-snippet stop condition. r019 measured 4.4 actions/call and
#         841 generated tokens per action: the pool buys 206 actions/game
#         while the human baselines of the same levels total ~717. Actions
#         per CALL is the only variable with that magnitude.
#   wide  c45 + more decode streams (MAXREQ/streams 10 -> 14). c87 measured
#         KV usage 0.71 median / 0.99 max at 10 streams, so this can OOM and
#         is deliberately not the default.
PROFILE = "c45"          # "c45" | "deep" | "wide"

V9 = {
    "id": "v9",
    "profile": PROFILE,
    # analyzer
    "max_output_tokens": 12 * 1024,
    "context_window": (116 + 12) * 1024,
    "system_prompt_prefix": "",
    # serving (read by the launcher through V9_MAXREQ / V9_CTX)
    "maxreq": 10,
    "ctx": (116 + 12 + 8) * 1024,
    "streams": 10,
    # level budget (the c45 hook in cell 21 reads ARC3_LEVEL_TOKEN_CAP)
    "level_token_cap": 45000,
    "level_resets_max": 1,
}

_ROUTE_PREFIX = (
    "Operating directive for this run: your thinking is the scarce resource, "
    "in-game actions are not. Once a route is validated, execute it as one "
    "deep batch inside a single python snippet - 8 to 15 actions per call - "
    "with an in-code stop condition that aborts the batch on any unexpected "
    "frame, on a level change or on game over, and print a two-line outcome. "
    "Never re-describe a board you already described; one short sentence of "
    "reasoning per call is the target. If the next actions are already fully "
    "determined by the previous frame, skip the deliberation entirely."
)

if PROFILE == "deep":
    V9.update(system_prompt_prefix=_ROUTE_PREFIX, max_output_tokens=10 * 1024)
elif PROFILE == "wide":
    V9.update(maxreq=14, streams=14)

assert PROFILE in {"c45", "deep", "wide"}, PROFILE
print(f"v9 profile={PROFILE} maxreq={V9['maxreq']} streams={V9['streams']} "
      f"max_output={V9['max_output_tokens']} prefix={'on' if V9['system_prompt_prefix'] else 'off'}",
      flush=True)
'''

METER_CELL = '''# === v9 metering: the six numbers a slot is supposed to buy ================
# Read-only over bm.game_runs. No GPU, no tokens, runs in smoke and in a real
# submission alike. Device: every number below is measured, not estimated.
#
#   actions/call      depth bought per model call; r019 = 4.4
#   tok/action        generated tokens per engine action; r019 = 841
#   actions           engine actions in the whole game; r019 = 206
#   actions_need      human baseline sum = actions needed to finish every level
#   weight_pct        completed level weight (the score's real numerator)
#   score             the game score, r019 mean 27.21
import json as _v9_json


def _v9_int(x):
    try:
        return int(x or 0)
    except (TypeError, ValueError):
        return 0


def _v9_row(run):
    hist = list(getattr(run, "history", []) or [])
    gen = [_v9_int(getattr(h, "generated_tokens", 0)) for h in hist]
    calls = sum(1 for t in gen if t > 0)
    tok = sum(gen) + _v9_int(getattr(run, "final_generated_tokens", 0))
    acts = sum(_v9_int(x) for x in (getattr(run, "actions_per_level", []) or []))
    levels = _v9_int(getattr(run, "levels_completed", 0))
    total = _v9_int(getattr(run, "number_of_levels", 0))
    weights = sum(range(1, total + 1)) or 1
    done_w = sum(range(1, levels + 1))
    need = sum(_v9_int(x) for x in (getattr(run, "base_actions_per_level", []) or []))
    score = getattr(run, "final_score", None)
    if score is None:
        try:
            score = run._compute_final_score()
        except Exception:
            score = 0.0
    return {
        "game_id": str(getattr(run, "game_id", "?")),
        "state": str(getattr(run, "state", "?")),
        "levels": f"{levels}/{total}",
        "weight_pct": round(100.0 * done_w / weights, 1),
        "score": round(float(score or 0.0), 2),
        "actions": acts,
        "actions_need": need,
        "calls": calls,
        "tok": tok,
        "tok_per_action": round(tok / acts, 1) if acts else 0.0,
        "actions_per_call": round(acts / calls, 2) if calls else 0.0,
        "tok_per_call": round(tok / calls, 1) if calls else 0.0,
        "wall_min": round(float(getattr(run, "final_wallclock_seconds", 0.0) or 0.0) / 60.0, 1),
    }


try:
    _v9_rows = [_v9_row(r) for r in (getattr(bm, "game_runs", None) or [])]
except Exception as _v9_exc:  # never let reporting break a finished run
    print(f"v9 metering skipped: {_v9_exc!r}", flush=True)
    _v9_rows = []

if _v9_rows:
    _v9_header = (f"{'game':22}{'levels':>8}{'w%':>6}{'score':>7}{'actions':>8}"
                  f"{'need':>6}{'calls':>6}{'a/call':>7}{'tok/act':>8}{'tok/call':>9}{'min':>6}")
    print("\\n=== v9 metering " + "=" * (len(_v9_header) - 16), flush=True)
    print(_v9_header, flush=True)
    for r in _v9_rows:
        print(f"{r['game_id'][:21]:22}{r['levels']:>8}{r['weight_pct']:6.1f}{r['score']:7.2f}"
              f"{r['actions']:8d}{r['actions_need']:6d}{r['calls']:6d}"
              f"{r['actions_per_call']:7.2f}{r['tok_per_action']:8.0f}"
              f"{r['tok_per_call']:9.0f}{r['wall_min']:6.0f}", flush=True)

    _n = len(_v9_rows)
    _mean = lambda key: sum(r[key] for r in _v9_rows) / _n  # noqa: E731
    _summary = {
        "profile": V9["profile"],
        "games": _n,
        "mean_score": round(_mean("score"), 2),
        "mean_weight_pct": round(_mean("weight_pct"), 1),
        "mean_actions": round(_mean("actions"), 0),
        "mean_actions_need": round(_mean("actions_need"), 0),
        "mean_actions_per_call": round(_mean("actions_per_call"), 2),
        "mean_tok_per_action": round(_mean("tok_per_action"), 0),
        "mean_tok_per_call": round(_mean("tok_per_call"), 0),
        "depth_budget_used_pct": round(100.0 * _mean("actions") / max(1.0, _mean("actions_need")), 1),
    }
    print("-" * len(_v9_header), flush=True)
    print(f"MEAN game: score={_summary['mean_score']} weight={_summary['mean_weight_pct']}% "
          f"actions={_summary['mean_actions']:.0f}/{_summary['mean_actions_need']:.0f} "
          f"({_summary['depth_budget_used_pct']}% of a full clear) "
          f"a/call={_summary['mean_actions_per_call']} tok/act={_summary['mean_tok_per_action']:.0f}",
          flush=True)

    # Gates. v3 smoke was 29.02 and its LB 26.25; calibration is -2.8..-6.7.
    _gate = "NO-GO (below v3 smoke 29.02)" if _summary["mean_score"] <= 29.02 else "GO (above v3 smoke)"
    print(f"v9 gate: {_gate}", flush=True)
    if PROFILE == "deep" or V9.get("system_prompt_prefix"):
        _delta = _summary["mean_actions_per_call"] - 4.36
        print(f"v9 lever: actions/call {_summary['mean_actions_per_call']} vs r019 4.36 "
              f"({_delta:+.2f}); lever {'WORKS' if _delta > 0.5 else 'DID NOT MOVE'}",
              flush=True)
    try:
        (WORKING_DIR / "v9_metrics.json").write_text(
            _v9_json.dumps({"summary": _summary, "v9": V9, "games": _v9_rows}, indent=1)
        )
        print("v9 metrics -> /kaggle/working/v9_metrics.json", flush=True)
    except Exception as _v9_exc:
        print(f"v9 metrics not written: {_v9_exc!r}", flush=True)
'''


def lines_of(text: str) -> list[str]:
    out = text.split("\n")
    return [line + "\n" for line in out[:-1]] + ([out[-1]] if out[-1] else [])


def find_cell(cells: list[dict], needle: str, *, required: bool = True) -> int:
    for i, cell in enumerate(cells):
        if needle in "".join(cell.get("source", [])):
            return i
    if required:
        raise SystemExit(f"marker not found in base notebook: {needle!r}")
    return -1


def replace_once(src: str, old: str, new: str, *, where: str) -> str:
    if src.count(old) != 1:
        raise SystemExit(f"expected exactly one {old!r} in {where}, found {src.count(old)}")
    return src.replace(old, new)


def build(base: Path, out: Path) -> dict:
    nb = json.loads(base.read_text())
    cells = nb["cells"]
    if len(cells) != MARK_BASE_CELLS:
        raise SystemExit(f"base has {len(cells)} cells, expected {MARK_BASE_CELLS}")

    # 1. profile cell, right after the title markdown
    profile_cell = {
        "cell_type": "code",
        "execution_count": None,
        "id": "v9-profile",
        "metadata": {"tags": ["v9"]},
        "outputs": [],
        "source": lines_of(V9_CELL),
    }
    cells.insert(1, profile_cell)

    # 2. wire the analyzer env through V9
    i9 = find_cell(cells, "LOCAL_ANALYZER_MODEL_ID")
    src = "".join(cells[i9]["source"])
    src = replace_once(
        src,
        "'LOCAL_ANALYZER_MAX_OUTPUT': 12*1024,",
        "'LOCAL_ANALYZER_MAX_OUTPUT': V9[\"max_output_tokens\"],",
        where="cell 9 (analyzer config)",
    )
    src = replace_once(
        src,
        "'INFERENCE_ANALYZER_MODEL': SERVED_MODEL_NAME,",
        "'INFERENCE_ANALYZER_MODEL': SERVED_MODEL_NAME,\n"
        "    # v9: optional prefix, the harness prepends it verbatim to the system prompt\n"
        "    'ARC3_SYSTEM_PROMPT_PREFIX': V9[\"system_prompt_prefix\"],",
        where="cell 9 (analyzer config)",
    )
    src = replace_once(
        src,
        "'ARC3_MAX_ACTIVE_STREAMS': 10,",
        "'ARC3_MAX_ACTIVE_STREAMS': V9[\"streams\"],",
        where="cell 9 (scheduler)",
    )
    src = replace_once(
        src,
        "os.environ[\"ONLY_RESET_LEVELS\"] = \"true\"",
        "os.environ[\"ONLY_RESET_LEVELS\"] = \"true\"\n"
        "# v9: launcher knobs (cell 5 reads these); unset would keep Franzen's 10/136k\n"
        "os.environ[\"V9_MAXREQ\"] = str(V9[\"maxreq\"])\n"
        "os.environ[\"V9_CTX\"] = str(V9[\"ctx\"])",
        where="cell 9 (env block)",
    )
    cells[i9]["source"] = lines_of(src)

    # 3. launcher knobs
    i17 = find_cell(cells, "MAXREQ=10,")
    src = "".join(cells[i17]["source"])
    src = replace_once(src, "MAXREQ=10,", 'MAXREQ=int(os.environ.get("V9_MAXREQ", 10)),', where="cell 17 (launcher)")
    src = replace_once(
        src, "CTX=(116+12+8)*1024,", 'CTX=int(os.environ.get("V9_CTX", (116 + 12 + 8) * 1024)),', where="cell 17 (launcher)"
    )
    src = replace_once(
        src, "CUDAGRAPH_MAXBS=10,", 'CUDAGRAPH_MAXBS=max(10, int(os.environ.get("V9_MAXREQ", 10))),', where="cell 17 (launcher)"
    )
    cells[i17]["source"] = lines_of(src)

    # 4. metering cell at the very end
    cells.append(
        {
            "cell_type": "code",
            "execution_count": None,
            "id": "v9-metering",
            "metadata": {"tags": ["v9"]},
            "outputs": [],
            "source": lines_of(METER_CELL),
        }
    )

    # title markdown: say what this notebook is
    md = "".join(cells[0]["source"])
    banner = (
        "# ARC3 Duck — variant `v9`\n\n"
        "> Built from `duck-c45` (accepted 24.10) by `tools/build_v9.py`.\n"
        "> Differences: the `V9` profile cell, three env values routed through it,\n"
        "> overridable sglang `MAXREQ`/`CTX`, and a read-only metering cell at the end.\n"
        "> The 498 KB harness patch and the three extra patches are untouched.\n\n"
    )
    cells[0]["source"] = lines_of(banner + md)

    out.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
    return {
        "cells": len(cells),
        "bytes": out.stat().st_size,
        "patched_analyzer_cell": i9,
        "patched_launcher_cell": i17,
    }


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=str(root / "src" / "base-c45.ipynb"))
    ap.add_argument("--out", default=str(root / "arc3-duck-v9.ipynb"))
    args = ap.parse_args()
    info = build(Path(args.base), Path(args.out))
    print(json.dumps(info, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
