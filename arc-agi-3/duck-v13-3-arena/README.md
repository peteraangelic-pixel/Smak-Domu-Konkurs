# duck-v13.3-arena — kandydat do zgłoszenia (wariant Areny, 30.10 2026)

**v13.3-arena = v13.2 (Pokemon 6b10853, certyfikowana) + 2 dźwignie z audytów 30.10,
obie z kill-switchem.** Nic nie jest wysyłane — push i „Submit to Competition"
należą do właściciela konta (GO usera).

## Co zmienia względem v13.2 (pełny diff w `OCENA-ARENA-V13-3-ARENA.md`)

| # | zmiana | mechanizm | podstawa |
|---|---|---|---|
| 1 | `ARC3_OPENER_COMMIT_HINT=1` | **env-only** (0 nowych patchy): wzmocnienie batchowania w KAŻDYM świeżym openerze — „call `action(actions)` with the sequence it supports. Probe with a single action when you genuinely need to distinguish two possibilities" | wbudowane w harness (`tool_agent.py::_opener_commit_hint`), domyślnie OFF; upstreamowy pomiar w docstringu: **opener batche 3,91–5,43 → 6,73–6,91 akcji** (tyle co po resumption). To jest „wymuszenie batcha na 1. turze" z listy tanich napraw c87 — dziś pierwsze ~10 akcji poziomu idzie pojedynczo |
| 2 | **patch 0007** (`duck-extra-05`): log zdarzeń win-path | jednoLINIOWY log stdout `[arc3-winpath] …`: session begin/end, playbook match, **replay start / ok / abort + powód** (hash-mismatch z numerem kroku, action-unavailable, game-over, init-mismatch, exhausted), record, dead-skip. Loguje się tylko zdarzenia, nigdy gorące ścieżki per-iteracja | żądanie audytów 7911f950 + c87: „cicha awaria replayu = ryzyko diagnostyki, nie wyniku". Kill-switch: `ARC3_WINPATH_LOG=0` (log nie dotyka logiki) |

Playbook, komórka serwująca, `ESCALATE_ACTIONS=10`, `PLAN_COMMIT=1`, `CAP=0`,
`WINPATH=1`, `DEAD_SKIP=1`, `conc=10` — **bajtowo v13.2**. Komórki notebooka
różnią się tylko: 1 (wariant env + rejestracja patcha), 2 (print v13.3-arena +
komentarz kill-switchy) i wstawiona komórka 12 (writer extra-05).

## Dlaczego to „lepsze od v13.2" — logika

Konwergentna diagnoza 4 sesji (SYNC §15–§17): wynik = przepustowość
(akcje/grę z ~213 do ~300+), nie mądrzejszy model. Model budżetu:
`akcje/grę = 2 945 s / (tok/akcję × ms/tok)`. v13.2 dotyka lewara
akcje/decyzję tylko presją eskalacyjną co 10 akcji (pierwsze ~10 akcji
poziomu = pojedyncze wywołania ~13–15 s każde). Dźwignia 1 skraca ten start;
dźwignia 2 nie dodaje punktów, ale **z runa 30.10 da się w ogóle zdiagnozować,
czy replay żył** (probe wartości pamięci bez zewnętrznych plików).

Oczekiwanie: jeśli model słucha hinta (zmierzone upstreamem), ~+25–50% akcji/decyzję
na openerach → wg projekcji Gemmy (200 akcji/grę ≈ 35,6) ruch w górę o kilka punktów;
ryzyko: model może batchować gorzej niż eksploruje pojedynczo — stąd 1. pomiar
na osobnym slocie i kill-switch.

## Weryfikacja (Arena, 30.10 — wszystko wykonane samodzielnie)

- **7/7 patchy** na czystym bundle r033 (`tools/verify_v13.py --bundle … --tests`):
  **ALL CHECKS PASSED** (36 komórek, 21 komórek kodu się kompiluje, 7/7 aplikuje,
  drzewo się kompiluje, **12/12 plan-commit, 11/11 winpath** na spatchowanym drzewie).
- standalone `src/arc3_winpath.py` == spatchowany moduł **bajt-w-bajt** (cmp).
- **Playbook bajtowo identyczny z v13.2** i **14/14 na żywym silniku**
  (arcengine 0.9.3 / arc_agi 0.9.9).
- 3 nowe testy logowania (zdarzenia sukcesu, init-mismatch, tryb cichy) → 11.
- Serving komórka nietknięta (parity z c45 — przenosi się z v13.1/v13.2).

## Jak wypchnąć (właściciel konta)

```bash
kaggle kernels push -p arc-agi-3/duck-v13-3-arena
```
potem UI Kaggle: Run → **Submit to Competition**. W logu muszą się pojawić:
`v13.3-arena profile=plan plan_commit=1 escalate=10 true_concurrency=10`,
`ARC3 variant env: {... 'ARC3_OPENER_COMMIT_HINT': '1' ...}`,
`ARC3 extra patch applied: /kaggle/duck-extra-05.patch`,
`v13 playbook: 9 gier, 14 poziomów`.

## Kill-switche (każdy niezależny)

- hint szkodzi → w komórce wariantu `"ARC3_OPENER_COMMIT_HINT": "0"` (wraca v13.2).
- log przeszkadza → `"ARC3_WINPATH_LOG": "0"`.
- dalej jak w v13.2: `PLAN_COMMIT="0"` (kontrola), `"ARC3_WINPATH": "0"`, `"ARC3_DEAD_SKIP": "0"`, `"ARC3_LEVEL_TOKEN_CAP": "45000"`.

## Uczciwie o niepewności

Hint jest zmierzony upstreamem (Tufa lineage), ale **nie na naszej linii
modelu/konfiguracji** — dlatego wchodzi jako osobny slot (31.10), nie jako
nadpisania GO#1 (30.10 = v13.2). Metr rozstrzygający: `v11_metrics.json`
(akcje/wywołanie; dziś ~4,36; cel 6–9) — rozstrzyga mechanizm nawet przy
σ≈2,5–3,9 pkt hałasu punktowego.
