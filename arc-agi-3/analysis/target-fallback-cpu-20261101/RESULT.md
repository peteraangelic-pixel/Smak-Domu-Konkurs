# Targeted fallback test — no promotion

Twelve jobs finished: three quarantined clone backends, two arms, two fresh replicas. Budgets were identical: node50000/sec120/max6, hard process timeout240s; at most12 active workers in a16-slot pool, inner threads1, Rust FFI features. Non-timeout search solutions would be independently replayed on a fresh original engine.

| Arm | Jobs | Verified completions | Timeouts |
|---|---:|---:|---:|
| Original priority, beam120 | 6 | 0 | 1 |
| Full fallback guard: original priority and beam120 when clone unsupported | 6 | 0 | 2 |

All three timeouts are lf52. bp35 and tn36 returned without process errors. The proposed full fallback guard therefore did **not** establish a timeout fix and is not promoted. It uses the same effective heuristic as control on these fixtures; timeout variation also appears in control. The240s process guard is distinct from the soft per-game search budget and should not be presented as a precisely enforced120s end-to-end limit.

Keep `LOCAL-SEARCH-PROFILE-20261101.json` experimental and keep the original default. Do not run another full matrix to rescue this result. Raw `trials.jsonl`, `manifest.json` and `report.json` remain authoritative; this is an offline infrastructure experiment, not a result for the LLM agent or Kaggle.
