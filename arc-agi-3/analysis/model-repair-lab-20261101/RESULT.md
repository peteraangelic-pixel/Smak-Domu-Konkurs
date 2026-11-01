# Model-repair CPU laboratory — prediction improvement, not a ready planner

Latest stage: [composed repair and one actual discriminating experiment](composed/RESULT.md). On a new final bank it predicts68/107changed states correctly versus17/107for the earlier repair, with78/78unchanged states correct. This remains prediction research, not an improved Kaggle agent. The earlier stages below remain unchanged evidence.

The experiment starts from the first complete model program written by the target LLM in the recorded su15 run. It does not read the game's implementation to repair that program. An evaluation-only runner replays a public trace to obtain the fixture, then gathers NEW forward probe episodes. The repairer receives only model code and encoded before/action/after observations. No engine API, game ID or replay prefix is part of a submission policy.

Sixteen processes generated8training and8validation episodes,96transitions each. Click proposals used the existing Rust ctypes connected-component kernel, serial inside each worker; exact frame encoding used the SDK's Python segmentation. Dynamic Python model programs were evaluated in16processes; no Rust speedup is claimed for their execution. The frozen encoder and seed split were recorded before evaluation. This is one public environment/level, not32different games.

## What the experiments found

| Program search | Programs evaluated | Training changed transitions correct | Validation changed correct |
|---|---:|---:|---:|
| Original LLM model | 1 | 0/47 | 0/51 |
| Numeric AST mutations | 3072 | 2/47 | 0/51 |
| Structural guard/distance/rounding/radius mutations | 192 | 1/47 | 0/51 |
| Added missing point-motion branch, train-selected parameters | 193 | 6/47 | 4/51 |

All four retained correct predictions on the unchanged class. Selection used balanced exact-transition accuracy, so a program predicting no change everywhere could not hide behind the many no-op examples. Changing more constants was insufficient: the generated model lacked a branch for moving a single dot to a nearby click. A TRAINING counterexample showed a dot moving from(47,12)to(48,14); the original model returnedNone. The new branch hypothesis came from that training observation, not an engine-source rule.

Because the original holdout had already been used by the numeric experiment, later reports call it validation. After the point-motion program was selected and written to disk, the runner opened a previously unused bank of16new probe seeds. It produced192transitions; after removing inputs already present in training/validation and duplicates within this final bank,185novel state/action inputs remained.

| Frozen program on the new final bank | Changed transitions | Unchanged transitions | Balanced exact accuracy |
|---|---:|---:|---:|
| Original LLM model | 0/101 | 84/84 | 50.00% |
| Repaired model | 16/101 | 84/84 | 57.92% |

All final probe episodes and model evaluations returned without runtime errors. The repaired program still gets85of101changed transitions wrong. **Do not use it as a trusted planner or claim an improved Kaggle agent.** This is a measured proof that adding a missing behavior can improve predictions where thousands of constant changes failed. It does not establish generalization to new games, level completions, or60points.

## Evidence and reproduction

- `base_model.py`, `dataset-manifest.json`, `episode-reports.jsonl`, `train.json`, `holdout.json`: original frozen code and new observations.
- `repair-report.json`, `repair-trials.jsonl`: numeric search and its failure on validation.
- `structural/report.json`: structural search; final bank remained unopened.
- `point-motion/selection.json`, `selected-model.py`, `trials.jsonl`, `final-episodes.json`, `report.json`: frozen point-motion program and independent final observations.
- Scripts: `analysis/model_repair_dataset.py`, `repair_model_constants.py`, `repair_model_structure.py`, `repair_point_motion.py`. They preserve existing result paths rather than overwrite experiments. Use a separate checkout/output path for a rerun.

The original LLM had already seen its historical trajectory; those old transitions were therefore not described as held out. The final observations come from new deterministic probe sequences from the same fixture. Program variants share an encoder and contain a model-specific repair template; this is not yet a general online code-repair system. Terminal transitions are excluded by the evaluator and that censoring is recorded. A follow-up must use fresh final seeds and must diagnose the remaining TRAINING residuals rather than tune against this final bank.

`verification.json` checks disjoint seed banks, selection written before final observations, source identity and counts. Recorded program SHA values hash UTF-8 code strings with LF newlines; Windows `Path.write_text` saved CRLF artifacts. Both normalized program and local artifact hashes are recorded explicitly, with the original files preserved. The same program is being evaluated; raw-byte hashes across newline conversions must not be conflated.
