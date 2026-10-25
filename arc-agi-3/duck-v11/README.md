# ARC-AGI-3 — arc3-duck-v11-plan-safe

Candidate built from the e499c604 v10 package. It keeps the verified chunked harness patch, the `commit(plan)` action-by-action checks, and the stuck-level escalation after 60 actions.

## Change in this version

During the competition rerun, the prior notebook raised solver concurrency to 120 against a backend configured for 10 active requests. This version caps both `bm.solver.concurrency` and `ARC3_MAX_ACTIVE_STREAMS` at 10 for the submission path. That is intended to prevent the high-fanout failure mode described in the branch notes. It does not prove that concurrency alone caused the 0.00 score; the scoring rerun log is still needed to establish that.

The smoke path and the rest of the agent are unchanged so the next measured result can isolate the submission concurrency correction. The profile remains `plan`, which enables `commit(plan)` and the 60-action escalation. The `commit(plan)` mechanism checks each predicted transition and stops when an expectation fails; the model still has to infer the game's mechanics and produce a useful plan.

## Important limitation

This is a candidate, not a demonstrated 50+ solver. The supplied notes report a best prior leaderboard result of 26.25, a c45 rerun of 0.00, and an unmeasured v10 `commit(plan)` score. Those results do not support a promise of 50+. A live Kaggle run, per-game diagnostics, and a score comparison are required before claiming improvement. Public leaderboard score also does not guarantee a top-five private leaderboard finish.

## Kaggle files

- `arc3-duck-v11.ipynb`
- `kernel-metadata-v11.json`

The metadata retains the v10 dataset, competition, and model inputs and uses a new kernel id. Review the Kaggle rerun log before spending another full GPU slot; do not infer success from the interactive smoke alone.