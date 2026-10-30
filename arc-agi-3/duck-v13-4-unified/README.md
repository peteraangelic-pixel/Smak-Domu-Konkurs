# duck-v13.4-unified — kandydat do zgłoszenia (Arena, 30.10 2026)

**v13.4-unified = v13.2 + v13.3-arena + v14 (Gemma) + patch 0008** — wszystko zmierzone
albo observability-only, każdy komponent z kill-switchem. Szczegóły i matryca ryzyk:
`OCENA-ARENA-V13-4-UNIFIED.md`.

| warstwa | element | skąd |
|---|---|---|
| baza | PLAN_COMMIT=1, CAP=0, WINPATH=1, DEAD_SKIP=1, conc=10, playbook 14/14 | v13.2 (6b10853) |
| presja batcha na openerach | `ARC3_OPENER_COMMIT_HINT=1` | v13.3-arena (harness wbudowany) |
| log replayu/dead-skip | patch 0007 `[arc3-winpath] …` | v13.3-arena |
| zmierzony spust eskalacji | `ESCALATE_ACTIONS=20` + patch 0008 `ARC3_ESCALATE_RELATIVE=1` (max(floor, 1,2×baseline), cap 2/level) | v14 (pomiar) + Arena (patch) |
| crash-proof | guard hooka sondy (AttributeError-proof) | v14 |
| obserwowalność | sonda budżetu (przed) + sonda rosteru (po, `roster_probe_runs.jsonl`) + alarm `actions_per_call<1,5` | v14 |

Weryfikacja: **ALL CHECKS PASSED** — 8/8 patchy czysty r033, 12+6+11 testów na spatchowanym
drzewie (w tym odtworzenie pomiaru 8 nudge'ów/0 przedwczesnych przez spatchowany kod na
prawdziwym r085), sondy na stubach, playbook bajtowo identyczny (14/14 na silniku),
serving nietknięty.

## Jak wypchnąć (właściciel konta)

```bash
kaggle kernels push -p arc-agi-3/duck-v13-4-unified
```
potem UI Kaggle: Run → **Submit to Competition**. W logu muszą się pojawić:
`v13.4-unified profile=plan plan_commit=1 escalate=20 true_concurrency=10`,
`ARC3 variant env: {... 'ARC3_ESCALATE_RELATIVE': '1', 'ARC3_OPENER_COMMIT_HINT': '1' ...}`,
`ARC3 extra patch applied: /kaggle/duck-extra-05.patch` i `...-06.patch`,
`v13.4 budget: ...`, `probe: OK -> ...`, `v13 playbook: 9 gier, 14 poziomów`,
a po biegu `v13.4 roster: {...}` z werdyktem duplikatów.

## Kill-switche

`"ARC3_ESCALATE_RELATIVE": "0"` (= v14 exact) · `"ARC3_ESCALATE_MAX_PER_LEVEL": "0"` ·
`"ARC3_OPENER_COMMIT_HINT": "0"` (= v14) · `"ARC3_WINPATH_LOG": "0"` · `"ARC3_WINPATH": "0"` ·
`"ARC3_DEAD_SKIP": "0"` · `PLAN_COMMIT = "0"` · `"ARC3_LEVEL_TOKEN_CAP": "45000"`.

## Uczciwie

Prognoza rerunu: **26–31** (konwergencja 4 sesji); przewaga nad v13.2/v14 to ostrzejszy,
zmierzony spust jedynej dźwigni >50 (commit(plan)) + pełna obserwowalność z jednego biegu —
nie nowa, niemierzona magia. Ryzyko interakcji (relatywny spust × hint) mierzy metering
w tym samym biegu; każdy komponent można wyłączyć jedną linią.
