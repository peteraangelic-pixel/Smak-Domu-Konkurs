# Observation cache — reject

Private target-model run completed29levels /19.7412252, below both exact-v3 controls33/27.49667 and38/36.09039. All ten games completed at least one level; no new zeros. Against control1:1win/3losses/6ties; against control2:2/6/2. No confirmed quality improvement; do not promote or repeat unchanged.

Actual restore markers appear in retained TOOL RESULT blocks in all ten games. Thus this was not a dormant feature. Counts are observed lower bounds from retained snapshots, not a full-run activation census. Fewer NameErrors or more successful variable restores would not outweigh fewer completed levels.

The run reports1,311,777 generated tokens, lower than the controls around1.70–1.77million. This alone does not establish why throughput differed. More retained state, model behavior, runtime overhead and run variation must not be conflated; no causal timing attribution is made. Raw notebook/server logs and benchmark are preserved.

This is a public private-test result, not a competition score or prediction. Scratch variables and their changed prompt semantics remain experimental; default exactv3 is preserved. Next independent mechanism tests stale-state latch behavior after an actual read of the fresh board, with no observation cache or validation nudge.
