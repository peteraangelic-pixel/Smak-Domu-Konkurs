"""Build arc3-duck-v10.ipynb from the v9 package.

v10 = Franzen's complete harness patch + 0001 + 0002 + 0004 + 0007, shipped as
ONE patch split across notebook cells.

Why split: the v9 notebook carried Franzen's patch in a single `%%writefile`
cell of 498,799 characters, and the file ends mid-hunk ("corrupt patch at line
10086"). That is a hard Kaggle/editor cell limit, and it means the accepted
package would have died in cell 10 before a single game started. The patch is
therefore cut into chunks well under the limit and concatenated at runtime, and
the sha256 is printed.
"""
import hashlib
import json
import sys
from pathlib import Path

SRC = Path("work/smak/arc-agi-3/new/arc3-duck-v9.ipynb")
PATCH = Path("/tmp/patches/0010-v10-all.patch")
OUT = Path("work/smak/arc-agi-3/new/arc3-duck-v10.ipynb")
META = Path("work/smak/arc-agi-3/new/kernel-metadata-v10.json")

CHUNK = 380_000

BASE_ENV = {
    "ARC3_ABANDON_MIN_LEVELS": "0",
    "ARC3_ABANDON_TOKENS": "0",
    "ARC3_EXPERIMENT_HINT": "1",
    "ARC3_LEVEL_MIN_DONE": "0",
    "ARC3_LEVEL_NOTES": "1",
    "ARC3_LEVEL_RESETS_MAX": "1",
    "ARC3_LEVEL_TOKEN_CAP": "45000",
    "ARC3_STUCK_AUDIT_TOKENS": "60000",
    "ARC3_WORLD_MODEL": "0",
    "ARC3_WORLD_MODEL_NUDGE": "0",
}

PROFILE_CELL = '''# === v10 profile: one switch, one measured lever ===========================
# Base is duck-c45 as accepted on 24.10 (Franzen fast engine: INT4 + MTP +
# sglang, Tufa duck harness, level token cap 45k).
# v10 adds ONE mechanism on top of v9: `commit(plan)` - a plan is played one
# step at a time and stops at the first failed prediction, so a wrong rule
# costs one action and returns a diff instead of spending the whole plan.
#
#   c45      faithful re-run of c45 (control; no new prompt, no new helper).
#   deep     c45 + route-batching directive (v9).
#   wide     c45 + more decode streams (MAXREQ/streams 10 -> 14, v9).
#   plan     c45 + commit()/frame_digest() + escalation after 60 actions on a
#            level: retrodict from the log, write model_state/model_step,
#            check_model(), plan(), then commit() the result.
#   plan-esc same as plan with escalation after 30 actions (more aggressive).
PROFILE = "plan"          # "c45" | "deep" | "wide" | "plan" | "plan-esc"
assert PROFILE in {"c45", "deep", "wide", "plan", "plan-esc"}, PROFILE

V9 = {
    "id": "v10",
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
    # profile-specific environment; merged into ARC3_VARIANT in the next cell
    "env_extra": {},
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
elif PROFILE in {"plan", "plan-esc"}:
    V9.update(
        env_extra={
            "ARC3_PLAN_COMMIT": "1",
            "ARC3_WORLD_MODEL": "0",
            "ARC3_ESCALATE_ACTIONS": "30" if PROFILE == "plan-esc" else "60",
        },
    )

print(f"v10 profile={PROFILE} maxreq={V9['maxreq']} streams={V9['streams']} "
      f"max_output={V9['max_output_tokens']} env_extra={V9['env_extra']}",
      flush=True)
'''

