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
import re
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
    text += f"## Submissions CLI2.x (rc={code2})\n{out2}\n"
    if code2 != 0 and "Authentication required" in out2:
        # Fallback: CLI 1.x czyta kaggle.json {username,key} (legacy sekret).
        text += "\n## Fallback: kaggle==1.5.12 (legacy auth)\n"
        rc3, out3 = sh([sys.executable, "-m", "pip", "install", "--quiet", "kaggle==1.5.12"])
        text += f"pip rc={rc3}\n"
        rc4, out4 = kaggle("competitions", "submissions", "-c", COMP)
        text += f"## Submissions CLI1.x (rc={rc4})\n{out4}\n"
        if rc4 == 0:
            text += ("WNIOSEK: sekret to LEGACY klucz (kaggle.json) — działa na 1.x.\n"
                     "Do submitu -k (CLI 2.x) trzeba będzie odnowić token w Kaggle UI.\n")
            out2 = out4
        else:
            text += "WNIOSEK: klucz odrzucony także przez 1.x → token nieaktualny.\n"
    (out_dir / "submissions.txt").write_text(out2, encoding="utf-8")
    if "## Zgłoszeń dziś" not in text:
        try:
            today = todays_submissions()
            text += f"## Zgłoszeń dziś (UTC): {len(today)}\n"
            if today:
                text += "UWAGA: limit dzienny już wykorzystany — submit dziś odmówi.\n"
        except Exception as exc:  # noqa: BLE001
            text += f"## Zgłoszeń dziś: nieznane ({exc})\n"
    return text


def op_submissions(args: dict, out_dir: Path) -> str:
    code, out = kaggle("competitions", "submissions", "-c", COMP)
    (out_dir / "submissions.txt").write_text(out, encoding="utf-8")
    return f"rc={code}\n{out}\n"


def op_pull_their_duck(args: dict, out_dir: Path) -> str:
    code, out = kaggle("kernels", "pull", DUCK_KERNEL, "-p", str(out_dir), "-m")
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
    ver = str(args.get("version") or "")
    file = str(args.get("file") or "submission.parquet")
    cmd = ["competitions", "submit", "-c", COMP, "-k", kernel]
    if ver:
        cmd += ["-v", ver]
    cmd += ["-f", file, "-m", msg]
    code, out = kaggle(*cmd)
    return f"## competitions submit {cmd}\nrc={code}\n{out}\n"


def _safe_pkg_dir(raw: str) -> Path:
    """Tylko pakiety pod arc-agi-3/kaggle/ (zero ścieżek absolute/..)."""
    candidate = (Path.cwd() / raw).resolve() if not raw.startswith("/") else Path(raw).resolve()
    root = (Path.cwd() / "arc-agi-3" / "kaggle").resolve()
    if root not in candidate.parents:
        raise ValueError(f"push dozwolony tylko pod {root}; dostalem {candidate}")
    return candidate


def op_push(args: dict, out_dir: Path) -> str:
    if not args.get("confirm"):
        return "ODMOWA: op push wymaga args.confirm=true.\n"
    pkg = _safe_pkg_dir(str(args.get("dir") or ""))
    if not (pkg / "kernel-metadata.json").exists():
        return f"ODMOWA: {pkg} nie ma kernel-metadata.json.\n"
    code, out = kaggle("kernels", "push", "-p", str(pkg))
    return f"## kernels push {pkg}\nrc={code}\n{out}\n"


def op_kernel_status(args: dict, out_dir: Path) -> str:
    slug = str(args.get("kernel") or "")
    code, out = kaggle("kernels", "status", slug)
    return f"## kernels status {slug}\nrc={code}\n{out}\n"


def op_kernel_output(args: dict, out_dir: Path) -> str:
    slug = str(args.get("kernel") or "")
    code, out = kaggle("kernels", "output", slug, "-p", str(out_dir / "output"))
    text = f"## kernels output {slug}\nrc={code}\n{out}\n"
    d = out_dir / "output"
    if d.exists():
        files = sorted(d.rglob("*"))
        text += f"\nplików: {len([f for f in files if f.is_file()])}\n"
        for f in files[:25]:
            if f.is_file():
                text += f"  {f.relative_to(d)} ({f.stat().st_size} B)\n"
    return text


