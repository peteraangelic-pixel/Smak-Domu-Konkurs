#!/usr/bin/env python3
"""Builder: duck-v13-6-final -> duck-v13-7-final.

RULE (v13.5 lesson): the builder of a new version edits ONLY INCREMENTALLY on
top of the PREVIOUS BUILT notebook. v13.7 adds exactly ONE thing: patch 0010
dyn-level-budget (from the "strategia" session handoff, arc-v16-package/patches/
0009-dyn-level-budget.patch — byte-for-byte; THEIR number 0009, OURS 0010 =
duck-extra-08), as a DORMANT lever:

  * touches ONLY ARC3-Inference/inference/framework/arc3_level_budget.py
    (0004 module) — file-disjoint from 0001-0009 (self-pace is tool_agent.py);
  * ARC3_LEVEL_TOKEN_CAP="0" stays => module inert, behaviour IDENTICAL to v13.6
    (dormancy verified by their verify_v16 + our chain run);
  * arming later = ONE value (LEVEL_TOKEN_CAP 0->60000); kill = ARC3_DYN_CAP=0
    => exact static 0004 semantics (A/B control).

Their package verified by us before composition (30.10): 16/16 dyn tests,
verify_v16 ALL LOCAL CHECKS PASSED, pending r033 chain gate CLOSED by us
(9/9 patches clean on r033, tree compiles, 12+6+11 our tests on their tree,
11/11 winpath), src reconstruction == patched bytes (cmp), writer == package
file (cmp).
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
MARK_V136_CELLS = 40

V137_NOTE = """# v13.7-final = v13.6-final + patch 0010 dyn-level-budget (handoff sesji strategii
# 30.10 ~12:00 UTC, arc-v16-package; w ich numeracji 0009). Dotyczy WYŁĄCZNIE
# framework/arc3_level_budget.py (moduł 0004) — plik rozłączny z tool_agent.py,
# zero kolizji z 0001-0009. DORMANT: ARC3_LEVEL_TOKEN_CAP="0" => moduł inertny,
# zachowanie identyczne z v13.6 na submisji. Uzbrojenie (propozycja na 1.11,
# tylko wg GO): jedna wartość LEVEL_TOKEN_CAP 0->60000; wtedy cap poziomu =
# clamp(mediana(koszty ukończonych poziomów gry) x ARC3_DYN_CAP_MULT(4), 45k, 150k),
# drabina RESET x1.5, ABANDON tylko po wyczerpaniu resetów i >=1.5x cap — nigdy
# ostrzejszy od statycznego. Kill: ARC3_DYN_CAP=0 => wierny kontrolny 0004 (A/B).
# UZBROJENIE (korekta po opinii Gemmy 6d081d52, odtworzonej przeze mnie 1:1 na 40
# grach r085/r093/r110/r118): ARC3_LEVEL_TOKEN_CAP 0 -> **20000**, NIE 60000.
# Kod: base = max(static, mediana*4) => dyn NIGDY nie tnie ciaśniej od armingu;
# @60000 dyn aktywny w 16/40 gier (≥2 ukończone), 15 luźniej / 0 ciaśniej,
# mediana capa 128612, a 15 gier palących 100% budżetu (0 ukończonych) — NIE
# dotknięte. @20000: gry z historią mają TE SAME capa (mediana*4 ≥ 46k), a
# marnotrawcy bez historii są cięci na 20k + darmowy RESET (~40k). Ryzyko do
# POMIARU na 1.11: 14 ukończonych poziomów kosztowało >45k (max ~91k) — część
# mogłaby nie ukończyć; metryka ochronna: completed/game przed/po; opcja
# ARC3_LEVEL_MIN_DONE=1 jako OSOBNA następna zmienna.
# Weryfikacja: 16/16 testów dyn na bajtach == wyjściu łańcucha r033 (cmp);
# 10/10 patchy czysty r033; dormancja potwierdzona (verify_v16 + nasz łańcuch).
"""


def cell_source(cell: dict) -> str:
    return "".join(cell.get("source", []))


def set_source(cell: dict, text: str) -> None:
    cell["source"] = text.splitlines(keepends=True)


def replace_once(src: str, old: str, new: str, what: str) -> str:
    assert src.count(old) == 1, f"{what}: anchor {src.count(old)}x, expected exactly 1"
    return src.replace(old, new, 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prev", default=str(PKG.parent / "duck-v13-6-final" / "arc3-duck-v13.ipynb"))
    ap.add_argument("--out", default=str(PKG / "arc3-duck-v13.ipynb"))
    args = ap.parse_args()

    nb = json.loads(Path(args.prev).read_text())
    cells = nb["cells"]
    assert len(cells) == MARK_V136_CELLS, f"prev has {len(cells)} cells, expected {MARK_V136_CELLS}"

    # 1. ARC3_VARIANT: register 0010 + name. Env UNTOUCHED (dormancy by construction).
    variant_idx = next(i for i, c in enumerate(cells) if "ARC3_VARIANT" in cell_source(c))
    src = cell_source(cells[variant_idx])
    m = re.search(r"ARC3_VARIANT = (\{.*\})$", src, flags=re.M)
    assert m, "ARC3_VARIANT literal not found"
    variant = json.loads(m.group(1))
    assert variant["name"] == "v13-6-final", variant["name"]
    assert variant["env"].get("ARC3_LEVEL_TOKEN_CAP") == "0", "dormancy: cap must stay 0"
    assert variant["env"].get("ARC3_ESCALATE_SELF_PACE") == "1"
    assert "/kaggle/duck-extra-07.patch" in variant["patch_files"]
    assert not any("extra-08" in p for p in variant["patch_files"])
    variant["name"] = "v13-7-final"
    variant["patch_files"] = list(variant["patch_files"]) + ["/kaggle/duck-extra-08.patch"]
    variant["patches"] = list(variant["patches"]) + ["0010-dyn-level-budget.patch"]
    src = src[:m.start(1)] + json.dumps(variant) + src[m.end(1):]
    set_source(cells[variant_idx], src)

    # 2. Switch cell: v13.7 note + version print rebrand.
    switch_idx = next(i for i, c in enumerate(cells) if "v13 switch" in cell_source(c))
    src = cell_source(cells[switch_idx])
    tail_anchor = "# escalation debate (7911 cad326c): keep escalating at 20, watch the a/call print.\n"
    assert src.count(tail_anchor) == 1, "v136 note tail anchor"
    src = src.replace(tail_anchor, tail_anchor + V137_NOTE, 1)
    src = replace_once(src, "v13.6-final profile", "v13.7-final profile", "switch print")
    set_source(cells[switch_idx], src)

    # 3. extra-05 writer comment rebrand.
    w5_idx = next(i for i, c in enumerate(cells)
                  if "duck-extra-05.patch" in cell_source(c) and "write_text" in cell_source(c))
    src = cell_source(cells[w5_idx])
    src, n = re.subn(r"ARC3 Duck v13\.6-final: patch 0007", "ARC3 Duck v13.7-final: patch 0007",
                     src, count=1)
    assert n == 1, "extra-05 comment rebrand"
    set_source(cells[w5_idx], src)

    # 4. extra-07 writer comment rebrand (self-pace writer from the v13.6 build).
    w7_idx = next(i for i, c in enumerate(cells)
                  if "duck-extra-07.patch" in cell_source(c) and "write_text" in cell_source(c))
    src = cell_source(cells[w7_idx])
    src, n = re.subn(r"ARC3 Duck v13\.6-final: patch 0009", "ARC3 Duck v13.7-final: patch 0009",
                     src, count=1)
    assert n == 1, "extra-07 comment rebrand"
    set_source(cells[w7_idx], src)

    # 5. Budget probe labels.
    b_idx = next(i for i, c in enumerate(cells) if "v13.6 budget probe" in cell_source(c))
    src = cell_source(cells[b_idx])
    src = src.replace("v13.6 budget probe", "v13.7 budget probe")
    src = src.replace("v13.6 budget:", "v13.7 budget:")
    set_source(cells[b_idx], src)

    # 6. Roster probe labels (incl. the unconditional a/call print label).
    r_idx = next(i for i, c in enumerate(cells) if "v13.6 roster probe" in cell_source(c))
    src = cell_source(cells[r_idx])
    src = src.replace("v13.6 roster probe", "v13.7 roster probe")
    src = src.replace("v13.6-final roster:", "v13.7-final roster:")
    src = src.replace("v13.6 batch: a/call", "v13.7 batch: a/call")
    set_source(cells[r_idx], src)

    # 7. New writer cell duck-extra-08.patch (0010 dyn-level-budget), after extra-07.
    patch_text = (PKG / "patches" / "0010-dyn-level-budget.patch").read_text()
    writer = (
        "# ARC3 Duck v13.7-final: patch 0010-dyn-level-budget — adaptacyjny budżet poziomu\n"
        "# (handoff sesji strategii 30.10, arc-v16-package; u nich 0009 — u nas 0010;\n"
        "# docstring modułu „patch 0007/v13.2” = ich wewnętrzna etykieta, bajty nietknięte).\n"
        "# Plik rozłączny (arc3_level_budget.py), DORMANT przy ARC3_LEVEL_TOKEN_CAP=\"0\";\n"
        "# uzbrojenie = LEVEL_TOKEN_CAP 60000; kill ARC3_DYN_CAP=0 -> exact 0004.\n"
        "from pathlib import Path as _P\n"
        f"_P(\"/kaggle/duck-extra-08.patch\").write_text({patch_text!r})\n"
    )
    cells.insert(w7_idx + 1, {"cell_type": "code", "execution_count": None,
                              "metadata": {}, "outputs": [], "source": writer.splitlines(keepends=True)})

    # 8. kernel-metadata.json: slug (unique, per handoff slug hygiene).
    km_path = PKG / "kernel-metadata.json"
    km = json.loads(km_path.read_text())
    km["id"] = "petersharps/arc3-duck-v13-7-final"
    km["title"] = "arc3-duck-v13-7-final"
    km_path.write_text(json.dumps(km, indent=2, ensure_ascii=False) + "\n")

    out = Path(args.out)
    out.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")
    print(f"built {out} ({len(cells)} cells, {out.stat().st_size} bytes)")
    print(f"kernel-metadata id -> {km['id']} (dormant 0010: LEVEL_TOKEN_CAP=0)")


if __name__ == "__main__":
    main()