HEADER = """# ARC3 Duck — variant `v10`

> Built from `arc3-duck-v9.ipynb`. Two changes: the harness patch is now
> **complete**, and `commit(plan)` is available.

## Why the patch changed

v9 (and v7) shipped Franzen's harness patch as a single `%%writefile` cell of
**498,799 characters**, and the text ends inside a hunk of `segmentation.py`
(`git apply`: *corrupt patch at line 10086*). 498,799 is a cell-length ceiling,
not a coincidence: the tail of the patch never made it into the notebook, so the
accepted package would have failed in the environment cell before the model
loaded. v10 rebuilds the patch from Franzen's public tree
(`da-fr/arc-agi-3-solution`) and splits it into chunks, concatenated at runtime
with a printed sha256.

## What is new

- One harness patch = Franzen's changes + `0001` (level notes, stuck audit) +
  `0002` (executable world model: `model_state`/`model_step`/`check_model`/
  `plan`) + `0004` (level token cap) + `0007` (plan-commit).
- `commit(plan)` in the python sandbox: each step may carry `expect={...}`
  (`level`, `board_changed`, `step`, `digest`, `cells`). Steps run one at a
  time; the plan halts at the first failed expectation and returns `mismatch`
  with the field that differed. It also stops on level completion, game over,
  run completion, or `max_actions` (default 40).
- `frame_digest()` — process-independent digest, so an expectation can be
  computed in one snippet and checked in another.
- Escalation directive (`ARC3_ESCALATE_ACTIONS`): after N actions on a level
  without completing it, the turn demands retrodiction → `model_state`/
  `model_step` → `check_model()` → `plan()` → `commit()`.
- Offline tests: `tests/test_plan_commit.py` (11 tests, including the real
  sandbox bootstrap). Measured cost of one commit step: 4 ms at empty history,
  146 ms at 200 recorded transitions.

`commit()` is off unless `ARC3_PLAN_COMMIT=1`, so `PROFILE="c45"` reproduces
the accepted configuration.

---
"""

APPLY_BLOCK_OLD = '''subprocess.run(["git", "apply", "--include=ARC3-Inference/*", "-v", "/kaggle/harness-changes.patch"], cwd=f"{BUNDLE_DIR}/src", check=True)
print('harness patch applied successfully')

# ARC3 Duck: our own harness patches, applied on top of Franzen's patch.
for _extra_patch in ARC3_VARIANT.get("patch_files", []):
    subprocess.run(["git", "apply", "--include=ARC3-Inference/*", "-v", _extra_patch],
                   cwd=f"{BUNDLE_DIR}/src", check=True)
    print(f"ARC3 extra patch applied: {_extra_patch}", flush=True)'''

APPLY_BLOCK_NEW = '''# v10: ONE patch (franzen + 0001 + 0002 + 0004 + 0007), assembled from chunks
# above because a single cell longer than ~498,799 characters is truncated.
_assembled = Path("/kaggle/v10-harness.patch")
_assembled.write_text("".join(p.read_text() for p in sorted(PARTS)), encoding="utf-8")
import hashlib as _h
print(f"v10 harness patch: {_assembled.stat().st_size} bytes sha256="
      f"{_h.sha256(_assembled.read_bytes()).hexdigest()}", flush=True)
subprocess.run(["git", "apply", "--include=ARC3-Inference/*", "-v", str(_assembled)],
               cwd=f"{BUNDLE_DIR}/src", check=True)
print('v10 harness patch applied', flush=True)'''

CONCAT_CELL = (
    "# v10: concatenate the patch chunks written by the cells above.\n"
    "from pathlib import Path\n"
    "\n"
    "PARTS = [Path(f'/kaggle/v10-part-{i:02d}.txt') for i in range(__NPARTS__)]\n"
    "for _part in PARTS:\n"
    "    assert _part.is_file(), f'missing patch chunk {_part}'\n"
    "print('v10 patch chunks:', [p.stat().st_size for p in PARTS], "
    "f'total={sum(p.stat().st_size for p in PARTS)}', flush=True)\n"
)


