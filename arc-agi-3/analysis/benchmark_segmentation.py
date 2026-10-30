"""Compare the ARC Python and Rust segmentation kernels on identical frames.

Run from the project root, for example:
    python arc-agi-3/analysis/benchmark_segmentation.py --mode blobs --frames 100
    python arc-agi-3/analysis/benchmark_segmentation.py --mode salt --frames 3

The deterministic generators mirror `rust/src/bin/arc3.rs`; Rust is timed once
with one Rayon worker and once with the configured/default worker count.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "llm-agent"))
from grid_utils import segment_grid  # noqa: E402

MASK = (1 << 64) - 1
MULTIPLIER = 6364136223846793005


def _xorshift(state: int) -> int:
    state ^= (state << 13) & MASK
    state ^= state >> 7
    state ^= (state << 17) & MASK
    return state & MASK


def grid_for(mode: str, size: int, seed: int) -> list[list[int]]:
    if mode == "salt":
        state = (seed * MULTIPLIER + 1) & MASK
        grid = []
        for _ in range(size):
            row = []
            for _ in range(size):
                state = _xorshift(state)
                row.append((state >> 33) % 4)
            grid.append(row)
        return grid

    state = (seed * MULTIPLIER + 1442695040888963407) & MASK

    def rand() -> int:
        nonlocal state
        state = _xorshift(state)
        return state

    grid = [[0] * size for _ in range(size)]
    for _ in range(18):
        color = rand() % 5 + 1
        height = rand() % 8 + 3
        width = rand() % 8 + 3
        row0 = rand() % (size - height + 1)
        col0 = rand() % (size - width + 1)
        for row in range(row0, row0 + height):
            for col in range(col0, col0 + width):
                grid[row][col] = color
    return grid


def rust_result(binary: Path, mode: str, size: int, frames: int, threads: int | None) -> dict:
    env = os.environ.copy()
    if threads is not None:
        env["RAYON_NUM_THREADS"] = str(threads)
    else:
        env.pop("RAYON_NUM_THREADS", None)
    proc = subprocess.run(
        [str(binary), "bench", "--size", str(size), "--frames", str(frames), "--mode", mode],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    output = proc.stdout
    def value(pattern: str, cast):
        match = re.search(pattern, output)
        if not match:
            raise RuntimeError(f"Rust output missing {pattern!r}: {output}")
        return cast(match.group(1))
    return {
        "threads": value(r"threads\s*:\s*(\d+)", int),
        "seconds": value(r"wall clock\s*:\s*([\d.]+)", float),
        "frames_per_second": value(r"throughput\s*:\s*([\d.]+)", float),
        "avg_components": value(r"avg components\s*:\s*([\d.]+)", float),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("blobs", "salt"), required=True)
    parser.add_argument("--frames", type=int, default=None)
    parser.add_argument("--size", type=int, default=64)
    parser.add_argument("--rust-binary", type=Path, default=ROOT / "rust" / "target" / "release" / "arc3.exe")
    args = parser.parse_args()
    frames = args.frames or (100 if args.mode == "blobs" else 3)
    if frames < 1 or args.size < 1:
        parser.error("--frames and --size must be positive")
    if not args.rust_binary.is_file():
        parser.error(f"Rust binary not found: {args.rust_binary}; build with cargo build --release")

    grids = [grid_for(args.mode, args.size, seed) for seed in range(1, frames + 1)]
    start = time.perf_counter()
    components = sum(len(segment_grid(grid)["nodes"]) for grid in grids)
    python_seconds = time.perf_counter() - start

    report = {
        "mode": args.mode,
        "grid": f"{args.size}x{args.size}",
        "frames": frames,
        "python": {
            "seconds": round(python_seconds, 6),
            "frames_per_second": round(frames / max(python_seconds, 1e-12), 3),
            "avg_components": round(components / frames, 1),
        },
        "rust_1_thread": rust_result(args.rust_binary, args.mode, args.size, frames, 1),
        "rust_default_threads": rust_result(args.rust_binary, args.mode, args.size, frames, None),
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
