# Local Rust FFI and multiprocessing

The local sweep defaults to the Rust candidate kernel and 16 Python game processes.
Run from PowerShell with ./arc-agi-3/analysis/RUN-PC.ps1. Optional parameters are
-Only ft09,lp85, -NodeCap 20000, -Seconds 90 and -Output <path>.

rust/src/ffi.rs implements the sweep's candidate extraction with the same ordering
as its original Python implementation. Cargo produces arc3.dll on Windows.
analysis/native_kernels.py calls it directly through ctypes and NumPy buffers.
The library must be present. Missing Rust produces an error before worker startup.
--backend python selects the comparison control explicitly.

For a single search frame the Rust call uses one thread. Across independent games,
16 Python processes execute the real arcengine logic and invoke the DLL. The
batched FFI entry point uses Rayon when parallel=True. benchmark_native.py limits
that batch pool to 16 threads. Avoid nesting 16 Rayon threads inside each worker.

Measured on this PC on 30 October 2026, best of three timing repetitions including
the Python/FFI conversion and output construction

| Input batch | Python | Rust serial FFI | Rust FFI + Rayon16 |
|---|---:|---:|---:|
| 25 public initial frames | 134.99 ms | 3.08 ms | 1.45 ms |
| 64 seeded random frames | 379.70 ms | 21.38 ms | 6.48 ms |

Candidate outputs matched in 267 frame/limit cases, using limits 1, 3 and 28,
with both serial and parallel native execution. Existing Rust suite passes 36 tests.
The benchmark can be repeated with the local venv Python and benchmark_native.py.

The end-to-end 3-game smoke used 16 workers, a 2000-node limit and a 25-second
game budget. Python and Rust both solved ft09 in 4 actions and lp85 in 5 actions.
Both exhausted the node limit on tu93. Rounded runtime was 2.9/2.8 seconds for
ft09, 1.3/1.3 for lp85 and 3.7/3.6 for tu93. This small smoke establishes matching
search results. The overall timing difference needs repeated measurements.

The native acceleration currently covers candidate extraction. Game transitions
and deepcopy remain in Python. Large batch speedups do not describe the whole
search. Results are stored in native-benchmark-results.json and the two
sweep-*-control/ffi JSONL files in this directory.

This is the local development harness. The Kaggle v18 notebook remains a separate
artifact and needs comparison with the full target model.
