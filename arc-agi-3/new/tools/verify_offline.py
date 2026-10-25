#!/usr/bin/env python3
"""Offline verification of the v9 package. No GPU, no Kaggle, no network.

Checks, in order of how much they have cost this project before:

1. notebook integrity   — parses, cell count, the four v9 edits are present and
                          applied exactly once;
2. metadata <-> paths   — every /kaggle/input path the notebook uses is backed
                          by a declared dataset/model/competition source.
                          c45 as committed failed this one: its notebook reads
                          dfranzen's models while its metadata declared the
                          slow line's datasets, so the run would have died on a
                          missing directory;
3. patch chain          — extracts the 498 KB harness patch and the three extra
                          patches from the notebook cells, applies them to a
                          pristine bundle, and compiles the result (needs
                          --bundle, e.g. r033-recon-bundle/bundle);
4. analyzer             — unit tests plus one real r019 game run through the
                          formula, if the artefact is available.

Usage:
  python3 tools/verify_offline.py
  python3 tools/verify_offline.py --bundle /path/to/r033-recon-bundle/bundle \\
      --r019 /path/to/r019-kernel-output/output/benchmark.json
Exit code 0 = everything that can be checked offline is good.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOK = ROOT / "arc3-duck-v9.ipynb"
METADATA = ROOT / "kernel-metadata.json"

OK = "OK  "
BAD = "FAIL"
SKIP = "SKIP"

results: list[tuple[str, str]] = []


def check(name: str, ok: bool, detail: object = "") -> bool:
    suffix = f": {detail}" if detail else ""
    results.append((OK if ok else BAD, f"{name}{suffix}"))
    return ok


def skip(name: str, detail: str) -> None:
    results.append((SKIP, f"{name}: {detail}"))


def notebook_cells(path: Path) -> list[str]:
    nb = json.loads(path.read_text())
    return ["".join(c.get("source", [])) for c in nb.get("cells", [])]


def extract_patches(cells: list[str]) -> dict[str, str]:
    """Pull every patch the notebook writes, from %%writefile and write_text cells."""
    patches: dict[str, str] = {}
    for src in cells:
        if src.startswith("%%writefile"):
            head, _, body = src.partition("\n")
            name = head.split(maxsplit=1)[1].strip()
            patches[Path(name).name] = body
            continue
        if ".write_text(" not in src or ".patch" not in src:
            continue
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "write_text"
                and node.args
            ):
                try:
                    body = ast.literal_eval(node.args[0])
                except Exception:
                    continue
                match = re.search(r"['\"]([^'\"]+\.patch)['\"]", src)
                if match and isinstance(body, str):
                    patches[Path(match.group(1)).name] = body
    return patches


def check_notebook() -> list[str]:
    if not check("notebook exists", NOTEBOOK.is_file(), str(NOTEBOOK)):
        return []
    try:
        nb = json.loads(NOTEBOOK.read_text())
        cells = ["".join(c.get("source", [])) for c in nb["cells"]]
        code_cells = [
            (i, "".join(c.get("source", [])))
            for i, c in enumerate(nb["cells"])
            if c.get("cell_type") == "code" and not "".join(c.get("source", [])).lstrip().startswith("%%")
        ]
        check("notebook parses", True, f"{len(cells)} cells, {len(code_cells)} plain code cells")
    except Exception as exc:  # noqa: BLE001
        check("notebook parses", False, repr(exc))
        return []

    joined = "\n".join(cells)
    check("V9 profile cell present", 'PROFILE = "c45"' in joined)
    check(
        "analyzer output routed through V9",
        'V9["max_output_tokens"]' in joined and 'V9["system_prompt_prefix"]' in joined,
    )
    check(
        "launcher MAXREQ routed through V9",
        'os.environ.get("V9_MAXREQ"' in joined and 'os.environ.get("V9_CTX"' in joined,
    )
    check("metering cell present", "v9 metering" in joined and "v9_metrics.json" in joined)
    check("harness patch written once", joined.count("%%writefile /kaggle/harness-changes.patch") == 1)
    check("smoke/submit switch untouched", "TRUE_SUBMISSION = os.environ.get" in joined)
    check("ONLY_RESET_LEVELS pinned", 'os.environ["ONLY_RESET_LEVELS"] = "true"' in joined)

    # every plain-python cell must parse; %%writefile / !shell cells are skipped
    bad = []
    for idx, src in code_cells:
        if not src.strip():
            continue
        filtered = "\n".join(
            "" if ln.lstrip().startswith(("!", "%")) else ln for ln in src.splitlines()
        )
        try:
            ast.parse(filtered)
        except SyntaxError as exc:
            bad.append(f"cell {idx}: {exc.msg}")
    check("all code cells parse", not bad, "; ".join(bad))

    # the V9 switch itself: each profile must produce the intended values
    profile_src = next((c for c in cells if "PROFILE = " in c and "V9 = {" in c), "")
    if not profile_src:
        check("V9 switch executable", False, "profile cell not found")
    else:
        expected = {
            "c45": {"maxreq": 10, "streams": 10, "prefix": False},
            "deep": {"maxreq": 10, "streams": 10, "prefix": True},
            "wide": {"maxreq": 14, "streams": 14, "prefix": False},
        }
        for profile, want in expected.items():
            ns: dict = {}
            try:
                exec(profile_src.replace('PROFILE = "c45"', f'PROFILE = "{profile}"', 1), ns)
                v9 = ns["V9"]
                ok = (
                    v9["maxreq"] == want["maxreq"]
                    and v9["streams"] == want["streams"]
                    and bool(v9["system_prompt_prefix"]) == want["prefix"]
                )
                check(f"V9 profile {profile} resolves", ok, json.dumps({k: v9[k] for k in ('maxreq', 'streams', 'system_prompt_prefix')})[:90])
            except Exception as exc:  # noqa: BLE001
                check(f"V9 profile {profile} resolves", False, repr(exc))
    return cells


def check_metadata(cells: list[str]) -> None:
    if not check("kernel-metadata.json exists", METADATA.is_file()):
        return
    meta = json.loads(METADATA.read_text())
    datasets = {s.lower() for s in meta.get("dataset_sources") or []}
    models = {s.lower() for s in meta.get("model_sources") or []}
    competitions = {s.lower() for s in meta.get("competition_sources") or []}

    joined = "\n".join(cells)
    declared: list[str] = []

    for match in re.finditer(r"/kaggle/input/datasets/([^/'\"\s]+)/([^/'\"\s]+)", joined):
        slug = f"{match.group(1)}/{match.group(2)}".lower()
        declared.append(slug)
        check(f"dataset declared: {slug}", slug in datasets, "" if slug in datasets else "missing from dataset_sources")

    for match in re.finditer(r"/kaggle/input/models/([^/'\"\s]+)/([^/'\"\s]+)/", joined):
        slug = f"{match.group(1)}/{match.group(2)}".lower()
        declared.append(slug)
        hits = [m for m in models if m.startswith(slug + "/")]
        check(f"model declared: {slug}", bool(hits), "" if hits else "missing from model_sources")

    for match in re.finditer(r"/kaggle/input/competitions/([^/'\"\s]+)/", joined):
        slug = match.group(1).lower()
        check(f"competition declared: {slug}", slug in competitions)

    slug = str(meta.get("id") or "").split("/")[-1]
    check(
        "metadata title equals slug",
        bool(slug) and slug == meta.get("title"),
        f"title={meta.get('title')!r} slug={slug!r}",
    )
    check("metadata code_file matches notebook", meta.get("code_file") == NOTEBOOK.name)
    check("private flag recorded", "is_private" in meta, f"is_private={meta.get('is_private')}")
    check("no stale sources", bool(declared), "notebook declares no /kaggle/input path")


def check_patches(cells: list[str], bundle: Path | None) -> None:
    patches = extract_patches(cells)
    expected = ["harness-changes.patch", "duck-extra-00.patch", "duck-extra-01.patch", "duck-extra-02.patch"]
    missing = [p for p in expected if p not in patches]
    if not check("all four patches extracted", not missing, f"missing {missing}" if missing else ", ".join(expected)):
        return
    sizes = {name: len(patches[name]) for name in expected}
    check("harness patch is the full 498 KB", sizes["harness-changes.patch"] > 498_000, str(sizes["harness-changes.patch"]))
    if bundle is None or not (bundle / "src").is_dir():
        skip("patch chain applies", "no --bundle given (pass r033-recon-bundle/bundle)")
        return
    tmp = Path(tempfile.mkdtemp(prefix="v9-verify-"))
    try:
        work = tmp / "src"
        shutil.copytree(bundle / "src", work)
        for name in expected:
            (tmp / name).write_text(patches[name] if patches[name].endswith("\n") else patches[name] + "\n")
        subprocess.run(["git", "init", "-q"], cwd=work, check=True)
        subprocess.run(["git", "add", "-A", "-f"], cwd=work, check=True, capture_output=True)
        subprocess.run(
            ["git", "-c", "user.email=v9@local", "-c", "user.name=v9", "commit", "-qm", "base"],
            cwd=work,
            check=True,
            capture_output=True,
        )
        for name in expected:
            proc = subprocess.run(
                ["git", "apply", "--include=ARC3-Inference/*", str(tmp / name)],
                cwd=work,
                capture_output=True,
                text=True,
            )
            check(f"applies: {name}", proc.returncode == 0, proc.stderr.strip().splitlines()[-1] if proc.stderr else "")
            if proc.returncode != 0:
                return
        targets = [
            "ARC3-Inference/inference/agent/tool_agent.py",
            "ARC3-Inference/inference/agent/prompts.py",
            "ARC3-Inference/inference/framework/solver.py",
            "ARC3-Inference/inference/framework/arc3_level_budget.py",
            "ARC3-Inference/inference/utils/segmentation.py",
        ]
        proc = subprocess.run([sys.executable, "-m", "py_compile", *targets], cwd=work, capture_output=True, text=True)
        check("patched tree compiles", proc.returncode == 0, proc.stderr.strip().splitlines()[-1] if proc.stderr else "")

        agent = (work / "ARC3-Inference/inference/agent/tool_agent.py").read_text()
        for var in ("ARC3_SYSTEM_PROMPT_PREFIX", "ARC3_MAX_ACTIVE_STREAMS", "ARC3_LEVEL_TOKEN_CAP"):
            check(f"env honoured in code: {var}", var in agent or var in (
                work / "ARC3-Inference/inference/framework/arc3_level_budget.py"
            ).read_text())
        scope = re.search(r"return scope if scope in \(([^)]*)\)", agent)
        check(
            "PERSISTENT_FUNCTIONS_SCOPE accepts 'game'",
            bool(scope) and "game" in scope.group(1),
            scope.group(0) if scope else "scope validator not found",
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_analyzer(r019: Path | None) -> None:
    tests = ROOT / "tools" / "test_v9_metrics.py"
    proc = subprocess.run([sys.executable, str(tests)], capture_output=True, text=True)
    check("analyzer unit tests", proc.returncode == 0, proc.stdout.strip().splitlines()[-1] if proc.stdout else "")
    if r019 is None or not r019.is_file():
        skip("analyzer on a real r019 dump", "no --r019 given")
        return
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "v9_metrics.py"), str(r019)],
        capture_output=True,
        text=True,
    )
    out = proc.stdout
    check("r019 formula reproduces final_score", "max |diff|=0.0" in out or "max |diff|=0.0000" in out)
    mean_line = next((ln for ln in out.splitlines() if ln.startswith("MEAN")), "")
    check("r019 mean score is 27.21", "score=27.21" in out, mean_line)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", type=Path, default=None)
    ap.add_argument("--r019", type=Path, default=None)
    args = ap.parse_args()

    cells = check_notebook()
    if cells:
        check_metadata(cells)
        check_patches(cells, args.bundle)
    check_analyzer(args.r019)

    width = max(len(msg) for _, msg in results) + 2
    for status, msg in results:
        print(f"{status} {msg}")
    failures = sum(1 for status, _ in results if status == BAD)
    print(f"\n{len(results)} checks, {failures} failed, "
          f"{sum(1 for status, _ in results if status == SKIP)} skipped")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