def op_kernel_info(args: dict, out_dir: Path) -> str:
    """Zrzut /api/v1/kernels/list (mine) — szukam numeru wersji kernela."""
    import base64
    import urllib.request
    tok = os.environ.get("KAGGLE_API_TOKEN", "")
    auth = base64.b64encode(f"petersharps:{tok}".encode()).decode()
    out = ""
    for url in (
        "https://www.kaggle.com/api/v1/kernels/list?mine=true&search=arc3-duck&page_size=5",
        "https://www.kaggle.com/api/v1/kernels/list?user=petersharps&search=arc3-duck&page_size=5",
    ):
        try:
            req = urllib.request.Request(url, headers={"Authorization": f"Basic {auth}"})
            body = urllib.request.urlopen(req, timeout=60).read().decode()
            out += f"## {url}\n{body[:4000]}\n\n"
        except Exception as exc:  # noqa: BLE001
            out += f"## {url}\nBŁĄD: {exc}\n\n"
    return out


def op_submit_after_midnight(args: dict, out_dir: Path) -> str:
    """Czeka do początku następnego dnia UTC (reset dziennego slotu),
    potem wykonuje standardowy guarded submit. Limity pętli twarde."""
    import time as _time
    started = dt.datetime.now(dt.timezone.utc)
    text = f"start {started:%Y-%m-%d %H:%M:%S} UTC; czekam na 00:00 UTC...\n"
    print(text, flush=True)
    for i in range(40):  # twardy limit ~3.3h
        now = dt.datetime.now(dt.timezone.utc)
        if now.date() != started.date():
            text += f"\nok, nowy dzień UTC o {now:%H:%M:%S}; odpalam submit\n"
            break
        _time.sleep(300)
    else:
        return text + "PRZEKROCZONY LIMIT CZEKANIA — submit NIE wykonany.\n"
    sub = op_submit(args, out_dir)
    # dorzuć aktualną listę zgłoszeń dla pewności
    code, out = kaggle("competitions", "submissions", "-c", COMP)
    (out_dir / "submissions.txt").write_text(out, encoding="utf-8")
    return text + sub + f"\n## Submissions po submit (rc={code})\n{out[:2000]}\n"


def op_try_v7(args: dict, out_dir: Path) -> str:
    """Po 00:05 UTC: próby push obu v7 (duck-v7 nasz + llm-agent-v7 ich) i statusy.
    Realistycznie: tygodniowa kwota GPU dalej zamknięta -> odmowa w logu.
    Jeśli kwota puści: save-runy ruszają same; smoke/submit wg planu sobotniego."""
    import time as _time
    started = dt.datetime.now(dt.timezone.utc)
    target = started.replace(hour=0, minute=5, second=0, microsecond=0)
    if target > started:
        wait_min = int((target - started).total_seconds() // 60)
        text = f"start {started:%H:%M:%S} UTC; czekam ~{wait_min} min do 00:05 UTC\n"
        print(text, flush=True)
        for _ in range(20):
            if dt.datetime.now(dt.timezone.utc) >= target:
                break
            _time.sleep(300)
    text = f"PRÓBY o {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M:%S} UTC\n\n"
    duck_v7 = OPS_DIR.parent / "duck-v7"
    agent_v7 = OPS_DIR.parent / "llm-agent-v7"
    c1, o1 = kaggle("kernels", "push", "-p", str(duck_v7))
    text += f"## push duck-v7 (nowa wersja petersharps/arc3-duck)\nrc={c1}\n{o1}\n\n"
    c2, o2 = kaggle("kernels", "push", "-p", str(agent_v7))
    text += f"## push llm-agent-v7 (nowy kernel petersharps/arc3-llm-agent-v7)\nrc={c2}\n{o2}\n\n"
    for slug in ("petersharps/arc3-duck", "petersharps/arc3-llm-agent-v7"):
        cs, os_ = kaggle("kernels", "status", slug)
        text += f"## status {slug}\nrc={cs}\n{os_}\n\n"
    return text


def op_pull_original(args: dict, out_dir: Path) -> str:
    """krok 1 planu 45+: pull publicznego oryginalnego kernela Duck (Tufa)."""
    code, out = kaggle("kernels", "pull", "jeroencottaar/tufa-labs-duck-harness-june-30-milestone-winner", "-p", str(out_dir), "-m")
    text = f"## pull oryginalnego Ducka (milestone winner, publiczny)\nrc={code}\n{out}\n"
    meta = out_dir / "kernel-metadata.json"
    if meta.exists():
        text += "\n## ich metadata\n" + meta.read_text(encoding="utf-8")[:1500] + "\n"
    return text


def op_prep_original(args: dict, out_dir: Path) -> str:
    """krok 2: przygotuj petersharps-metadata na bazie pobleanej."""
    src_meta = out_dir / "kernel-metadata.json"
    if not src_meta.exists():
        return "brak metadata w out_dir (najpierw pull-original)"
    blob = json.loads(src_meta.read_text(encoding="utf-8"))
    blob["id"] = "petersharps/arc3-duck-original"
    blob["title"] = "ARC3 Duck Original (Tufa milestone winner)"
    blob["is_private"] = True
    dest = OPS_DIR.parent / "duck-original"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "kernel-metadata.json").write_text(json.dumps(blob, indent=2), encoding="utf-8")
    for f in out_dir.glob("*.ipynb"):
        (dest / f.name).write_bytes(f.read_bytes())
    return f"przygotowane: {dest} -> {[p.name for p in dest.iterdir()]}"


