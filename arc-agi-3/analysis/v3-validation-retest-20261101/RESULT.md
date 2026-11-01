# Validation replica — advantage not confirmed

The identical validation notebook, SHA9050146da8f5a7dee600d92dbfb5d5931eff1c81266192f13d39a92ddb7f694b, completed the target-model private test: **32levels /29.4721673**, versus validation1 **37/36.9206361**. Exact-v3 controls are33/27.49667 and38/36.09039. No advantage is established; do not promote the validation hook or inherit its highest result in another candidate.

Same ten game IDs, level counts and action baselines verified. Notebook log confirms target Flash-Next W4A16, max_runtime_s_per_game2880, concurrency10, `ARC3_SMOKE_OK`, crashed=[] and1,776,257 generated tokens. The final benchmark export has zero token counters; those are missing telemetry, **not zero inference**. Raw files are preserved. There are final analyzer timeouts near the48-minute boundary; these are recorded separately from process crashes.

Per-game levels: tn36=2,m0r0=5,cn04=2,dc22=4,ka59=5,sc25=5,s5i5=2,ls20=3,su15=3,g50t=1. Against control1:3wins/4losses/3ties; against control2:2/3/5; against validation1:2/4/4. No new zeros in these comparisons. Fewer completions cannot be presented as a successful replication because the score exceeds control1.

## Actual model checking

Retained su15 tool results contain two executed `check_model` calls, not merely API text:

- First:35 checked,5correct,accuracy0.143; MOUSE4/19,UNDO1/16; one model exception.
- Second:accuracy0.222; MOUSE7/20,UNDO1/16.

Both include mismatch reports. UNDO needs history and is poorly represented in this model, so the aggregate accuracy must not be equated with accuracy on planning moves: MOUSE alone is approximately21% then35%, still poor. su15 remained at3 completed levels. This is evidence that the helper ran and exposed wrong predictions, not that the model was successfully corrected or planning improved. Other retained snapshots may omit earlier calls. The first caller also looked for `first_mismatches`, whereas the helper returns `mismatches`; the second caller used the actual key. Full call/result excerpts are in CHECK-MODEL-EVIDENCE.json.

Next independent experiment: already verified observation-cache on exactv3, without this nudge or any other experimental policy patch. It requires its own target-model result. These are public private-test results, not competition submission scores or forecasts.
