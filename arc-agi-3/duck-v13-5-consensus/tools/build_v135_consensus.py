#!/usr/bin/env python3
"""Build `arc3-duck-v13.ipynb` (v13.5-consensus) from the BUILT v13.4-unified notebook.

v13.5-consensus = v13.4-unified + the 08:00-08:12 UTC round from the other
branches, folded in as INCREMENTAL cell edits (no re-application of v13.4
transforms — the input is the already-built notebook):

  1. Variant name -> v13-5-consensus (env unchanged).
  2. Switch cell: version print v13.5-consensus + a comment recording the
     consensus facts: in submission the engine HIDES baselines (a450
     8d96c68, checked on r033) -> patch 0008's relative trigger degrades to
     absolute 20 + cap 2 = 42 injections on r085 (2.9% pool; @10 was
     154/15.3%); Gemma measures 20, 7911 argues 30-60 — cap 2 bounds both;
     corrected metric (7911, 30/30): score <= 100 x weighted coverage.
  3. extra-05 writer comment rebrand.
  4. Budget probe cell: labels v13.4 -> v13.5.
  5. Roster probe cell: labels v13.4 -> v13.5 AND extends the per-run
     record with `baseline` (hidden/present/missing — resolves 7911's
     "czy wypelnione w rerunie = sonda, nie zalozenie") and `coverage_pct`
     (weighted coverage; score <= 100 x coverage), plus summary verdicts.

Usage:
  python3 tools/build_v135_consensus.py \
      [--prev ../duck-v13-4-unified/arc3-duck-v13.ipynb] [--out arc3-duck-v13.ipynb]
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
MARK_V134_CELLS = 39  # built v13.4-unified has exactly 39 cells


def cell_source(cell: dict) -> str:
    return "".join(cell.get("source", []))


def set_source(cell: dict, text: str) -> None:
    cell["source"] = text.splitlines(keepends=True)


V135_NOTE = """# v13.5-consensus (08:00-08:12 UTC round): in submission the engine HIDES
# baselines (a450 8d96c68 on r033) -> patch 0008's relative trigger degrades
# to absolute 20 + cap 2 = 42 injections on r085 (2.9% pool; @10 was 154,
# 15.3%). Gemma measures 20; 7911 argues 30-60 -> cap 2 bounds both; the
# printed escalate= value verifies it from the rerun log. Corrected metric
# (7911 724189b, 30/30 saved scores): score <= 100 x weighted coverage ->
# the roster probe now logs coverage + the baseline visibility verdict.
"""


def rebranded_budget(src: str) -> str:
    src = src.replace("v13.4 budget probe", "v13.5 budget probe")
    src = src.replace("v13.4 budget:", "v13.5 budget:")
    src = src.replace("v13.4 budget probe skipped", "v13.5 budget probe skipped")
    return src


def rebranded_roster(src: str) -> str:
    src = src.replace("v13.4 roster probe", "v13.5 roster probe")
    src = src.replace("v13.4 roster:", "v13.5 roster:")
    src = src.replace("v13.4 roster probe skipped", "v13.5 roster probe skipped")
    return src


def extended_roster(src: str) -> str:
    """Add baseline visibility + weighted coverage to the per-run record and
    the summary verdicts (read-only, post-run, all inside the existing try)."""
    old_recs = """        _calls = sum(1 for _h in _hist if int(getattr(_h, "generated_tokens", 0) or 0) > 0)
        _acts = sum(int(_x or 0) for _x in (getattr(_r, "actions_per_level", []) or []))
        _v14_recs.append({
            "index": _i,"""
    new_recs = """        _calls = sum(1 for _h in _hist if int(getattr(_h, "generated_tokens", 0) or 0) > 0)
        _acts = sum(int(_x or 0) for _x in (getattr(_r, "actions_per_level", []) or []))
        _ba = getattr(_r, "base_actions_per_level", "brak-atrybutu")
        _nlv = int(getattr(_r, "number_of_levels", 0) or 0)
        _clv = int(getattr(_r, "levels_completed", 0) or 0)
        _cov = round(100.0 * (_clv * (_clv + 1)) / (_nlv * (_nlv + 1)), 1) if _nlv else 0.0
        _v14_recs.append({
            "index": _i,
            "baseline": None if _ba == "brak-atrybutu" else ("hidden" if _ba is None else len(_ba)),
            "coverage_pct": _cov,"""
    assert src.count(old_recs) == 1, "roster recs anchor"
    src = src.replace(old_recs, new_recs, 1)

    old_sum = """            "mean_wall_min": round(sum(_r["wall_min"] for _r in _v14_recs) / len(_v14_recs), 1),
        }
        print("v13.5 roster: " + _v14_json.dumps(_summary, sort_keys=True), flush=True)"""
    new_sum = """            "mean_wall_min": round(sum(_r["wall_min"] for _r in _v14_recs) / len(_v14_recs), 1),
            "mean_coverage_pct": round(sum(_r["coverage_pct"] for _r in _v14_recs) / len(_v14_recs), 1),
            "baselines_hidden": sum(1 for _r in _v14_recs if _r["baseline"] == "hidden"),
            "baselines_present": sum(1 for _r in _v14_recs if isinstance(_r["baseline"], int)),
        }
        print("v13.5 roster: " + _v14_json.dumps(_summary, sort_keys=True), flush=True)
        if _summary["mean_coverage_pct"]:
            print(f"v13.5 roster: srednie wazone pokrycie {_summary['mean_coverage_pct']}% "
                  f"-> sufit wyniku ~{_summary['mean_coverage_pct']:.0f} pkt "
                  f"(score <= 100 x pokrycie, regula 30/30)", flush=True)
        if _summary["baselines_hidden"] and not _summary["baselines_present"]:
            print("v13.5 roster: baseline UKRYTY w submisji -> prog wzgledny nieaktywny "
                  "(w rerunie dziala absolutna 20 + cap 2)", flush=True)
        elif _summary["baselines_present"]:
            print(f"v13.5 roster: baseline widoczny w {_summary['baselines_present']} runach "
                  f"-> prog wzgledny ZYWY", flush=True)"""
    assert src.count(old_sum) == 1, "roster summary anchor"
    src = src.replace(old_sum, new_sum, 1)
    return src


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prev", default=str(PKG.parent / "duck-v13-4-unified" / "arc3-duck-v13.ipynb"))
    ap.add_argument("--out", default=str(PKG / "arc3-duck-v13.ipynb"))
    args = ap.parse_args()

    nb = json.loads(Path(args.prev).read_text())
    cells = nb["cells"]
    assert len(cells) == MARK_V134_CELLS, f"prev has {len(cells)} cells, expected {MARK_V134_CELLS}"

    # 1. ARC3_VARIANT cell: name only (env unchanged).
    variant_idx = next(i for i, c in enumerate(cells) if "ARC3_VARIANT" in cell_source(c))
    src = cell_source(cells[variant_idx])
    m = re.search(r"ARC3_VARIANT = (\{.*\})$", src, flags=re.M)
    assert m, "ARC3_VARIANT literal not found"
    variant = json.loads(m.group(1))
    assert variant["env"].get("ARC3_ESCALATE_RELATIVE") == "1"
    assert variant["env"].get("ARC3_OPENER_COMMIT_HINT") == "1"
    assert "/kaggle/duck-extra-06.patch" in variant["patch_files"]
    variant["name"] = "v13-5-consensus"
    src = src[:m.start(1)] + json.dumps(variant) + src[m.end(1):]
    set_source(cells[variant_idx], src)

    # 2. Switch cell: consensus note + version print.
    switch_idx = next(i for i, c in enumerate(cells) if "v13 switch" in cell_source(c))
    src = cell_source(cells[switch_idx])
    assert re.search(r"^ESCALATE_ACTIONS = 20$", src, flags=re.M), "v13.4 ships 20"
    tail_anchor = "# ARC3_ESCALATE_MAX_PER_LEVEL, default 2 in variant), guarded roster-probe hook\n"
    assert src.count(tail_anchor) == 1, "v134 comment tail anchor"
    src = src.replace(tail_anchor, tail_anchor + V135_NOTE, 1)
    src, n = re.subn(r"v13\.4-unified profile", "v13.5-consensus profile", src, count=1)
    assert n == 1, "switch print anchor"
    set_source(cells[switch_idx], src)

    # 3. extra-05 writer comment rebrand.
    w5_idx = next(i for i, c in enumerate(cells)
                  if "duck-extra-05.patch" in cell_source(c) and "write_text" in cell_source(c))
    src = cell_source(cells[w5_idx])
    src, n = re.subn(r"ARC3 Duck v13\.4-unified: patch 0007", "ARC3 Duck v13.5-consensus: patch 0007",
                     src, count=1)
    assert n == 1, "extra-05 comment rebrand"
    set_source(cells[w5_idx], src)

    # 4. Budget probe cell: labels only.
    b_idx = next(i for i, c in enumerate(cells) if "v13.4 budget probe" in cell_source(c))
    set_source(cells[b_idx], rebranded_budget(cell_source(cells[b_idx])))

    # 5. Roster probe cell: labels + baseline/coverage extension.
    r_idx = next(i for i, c in enumerate(cells) if "v13.4 roster probe" in cell_source(c))
    src = rebranded_roster(cell_source(cells[r_idx]))
    set_source(cells[r_idx], extended_roster(src))

    out = Path(args.out)
    out.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")
    print(f"built {out} ({len(cells)} cells, {out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