def _chain_branch() -> str:
    return os.environ.get("GITHUB_REF_NAME") or "arena/5ed750ef-smak-domu-konkurs"


def _git_commit_and_push(paths: list[str], message: str) -> str:
    """Commit + push z runnera (bot). Rebase-retry (druga sesja może pchać)."""
    repo = OPS_DIR.parents[2]
    branch = _chain_branch()
    full = [str(repo / p) for p in paths]
    log = []
    subprocess.run(["git", "add", *full], cwd=repo, capture_output=True, text=True)
    r = subprocess.run(["git", "commit", "-q", "-m", message], cwd=repo, capture_output=True, text=True)
    log.append(f"commit rc={r.returncode} {r.stdout}{r.stderr}".strip())
    if r.returncode != 0:
        return "\n".join(log)  # nic do komitu (czysto) — nie pushujemy
    for i in range(5):
        r = subprocess.run(["git", "push", "-q", "origin", f"HEAD:{branch}"], cwd=repo, capture_output=True, text=True)
        log.append(f"push[{i}] rc={r.returncode} {r.stdout}{r.stderr}".strip())
        if r.returncode == 0:
            break
        subprocess.run(["git", "pull", "-q", "--rebase", "origin", branch], cwd=repo, capture_output=True, text=True)
    return "\n".join(log)


def _dispatch_next(next_req: dict) -> str:
    """Zapisz request.json = next, commit+push, dispatch workflow.
    workflow_dispatch utworzony przez GITHUB_TOKEN JEST udokumentowanym
    wyjątkiem od blokady eventów bota — odpala nowy run."""
    req_path = OPS_DIR / "request.json"
    req_path.write_text(json.dumps(next_req, indent=2) + "\n", encoding="utf-8")
    log = _git_commit_and_push(
        ["arc-agi-3/kaggle/ops/request.json"],
        f"ops: request {next_req.get('id')} ({next_req.get('op')}) [auto-chain]",
    )
    code, out = sh(["gh", "workflow", "run", "arc3-ops.yml", "--ref", _chain_branch(),
                    "-R", "peteraangelic-pixel/Smak-Domu-Konkurs"])
    return log + f"\ndispatch rc={code}: {out}\n"


