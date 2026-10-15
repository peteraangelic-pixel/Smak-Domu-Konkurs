"""Przygotowanie uwierzytelnienia Kaggle w runie Actions. Nigdy nie drukuje tokenu.

Sekret KAGGLE_API_TOKEN może być:
  a) gołym tokenem z UI Kaggle (Settings → API) — wtedy zostaje jak jest,
  b) legacy JSON {"username": ..., "key": ...} — wtedy wyciągamy `key`
     i to ono staje się KAGGLE_API_TOKEN (przez $GITHUB_ENV, bez echo),
a dodatkowo zawsze zapisujemy ~/.kaggle/access_token (Option B CLI 2.x)
i ~/.kaggle/kaggle.json (fallback dla CLI 1.x).
Diagnostyka: wyłącznie długość i kształt — nigdy zawartość.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

DEFAULT_USER = "petersharps"


def main() -> int:
    raw = (os.environ.get("KAGGLE_API_TOKEN") or "").strip()
    if not raw:
        print("[auth] KAGGLE_API_TOKEN pusty/brak — sprawdź repo secret", flush=True)
        return 1
    print(f"[auth] sekret obecny: len={len(raw)}, shape={'json' if raw.startswith('{') else 'plain'}", flush=True)

    username, key = DEFAULT_USER, raw
    if raw.startswith("{"):
        try:
            blob = json.loads(raw)
        except json.JSONDecodeError:
            print("[auth] sekret wygląda na JSON, ale nie parsuje się", flush=True)
            return 1
        username = str(blob.get("username") or DEFAULT_USER)
        key = str(blob.get("key") or "")
        if not key:
            print("[auth] w JSON brak pola 'key'", flush=True)
            return 1
        print(f"[auth] legacy JSON rozpakowany: username={username}, key len={len(key)}", flush=True)

    cfg_dir = Path(os.environ.get("KAGGLE_CONFIG_DIR", str(Path.home() / ".kaggle")))
    cfg_dir.mkdir(parents=True, exist_ok=True)
    # Option B (CLI 2.x): plik access_token z gołym tokenem/kluczem
    token_file = cfg_dir / "access_token"
    token_file.write_text(key + "\n", encoding="utf-8")
    token_file.chmod(0o600)
    # Fallback (CLI 1.x): kaggle.json {username,key}
    legacy = cfg_dir / "kaggle.json"
    legacy.write_text(json.dumps({"username": username, "key": key}), encoding="utf-8")
    legacy.chmod(0o600)

    # Przepnij rozpakowany klucz do kolejnych kroków (bez echo wartości).
    gh_env = os.environ.get("GITHUB_ENV")
    if gh_env:
        with open(gh_env, "a", encoding="utf-8") as fh:
            fh.write(f"KAGGLE_API_TOKEN={key}\n")
        print("[auth] KAGGLE_API_TOKEN przepięty do kolejnych kroków (wartość UKRYTA)", flush=True)
    print(f"[auth] pliki zapisane w {cfg_dir}: access_token + kaggle.json", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
