# Observation scratch-cache experiment

Prepared notebook: `duck-lab-candidates/v3-observation-cache/agent.ipynb`.
SHA256: `79ce4a8359426c17d15703bddab4c2a30d05b295918aa5955d167e9b5b65c311`.
Base: exact v3, SHA `8d0195f92c5518a41d14edbfca596b72c27690f269f681bbaa9af0bc3d257bcc`.
Status: packaged, actual shipped sandbox verified, private version1 accepted; target-model result pending. RUN.json pins launch41327293449 and watcher41327369505. No quality measurement yet.

One mechanism: retain bounded literal scratch variables across read-only snippets on the identical observation. Real actions, attempted invalid actions, errors, changed frames, step, level, runtime path or agent identity invalidate the cache. Host invalidation occurs before invoking the action callback; a child flag also catches attempts rejected before the callback. No functions, modules, objects, pickle or eval are stored. Limits: 64 names / 65536 UTF-8 bytes. Existing function retention and all v3 budget/env settings are preserved; no validation nudge, slim, scope change or solved-level memory is included.

The system prompt and tool description now explain this bounded lifetime. `OBSERVATION_CACHE restored=N` in a tool result reports actual restoration, rather than merely presence of the API text. Larger Python state such as NumPy arrays is intentionally skipped. The cache does not preserve object alias identity across calls; literal values are reconstructed. Read-only variables can still contain stale model assumptions despite unchanged observations, so this is an experiment rather than an asserted improvement.

Reproduction from the project root, using `.venv-local/Scripts/python.exe` under `arc-agi-3`:

```powershell
& arc-agi-3/.venv-local/Scripts/python.exe -X utf8 arc-agi-3/analysis/build_v3_observation_cache.py
# materialize_duck requires a NEW output directory
& arc-agi-3/.venv-local/Scripts/python.exe -X utf8 arc-agi-3/analysis/materialize_duck.py arc-agi-3/duck-lab-candidates/v3-observation-cache/agent.ipynb NEW_OUTPUT_DIRECTORY
& arc-agi-3/.venv-local/Scripts/python.exe -X utf8 arc-agi-3/analysis/verify_observation_cache_sandbox.py --source NEW_OUTPUT_DIRECTORY/ARC3-Inference --out NEW_OUTPUT_DIRECTORY/verification.json
& arc-agi-3/.venv-local/Scripts/python.exe -X utf8 arc-agi-3/analysis/verify_observation_literal_cache.py
```

Saved `shipped-verification.json` covers actual ToolAgent, real isolated subprocesses, invalidation boundaries, agent isolation, protected globals, restore telemetry and rendered prompt. `shipped-materialized/source-manifest.json` pins the four clean patches and shipped source hashes. These are infrastructure checks, not game completions.

Validation-retest/1 finished32/29.47217 and was not promoted. Its raw result and analysis were saved before launching this independent experiment. Launch artifact confirms canonical `petersharps/arc3-duck-codex-v3-observation-cache-1101/1`; observation-cache-watch is read-only. Do not launch another GPU test or change the pinned candidate while this version runs. This is not a competition submission.

Compare ten identical public games / target model / 48 minute budget / concurrency10 with BOTH exact-v3 controls (33/27.49667 and38/36.09039), and report per-game completions, new zeros, crashes, tokens and actual restore markers in tool results. A single high score does not establish superiority under the measured control variation. The candidate requires its own result, then replication if promising.
