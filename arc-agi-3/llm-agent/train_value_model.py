"""Trener value modelu 12->64->32->1 — split PER GRA, nie per wiersz.

Dlaczego: stany kolejne w jednej grze są niemal identyczne, więc losowy
80/20 split po wierszach daje walidację praktycznie po tym samym stanie —
tak zawyżał się „acc 0.913" w Pokemonie (obalone przez a450) i tak nie robić.
Tutaj: hold-out = całe gry. Walidacja mierzy generalizację na NIEWIDZIANE gry.

Wejście: CSV z kolumnami `game_id`, `label`, oraz f0..f11 (kolejność = FEATURES).
Wyjście: JSON z wagami dla value_gate.ValueGate (env VALUE_MODEL_JSON).

Użycie:
  python3 train_value_model.py dane.csv --out mlp_arc_weights.json
Wymaga numpy (na Kaggle jest; w sandboxie: pip install --break-system-packages numpy).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import sys
from pathlib import Path

FEATURES = [
    "rows", "cols", "size", "unique_colors", "density", "objects",
    "levels_completed", "actions_on_level", "noop_ratio", "tokens_level",
    "audits_on_level", "steps",
]

H1, H2 = 64, 32


def load_csv(path: str) -> tuple[list[str], list[list[float]], list[int]]:
    games: list[str] = []
    xs: list[list[float]] = []
    ys: list[int] = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        missing = {"game_id", "label", *FEATURES} - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"brak kolumn: {sorted(missing)}")
        for row in reader:
            games.append(row["game_id"])
            xs.append([float(row[f]) for f in FEATURES])
            ys.append(1 if float(row["label"]) >= 0.5 else 0)
    if not xs:
        raise SystemExit("pusty CSV")
    return games, xs, ys


def game_split(games: list[str], holdout: float, seed: int = 7
               ) -> tuple[set[str], set[str]]:
    unique = sorted(set(games))
    rng = random.Random(seed)
    rng.shuffle(unique)
    n_val = max(1, int(len(unique) * holdout))
    return set(unique[n_val:]), set(unique[:n_val])


def init_weights(d: int, seed: int = 13):
    rng = random.Random(seed)

    def rand(a: int, b: int) -> list[list[float]]:
        scale = math.sqrt(2.0 / a)
        return [[rng.gauss(0.0, scale) for _ in range(b)] for _ in range(a)]

    bias = lambda n: [0.0] * n  # noqa: E731
    # kształty pod _forward: W0 (H1, d), W1 (H2, H1), W2 (1, H2)
    return rand(H1, d), bias(H1), rand(H2, H1), bias(H2), rand(1, H2), bias(1)


def _forward(x: list[float], w) -> tuple[list[float], list[float], float]:
    W0, b0, W1, b1, W2, b2 = w
    h1 = [max(0.0, sum(W0[i][j] * x[j] for j in range(len(x))) + b0[i])
          for i in range(H1)]
    h2 = [max(0.0, sum(W1[i][j] * h1[j] for j in range(H1)) + b1[i])
          for i in range(H2)]
    z = sum(W2[0][i] * h2[i] for i in range(H2)) + b2[0]
    return h1, h2, 1.0 / (1.0 + math.exp(-max(-20.0, min(20.0, z))))


def train(xs, ys, epochs: int, lr: float, seed: int = 13):
    w = init_weights(len(xs[0]), seed)
    order = list(range(len(xs)))
    rng = random.Random(seed)
    for _ in range(epochs):
        rng.shuffle(order)
        for idx in order:
            x, y = xs[idx], ys[idx]
            W0, b0, W1, b1, W2, b2 = w
            h1, h2, p = _forward(x, w)
            dz = p - y  # pochodna BCE po z (sigmoid)
            # warstwa 2
            gh2 = [dz * (1.0 if h2[i] > 0 else 0.0) for i in range(H2)]
            for i in range(H2):
                W2[0][i] -= lr * dz * h2[i]
            b2[0] -= lr * dz
            # warstwa 1
            gh1 = [sum(gh2[i] * W1[i][j] for i in range(H2)) for j in range(H1)]
            for i in range(H2):
                for j in range(H1):
                    W1[i][j] -= lr * gh2[i] * h1[j]
                b1[i] -= lr * gh2[i]
            # warstwa 0
            gh0 = [gh1[j] * (1.0 if h1[j] > 0 else 0.0) for j in range(H1)]
            for i in range(H1):
                for j in range(len(x)):
                    W0[i][j] -= lr * gh0[i] * x[j]
                b0[i] -= lr * gh0[i]
    return w


def accuracy(xs, ys, w) -> float:
    good = 0
    for x, y in zip(xs, ys):
        _, _, p = _forward(x, w)
        good += int((p >= 0.5) == bool(y))
    return good / len(xs) if xs else 0.0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv")
    parser.add_argument("--out", default="mlp_arc_weights.json")
    parser.add_argument("--holdout", type=float, default=0.25,
                        help="udział GIER do walidacji (nie wierszy!)")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--lr", type=float, default=0.05)
    args = parser.parse_args(argv)

    import numpy  # noqa: F401  — deklaracja zależności; obliczenia czysty Python

    games, xs, ys = load_csv(args.csv)
    train_ids, val_ids = game_split(games, args.holdout)
    tr_x = [x for g, x in zip(games, xs) if g in train_ids]
    tr_y = [y for g, y in zip(games, ys) if g in train_ids]
    va_x = [x for g, x in zip(games, xs) if g in val_ids]
    va_y = [y for g, y in zip(games, ys) if g in val_ids]
    if not tr_x or not va_x:
        raise SystemExit("za mało gier do splitu")

    base = sum(va_y) / len(va_y)
    w = train(tr_x, tr_y, args.epochs, args.lr)
    acc = accuracy(va_x, va_y, w)

    print(f"gry: train={len(train_ids)} val={len(val_ids)} | "
          f"wiersze: train={len(tr_x)} val={len(va_x)}")
    print(f"walidacja (niewidziane gry): acc={acc:.3f} vs base rate={base:.3f}")
    if acc < base + 0.10:
        print("UWAGA: model niewiele lepszy od zgadywania — NIE włączać gate'a; "
              "potrzebne lepsze cechy albo więcej danych.")

    Path(args.out).write_text(json.dumps({
        "features": FEATURES,
        "thresholds": {"low": 0.3, "high": 0.7},
        "weights": {"W0": w[0], "b0": w[1], "W1": w[2], "b1": w[3],
                    "W2": w[4], "b2": w[5]},
        "meta": {"val_acc": acc, "val_base_rate": base,
                 "games_val": sorted(val_ids)},
    }, indent=1), encoding="utf-8")
    print(f"wagi: {args.out} (env VALUE_MODEL_JSON={args.out} włącza gate)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
