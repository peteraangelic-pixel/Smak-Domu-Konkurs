# Research and implementation update, 30 October 2026

## Direct Kaggle observations

GitHub Actions used the repository's KAGGLE_API_TOKEN for read-only leaderboard,
public notebook listing and public source downloads. The token stayed inside
Actions. The workflow runs were 41131263569 and 41131379942, on the separate
branch codex/arc-leader-research-20261030 in Smak-Domu-Konkurs. That branch
contains a read-only replacement of arc3-ops.yml with contents:read permission.

The downloaded leaderboard reports Yi-Chia Chen @ Fields Model at 75.56 and
Tufa Labs at 70.02. Evidence is in kaggle-public-sources-20261030/.

The account threerabbits returned seven public notebooks in this listing.
The downloaded submission-32b-fix4 targets another competition, as identified
by its competition_sources metadata. Its serving techniques cannot establish
the architecture behind the current ARC score.

The leader's public comment in discussion 742935 says she chose not to publish
her Milestone 2 solution. No inspected source establishes her current recipe.
An authenticated Kaggle key grants the caller's permissions; it does not grant
access to competitors' private notebooks or their hidden-game trajectories.

Public notebooks downloaded and inspected

- romantamrazov/the-agi-boys-i-am-better
- heliosli/try-merging-it-you-might-get-lucky-and-win-gold
- vickyfym/arc-agi-3-lalalia-final
- tantan0327/arc3-franzen-dprime
- threerabbits/submission-32b-fix4

The first two have identical executable cell sources, SHA256 prefix
e286994f4f83cb6a. Names and list positions do not establish novel methods.
The lalalia notebook describes a 31.46 public score and a cache-conscious
solved-level memory patch. The memory is updated when history trimming already
causes a reread. That is an inspectable technique, with performance claims
attributed to its authors. It is not evidence for a 75-point method.

Franzen's public solution documents Qwen3.8-Flash-Next, optimized SGLang,
prefix-cache retention, blockwise history trimming, bounded admission,
priority scheduling and agent tools. Our base already inherits much of this.
The current leader's gains cannot be assigned to any one of those mechanisms
from the sources available.

## Evolution improvements

The old Kaggriculture V8 experiment varied parents whose realized behavior
differed on only one turn. This constrained the attainable outcome regardless
of the number of games evaluated. Feasibility clipping also mapped multiple
nominal genomes to the same actions. That supports phenotype deduplication,
broader meaningful mutations and observation-dependent routing.

Useful additional work in riemann

- reactive_state and reactive_selector implement observation estimation,
  bounded candidates, sequential resource accounting and action adaptation.
- search_pulse_router evaluates shallow observation-dependent decision rules
  with identity controls and per-opponent regression metrics.
- gate_v18_observable_routers checks positive and negative opponent groups in
  closed-loop Python games, supplementing the high-throughput Rust tape path.
- trace/parity checks are essential when introducing native primitives that
  the original fixed-tape simulator could not execute faithfully.

For ARC, the transferable pattern is a policy conditioned on observed mechanics
and uncertainty, with per-game-family regression reports and differential
engine checks. Copying fixed action tapes does not provide generalization to
new environments. Evolution over six search knobs is an initial lab rather
than the complete architecture search the user wants.

Implemented propose_search.py uses one-hot genes and game interactions with
24 bootstrap ridge models. It proposes eight untried genomes using predicted
coverage, ensemble spread and gene diversity. Validation outcomes are excluded
from fitting. The spread is uncalibrated and does not establish an improvement.

Leave-one-genome-out results on 111 training observations from 13 genomes

| Predictor | Mean squared error |
|---|---:|
| Global mean | 2.0703 |
| Per-game training mean | 0.5946 |
| Ridge surrogate | 0.5605 |

Against the more appropriate per-game reference the reduction is about 5.7%.
This is a small preliminary predictive gain. No end-to-end comparison of
surrogate-guided search versus random evolution has been completed. The output
is surrogate-proposals.json. Repeated architectures, realized-behavior diversity
and uncertainty about the next environment remain open research requirements.

## LM Studio

Started the service with lms server start and loaded local qwen3.5-4b with
identifier arc-lab-fast, context8192, GPU offload0.9, parallel1 and idle TTL1800s.
Native /api/v1/chat with reasoning=off returned parseable hypothesis/probe JSON,
zero reasoning tokens and approximately35.2 generated tokens/s. This verifies
local operation and structured output, not puzzle-solving quality.
The service remains running and the model has an idle unload timeout.

## Sources

- https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/742935
- https://github.com/da-fr/arc-agi-3-solution
- https://www.kaggle.com/code/vickyfym/arc-agi-3-lalalia-final
- https://github.com/peteraangelic-pixel/riemann/tree/arena/01a087c0-riemann
- https://github.com/peteraangelic-pixel/Smak-Domu-Konkurs/actions/runs/41131379942