def op_chain(args: dict, out_dir: Path) -> str:
    """Segment łańcucha nocnego: śpij do sleep_until_utc / sleep_minutes,
    potem wykonaj then (op w tym samym runie) i/lub dispatch next request.
    Twardy limit snu 330 min (timeout joba 355)."""
    import time as _time
    now = dt.datetime.now(dt.timezone.utc)
    text = f"chain start {now:%Y-%m-%d %H:%M:%S} UTC\n"
    if args.get("sleep_until_utc"):
        target = dt.datetime.fromisoformat(str(args["sleep_until_utc"])).replace(tzinfo=dt.timezone.utc)
    elif args.get("sleep_minutes"):
        target = now + dt.timedelta(minutes=int(args["sleep_minutes"]))
    else:
        return text + "brak sleep_until_utc/sleep_minutes\n"
    print(text + f"cel: {target:%Y-%m-%d %H:%M:%S} UTC\n", flush=True)
    hard_cap = dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=330)
    while True:
        now = dt.datetime.now(dt.timezone.utc)
        if now >= target or now >= hard_cap:
            break
        _time.sleep(60)
    text += f"koniec snu {now:%Y-%m-%d %H:%M:%S} UTC\n"
    if now < target:
        return text + "HARD CAP — nie obudziłem się na czas; NIE dispatchuję (wymaga interwencji)\n"
    then = args.get("then")
    if then:
        t_name = str(then.get("op") or "")
        t_args = dict(then.get("args") or {})
        if t_name not in OPS:
            return text + f"then: nieznany op {t_name!r}\n"
        text += f"\n== then: {t_name} ==\n" + OPS[t_name](t_args, out_dir) + "\n"
    nxt = args.get("next")
    if nxt:
        text += "\n== dispatch next ==\n" + _dispatch_next(dict(nxt)) + "\n"
    return text


def op_echo(args: dict, out_dir: Path) -> str:
    return f"echo OK; args={args}\n"


