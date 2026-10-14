#!/usr/bin/env python3
"""Analiza transkryptow i events.jsonl z runow Kaggle — multiprocessing.

Praca na CPU (parsowanie sekcji, zliczanie akcji, hashowanie plansz 64x64)
jest rownoleglena per plik: Pool.map z chunksize=1, wieksze pliki najpierw.
Przy 1 pliku albo --workers 1 liczy sekwencyjnie (narzut puli wiekszy niz zysk).

Uzycie:
  python3 transcript_stats.py KATALOG --json OUT.json
  python3 transcript_stats.py PLIK1 PLIK2 ...
  python3 transcript_stats.py --benchmark [N_PLIKOW]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
import time
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

STEP_MARKER = re.compile(
    r"^--- analysis_step=(\d+) \| action=(\S+) \| (\d\d:\d\d:\d\d) \| ",
    re.MULTILINE,
)
ACTION_RE = re.compile(r"\b(?:ACTION[1-6]|UP|DOWN|LEFT|RIGHT|RESET)\b")


def parse_transcript(text: str) -> dict:
    """Statystyki jednego transkryptu (tekst)."""
    steps = 0
    actions: Counter[str] = Counter()
    think_chars = 0
    prev_step = 0
    for match in STEP_MARKER.finditer(text):
        steps += 1
        prev_step = int(match.group(1))
        actions[match.group(2)] += 1
    # Tekst poza znacznikami = "myslenie" (prompt, plan, narzedzia).
    think_chars = len(STEP_MARKER.sub("", text))
    return {
        "kind": "transcript",
        "steps": steps,
        "max_step_no": prev_step,
        "actions": dict(actions),
        "total_actions": sum(actions.values()),
        "think_chars": think_chars,
        "chars_per_step": round(think_chars / steps) if steps else 0,
    }


def parse_events(text: str) -> dict:
    """Statystyki events.jsonl (plansze 64x64 JSON na linie)."""
    lines = 0
    boards: set[str] = set()
    repeats = 0
    max_repeat = 0
    last: str | None = None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        board = obj.get("board")
        if board is None:
            continue
        lines += 1
        digest = hashlib.md5(json.dumps(board, separators=(",", ":")).encode()).hexdigest()
        boards.add(digest)
        if digest == last:
            repeats += 1
            max_repeat = max(max_repeat, repeats)
        else:
            repeats = 0
        last = digest
    return {
        "kind": "events",
        "boards": lines,
        "unique_boards": len(boards),
        "duplicate_consecutive": repeats,
        "max_consecutive_repeat": max_repeat,
        "diversity": round(len(boards) / lines, 3) if lines else 0,
    }


def _work_one(path_str: str) -> dict:
    """Worker puli: wczytuje jeden plik i zwraca jego statystyki."""
    path = Path(path_str)
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix == ".jsonl":
        result = parse_events(text)
    else:
        result = parse_transcript(text)
    result["file"] = path.name
    result["bytes"] = path.stat().st_size
    return result


def analyze_paths(paths: list[Path], workers: int | None = None) -> list[dict]:
    """Analizuje pliki; multiprocessing gdy wiele plikow i >1 worker."""
    paths = sorted(paths, key=lambda p: p.stat().st_size, reverse=True)
    str_paths = [str(p) for p in paths]
    if len(str_paths) < 2:
        workers = 1
    if workers is None:
        import os

        workers = max(1, min(len(str_paths), os.cpu_count() or 1))
    if workers <= 1:
        return [_work_one(p) for p in str_paths]
    with Pool(processes=workers) as pool:
        return pool.map(_work_one, str_paths, chunksize=1)


def summarize(results: list[dict]) -> str:
    """Zbiorcze podsumowanie po plikach (tabela tekstowa)."""
    if not results:
        return "(brak plikow)"
    lines = []
    transcripts = [r for r in results if r["kind"] == "transcript"]
    events = [r for r in results if r["kind"] == "events"]
    if transcripts:
        lines.append(f"{'plik':<28} {'kroki':>6} {'akcje':>6} {'znaki':>9} {'zn/krok':>8}")
        for r in sorted(transcripts, key=lambda x: x["file"]):
            lines.append(
                f"{r['file']:<28} {r['steps']:>6} {r['total_actions']:>6} "
                f"{r['think_chars']:>9} {r['chars_per_step']:>8}"
            )
        total_steps = sum(r["steps"] for r in transcripts)
        total_actions = sum(r["total_actions"] for r in transcripts)
        if total_steps:
            lines.append(
                f"RAZEM: {total_steps} krokow, {total_actions} akcji "
                f"({total_actions / total_steps:.2f} akcji/krok)"
            )
    if events:
        lines.append(f"\n{'plik':<28} {'plansze':>7} {'unikat.':>7} {'roznor.':>7}")
        for r in sorted(events, key=lambda x: x["file"]):
            lines.append(
                f"{r['file']:<28} {r['boards']:>7} {r['unique_boards']:>7} {r['diversity']:>7}"
            )
    return "\n".join(lines)


def _synth_transcript(seed: int, steps: int = 500) -> str:
    """Deterministyczny syntetyczny transkrypt (~1 MB, jak prawdziwe)."""
    rng = random.Random(seed)
    parts = []
    for i in range(1, steps + 1):
        action = rng.choice(["1", "2", "3", "4", "6"])
        parts.append(f"--- analysis_step={i} | action={action} | 09:{i // 60:02d}:{i % 60:02d} | tool-agent ---\n")
        parts.append("Rozwazam plan i mechanike gry, sprawdzam hipotezy... " * rng.randint(150, 400))
    return "\n".join(parts)


def benchmark(n_files: int = 16) -> str:
    """Sekwencyjnie vs Pool na syntetycznych transkryptach."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        for i in range(n_files):
            p = Path(tmp) / f"synth-{i:02d}.txt"
            p.write_text(_synth_transcript(i), encoding="utf-8")
            paths.append(p)
        t0 = time.perf_counter()
        seq = analyze_paths(paths, workers=1)
        t1 = time.perf_counter()
        par = analyze_paths(paths)  # workers = cpu_count
        t2 = time.perf_counter()
        assert seq == par, "wyniki sekwencyjne i rownolegle roznia sie!"
        speedup = (t1 - t0) / (t2 - t1) if t2 > t1 else float("inf")
        import os

        return (
            f"benchmark: {n_files} plikow syntetycznych; "
            f"rdzenie: {os.cpu_count()}\n"
            f"sekwencyjnie: {t1 - t0:.2f}s | Pool: {t2 - t1:.2f}s | "
            f"przyspieszenie: {speedup:.2f}x (wyniki identyczne)"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="pliki lub katalog")
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--json", dest="json_out", default=None)
    parser.add_argument("--benchmark", action="store_true")
    args = parser.parse_args(argv)

    if args.benchmark:
        print(benchmark())
        return 0
    paths: list[Path] = []
    for raw in args.paths:
        p = Path(raw)
        if p.is_dir():
            paths.extend(sorted(p.iterdir()))
        elif p.is_file():
            paths.append(p)
    if not paths:
        parser.error("podaj plik, katalog albo --benchmark")
    results = analyze_paths(paths, workers=args.workers)
    print(summarize(results))
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"\nJSON: {args.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
