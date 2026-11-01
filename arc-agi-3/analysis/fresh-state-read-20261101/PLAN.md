# Fresh-board read after a no-op

Status: COMPLETE and REJECTED,27levels /22.5073950, new zero dc22. See RESULT.md and raw results. Do not repeat or promote based on the earlier infrastructure verification.

Candidate: exactv3 plus one sandbox behavior change. SHA517ef0970880357c70fd2c76fa1fd53288833839f60dc09c4067a0894af1fe6e. No scratchcache, nudge, slim, scope change or solved-level memory. Base SHA8d0195f92c5518a41d14edbfca596b72c27690f269f681bbaa9af0bc3d257bcc. Environment/model/budgets remain unchanged.

Motivation: actual control snippets explicitly recompute positions after an UP no-op and then try LEFT; the stale-state latch still rejects LEFT. The existing error tells the model to re-read current_frame. This variant makes a real read of the current FrameView.ascii or segmentation clear only that latch. Reading before the no-op, old aliases, history frames or step/level metadata does not clear it. Internal frame refreshes inside action() do not count as user reads.

KnownNoOpActionError, KnownDeathActionError, RepeatedActionInStateError and TerminalStateActionError remain. This is unrelated to the rejected rule based on three identical actions. Batched actions without an intervening board read retain their behavior. A board read does not prove correct reasoning, so the change could also permit bad moves: only the full agent test can decide its value.

Actual isolated sandbox tests and actual ToolAgent callback fixtures passed on the shipped clean materialization. `FRESH_STATE_READ reobserved=1` is emitted only when the current board was read after the latch armed. Tests cover both positive reads and negative/stale reads, other guard preservation, host-internal reads and idempotence. Synthetic fixtures are infrastructure evidence, not completed game levels or LLM results.

Reproduce using analysis/build_v3_fresh_read.py, analysis/materialize_duck.py with a NEW output directory, then analysis/verify_fresh_state_read.py --source NEW_OUTPUT/ARC3-Inference --out NEW_OUTPUT/verification.json. Source-manifest.json pins all four clean patches. Only sandbox.py and the new utils/fresh_state_read.py change.

Run one authorized private target test through fresh-read-smoke only after checking that no previous GPU run is active; confirm canonical slug/version, then fresh-read-watch. Compare the same ten games, target model,48min/concurrency10 with BOTH exact-v3 controls. Check real tool-result markers, completions per game, new zeros, errors and token/log telemetry. A higher single score needs replication. Do not submit to the competition automatically.
