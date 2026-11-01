# Composed repair: active hypothesis test and causal stage ordering

This extends the earlier point-motion model, using TRAINING residuals only. Most remaining errors were in the autonomous actor position:38/96training transitions had wrong actor predictions, versus18dot-set and7block-set errors. Some valid clicks moved no object yet still advanced the actor. Merely tuning the old model's constants could not express that rule.

## One real discriminating experiment

Training observations supported three activation intervals:[10,60],[10,61],[10,62]for click rows. The evaluator chose row62,col32 because the hypotheses disagreed there. A real forward action changed the encoded state, leaving only[10,62]. This is an actual hypothesis→selected experiment→observation→elimination loop, recorded in `active-region.json`; not a synthetic assertion or an uncalled helper. It applies to this observed fixture/context, not arbitrary games.

The learner separated object motion, autonomous actor motion and contact effects. It tested768composed programs on97training transitions (96plus the single active observation), selected one using training only, then checked the old validation bank. The chosen causal model selects the actor's target from the **before** object positions, rather than the already moved positions assumed in the original program. That order was selected from data; the engine implementation was not inspected for rules.

## Fresh final observations

After freezing the program,16new probe episodes used seeds9300–9315. Inputs already present in training, validation or the earlier final bank were removed, as were duplicates inside the new bank.185novel state/action inputs remained.

| Program on the SAME new final inputs | Changed states predicted exactly | Unchanged states predicted exactly | Balanced exact accuracy |
|---|---:|---:|---:|
| Previous point-motion repair | 17/107 | 76/78 | 56.66% |
| Composed repair | 68/107 | 78/78 | 81.78% |

Both finished without model or episode runtime errors. Training balanced exact accuracy rose56.25%→85.42%; validation53.92%→84.31%. Those are prediction metrics, **not Kaggle scores**. The final model still predicts39of107changed states incorrectly. It is not a trusted planner and has not demonstrated any additional completed level.

All observations concern one public environment/level. This is a model-specific program-repair template and an evaluation-only trace-replay fixture, not a general online ARC agent. Do not put its fixed public model, replay prefix or game ID into a competition policy. A transferable implementation would have to infer such hypotheses from the live agent's own observations and pass prediction and action-level validation on more mechanisms.

`manifest.json` fixes the code hash and new final seed bank; `selection.json` and `selected-model.py` were written before `final-episodes.json`. The selected source is saved as exact UTF-8 LF bytes this time. Keep the opened final labels out of further fitting. A next change requires a new final seed bank and a new report.
