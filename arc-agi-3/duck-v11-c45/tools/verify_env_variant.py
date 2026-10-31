#!/usr/bin/env python3
"""Verify an env-only variant against the control package.

Checks (no GPU, no Kaggle, no r033 bundle):
  1. notebook parses, 33 cells, every code cell compiles;
  2. every cell except the markdown header (0) and the ARC3_VARIANT cell is
     byte-identical to the control -> the 5/5 patch chain cannot have drifted;
  3. ARC3_VARIANT["env"] equals VARIANT.json exactly;
  4. PLAN_COMMIT="0" and TRUE_CONCURRENCY=10 (same control path as slot A);
  5. metadata id/title/code_file match the package; sources match the control;
  6. the LevelBudget state machine extracted from patch 0004 behaves exactly as
     the three env configs claim. This is the real test of the lever: it runs
     the module source that ships in the patch, not a re-implementation.

Usage:
    python tools/verify_env_variant.py --pkg ../duck-v11-c45-abandon
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from verify_v11 import extract_patches  # noqa: E402

PKG = HERE.parent
CONTROL_NB = PKG / "arc3-duck-v11.ipynb"
CONTROL_META = PKG / "kernel-metadata.json"

FAIL: list[str] = []


def check(name: str, ok: bool, detail: object = "") -> None:
    print(("OK   " if ok else "FAIL ") + name + ("" if ok else f"  {detail}"))
    if not ok:
        FAIL.append(name)


def cells_of(nb: dict) -> list[str]:
    return ["".join(c.get("source", [])) for c in nb.get("cells", [])]


def variant_cell_index(cells: list[str]) -> int:
    hits = [i for i, s in enumerate(cells) if re.search(r"^ARC3_VARIANT = ", s, re.M)]
    if len(hits) != 1:
        raise SystemExit(f"expected one ARC3_VARIANT cell, got {hits}")
    return hits[0]


def budget_source(patches: dict[str, str]) -> str:
    """Extract arc3_level_budget.py verbatim from the 0004 patch."""
    patch = patches["duck-extra-02.patch"]
    m = re.search(
        r"diff --git a/[^\n]*arc3_level_budget\.py.*?(?=\ndiff --git |\Z)",
        patch,
        re.S,
    )
    if not m:
        raise SystemExit("arc3_level_budget.py section not found in duck-extra-02.patch")
    section = m.group(0)
    hunk = section.find("@@")
    if hunk < 0:
        raise SystemExit("no hunk header in arc3_level_budget.py section")
    out = []
    for line in section[hunk:].splitlines()[1:]:
        if line.startswith("+"):
            out.append(line[1:])
    if not out:
        raise SystemExit("empty arc3_level_budget.py body")
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pkg", required=True)
    args = ap.parse_args()

    pkg = Path(args.pkg).resolve()
    variant = json.loads((pkg / "VARIANT.json").read_text(encoding="utf-8"))
    nb_path = pkg / f"arc3-duck-v11-c45-{variant['profile']}.ipynb"
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    control = json.loads(CONTROL_NB.read_text(encoding="utf-8"))

    cells = cells_of(nb)
    control_cells = cells_of(control)
    check("notebook parses (33 cells)", len(cells) == 33, len(cells))
    check("control parses (33 cells)", len(control_cells) == 33, len(control_cells))

    bad = []
    compiled = 0
    for i, c in enumerate(nb["cells"]):
        if c.get("cell_type") != "code":
            continue
        s = cells[i]
        if s.lstrip().startswith("%%"):
            continue
        s2 = "\n".join("pass" if ln.lstrip().startswith("!") else ln for ln in s.splitlines())
        try:
            compile(s2, f"<cell {i}>", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
            compiled += 1
        except SyntaxError as exc:
            bad.append(f"{i}: {exc}")
    check(f"code cells compile ({compiled})", not bad, "; ".join(bad))

    vidx = variant_cell_index(cells)
    drifted = [i for i, (a, b) in enumerate(zip(cells, control_cells))
               if i not in (0, vidx) and a != b]
    check("only header + variant cells differ", not drifted, drifted)
    check("same cell count as control", len(cells) == len(control_cells))

    m = re.search(r"^ARC3_VARIANT = (\{.*\})$", cells[vidx], re.M)
    variant_literal = ast.literal_eval(m.group(1)) if m else {}
    check("VARIANT.json env == notebook env",
          variant_literal.get("env") == variant["env"],
          {"notebook": variant_literal.get("env"), "file": variant["env"]})
    check("variant name matches profile",
          variant_literal.get("name") == f"v11-c45-{variant['profile']}",
          variant_literal.get("name"))

    joined = "\n".join(cells)
    check("PLAN_COMMIT=0 (control path)", 'PLAN_COMMIT = "0"' in joined)
    check("TRUE_CONCURRENCY=10", "TRUE_CONCURRENCY = 10" in joined)
    check("concurrency 120 gone", "concurrency = 120" not in joined)
    check("all five patches extracted",
          all(p in extract_patches(cells) for p in
              ["harness-changes.patch", "duck-extra-00.patch", "duck-extra-01.patch",
               "duck-extra-02.patch", "duck-extra-03.patch"]))

    meta = json.loads((pkg / "kernel-metadata.json").read_text(encoding="utf-8"))
    slug = f"arc3-duck-v11-c45-{variant['profile']}"
    check("metadata id/title/code_file",
          meta["id"] == f"petersharps/{slug}" and meta["title"] == slug
          and meta["code_file"] == f"{slug}.ipynb",
          {"id": meta["id"], "title": meta["title"], "code_file": meta["code_file"]})
    control_meta = json.loads(CONTROL_META.read_text(encoding="utf-8"))
    check("sources identical to control",
          all(meta.get(k) == control_meta.get(k) for k in
              ("dataset_sources", "model_sources", "competition_sources", "docker_image",
               "machine_shape", "enable_gpu", "enable_internet")))

    # --- the lever itself: run the module that ships in patch 0004 -------------
    src = budget_source(extract_patches(cells))
    ns: dict = {}
    exec(compile(src, "<arc3_level_budget>", "exec"), ns)
    LB = ns["LevelBudget"]
    KEEP, RESET, ABANDON = ns["KEEP_GOING"], ns["RESET_LEVEL"], ns["ABANDON"]

    # cap=0 must disable the WHOLE patch (the trap the other AI flagged).
    b = LB(0, 0, 0)
    check("cap=0 -> inert (peek)", b.peek(10**9, 0) == KEEP)
    check("cap=0 -> inert (step)", b.step(10**9, 0) == KEEP)

    # control profile: free RESET at 45k, ABANDON at 90k.
    b = LB(45000, 1, 0)
    check("control: RESET at 45k", b.step(45000, 0) == RESET and b.resets_used == 1)
    check("control: no abandon at 89 999", b.peek(89999, 0) == KEEP)
    check("control: ABANDON at 90k", b.step(90000, 0) == ABANDON)

    # abandon profile: no free reset, ABANDON at 60k, even at 0 levels.
    b = LB(60000, 0, 0)
    check("abandon: KEEP at 59 999", b.peek(59999, 0) == KEEP)
    check("abandon: ABANDON at 60k", b.peek(60000, 0) == ABANDON)
    check("abandon: ABANDON at 0 levels", b.step(60000, 0) == ABANDON)

    # completing a level starts a fresh budget (never abandon on progress).
    b = LB(60000, 0, 0)
    check("progress: step(50k, 0) keeps", b.step(50000, 0) == KEEP)
    check("progress: level done keeps", b.step(60000, 1) == KEEP)
    check("progress: fresh budget after level", b.peek(60000, 1) == KEEP)

    # min_done protects low-score games when asked. The completion has to be
    # observed by step() first: a level that just finished starts a fresh
    # budget, so peek(60k, 1) at level_start_levels=0 is KEEP by design.
    b = LB(60000, 0, 1)
    check("min_done=1 protects 0-level game", b.peek(60000, 0) == KEEP)
    check("min_done=1: step observes level 1", b.step(60000, 1) == KEEP)
    check("min_done=1 abandons at 120k on level 2", b.peek(120000, 1) == ABANDON)

    # cap90 profile: RESET at 90k, ABANDON at 180k, and every completed level
    # observed on r085 (max 88,114) stays inside the budget.
    b = LB(90000, 1, 0)
    check("cap90: KEEP at 88 114 (max observed)", b.peek(88114, 0) == KEEP)
    check("cap90: RESET at 90k", b.step(90000, 0) == RESET and b.resets_used == 1)
    check("cap90: KEEP at 179 999", b.peek(179999, 0) == KEEP)
    check("cap90: ABANDON at 180k", b.step(180000, 0) == ABANDON)

    # the package must carry the profile's values, not just any passing config.
    env = variant_literal.get("env", {})
    prof = variant["profile"]
    expected = {
        "hint": ("45000", "1", "0"),
        "abandon": ("60000", "0", "0"),
        "nocap": ("0", "0", "0"),
        "cap90": ("90000", "1", "0"),
    }[prof]
    got = (env.get("ARC3_LEVEL_TOKEN_CAP"), env.get("ARC3_LEVEL_RESETS_MAX"),
           env.get("ARC3_LEVEL_MIN_DONE"))
    check(f"profile {prof} carries cap/resets/min_done", got == expected, got)
    if prof == "hint":
        control_idx = variant_cell_index(control_cells)
        control_match = re.search(r"^ARC3_VARIANT = (\{.*\})$", control_cells[control_idx], re.M)
        control_variant = ast.literal_eval(control_match.group(1))
        expected_variant = dict(control_variant)
        expected_variant["name"] = "v11-c45-hint"
        expected_variant["env"] = dict(control_variant["env"], ARC3_OPENER_COMMIT_HINT="1")
        check("hint: exact single-env delta and provenance name", variant_literal == expected_variant)

    print()
    if FAIL:
        print(f"{len(FAIL)} FAILURES: {FAIL}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
