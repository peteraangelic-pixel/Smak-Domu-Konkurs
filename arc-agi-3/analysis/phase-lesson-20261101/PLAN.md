# General causal-model checking instruction on exactv3

Notebook SHA: b6140e3400ae7f33c83413128db33fda24b4a8fec12bd60b1aa1b7a434626f62. Base SHA8d0195f92c5518a41d14edbfca596b72c27690f269f681bbaa9af0bc3d257bcc. Only cell1 differs: internal name plus `ARC3_SYSTEM_PROMPT_PREFIX`. No extra patch;34materialized Python sources are identical to the exactv3 control.

The short prefix asks the agent to separate input activation, object motion, autonomous dynamics and contact; check before/after target-selection order against real observations; repair a counterexample before increasing search depth; and choose a discriminating action if rules still fit equally well. It supports the agent's own model functions as well as the existing check_model API. It does not assert that a particular causal order or rule is correct.

This transfers a general experimental procedure, not the offline public fixture's model, goal coordinates, learned row boundary, game ID or replay prefix. All v3 guards, retention, tools, model, datasets, budgets and serving settings remain. No scratchcache/fresh-read hook, validation-nudge hook, slim sections, scope change or solved-level memory.

Actual renderer verification shows that the prefix is at the beginning of the system prompt and the rest of that prompt is byte-identical after removing the prefix. This proves instruction delivery in the renderer, not LLM compliance or game quality. The full target test must check actual prediction/observation comparisons and useful probes in retained calls, not simply count the instruction text.

Compare the same ten public games / Flash-Next /48min/concurrency10 with BOTH controls33/27.49667 and38/36.09039. Check completions per game, new zeros, errors and tokens. A promising single result needs replication. No automatic competition submission is authorized. Private modes: phase-lesson-smoke, then phase-lesson-watch after canonical version acceptance is confirmed.
