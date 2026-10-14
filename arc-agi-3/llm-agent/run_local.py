"""Lokalny przebieg jednej gry ARC-AGI-3: nasz agent + LM Studio + arcengine.

Odpowiednik `run_local_v*.py` drugiej gałęzi, dla NASZEJ polityki (llm_policy.py).
Praca lokalna = testy pętli, parsowania i knobów — NIE ocena jakości
(lokalny model ≠ Qwen3.6-27B z konkursu).

Wymagania (po stronie Twojej maszyny):
  1. LM Studio: załaduj model, zakładka Developer → Start Server (port 1234).
  2. `pip install --no-deps --ignore-requires-python arcengine`
     `pip install pydantic numpy pillow`   (Python 3.11 działa mimo wymogu 3.12)
  3. Pliki gier demo: katalog `<g>/<g>/<g>.py` (environment_files w repo Pokemon).

Użycie:
  LLM_BASE_URL=http://127.0.0.1:1234/v1 LLM_MODEL_ID=<id-modelu> \
      python3 run_local.py <GAMES_DIR> ft09 --max-actions 40
Tryb `--mock` nie potrzebuje arcengine ani LM Studio (test okablowania).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import types as _types
_pkg = _types.ModuleType("llmagent")  # katalog ma myślnik — alias pakietu
_pkg.__path__ = [str(Path(__file__).resolve().parent)]
sys.modules.setdefault("llmagent", _pkg)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("games_dir", nargs="?", default="")
    parser.add_argument("game", nargs="?", default="")
    parser.add_argument("--max-actions", type=int, default=40)
    parser.add_argument("--mock", action="store_true",
                        help="bez arcengine/LM Studio: atrapy klatek, test okablowania")
    parser.add_argument("--png-last", default=None)
    args = parser.parse_args()

    if args.mock:
        from local_eval import play_mock
        result = play_mock(args.game or "mock", max_actions=args.max_actions)
    else:
        if not args.games_dir or not args.game:
            parser.error("podaj GAMES_DIR i GAME (albo --mock)")
        from local_eval import play_one
        result = play_one(args.games_dir, args.game,
                          max_actions=args.max_actions,
                          knobs_json="", png_last=args.png_last)
    print(json.dumps(result, indent=1))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    sys.exit(main())
