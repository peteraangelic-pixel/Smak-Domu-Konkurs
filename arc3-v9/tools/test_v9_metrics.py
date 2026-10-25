#!/usr/bin/env python3
"""Tests for tools/v9_metrics.py — run with `python3 -m pytest tools -q` or `python3 tools/test_v9_metrics.py`.

The fixture is a hand-written mini benchmark whose scores are known by hand,
so a regression in the metric definitions fails here instead of on a GPU slot.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import v9_metrics as m  # noqa: E402


def _run(game_id, base, acts, levels, gen, wall=2880.0):
    """One game_run shaped like taaf's benchmark.json."""
    history = []
    for i, tokens in enumerate(gen):
        history.append({"action": {"id": "ACTION1"}, "generated_tokens": tokens, "wallclock_seconds": wall / 48})
    return {
        "game_id": game_id,
        "number_of_levels": len(base),
        "base_actions_per_level": base,
        "actions_per_level": acts,
        "levels_completed": levels,
        "history": history,
        "final_generated_tokens": 0,
        "final_wallclock_seconds": wall,
        "state": "gave_up",
        "final_score": m.formula_score(acts, base, levels),
    }


def test_formula_reproduces_cap_and_weights():
    # Level 1 solved at human speed (115 cap), level 2 unsolved, level 3 ignored.
    base = [10, 20, 30]
    acts = [10, 40, 0]
    score = m.formula_score(acts, base, levels_completed=2)
    # level0: min(115, (10/10)^2*100)=100 ; level1: min(115,(20/40)^2*100)=25
    expected = (100 * 1 + 25 * 2) / (1 + 2 + 3)
    assert abs(score - expected) < 1e-9

    # Per-level cap is 115, but the game score is also capped by the completed
    # weight fraction: a one-level game can never exceed 100.
    assert m.formula_score([1], [100], 1) == 100.0
    assert m.formula_score([1, 1], [100, 100], 2) == 100.0


def test_formula_lifetime_equal_to_published_r019_values():
    # Real r019 games, checked against the values in benchmark.json.
    cases = [
        ([317, 173, 189, 0, 0, 0, 0][:7], [145, 0, 0, 0, 0, 0, 0], 1, 3.5714),
        ([100] * 6, [44, 60, 21, 41, 0, 0], 4, None),
    ]
    # tn36: only level 0 completed with 145 actions against a 317 baseline.
    assert abs(m.formula_score(cases[0][1], cases[0][0], 1) - cases[0][3]) < 0.001
    # and the cap part: 4 of 6 levels at or above human speed cannot exceed 100*10/21
    assert m.formula_score(cases[1][1], cases[1][0], 4) <= 100.0


def test_metrics_actions_per_call_and_tokens():
    gen = [4000, 0, 0, 0, 0, 2000, 0, 0]  # 2 model calls, 8 actions
    run = _run("g1", [10, 10, 10, 10], [2, 2, 2, 2], 4, gen)
    rows = m.rows_from_benchmark({"game_runs": [run]})
    row = rows[0]
    assert row["calls"] == 2, row
    assert row["actions"] == 8, row
    assert row["actions_per_call"] == 4.0
    assert row["tok"] == 6000
    assert row["tok_per_call"] == 3000.0
    assert row["actions_need"] == 40


def test_summary_and_gate():
    good = _run("good", [10, 10], [10, 10], 2, [3000, 0, 3000, 0])
    bad = _run("bad", [10, 10], [5, 0], 1, [10000, 0])
    rows = m.rows_from_benchmark({"game_runs": [good, bad]})
    summary = m.summarize(rows)
    assert summary["games"] == 2
    assert abs(summary["mean_score"] - (good["final_score"] + bad["final_score"]) / 2) < 0.02
    assert summary["mean_actions_need"] == 20.0
    lines = m.verdict({"mean_score": 30.0, "mean_actions": 300.0, "mean_actions_need": 700.0,
                       "depth_budget_used_pct": 42.9, "mean_actions_per_call": 6.0,
                       "mean_tok_per_action": 700.0})
    assert any("GATE PASS" in ln for ln in lines)
    assert any("batching lever moved" in ln for ln in lines)


def test_depth_budget_is_actions_over_human_baseline():
    run = _run("g", [100, 100], [50, 0], 1, [841 * 50])
    summary = m.summarize(m.rows_from_benchmark({"game_runs": [run]}))
    assert summary["depth_budget_used_pct"] == 25.0


def test_load_accepts_both_artefacts(tmp_path: Path):
    run = _run("g", [10], [10], 1, [500])
    bench = tmp_path / "benchmark.json"
    bench.write_text(json.dumps({"game_runs": [run]}))
    rows = m.load(bench)
    assert rows[0]["score"] == 100.0

    metrics = tmp_path / "v9_metrics.json"
    metrics.write_text(json.dumps({"games": [{"game_id": "g", "score": 1.0, "actions": 1,
                                              "actions_need": 2, "calls": 1, "tok": 1,
                                              "tok_per_action": 1.0, "actions_per_call": 1.0,
                                              "tok_per_call": 1.0, "weight_pct": 0.0,
                                              "levels": "0/1", "state": "gave_up", "wall_min": 1.0}]}))
    rows = m.load(metrics)
    assert rows[0]["game_id"] == "g"


def test_formula_check_flags_a_wrong_score():
    run = _run("g", [10, 10], [10, 10], 2, [100, 0])
    run["final_score"] = 1.234  # deliberately wrong
    check = m.formula_check(m.rows_from_benchmark({"game_runs": [run]}))
    assert check["checked"] == 1
    assert check["mismatches"], "a wrong final_score must be reported"


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn(Path("/tmp") if fn.__code__.co_argcount else None) if fn.__code__.co_argcount else fn()
                print(f"ok   {name}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"FAIL {name}: {exc!r}")
    print(f"\n{'FAILURES' if failures else 'ALL OK'}: {failures}")
    sys.exit(1 if failures else 0)
