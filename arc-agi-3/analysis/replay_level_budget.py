#!/usr/bin/env python3
"""Replay patch-0004 LevelBudget on a real Duck benchmark trace.

Why: the +5-7 "early abandon" estimate was a simulation on assumptions. The
r085 smoke trace has one history entry per action with marginal
generated_tokens and actions_per_level, so the budget's decisions can be
replayed on observed behaviour. The control config (cap=45k, resets=1) is
validated against the RESET actions that actually appear in the trace; the
predicted budget reset matches an actual reset within 0-4 actions.

This is a counterfactual on the observed token sequence, not a re-run: it
measures the COST side of abandon (games cut, levels lost, tokens saved). It
cannot measure the BENEFIT side in a 110-game queue (the smoke has 10 games =
10 slots, so there is no queue to reallocate to).

Usage:
  python analysis/replay_level_budget.py --cap 60000 --resets 0 --min-done 0
  python analysis/replay_level_budget.py --sweep
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTROL_NB = ROOT / "duck-v11-c45" / "arc3-duck-v11.ipynb"
DEFAULT_BENCH = (ROOT / "kaggle" / "ops" / "results" / "r085-kernel_output_pick"
                 / "output-pick" / "benchmark.json")

sys.path.insert(0, str(ROOT / "duck-v11-c45" / "tools"))
from verify_v11 import extract_patches  # noqa: E402
from verify_env_variant import budget_source  # noqa: E402


def load_budget():
    nb = json.loads(CONTROL_NB.read_text(encoding="utf-8"))
    cells = ["".join(c.get("source", [])) for c in nb["cells"]]
    ns: dict = {}
    exec(compile(budget_source(extract_patches(cells)), "<arc3_level_budget>", "exec"), ns)
    return ns


NS = load_budget()
LB = NS["LevelBudget"]
KEEP, RESET, ABANDON = NS["KEEP_GOING"], NS["RESET_LEVEL"], NS["ABANDON"]


def bounds(actions_per_level: list[int], levels: int) -> list[int]:
    out, acc = [], 0
    for a in actions_per_level[:levels]:
        acc += int(a)
        out.append(acc)
    return out


def load_rows(bench: Path) -> list[dict]:
    d = json.loads(bench.read_text(encoding="utf-8"))
    rows = []
    for r in d["game_runs"]:
        h = r.get("history") or []
        rows.append({
            "gid": r["game_id"],
            "lv": int(r.get("levels_completed", 0)),
            "h": h,
            "ap": r.get("actions_per_level", []),
            "total": sum(int(x.get("generated_tokens", 0) or 0) for x in h),
        })
    return rows


def replay(row: dict, cap: int, resets: int, min_done: int) -> dict:
    h, lv, ap = row["h"], row["lv"], row["ap"]
    b = bounds(ap, lv)
    lb = LB(cap, resets, min_done)
    cum = 0
    resets_at = []
    for i, hh in enumerate(h):
        lvl = sum(1 for x in b if x <= i)
        before = lb.describe()
        d = lb.step(cum, lvl)
        if d == RESET:
            resets_at.append(i)
        if d == ABANDON:
            return {"decision": ABANDON, "at": i, "level": lvl, "cum": cum,
                    "resets_at": resets_at, "before": before}
        cum += int(hh.get("generated_tokens", 0) or 0)
    return {"decision": KEEP, "at": len(h), "level": lv, "cum": cum,
            "resets_at": resets_at, "before": lb.describe()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", default=str(DEFAULT_BENCH))
    ap.add_argument("--cap", type=int, default=45000)
    ap.add_argument("--resets", type=int, default=1)
    ap.add_argument("--min-done", type=int, default=0)
    ap.add_argument("--sweep", action="store_true")
    args = ap.parse_args()

    rows = load_rows(Path(args.bench))
    total_tokens = sum(r["total"] for r in rows)
    total_levels = sum(r["lv"] for r in rows)
    print(f"{len(rows)} games, {total_levels} levels, {total_tokens:,} generated tokens")

    if args.sweep:
        print(f"\n{'cap':>7} {'r':>2} {'md':>3} {'cut':>4} {'lost':>5} {'resets':>7} {'saved':>10} games")
        for resets in (0, 1):
            for min_done in (0, 1):
                for cap in (45000, 60000, 75000, 88114, 90000, 105000):
                    cut = lost = saved = nres = 0
                    names = []
                    for row in rows:
                        out = replay(row, cap, resets, min_done)
                        nres += len(out["resets_at"])
                        if out["decision"] == ABANDON:
                            cut += 1
                            lost += row["lv"] - out["level"]
                            saved += row["total"] - out["cum"]
                            names.append(f"{row['gid'].split('-')[0]}:{row['lv']}->{out['level']}")
                    print(f"{cap:>7} {resets:>2} {min_done:>3} {cut:>4} {lost:>5} {nres:>7} "
                          f"{saved:>10,} {' '.join(names)}")
        return 0

    print(f"\nconfig cap={args.cap} resets={args.resets} min_done={args.min_done}")
    print(f"{'game':<20} {'lvl':>3} {'tok':>8} {'decision':>9} {'at':>5} {'lvl@':>5} {'resets':>7}")
    for row in rows:
        out = replay(row, args.cap, args.resets, args.min_done)
        print(f"{row['gid']:<20} {row['lv']:>3} {row['total']:>8,} {out['decision']:>9} "
              f"{out['at']:>5} {out['level']:>5} {len(out['resets_at']):>7}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
