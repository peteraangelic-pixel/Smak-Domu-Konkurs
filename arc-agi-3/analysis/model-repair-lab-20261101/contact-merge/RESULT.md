# Contact/merge repair: a more accurate model, still no agent result

1 November 2026. The preceding composed model's TRAINING residuals showed
two missing mechanisms: nearby points merging after movement, and an actor
stopping at its first contact rather than only testing its endpoint.
The proposed hypotheses came from training observations, not engine rules.

`repair_contact_merge.py` evaluated 1783 source variants with 16 processes.
They produced 309 distinct training-prediction fingerprints: source count
is not the number of different realized behaviors. Selection used the 97
training transitions only. The selected program retained radius/speed 8,
added a nearby-point merge and a first-contact test along movement. These
are learned fixture-specific parameters, not general rules for other games.

Training changed-state exact predictions improved 34/48 to 42/48; unchanged
states remained 49/49. The old validation bank improved 35/51 to 42/51
changed states, with 45/45 unchanged states correct. That validation bank
has been consulted in earlier stages; it is not an untouched final test.

## Fresh final bank

Only after source selection, the evaluator generated 16 new forward probe
episodes with seeds 9400–9415. Deduplication against training, validation,
both preceding final banks and other inputs in this bank left 167 inputs.
The manifest declares the new seeds before selection; verification checks
source hashes, seed disjointness, selection-before-final file timing and
independent metric recomputation.

| Frozen model on the same fresh inputs | Changed exact | Unchanged exact | Balanced exact |
|---|---:|---:|---:|
| Previous composed model | 64/94 | 73/73 | 84.04% |
| Contact/merge repair | 81/94 | 73/73 | 93.09% |

Zero model or episode runtime errors. Selected source SHA256:
`d5d1cf89177f5c3fb41df14532a68cb30f2cfae3c7dae9d5b481ab2028c91f79`.
There are still 13 wrong predictions among 94 changing transitions.
This is one public fixture/level, not new completed levels or a Kaggle score.
Do not ship its fixed model, public goal geometry, fixture replay or game ID
as competition policy. The final labels are now open and cannot become
training labels for a supposedly independent continuation.

## Does the improvement survive multiple predicted steps?

`audit_model_rollouts.py` takes the frozen models and the SAME recorded
forward action sequences. It starts from the true state, then rolls the
model forward without resetting to observations inside the window.
No fitting, new environment actions, LLM calls or goal-directed search.
Globally deduplicated novel starting inputs are identical for both models.

| Recorded horizon | Eligible windows | Previous exact endpoint | Repaired exact endpoint |
|---|---:|---:|---:|
| 1 | 167 | 137 | 154 |
| 2 | 151 | 100 | 129 |
| 4 | 119 | 51 | 90 |
| 8 | 59 | 11 | 41 |

The repaired 8-step endpoint accuracy is 41/59 =69.49%, leaving 18 incorrect
rollouts. Windows overlap and are not independent trials. This is useful
evidence of compounding-error limits, not a calibrated probability for
arbitrary plans. A better one-step model is still insufficient to trust a
long open-loop plan.

The first rollout audit only deduplicated inside each episode and retained
two duplicate starts across episodes. Its raw outputs remain in
`../contact-rollouts/`, marked superseded. The corrected authoritative audit
is `../contact-rollouts-dedup/`; its horizon-1 counts match `report.json`.
No model was refit or selected using either rollout audit.

A posthoc encoded-state alias audit across all 769 recorded transitions
found 726 unique state/action inputs and no conflicting observed outputs.
This finite check does not prove the encoder is a sufficient Markov state
or cover unseen actions; no final labels were used for another fit.

## Reproduction

From `arc-agi-3` with the existing local environment:

```
.venv-local/Scripts/python.exe -X utf8 analysis/repair_contact_merge.py
.venv-local/Scripts/python.exe -X utf8 analysis/audit_model_rollouts.py --lab analysis/model-repair-lab-20261101 --out analysis/model-repair-lab-20261101/contact-rollouts-dedup
```

Both commands refuse an existing output directory; retain the original
files and use a fresh isolated checkout for reproduction. The repair stage
depends on the frozen preceding model and dataset files preserved in this
lab. Rust ctypes supplies pixel click proposals in fresh episodes; model
programs run in Python subprocesses, not Rust. No LLM speedup is claimed.

Next priority: the full-agent phase-lesson result and its real prediction/
observation behavior. Further fitting of this fixture alone does not prove
coverage on more mechanisms. Use the observed failure of long rollouts to
motivate bounded execution and rechecking live observations, without
asserting that a new policy has already improved completions.
