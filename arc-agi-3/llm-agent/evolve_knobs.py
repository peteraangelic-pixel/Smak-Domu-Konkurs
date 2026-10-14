"""CEM — ewolucja KNOBS (wzorzec z projektu Pokemon, c87f7a48).

Ich wynik: 26 pokręteł, 100 mutantów × 138 gier, 163 s na FFI → best 0.879
(+pkt tam, gdzie płytkie ML dało ±0). U nas evaluator jest drogi (GPU/LM Studio),
więc skrypt: (1) realizuje CEM na pluggable fitness, (2) ma wbudowany toy-fitness
do testów, (3) adapter do prawdziwego ewaluatora zostawiony jako interfejs.

Użycie (gdy masz evaluator):
  python3 evolve_knobs.py --fitness moj_modul:funkcja --gens 4 --pop 8
Fitness(knobs: dict) -> float (im wyżej tym lepiej); mutanty to PODZBIORY KNOBS.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

from knobs import KNOBS

# Które pokrętła ewoluować (te, o które realnie warto pytać evaluator):
EVOLVABLE = {
    "AUDIT_ACTIONS": (20, 80),
    "AUDIT_ACTIONS_REARM": (8, 25),
    "AUDIT_TOKENS": (30_000, 90_000),
    "AUDIT_TOKENS_REARM": (10_000, 35_000),
    "TEMP_FRESH": (0.5, 0.9),
    "TEMP_STUCK": (0.7, 1.1),
    "PROBE_MAX": (2, 6),
    "NOOP_TRIGGER": (2, 5),
}


def mutate(mean: dict[str, float], std: dict[str, float], rng: random.Random) -> dict[str, float]:
    """Jeden mutant: próbkowanie gaussowskie w granicach [lo, hi]."""
    child: dict[str, float] = {}
    for key, (lo, hi) in EVOLVABLE.items():
        value = rng.gauss(mean[key], std[key])
        child[key] = max(lo, min(hi, value))
    return child


def cem(fitness, generations: int, population: int, elite_frac: float = 0.25,
        init_std_frac: float = 0.3, seed: int = 9, verbose: bool = True
        ) -> tuple[dict[str, float], float]:
    """Cross-Entropy Method nad EVOLVABLE. Zwraca (najlepsze knobs, fitness)."""
    rng = random.Random(seed)
    mean = {key: KNOBS[key] for key in EVOLVABLE}
    std = {key: (hi - lo) * init_std_frac for key, (lo, hi) in EVOLVABLE.items()}
    n_elite = max(2, int(population * elite_frac))
    best_key, best_value = dict(mean), float("-inf")

    for gen in range(generations):
        candidates = [dict(mutate(mean, std, rng)) for _ in range(population)]
        scored = []
        for knobs in candidates:
            value = fitness(knobs)
            scored.append((value, knobs))
        scored.sort(key=lambda pair: -pair[0])
        elite = [knobs for _, knobs in scored[:n_elite]]
        if scored[0][0] > best_value:
            best_value, best_key = scored[0]

        for key in EVOLVABLE:
            values = [knobs[key] for knobs in elite]
            mean[key] = sum(values) / len(values)
            var = sum((v - mean[key]) ** 2 for v in values) / len(values)
            std[key] = max(math_sqrt(var), (EVOLVABLE[key][1] - EVOLVABLE[key][0]) * 0.02)
        if verbose:
            print(f"gen {gen}: best={scored[0][0]:.4f} mean_top={sum(v for v, _ in scored[:n_elite]) / n_elite:.4f}")

    return best_key, best_value


def math_sqrt(x: float) -> float:
    return x ** 0.5


def toy_fitness(knobs: dict[str, float]) -> float:
    """Zamknięty toy: optimum w AUDIT_ACTIONS=55, TEMP_STUCK=0.85 (do testów)."""
    return -(
        ((knobs["AUDIT_ACTIONS"] - 55) / 15) ** 2
        + ((knobs["TEMP_STUCK"] - 0.85) / 0.1) ** 2
    )


def load_fitness(spec: str):
    """`modul:funkcja` -> funkcja fitness."""
    module_name, _, func_name = spec.partition(":")
    if not func_name:
        raise SystemExit("--fitness w formacie modul:funkcja")
    import importlib
    module = importlib.import_module(module_name)
    return getattr(module, func_name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fitness", default=None,
                        help="modul:funkcja; brak = toy_fitness (do testów)")
    parser.add_argument("--gens", type=int, default=4)
    parser.add_argument("--pop", type=int, default=8)
    parser.add_argument("--out", default="best_knobs.json")
    args = parser.parse_args(argv)

    fitness = toy_fitness if args.fitness is None else load_fitness(args.fitness)
    best, value = cem(fitness, args.gens, args.pop)
    print(f"best fitness={value:.4f}")
    Path(args.out).write_text(json.dumps(best, indent=1), encoding="utf-8")
    print(f"zapis: {args.out} → użyj jako ARC3_KNOBS_JSON po weryfikacji paired A/B")
    return 0


if __name__ == "__main__":
    sys.exit(main())
