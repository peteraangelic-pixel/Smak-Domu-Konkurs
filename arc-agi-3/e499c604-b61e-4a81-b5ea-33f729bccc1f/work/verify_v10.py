"""Offline verification for arc3-duck-v10.ipynb.

  1. every code cell compiles (shell/magic cells and top-level await excluded),
  2. every PROFILE resolves to the expected environment,
  3. the patch chunks reassemble into the exact patch this repo built
     (sha256 must match the one recorded in ARC3_VARIANT),
  4. that patch applies to a pristine Tufa bundle with `git apply`, the tree
     compiles, and the plan-commit tests pass on it,
  5. every input the notebook names is declared in the metadata.
"""
import ast
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

NB = Path("work/smak/arc-agi-3/new/arc3-duck-v10.ipynb")
META = Path("work/smak/arc-agi-3/new/kernel-metadata-v10.json")
SOURCE_PATCH = Path("/tmp/patches/0010-v10-all.patch")
PRISTINE = Path("work/tufa/ARC3-Inference")
TESTS = Path("work/c45base/ARC3-Inference/tests/test_plan_commit.py")

failures = []


def check(name, condition, detail=""):
    print(("OK   " if condition else "FAIL ") + name + ("" if condition else f" {detail}"))
    if not condition:
        failures.append(name)


def src(cell):
    return "".join(cell["source"])


def main():
    notebook = json.loads(NB.read_text(encoding="utf-8"))
    cells = notebook["cells"]
    print(f"notebook: {len(cells)} cells, {NB.stat().st_size} bytes")

    # 1. compile
    compiled = skipped = 0
    for index, cell in enumerate(cells):
        if cell["cell_type"] != "code":
            continue
        source = src(cell)
        if source.lstrip().startswith("%"):
            skipped += 1
            continue
        # IPython shell escapes are valid cells but not Python statements.
        source = "\n".join(
            "pass" if line.lstrip().startswith("!") else line
            for line in source.splitlines())
        try:
            compile(source, f"<cell {index}>", "exec",
                    flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
            compiled += 1
        except SyntaxError as exc:
            check(f"cell {index} compiles", False, repr(exc))
    check(f"{compiled} code cells compile ({skipped} magic cells skipped)", compiled >= 14)

    # 2. profiles
    profile_cell = src(cells[1])
    for profile, expected in [
        ("c45", {}),
        ("deep", {}),
        ("wide", {}),
        ("plan", {"ARC3_PLAN_COMMIT": "1", "ARC3_WORLD_MODEL": "0", "ARC3_ESCALATE_ACTIONS": "60"}),
        ("plan-esc", {"ARC3_PLAN_COMMIT": "1", "ARC3_WORLD_MODEL": "0", "ARC3_ESCALATE_ACTIONS": "30"}),
    ]:
        source = profile_cell.replace('PROFILE = "plan"', f'PROFILE = "{profile}"', 1)
        namespace = {}
        buffer, real = io.StringIO(), sys.stdout
        sys.stdout = buffer
        try:
            exec(compile(source, "<profile>", "exec"), namespace)
        finally:
            sys.stdout = real
        resolved = namespace["V9"]
        check(f"profile {profile}", resolved["profile"] == profile)
        for key, value in expected.items():
            check(f"  {profile}.{key}={value}", resolved["env_extra"].get(key) == value,
                  repr(resolved["env_extra"]))
        if profile == "c45":
            check("  c45 arms no new env", resolved["env_extra"] == {})

    # 3. chunks -> patch
    parts = {}
    for cell in cells:
        match = re.match(r"%%writefile /kaggle/v10-part-(\d+)\.txt\n", src(cell))
        if match:
            parts[int(match.group(1))] = src(cell).split("\n", 1)[1]
    check("patch chunks present", len(parts) >= 2, str(sorted(parts)))
    assembled = "".join(parts[i] for i in sorted(parts))
    expected = SOURCE_PATCH.read_text(encoding="utf-8")
    check("reassembled length matches", len(assembled) == len(expected),
          f"{len(assembled)} vs {len(expected)}")
    check("reassembled sha256 matches", assembled == expected)
    recorded = json.loads(re.search(r"ARC3_VARIANT = (\{.*?\})\n", src(cells[2]), re.S).group(1))
    check("recorded sha256 matches",
          recorded["patch_sha256"] == hashlib.sha256(expected.encode()).hexdigest(),
          recorded.get("patch_sha256"))
    check("no chunk reaches the 498,799 ceiling",
          all(len(part) < 498_000 for part in parts.values()),
          str({i: len(p) for i, p in parts.items()}))

    # 4. apply to a pristine bundle
    workdir = Path(tempfile.mkdtemp(prefix="v10verify_"))
    try:
        shutil.copytree(PRISTINE, workdir / "ARC3-Inference")
        (workdir / "v10.patch").write_text(assembled, encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=workdir, check=True)
        subprocess.run(["git", "add", "-A"], cwd=workdir, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-c", "user.email=a@b", "-c", "user.name=t",
                        "commit", "-qm", "base"], cwd=workdir, check=True)
        applied = subprocess.run(["git", "apply", "--include=ARC3-Inference/*",
                                  str(workdir / "v10.patch")],
                                 cwd=workdir, capture_output=True, text=True)
        check("patch applies with git apply", applied.returncode == 0, applied.stderr[-400:])
        compiled_tree = subprocess.run([sys.executable, "-m", "compileall", "-q",
                                        "ARC3-Inference/inference"], cwd=workdir,
                                       capture_output=True, text=True)
        check("patched tree compiles", compiled_tree.returncode == 0,
              compiled_tree.stderr[-400:])
        target = workdir / "ARC3-Inference" / "tests"
        target.mkdir(exist_ok=True)
        shutil.copyfile(TESTS, target / "test_plan_commit.py")
        env = dict(os.environ, ARC3_PLAN_COMMIT="1")
        tests = subprocess.run([sys.executable, "-m", "unittest", "tests.test_plan_commit"],
                               cwd=workdir / "ARC3-Inference", capture_output=True,
                               text=True, env=env)
        check("plan-commit tests pass on the patched tree", tests.returncode == 0,
              tests.stderr[-400:])
        check("world model module present", (workdir / "ARC3-Inference/inference/utils/world_model.py").is_file())
        check("plan commit module present", (workdir / "ARC3-Inference/inference/utils/plan_commit.py").is_file())
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    # 5. declared inputs
    metadata = json.loads(META.read_text(encoding="utf-8"))
    text = "\n".join(src(c) for c in cells)
    datasets = {d.lower() for d in metadata.get("dataset_sources", [])}
    models = {m.lower().split("/transformers")[0] for m in metadata.get("model_sources", [])}
    competitions = {c.lower() for c in metadata.get("competition_sources", [])}
    for match in re.finditer(r"/kaggle/input/(datasets|models|competitions)/([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)",
                             text):
        kind, ref = match.group(1), match.group(2).lower()
        pool = {"datasets": datasets, "models": models, "competitions": competitions}[kind]
        check(f"input {kind}/{ref} declared", any(ref == p or ref.startswith(p + "/") for p in pool),
              str(sorted(pool)))
    check("metadata id/title/code_file agree",
          metadata["title"] == metadata["id"].split("/")[-1] == metadata["code_file"].replace(".ipynb", ""))

    print()
    if failures:
        print(f"{len(failures)} FAILURES: {failures}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
