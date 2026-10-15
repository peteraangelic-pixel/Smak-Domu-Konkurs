"""Dispatcher operacji Kaggle (ten repo). Request: arc-agi-3/kaggle/ops/request.json
{"id": "rNNN", "op": "...", "args": {...}}

Ops:
  preflight        — wersja CLI + ostatnie zgłoszenia (read-only)
  submissions      — lista zgłoszeń konkursu (read-only)
  pull-their-duck  — kaggle kernels pull petersharps/arc3-duck (read-only) + grep hooków
  push-duck200k    — kernels push arc-agi-3/kaggle/duck-200k (Save & Run, NIE submit)
  submit           — competitions submit -k (GUARDY: confirm=true w args,
                     limit dzienny 1, kernel musi być wypchnięty)

Wyniki: arc-agi-3/kaggle/ops/results/<id>-<op>/SUMMARY.md (+ pliki pomocnicze).
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import json
import os
import subprocess
import sys
from pathlib import Path

OPS_DIR = Path(__file__).resolve().parent
RESULTS = OPS_DIR / "results"
COMP = "arc-prize-2026-arc-agi-3"
DUCK_KERNEL = "petersharps/arc3-duck"
DUCK200K_DIR = OPS_DIR.parent / "duck-200k"


def sh(args: list[str], cwd: Path | None = None) -> tuple[int, str]:
    proc = subprocess.run(args, capture_output=True, text=True, cwd=cwd)
    return proc.returncode, (proc.stdout + ("\n[stderr]\n" + proc.stderr if proc.stderr else ""))


def kaggle(*args: str) -> tuple[int, str]:
    return sh(["kaggle", *args])


def todays_submissions() -> list[dict]:
    """Zgłoszenia konkursu z dziś (UTC) — do guarda limitu dziennego."""
    code, out = kaggle("competitions", "submissions", "-c", COMP)
    rows: list[dict] = []
    if code != 0:
        raise RuntimeError(f"kaggle competitions submissions failed:\n{out}")
    reader = csv.DictReader(io.StringIO(out))
    today = dt.datetime.now(dt.timezone.utc).date()
    for row in reader:
        raw = (row.get("date") or "").strip()
        if raw:
            try:
                when = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
                if when.astimezone(dt.timezone.utc).date() == today:
                    rows.append(row)
            except ValueError:
                pass
    return rows


def op_preflight(_: dict, out_dir: Path) -> str:
    code, out = kaggle("--version")
    text = f"## CLI\nrc={code}\n{out}\n"
    code2, out2 = kaggle("competitions", "submissions", "-c", COMP)
    text += f"## Submissions (rc={code2})\n{out2}\n"
    today = todays_submissions()
    text += f"## Zgłoszeń dziś (UTC): {len(today)}\n"
    if today:
        text += "UWAGA: limit dzienny już wykorzystany — submit dziś odmówi.\n"
    (out_dir / "submissions.txt").write_text(out2, encoding="utf-8")
    return text


def op_submissions(args: dict, out_dir: Path) -> str:
    code, out = kaggle("competitions", "submissions", "-c", COMP)
    (out_dir / "submissions.txt").write_text(out, encoding="utf-8")
    return f"rc={code}\n{out}\n"


def op_pull_their_duck(args: dict, out_dir: Path) -> str:
    code, out = kaggle("kernels", "pull", DUCK_KERNEL, "-p", str(out_dir))
    text = f"## kernels pull {DUCK_KERNEL}\nrc={code}\n{out}\n"
    src = out_dir / f"{DUCK_KERNEL.split('/')[1]}.ipynb"
    if not src.exists():
        candidates = list(out_dir.glob("*.ipynb"))
        src = candidates[0] if candidates else src
    if src.exists():
        blob = src.read_text(encoding="utf-8", errors="replace")
        for marker in ("budget", "token", "max_runtime", "bm.solver", "long200",
                       "100", "150", "200"):
            hits = [line.strip()[:160] for line in blob.splitlines() if marker in line]
            if hits:
                text += f"\n## marker {marker!r} ({len(hits)}x)\n" + "\n".join(hits[:8]) + "\n"
        (out_dir / "their-kernel-full.ipynb").write_text(blob, encoding="utf-8")
    else:
        text += "\n(nie znaleziono .ipynb w outputach pull)\n"
    return text


def op_push_duck200k(args: dict, out_dir: Path) -> str:
    code, out = kaggle("kernels", "push", "-p", str(DUCK200K_DIR))
    return f"## kernels push duck-200k (Save & Run)\nrc={code}\n{out}\n"


def op_submit(args: dict, out_dir: Path) -> str:
    if not args.get("confirm"):
        return "ODMOWA: op submit wymaga args.confirm=true (jawnie w request.json).\n"
    kernel = str(args.get("kernel") or "")
    if not kernel:
        return "ODMOWA: args.kernel (np. petersharps/taaf-duck-long200) wymagany.\n"
    today = todays_submissions()
    if today:
        rows = "\n".join(str(r) for r in today)
        return f"ODMOWA: limit dzienny już wykorzystany ({len(today)} zgłoszeń dziś):\n{rows}\n"
    msg = str(args.get("message") or "duck @long200 (Smak-Domu-Konkurs arc3-ops)")
    code, out = kaggle("competitions", "submit", "-c", COMP, "-k", kernel, "-m", msg)
    return f"## competitions submit -k {kernel}\nrc={code}\n{out}\n"


OPS = {
    "preflight": op_preflight,
    "submissions": op_submissions,
    "pull-their-duck": op_pull_their_duck,
    "push-duck200k": op_push_duck200k,
    "submit": op_submit,
}


def main() -> int:
    request = json.loads((OPS_DIR / "request.json").read_text(encoding="utf-8"))
    op_id = str(request.get("id") or "r000")
    op_name = str(request.get("op") or "")
    args = dict(request.get("args") or {})
    if op_name not in OPS:
        print(f"[ops] nieznana operacja: {op_name!r}; dozwolone: {sorted(OPS)}", flush=True)
        return 2
    out_dir = RESULTS / f"{op_id}-{op_name}"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[ops] {op_id} · {op_name}", flush=True)
    import traceback
    try:
        text = OPS[op_name](args, out_dir)
        status = "OK"
    except Exception as exc:  # noqa: BLE001 — raportujemy pełny ślad do SUMMARY
        text = f"BŁĄD: {exc}\n\nTRACEBACK:\n{traceback.format_exc()}"
        status = "FAILED"
    summary = f"# {op_id} · {op_name}\n\nSTATUS={status} (UTC {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M:%S})\n\n{text}\n"
    (out_dir / "SUMMARY.md").write_text(summary, encoding="utf-8")
    print(summary, flush=True)
    # ZAWSZE rc=0: step ma przejść, żeby „Commit results" wysłał SUMMARY do repo
    # (logi Actions są nieczytelne z sandboxa — czytamy wyniki z gita).
    return 0


if __name__ == "__main__":
    sys.exit(main())
