#!/usr/bin/env python3
"""Build an ENV-ONLY variant of `arc3-duck-v11.ipynb`.

Why this exists
---------------
The L1 "abandon" lever is NOT a new patch. Patch 0004 already implements
ABANDON, gated by three env vars:

    ARC3_LEVEL_TOKEN_CAP   cap=0 -> the whole patch is inert (peek/step KEEP_GOING)
    ARC3_LEVEL_RESETS_MAX  free RESETs per level before ABANDON
    ARC3_LEVEL_MIN_DONE    never ABANDON below this many completed levels

The control package runs cap=45000, resets=1, min_done=0: at 45k it issues a
free RESET, at 90k it ABANDONs. This script flips ONLY ARC3_VARIANT["env"] and
asserts that every other cell -- including all five patch-writer cells -- is
byte-identical to the control notebook, so the 5/5 patch chain cannot drift.

Profiles
--------
abandon : cap=60000, resets=0, min_done=0
          No free reset; ABANDON a game once one level ate 60k tokens.
          This is the first package where the v7-abandon hypothesis can fire:
          the old 0003 patch was a no-op (per-step token baseline), and 0004
          replaced it. ARC3_ABANDON_TOKENS is a dead variable in this tree.
nocap   : cap=0 (patch 0004 fully inert: no cap, no reset, no abandon)
          The subtraction recommended by the other AI, as a one-variable A/B
          against the control package.

Usage
-----
    python tools/build_env_variant.py --profile abandon
    python tools/build_env_variant.py --profile nocap
"""
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
CONTROL_NB = PKG / "arc3-duck-v11.ipynb"
CONTROL_META = PKG / "kernel-metadata.json"

PROFILES = {
    # Single policy change against v11. Quality must be measured separately;
    # actions per request alone cannot establish an improvement.
    "hint": {
        "ARC3_OPENER_COMMIT_HINT": "1",
    },
    "abandon": {
        "ARC3_LEVEL_TOKEN_CAP": "60000",
        "ARC3_LEVEL_RESETS_MAX": "0",
        "ARC3_LEVEL_MIN_DONE": "0",
    },
    "nocap": {
        "ARC3_LEVEL_TOKEN_CAP": "0",
        "ARC3_LEVEL_RESETS_MAX": "0",
        "ARC3_LEVEL_MIN_DONE": "0",
    },
    # Measured on r085: max completed-level cost is 88,114 (g50t L1), so 90k
    # preserves every observed completed level while removing all 9 resets.
    # ABANDON only fires at 180k (after the one free reset) - a real guard,
    # never reached on the smoke trace.
    "cap90": {
        "ARC3_LEVEL_TOKEN_CAP": "90000",
        "ARC3_LEVEL_RESETS_MAX": "1",
        "ARC3_LEVEL_MIN_DONE": "0",
    },
}


def cell_source(cell: dict) -> str:
    src = cell.get("source", [])
    return "".join(src) if isinstance(src, list) else src


def find_variant_cell(cells: list[dict]) -> int:
    hits = [i for i, c in enumerate(cells) if re.search(r"^ARC3_VARIANT = ", cell_source(c), re.M)]
    if len(hits) != 1:
        raise SystemExit(f"expected exactly one ARC3_VARIANT cell, got {hits}")
    return hits[0]


def parse_variant(src: str) -> tuple[dict, re.Match]:
    m = re.search(r"^ARC3_VARIANT = (\{.*\})$", src, re.M)
    if not m:
        raise SystemExit("ARC3_VARIANT assignment is not a single-line dict literal")
    return ast.literal_eval(m.group(1)), m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True, choices=sorted(PROFILES))
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    profile = args.profile
    out_dir = Path(args.out) if args.out else PKG.parent / f"duck-v11-c45-{profile}"
    out_nb = out_dir / f"arc3-duck-v11-c45-{profile}.ipynb"

    nb = json.loads(CONTROL_NB.read_text(encoding="utf-8"))
    cells = nb["cells"]
    control_cells = [cell_source(c) for c in cells]

    variant_idx = find_variant_cell(cells)
    variant, match = parse_variant(control_cells[variant_idx])

    expected_env = dict(variant.get("env", {}))
    expected_env.update(PROFILES[profile])
    variant["env"] = expected_env
    variant["name"] = f"v11-c45-{profile}"

    src = control_cells[variant_idx]
    src = src[: match.start(1)] + json.dumps(variant, sort_keys=True) + src[match.end(1):]
    cells[variant_idx]["source"] = src.splitlines(keepends=True)

    # Human-readable provenance on the markdown cell. Cell count stays 33.
    note = f"""

## This package: env-only variant `{profile}`

This notebook is byte-identical to `arc3-duck-v11.ipynb` except for
`ARC3_VARIANT["env"]` in the preflight cell and this note. No new patch was
added; all five patch-writer cells are unchanged.

| env | control (c45) | this package |
|---|---|---|
| `ARC3_LEVEL_TOKEN_CAP` | 45000 | {expected_env['ARC3_LEVEL_TOKEN_CAP']} |
| `ARC3_LEVEL_RESETS_MAX` | 1 | {expected_env['ARC3_LEVEL_RESETS_MAX']} |
| `ARC3_LEVEL_MIN_DONE` | 0 | {expected_env['ARC3_LEVEL_MIN_DONE']} |
| `ARC3_OPENER_COMMIT_HINT` | unset (off) | {expected_env.get('ARC3_OPENER_COMMIT_HINT', 'unset (off)')} |

Patch 0004 semantics (`inference/framework/arc3_level_budget.py`):

- `cap=0` disables the **whole** patch (peek and step return KEEP_GOING), so
  `ARC3_LEVEL_TOKEN_CAP=0` also disables RESET_LEVEL and ABANDON.
- `resets=0` means no free RESET is ever issued: the first exhaustion is ABANDON.
- `min_done=0` means even a game with 0 completed levels can be abandoned.

`ARC3_ABANDON_TOKENS` / `ARC3_ABANDON_MIN_LEVELS` are **dead variables** in this
tree: they belong to patch 0003, which 0004 replaced (and which never applied
after `harness-changes.patch`). They are kept at 0 for provenance only.
"""
    cells[0]["source"] = (control_cells[0].rstrip() + note).splitlines(keepends=True)

    # Hard guarantee: only the markdown cell and the variant cell may differ.
    for i, (c, before) in enumerate(zip(cells, control_cells)):
        if i in (0, variant_idx):
            continue
        if cell_source(c) != before:
            raise SystemExit(f"cell {i} drifted; refusing to write a package with a changed patch chain")

    out_dir.mkdir(parents=True, exist_ok=True)
    out_nb.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    meta = json.loads(CONTROL_META.read_text(encoding="utf-8"))
    slug = f"arc3-duck-v11-c45-{profile}"
    meta["id"] = f"petersharps/{slug}"
    meta["title"] = slug
    meta["code_file"] = out_nb.name
    (out_dir / "kernel-metadata.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )

    (out_dir / "VARIANT.json").write_text(
        json.dumps(
            {
                "profile": profile,
                "base": CONTROL_NB.name,
                "name": variant["name"],
                "env": expected_env,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"built {out_nb} ({len(cells)} cells, {out_nb.stat().st_size} bytes)")
    print(f"profile={profile} env={json.dumps(PROFILES[profile], sort_keys=True)}")
    print("patch cells unchanged: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
