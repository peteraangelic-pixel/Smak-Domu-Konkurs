"""Value gate stanu gry (v6.5) — pomysł z ich v5.1, bez ich wad.

Różnice wobec `llm_policy_v5_1.py` (1675aa4):
- Brak wag => gate jest WYŁĄCZONY (u nich: losowa inicjalizacja = szum).
- Predykcja wymaga JSON z wagami (z train_value_model.py) podanym przez
  env VALUE_MODEL_JSON; każda usterka = None (cisza), nigdy losowy wynik.
- Split treningowy per GRA jest w trainerze — nie ma wycieku wierszowego,
  który zawyżał „acc 0.913" w Pokemonie (stany kolejne są niemal identyczne).

Cechy: 12 sygnałów z FrameInfo i stanu polityki, wszystkie w [0, 1].
"""

from __future__ import annotations

import json
import os
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # tylko dla typów; unika cyklicznego importu
    from . import llm_policy as _lp

FEATURES: list[str] = [
    "rows",              # grid.rows / 64
    "cols",              # grid.cols / 64
    "size",              # rows*cols / 4096
    "unique_colors",     # unikalne kolory / 16
    "density",           # udział pól != 0
    "objects",           # obiekty z segmentacji / 30
    "levels_completed",  # levels_completed / 5
    "actions_on_level",  # akcje na poziomie / 120
    "noop_ratio",        # no-opy w oknie 10
    "tokens_level",      # tokeny na poziomie / 100k
    "audits_on_level",   # audyty na poziomie / 3
    "steps",             # frame.step / 115 (limit kroków poziomu)
]

_OBJ_RE = re.compile(r"Objects:\s*(\d+)")


def extract_features(policy: Any, frame: Any) -> list[float]:
    """12 cech stanu w stałej kolejności FEATURES. Deterministyczne."""
    rows, cols = frame.shape
    grid = frame.grid
    colors: set[int] = set()
    nonzero = 0
    total = 0
    for row in grid:
        for cell in row:
            total += 1
            if cell:
                nonzero += 1
                colors.add(cell)

    seg = frame.segmentation_summary()
    match = _OBJ_RE.search(seg)
    objects = int(match.group(1)) if match else 0

    noop_total = len(getattr(policy, "_noop_recent", []) or [])
    noops = sum(1 for _, changed in getattr(policy, "_noop_recent", []) if not changed)
    noop_ratio = noops / noop_total if noop_total else 0.0

    level_tokens = max(0, policy.total_tokens - policy._level_start_tokens) \
        if hasattr(policy, "_level_start_tokens") else 0

    return [
        min(1.0, rows / 64.0),
        min(1.0, cols / 64.0),
        min(1.0, (rows * cols) / 4096.0),
        min(1.0, len(colors) / 16.0),
        nonzero / total if total else 0.0,
        min(1.0, objects / 30.0),
        min(1.0, frame.levels_completed / 5.0),
        min(1.0, getattr(policy, "_actions_on_level", 0) / 120.0),
        noop_ratio,
        min(1.0, level_tokens / 100_000.0),
        min(1.0, getattr(policy, "_audits_on_level", 0) / 3.0),
        min(1.0, frame.step / 115.0),
    ]


class ValueGate:
    """Opcjonalny, wytrenowany oceniający stanu. `ok=False` => całkiem wyłączony."""

    def __init__(self, weights: dict[str, list[list[float]]], thresholds: dict[str, float]):
        self.W0 = weights["W0"]
        self.b0 = weights["b0"]
        self.W1 = weights["W1"]
        self.b1 = weights["b1"]
        self.W2 = weights["W2"]
        self.b2 = weights["b2"]
        self.features: list[str] = list(weights.get("features", FEATURES))
        self.low = float(thresholds.get("low", 0.3))
        self.high = float(thresholds.get("high", 0.7))
        self.ok = True

    @classmethod
    def load(cls, path: str | None) -> "ValueGate | None":
        """Wczytaj wagi z JSON. Brak ścieżki/pliku/błędu => None (gate OFF)."""
        if not path:
            return None
        try:
            with open(path, encoding="utf-8") as fh:
                blob = json.load(fh)
            return cls(blob["weights"], blob.get("thresholds", {}))
        except (OSError, KeyError, ValueError, TypeError):
            return None

    @classmethod
    def from_env(cls) -> "ValueGate | None":
        return cls.load(os.environ.get("VALUE_MODEL_JSON", ""))

    @staticmethod
    def _forward_x(x: list[float], W0: list[list[float]], b0: list[float],
                   W1: list[list[float]], b1: list[float],
                   W2: list[list[float]], b2: list[float]) -> float:
        h1 = [max(0.0, sum(w[j] * x[j] for j in range(len(x))) + b)
              for w, b in zip(W0, b0)]
        h2 = [max(0.0, sum(w[j] * h1[j] for j in range(len(h1))) + b)
              for w, b in zip(W1, b1)]
        z = sum(w[0] * h2[j] for j, w in enumerate(W2)) + b2[0]
        return 1.0 / (1.0 + pow(2.718281828459045, -max(-20.0, min(20.0, z))))

    def _forward(self, x: list[float]) -> float:
        # Czysty Python: sieć ma 128+64 neuronów, wywoływana max raz na turę LLM.
        return self._forward_x(x, self.W0, self.b0, self.W1, self.b1,
                               self.W2, self.b2)

    def value(self, policy: Any, frame: Any) -> float | None:
        """Wartość stanu w [0,1] albo None, gdy gate wyłączony/uszkodzony."""
        if not getattr(self, "ok", False):
            return None
        try:
            x = extract_features(policy, frame)
            if len(x) != len(self.features):
                return None
            return self._forward(x)
        except Exception:
            self.ok = False  # nigdy nie ryzykuj gry błędem oceniającego
            return None
