# v18 click planner — status 30 October 2026

Candidate notebook and metadata are in candidate/. The ZIP contains those two files.

The base is Smak v13.7 at de67be443cf234702af32dce7cfb661fb75d22bb. The additional patch supplies default mouse actions to the executable world-model planner from visible components and recent observed clicks. Explicit actions override the default vocabulary.

Checks performed

- Applied the base and candidate patches in notebook order on a fresh local r033 tree.
- Compiled the changed modules.
- Executed the candidate plan() in the isolated sandbox and checked the explicit-actions override. Result is in sandbox-verification.json.
- Used a Windows-only launcher adapter in that local check. It runs the identical bootstrap bytes from a file because Windows rejects the long command line. Kaggle's Linux launcher still needs its Save & Run check.
- Probed initial frames of 25 real public games using 16 worker processes. Candidate clicks produced visible changes in 14 of the 19 mouse-capable games. The probe includes no model reasoning and measures no completed-level advantage.

Full-agent v13.7 versus v18 comparison remains pending. Neither the click probe nor the synthetic sandbox regression establishes a score improvement.

evaluation-manifest.json pins the 25 game files and the historical r085 scoring fixture. Each new agent run must write its own benchmark.json. Keep game sources, model, quantization, runtime, concurrency and seeds aligned between paired runs. Historical replay of r085 estimates counterfactual costs and cannot generate new agent trajectories.

analysis/compare_runs.py checks roster equality and the official scoring rule before reporting paired differences. An exact game_id/baseline match does not independently establish equal model, seed or runtime settings.

Operational proposal

1. Preserve the measured best submission.
2. Run v13.7 control and v18 on the pinned public roster with the same model and budget in separate fresh runs. They can run sequentially.
3. Evaluate D-prime in another paired run against that control. Measure scores and completions after applying the scheduler.
4. Spend the next competition submission on the strongest verified candidate permitted by the remaining account quota.

Current competition quota and concurrent RTX session availability were not verified on the user's account. Scheduling assumes one scored submission per day until the account UI confirms another allowance.