def main() -> int:
    notebook = json.loads(SRC.read_text(encoding="utf-8"))
    cells = notebook["cells"]
    patch_text = PATCH.read_text(encoding="utf-8")
    if not patch_text.endswith("\n"):
        patch_text += "\n"
    digest = hashlib.sha256(patch_text.encode("utf-8")).hexdigest()

    # 1. header
    cells[0]["source"] = (HEADER + "\n" + "".join(cells[0]["source"])).splitlines(keepends=True)

    # 2. profile cell
    cells[1]["source"] = PROFILE_CELL.splitlines(keepends=True)

    # 3. preflight variant
    variant = {
        "env": dict(BASE_ENV),
        "git": "unknown",
        "name": "v10",
        "patch_sha256": digest,
        "patch_bytes": len(patch_text.encode("utf-8")),
        "patch_files": ["/kaggle/v10-harness.patch"],
        "patches": [
            "franzen-harness",
            "0001-level-notes-audit-experiment-hint",
            "0002-executable-world-model",
            "0004-level-token-cap",
            "0007-plan-commit",
        ],
        "smoke": {
            "games": ["cn04", "dc22", "g50t", "ka59", "ls20",
                      "m0r0", "s5i5", "sc25", "su15", "tn36"],
            "minutes": 48,
        },
    }
    lines = "".join(cells[2]["source"]).splitlines()
    replaced = False
    for index, line in enumerate(lines):
        if line.startswith("ARC3_VARIANT = "):
            lines[index] = (
                "ARC3_VARIANT = "
                + json.dumps(variant, sort_keys=True)
                + "\n# v10: profile env is merged here so the preflight and the run agree.\n"
                + 'ARC3_VARIANT["env"].update({k: str(v) for k, v in '
                + '(V9.get("env_extra") or {}).items()})\n'
            )
            replaced = True
            break
    if not replaced:
        print("preflight cell: ARC3_VARIANT assignment not found")
        return 1
    cells[2]["source"] = "\n".join(lines).splitlines(keepends=True)

    # 4. replace the truncated patch cell (index 5) and drop the three extras
    chunks = [patch_text[i:i + CHUNK] for i in range(0, len(patch_text), CHUNK)]
    patch_cells = []
    for index, chunk in enumerate(chunks):
        patch_cells.append({
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": (f"%%writefile /kaggle/v10-part-{index:02d}.txt\n" + chunk).splitlines(keepends=True),
        })
    concat = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": CONCAT_CELL.replace("__NPARTS__", str(len(chunks))).splitlines(keepends=True),
    }
    # cells 5..8 are: truncated franzen patch, 0001, 0002, 0004
    cells[5:9] = patch_cells + [concat]

    # 5. apply block in the environment cell
    env_index = next(i for i, c in enumerate(cells)
                     if "harness patch applied successfully" in "".join(c["source"]))
    env_source = "".join(cells[env_index]["source"])
    if APPLY_BLOCK_OLD not in env_source:
        print("environment cell: patch-application block not found")
        return 1
    cells[env_index]["source"] = env_source.replace(
        APPLY_BLOCK_OLD, APPLY_BLOCK_NEW).splitlines(keepends=True)

    # 6. metering: record the lever and the patch identity
    metering = "".join(cells[-1]["source"])
    metering = metering.replace(
        '        "profile": V9["profile"],',
        '        "profile": V9["profile"],\n'
        '        "plan_commit": bool(V9.get("env_extra", {}).get("ARC3_PLAN_COMMIT")),\n'
        '        "harness_patch_sha256": ARC3_VARIANT.get("patch_sha256"),',
    )
    metering += (
        "\n\n# v10: the lever is only worth a slot if the plans carried predictions.\n"
        "print(f\"v10 profile={PROFILE} plan_commit=\"\n"
        "      f\"{bool(V9.get('env_extra', {}).get('ARC3_PLAN_COMMIT'))} \"\n"
        "      f\"patch_sha256={ARC3_VARIANT.get('patch_sha256')}\", flush=True)\n"
    )
    cells[-1]["source"] = metering.splitlines(keepends=True)

    notebook["cells"] = cells
    OUT.write_text(json.dumps(notebook, indent=1, ensure_ascii=False), encoding="utf-8")

    metadata = json.loads((SRC.parent / "kernel-metadata.json").read_text(encoding="utf-8"))
    metadata["id"] = "petersharps/arc3-duck-v10"
    metadata["title"] = "arc3-duck-v10"
    metadata["code_file"] = "arc3-duck-v10.ipynb"
    META.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    print(f"patch: {len(patch_text)} bytes, {len(chunks)} chunks, sha256={digest}")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes, {len(cells)} cells)")
    print(f"wrote {META}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
