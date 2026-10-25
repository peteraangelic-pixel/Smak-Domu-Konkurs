#!/usr/bin/env python3
"""v9 metrics: read what a smoke or a rerun actually bought.

Works on either artefact the ops channel already downloads:

  * `benchmark.json` from `op: kernel-output`   (has `game_runs`)
  * `/kaggle/working/v9_metrics.json`           (written by the v9 metering cell)

and prints the six numbers that decide the next slot:

  actions/call      depth bought per model call   (r019: 4.36)
  tok/action        generated tokens per action   (r019: 841)
  actions           engine actions in the game    (r019: 206)
  actions_need      human baseline for every level (r019 mean: 718)
  weight_pct        completed level weight = the score's real numerator
  score             the game score                (r019 mean: 27.21)

It also re-derives every `final_score` from the published formula
(`min(115, (baseline/actions)**2*100)`, weight k+1, capped by completed
weight). If that check ever fails, the harness's score and Kaggle's score
have diverged and no comparison in the docs means anything.

Usage:
  python3 tools/v9_metrics.py ops/results/r019-kernel-output/output/benchmark.json
  python3 tools/v9_metrics.py benchmark.json --json out.json
  python3 tools/v9_metrics.py v9_metrics.json --profile deep
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LEVEL_CAP = 115.0
# The v3 baseline everything is calibrated against: smoke 29.02 -> LB 26.25.
V3_SMOKE = 29.02
R019_ACTIONS_PER_CALL = 4.36
R019_TOK_PER_ACTION = 841.0


def _int(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _float(value) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def rows_from_benchmark(doc: dict) -> list[dict]:
    """One row per game run, from the harness benchmark dump."""
    runs = doc.get("game_runs")
    if not isinstance(runs, list):
        raise SystemExit("benchmark.json without game_runs")
    rows = []
    for run in runs:
        if not isinstance(run, dict):
            continue
        hist = run.get("history") or []
        gen = [_int(h.get("generated_tokens")) for h in hist if isinstance(h, dict)]
        calls = sum(1 for t in gen if t > 0)
        tok = sum(gen) + _int(run.get("final_generated_tokens"))
        actions = sum(_int(x) for x in (run.get("actions_per_level") or []))
        levels = _int(run.get("levels_completed"))
        total = _int(run.get("number_of_levels"))
        base = [_int(x) for x in (run.get("base_actions_per_level") or [])]
        score = run.get("final_score")
        rows.append(
            {
                "game_id": str(run.get("game_id", "?")),
                "state": str(run.get("state", "?")),
                "levels": f"{levels}/{total}",
                "weight_pct": round(100.0 * sum(range(1, levels + 1)) / (sum(range(1, total + 1)) or 1), 1),
                "score": round(_float(score), 2),
                "actions": actions,
                "actions_need": sum(base),
                "calls": calls,
                "tok": tok,
                "tok_per_action": round(tok / actions, 1) if actions else 0.0,
                "actions_per_call": round(actions / calls, 2) if calls else 0.0,
                "tok_per_call": round(tok / calls, 1) if calls else 0.0,
                "wall_min": round(_float(run.get("final_wallclock_seconds")) / 60.0, 1),
                "_raw": run,
            }
        )
    return rows


def rows_from_metrics(doc: dict) -> list[dict]:
    games = doc.get("games")
    if not isinstance(games, list):
        raise SystemExit("v9_metrics.json without games")
    return [dict(g) for g in games if isinstance(g, dict)]


def load(path: Path) -> list[dict]:
    doc = json.loads(path.read_text())
    if isinstance(doc, list):
        return [dict(g) for g in doc if isinstance(g, dict)]
    if "game_runs" in doc:
        return rows_from_benchmark(doc)
    return rows_from_metrics(doc)


def formula_score(actions_per_level, base_actions_per_level, levels_completed) -> float:
    """taaf.game.GameRun._compute_final_score, re-implemented from the docstring."""
    total = len(base_actions_per_level)
    if total == 0:
        return 0.0
    total_score = 0.0
    total_weights = 0
    max_weights = 0
    for idx in range(total):
        weight = idx + 1
        total_weights += weight
        actions = actions_per_level[idx] if idx < len(actions_per_level) else 0
        baseline = base_actions_per_level[idx]
        completed = idx < levels_completed
        if completed and actions > 0:
            level_score = min(LEVEL_CAP, (baseline / actions) ** 2 * 100.0)
        else:
            level_score = 0.0
        if level_score > 0:
            max_weights += weight
        total_score += level_score * weight
    if total_weights == 0:
        return 0.0
    return min(total_score / total_weights, max_weights / total_weights * 100.0)


def formula_check(rows: list[dict]) -> dict:
    """Recompute every score from actions/baseline; report the worst mismatch."""
    checked = 0
    worst = 0.0
    bad = []
    for row in rows:
        raw = row.get("_raw")
        if not raw:
            continue
        base = [_int(x) for x in (raw.get("base_actions_per_level") or [])]
        acts = [_int(x) for x in (raw.get("actions_per_level") or [])]
        if not base:
            continue
        expected = formula_score(acts, base, _int(raw.get("levels_completed")))
        diff = abs(expected - _float(raw.get("final_score")))
        checked += 1
        worst = max(worst, diff)
        if diff > 0.01:
            bad.append((row["game_id"], round(expected, 2), round(_float(raw.get("final_score")), 2)))
    return {"checked": checked, "max_abs_diff": round(worst, 4), "mismatches": bad}


def summarize(rows: list[dict]) -> dict:
    if not rows:
        return {}
    n = len(rows)

    def mean(key: str) -> float:
        return sum(_float(r.get(key)) for r in rows) / n

    actions = mean("actions")
    need = mean("actions_need")
    return {
        "games": n,
        "mean_score": round(mean("score"), 2),
        "mean_weight_pct": round(mean("weight_pct"), 1),
        "mean_actions": round(actions, 1),
        "mean_actions_need": round(need, 1),
        "mean_actions_per_call": round(mean("actions_per_call"), 2),
        "mean_tok_per_action": round(mean("tok_per_action"), 1),
        "mean_tok_per_call": round(mean("tok_per_call"), 1),
        "depth_budget_used_pct": round(100.0 * actions / need, 1) if need else 0.0,
    }


def verdict(summary: dict, actions_per_call_baseline: float = R019_ACTIONS_PER_CALL) -> list[str]:
    """Plain-language read of the summary: what the slot proved."""
    out = []
    if not summary:
        return ["no games in the artefact"]
    score = summary["mean_score"]
    if score > V3_SMOKE:
        out.append(f"GATE PASS: mean score {score} > v3 smoke {V3_SMOKE} (calibrate -2.8..-6.7 to the LB)")
    else:
        out.append(f"GATE FAIL: mean score {score} <= v3 smoke {V3_SMOKE}; do not spend a slot on it")
    used = summary["depth_budget_used_pct"]
    out.append(
        f"depth budget used: {used}% of a full clear ({summary['mean_actions']:.0f} of "
        f"{summary['mean_actions_need']:.0f} actions). Below ~100% the score is depth-limited, not skill-limited."
    )
    apc = summary["mean_actions_per_call"]
    delta = apc - actions_per_call_baseline
    out.append(
        f"actions/call {apc} vs r019 {actions_per_call_baseline} ({delta:+.2f}): "
        + ("the batching lever moved." if delta > 0.5 else "the batching lever did not move.")
    )
    tpa = summary["mean_tok_per_action"]
    out.append(
        f"tok/action {tpa:.0f} vs r019 {R019_TOK_PER_ACTION:.0f}: "
        + ("cheaper per action." if tpa and tpa < R019_TOK_PER_ACTION * 0.9 else "no per-action saving.")
    )
    return out


def render(rows: list[dict], summary: dict, check: dict | None) -> str:
    header = (
        f"{'game':22}{'state':>10}{'levels':>8}{'w%':>6}{'score':>7}{'actions':>8}"
        f"{'need':>6}{'calls':>6}{'a/call':>7}{'tok/act':>8}{'tok/call':>9}{'min':>6}"
    )
    lines = [header, "-" * len(header)]
    for r in rows:
        lines.append(
            f"{str(r.get('game_id', '?'))[:21]:22}{str(r.get('state', '?'))[:9]:>10}"
            f"{str(r.get('levels', '?')):>8}{_float(r.get('weight_pct')):6.1f}"
            f"{_float(r.get('score')):7.2f}{_int(r.get('actions')):8d}"
            f"{_int(r.get('actions_need')):6d}{_int(r.get('calls')):6d}"
            f"{_float(r.get('actions_per_call')):7.2f}{_float(r.get('tok_per_action')):8.0f}"
            f"{_float(r.get('tok_per_call')):9.0f}{_float(r.get('wall_min')):6.0f}"
        )
    lines.append("-" * len(header))
    lines.append(
        f"MEAN: score={summary['mean_score']} weight={summary['mean_weight_pct']}% "
        f"actions={summary['mean_actions']:.0f}/{summary['mean_actions_need']:.0f} "
        f"({summary['depth_budget_used_pct']}%) a/call={summary['mean_actions_per_call']} "
        f"tok/act={summary['mean_tok_per_action']:.0f} tok/call={summary['mean_tok_per_call']:.0f}"
    )
    if check is not None:
        if check["checked"]:
            state = "OK" if not check["mismatches"] else f"MISMATCH {check['mismatches']}"
            lines.append(
                f"formula check: {check['checked']} games recomputed from actions/baseline, "
                f"max |diff|={check['max_abs_diff']} -> {state}"
            )
        else:
            lines.append("formula check: skipped (no raw game_runs in this artefact)")
    lines.extend(verdict(summary))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("artefact", type=Path)
    ap.add_argument("--json", type=Path, default=None, help="write the summary as JSON")
    ap.add_argument("--baseline-actions-per-call", type=float, default=R019_ACTIONS_PER_CALL)
    args = ap.parse_args(argv)

    rows = load(args.artefact)
    summary = summarize(rows)
    check = formula_check(rows) if rows and "_raw" in rows[0] else None
    print(render(rows, summary, check))
    if args.json:
        clean = [{k: v for k, v in r.items() if k != "_raw"} for r in rows]
        args.json.write_text(json.dumps({"summary": summary, "formula_check": check, "games": clean}, indent=1, default=str))
        print(f"\nwritten: {args.json}")
    if summary and summary["mean_score"] <= V3_SMOKE:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
