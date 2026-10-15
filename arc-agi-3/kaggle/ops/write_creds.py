"""Zapis poświadczeń Kaggle w runie Actions. Nigdy nie drukuje tokenu.

Akceptuje KAGGLE_API_TOKEN jako:
  - pełny JSON {"username": ..., "key": ...}, albo
  - sam klucz (wtedy username = petersharps).
Pisze $KAGGLE_CONFIG_DIR/kaggle.json (domyślnie ~/.kaggle), chmod 600.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

DEFAULT_USER = "petersharps"


def main() -> int:
    raw = (os.environ.get("KAGGLE_API_TOKEN") or "").strip()
    if not raw:
        print("[creds] KAGGLE_API_TOKEN pusty/brak — ustaw repo secret", flush=True)
        return 1

    username, key = DEFAULT_USER, raw
    if raw.startswith("{"):
        try:
            blob = json.loads(raw)
        except json.JSONDecodeError:
            print("[creds] KAGGLE_API_TOKEN wygląda na JSON, ale nie parsuje się", flush=True)
            return 1
        username = str(blob.get("username") or DEFAULT_USER)
        key = str(blob.get("key") or "")
        if not key:
            print("[creds] w JSON brak pola 'key'", flush=True)
            return 1

    cfg_dir = Path(os.environ.get("KAGGLE_CONFIG_DIR", Path.home() / ".kaggle"))
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cfg_path = cfg_dir / "kaggle.json"
    cfg_path.write_text(json.dumps({"username": username, "key": key}), encoding="utf-8")
    cfg_path.chmod(0o600)
    print(f"[creds] kaggle.json zapisany ({cfg_dir}); username={username}; klucz UKRYTY", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