def op_push_cpu_test(args: dict, out_dir: Path) -> str:
    """Push testowy CPU (bez kwoty GPU): waliduje utworzenie NOWEGO kernela
    (reguła: title musi slugować się do sluga id). Kopiuje pakiet do out_dir,
    ustawia title/enable_gpu=False, usuwa machine_shape, push, status."""
    pkg_src = OPS_DIR.parent / str(args.get("dir") or "")
    title = str(args.get("title") or "")
    kernel = str(args.get("kernel") or "")
    if not title or not kernel or not (pkg_src / "kernel-metadata.json").exists():
        return "ODMOWA: args.title, args.kernel i args.dir (pakiet z metadata) wymagane\n"
    work = out_dir / "pkg"
    work.mkdir(parents=True, exist_ok=True)
    for f in pkg_src.glob("*.ipynb"):
        (work / f.name).write_bytes(f.read_bytes())
    meta = json.loads((pkg_src / "kernel-metadata.json").read_text(encoding="utf-8"))
    meta["title"] = title
    meta["enable_gpu"] = False
    meta.pop("machine_shape", None)
    (work / "kernel-metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    code, out = kaggle("kernels", "push", "-p", str(work))
    text = f"## push CPU test {kernel} (title={title!r})\nrc={code}\n{out}\n"
    c2, o2 = kaggle("kernels", "status", kernel)
    text += f"\n## status {kernel}\nrc={c2}\n{o2}\n"
    c3, o3 = kaggle("kernels", "list", "-m", "-s", kernel.split("/")[-1], "--page-size", "3")
    text += f"\n## kernels list -m -s {kernel.split('/')[-1]}\nrc={c3}\n{o3}\n"
    return text


def op_midnight_launch(args: dict, out_dir: Path) -> str:
    """00:00 UTC: push GPU duck-original (retry aż kwota przepuści; guard po TREŚCI —
    rc=0 przy kwocie!), potem poll save-runu. COMPLETE/ERROR -> dispatch auto-submit."""
    import time as _time
    kernel = str(args.get("kernel") or "petersharps/arc3-duck-original")
    pkg = OPS_DIR.parent / str(args.get("dir") or "duck-original")
    text = ""
    pushed = False
    for i in range(9):  # 9 x 5 min = 45 min prób pushu
        code, out = kaggle("kernels", "push", "-p", str(pkg))
        text += f"## push[{i}] rc={code}\n{out}\n"
        if code == 0 and "Kernel push error" not in out:
            pushed = True
            break
        _time.sleep(300)
    if not pushed:
        return text + "\nWYNIK: push nie przeszedł po retryach — wymaga interwencji\n"
    # wykryj wersję: regex z outputu pusha, potem kernels list, fallback args/version_hint
    ver = ""
    m = re.search(r"version[:= ]+(\d+)", out, re.IGNORECASE)
    if m:
        ver = m.group(1)
    else:
        c3, o3 = kaggle("kernels", "list", "-m", "-s", kernel.split("/")[-1], "--page-size", "3")
        text += f"\n## kernels list -m -s {kernel.split('/')[-1]}\nrc={c3}\n{o3}\n"
        for line in o3.splitlines():
            if kernel in line:
                nums = re.findall(r"\d+", line)
                if nums:
                    ver = nums[-1]
                break
    if not ver:
        ver = str(args.get("version_hint") or "1")
    text += f"\nwykryta wersja do submitu: {ver}\n"
    for i in range(20):  # 20 x 5 min = ~100 min poll save-runu
        c2, o2 = kaggle("kernels", "status", kernel)
        text += f"## status[{i}] rc={c2} {o2.strip()}\n"
        if "COMPLETE" in o2 or "ERROR" in o2 or "CANCEL" in o2:
            break
        _time.sleep(300)
    nxt = dict(args.get("next") or {})
    if nxt:
        nxt.setdefault("args", {})
        if isinstance(nxt["args"], dict):
            nxt["args"].setdefault("version", ver)
        text += "\n== dispatch auto-submit ==\n" + _dispatch_next(nxt) + "\n"
    return text


def op_auto_submit(args: dict, out_dir: Path) -> str:
    """Poll statusu do COMPLETE (max ~100 min), potem guarded submit
    (limit dzienny + confirm) z parquetem z repo."""
    import time as _time
    kernel = str(args.get("kernel") or "petersharps/arc3-duck-original")
    if not args.get("confirm"):
        return "ODMOWA: op auto-submit wymaga args.confirm=true\n"
    text = ""
    status = ""
    for i in range(20):
        c2, o2 = kaggle("kernels", "status", kernel)
        status = o2.strip()
        text += f"## status[{i}] rc={c2} {status}\n"
        if "COMPLETE" in status or "ERROR" in status or "CANCEL" in status:
            break
        _time.sleep(300)
    if "COMPLETE" not in status:
        return text + "\nWYNIK: save-run nie COMPLETE — submit NIE wykonany\n"
    sub_args = {
        "confirm": True,
        "kernel": kernel,
        "version": str(args.get("version") or "1"),
        "file": str(args.get("file") or "arc-agi-3/kaggle/results/submission.parquet"),
        "message": str(args.get("message")
                       or "arc3-duck-original: Tufa Labs duck harness (June 30 milestone winner, public MIT) rerun by petersharps; attribution: Tufa Labs / jeroencottaar"),
    }
    text += "\n== submit ==\n" + op_submit(sub_args, out_dir) + "\n"
    code, out = kaggle("competitions", "submissions", "-c", COMP)
    (out_dir / "submissions.txt").write_text(out, encoding="utf-8")
    text += f"## submissions po submit (rc={code})\n{out[:2500]}\n"
    return text


OPS = {
    "preflight": op_preflight,
    "submissions": op_submissions,
    "pull-their-duck": op_pull_their_duck,
    "push-duck200k": op_push_duck200k,
    "submit": op_submit,
    "push": op_push,
    "kernel-status": op_kernel_status,
    "kernel-output": op_kernel_output,
    "kernel-info": op_kernel_info,
    "submit-after-midnight": op_submit_after_midnight,
    "try-v7": op_try_v7,
    "pull-original": op_pull_original,
    "prep-original": op_prep_original,
    "chain": op_chain,
    "echo": op_echo,
    "push-cpu-test": op_push_cpu_test,
    "midnight-launch": op_midnight_launch,
    "auto-submit": op_auto_submit,
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
