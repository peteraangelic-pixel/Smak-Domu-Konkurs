# Evolution from Kaggriculture applied to the ARC local lab

Reviewed riemann branches on 30 October 2026 through the GitHub connector.

Sources

- arena/01a087c0-riemann at 7a3e4ca78e40d3b905c0143c764b69b29ee7bd9b, kaggriculture_meta_lab/seat_087c0/scripts/search_rust_evolve.py
- arena/01a075fa-riemann at 41b1641a2f1fef01c33fb594b40202bee8a29194, kaggriculture_meta_lab/kaggriculture_lab/reactive_genetics.py
- arena/01a0712c-riemann at c5030cfd941e05ba86c97cb0d1b8f700d8c55755, kaggriculture/research/V8_EVOLUTION_LAB_20260910.md

The Kaggriculture search breeds bounded genomes, preserves control clones,
evaluates against fixed controls on matched seeds and both seats, and tests
finalists on separate seeds with regression thresholds. The Rust path batches
jobs to kg_sim. It has a native implementation of the game transitions.

One V8 report records 268800 Rust games without improvement over V7. Many
nominal genomes collapsed to the same feasible actions. The selected result
matched V7 on all 1680 cases of a separate comparison. Candidate diversity and
an independent promotion gate mattered as much as throughput.

The ARC implementation in evolve_search.py reuses that experimental structure
for six bounded search settings. It uses 16 game processes and the Rust FFI
candidate kernel. Every solved path is replay-checked by sweep2.py.

The first pilot executed 83 distinct configuration/game trials in 27.2 seconds,
with zero execution errors and no strict training completion improvement. It
used 300 nodes per search and one level. That budget is insufficient for many
games, so the second pilot increases it to 2000 nodes and screens on six games.

The family split is 17 training games and eight validation games. All 25 public
games were previously inspected, so this validation is exploratory. Changing
the breeding RNG seed produces different configurations, not new game families.
Each output directory pins source hashes, budgets, trial logs and selection.

The objective is weighted completion coverage and completed levels. It is an
upper bound on score at that depth and does not measure action efficiency or
predict the hidden Kaggle score. Ranking a search that clones the true engine
does not establish performance of a submitted LLM world-model planner. Transfer
requires a subsequent full-agent evaluation from allowed observations.

Next search spaces can include observation encoding, model validation rules,
exploration policies and execution policies, with one shared evaluation budget
and matched conditions. Full agents need actual model inference on every run.
CPU kernel timings cannot determine that throughput. A small LM Studio model
can propose or screen code changes and exercise parsers, but its performance
cannot substitute for the target competition model.

The LM Studio server at localhost:1234 was unreachable during this review.
The CPU pilots do not require it.

## Second pilot results

The second campaign used eight individuals, two generations, six screening
games, 2000 nodes and an eight-second soft game budget. It was interrupted
after 47 completed trials because one bp35 engine operation stopped returning.
External subprocess timeouts and reuse of matching saved trials were added.

The resumed campaign recorded 127 trials in total, including 47 reused trials.
The 80 new trials plus selection took 49.1 seconds. Saved trials had zero errors.
The Windows launcher adapter was further changed to invoke the base interpreter
directly, preventing a venv forwarding process from defeating timeout ownership.
That adapter was tested on a separate ft09 job. The resumed parent had already
loaded its earlier launcher. Game-search code and genes were unchanged by this
launcher adjustment.

| Variant | Training, 17 games | Validation, 8 games |
|---|---:|---:|
| Control | 2 completed levels | 2 completed levels |
| Selected beam32, click candidates12 | 4 completed levels | 2 completed levels |

The selected genome sets bfs_branch=0, beam=32, max_clicks=40,
click_candidates=12, min_moves=3 and calib_step=4. It searched fewer nodes
than control at both stages. The validation showed equal completion coverage.
No promotion or hidden-score claim follows from this pilot.

Evidence is in evolution-watchdog-20261030/report.json, manifest.json and
trials.jsonl. The first pilot is in evolution-pilot-20261030/. Reuse requires
matching budgets, game hashes and the search/FFI wrapper source hashes.

Reproduction from the project root

```powershell
& arc-agi-3/.venv-local/Scripts/python.exe arc-agi-3/analysis/evolve_search.py --out arc-agi-3/analysis/evolution-new-run --population 8 --generations 2 --screen-games 6 --node-cap 2000 --sec-cap 8
```

Use a fresh output directory. An optional --reuse directory supplies matching
completed trials. Each run starts up to 16 independent game processes, invokes
the Rust candidate kernel through FFI, and records per-trial results as they
finish. The supervisor uses threads only to launch and wait for those processes.
