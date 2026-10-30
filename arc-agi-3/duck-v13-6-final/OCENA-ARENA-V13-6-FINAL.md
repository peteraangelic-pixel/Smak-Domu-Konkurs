# OCENA ARENA — duck-v13-6-final (30.10.2026, ~13:10 UTC)

**Werdykt: CERTYFIKOWANA — ALL CHECKS PASSED (verify --bundle r033 --tests).**
Kandydat na slot 30.10 (przegląd v13.5-consensus; CZEKA NA GO usera).

## 1. Co to jest

`duck-v13-6-final` = `duck-v13-5-consensus` (kom. 63ede621) + **trzy rzeczy z fali 08:22–09:18**:

| # | zmiana | źródło | status weryfikacji |
|---|--------|--------|--------------------|
| 1 | **patch 0009 self-pace** (`duck-extra-07.patch`): próg eskalacji = `clamp(1,5 × mediana własnych akcji na ukończonych poziomach TEJ gry, floor 20, ceiling 120)`, cap 2/poziom | Gemma `duck-v16` (0ef2465, 08:38); patch przeniesiony **bajt w bajt** | a450 52b709e: 9/9 git apply + testy; my: `tests/test_self_pace.py` → **22 nudge'y / 14 przedwczesnych na r085 (1:1 z kodu patcha)**; extracted==file cmp OK |
| 2 | **fix martwego alarmu** w sonda rosteru: `a/call < 1.5` → **bezwarunkowy druk** `v13.6 batch: a/call = … (baza r019 = 4.357; cel ~5.7 dla 300 akcji/ge, ~7.6 dla 400; bramka 7911: >= 6.0 …)` | c87 28ed67f („warstwa 8: martwy instrument"); bramka ≥6,0 z 7911 cad326c | druk odtworzony na stubach; verify checkuje brak starego kodu alarmu |
| 3 | **fix testu** `test_escalate_relative.py`: `R085_BENCH.exists()` → **`is_file()`** | a450 52b709e (IsADirectoryError z czystego klona zamiast skipTest) | test skipuje czysto bez R085_BENCH, przechodzi z benchmarkiem |

Przy okazji: `kernel-metadata.json` id/title → `arc3-duck-v13-6-final` (unika rysy Gemmy
duck-v16, gdzie slug drift = nadpisanie kernela v13.4 przy pushu).

## 2. Dlaczego 0009 a nie relatywny (kluczowe)

- Baseline human **ukryty w submisji** (r033) → patch 0008 relatywny degraduje tam do
  absolutnej 20+cap2 (42 wstrzyknięcia na r085, 2,9% puli). **0009 kalibruje na
  `GameRun.actions_per_level` — NASZYM rekordzie, nieukrywanym w żadnym trybie** — więc
  działa dokładnie tam, gdzie liczony jest wynik.
- Na r085 (32 ukończone poziomy): relatywny(widoczny)=8/0, floor20+cap2=42/26,
  **self-pace=22/14** — mniej nudge'ów w poziomy, które gra wygrywa, dopuszcza dłuższe
  walki na poziomach przegrywanych (np. ls20 poziom 3: 222 akcji vs mediana 96 → nudge
  dopiero ~144).
- Baseline widoczny → gałąź relatywna dalej wygrywa (test 3); `ARC3_ESCALATE_SELF_PACE=0`
  → dokładnie v13.5.

## 3. Weryfikacja (pełna, jak poprzednio)

- verify_v13.py --bundle r033-recon-bundle --tests: **38 checków OK / 0 FAIL**, w tym:
  - **9/9 patchy** git apply na czystym r033 (0001–0007 + 0008 + **0009**), drzewo się kompiluje,
  - **12 plan-commit + 6 escalate-relative** testów na spatchowanym drzewie,
  - **test_self_pace**: 3 przypadki env + reprodukcja r085 **22/14** + „relatywny wygrywa przy widocznym baseline'ie" — 1:1 z kodu patcha (fixtures==shipped patch, cmp bajt),
  - **11 winpath** testów na spatchowanym module (PYTHONPATH czysty — lekcja z 30.10 rano),
  - sondy stub: budget 11,04× cap/UWAGA, roster z **nowym bezwarunkowym drukiem a/call**,
  - playbook embedded == playbook.json (9 gier), serving nietknięty, ONLY_RESET_LEVELS pinned.
- Notebook: **40 komórek, 743 616 B** (< 1 MB); cell-diff vs v13.5 = **{1,2,12,14,32,39}**
  (variant, switch, rebrand 0007, NOWY writer 0009, budget labels, roster+instrument fix).
- Builder `tools/build_v136_final.py`: wyłącznie edycje przyrostowe na zbudowanym v13.5
  (reguła po bugu v135); kotwice asercjone; idempotentny w swojej strukturze.

## 4. Lekcje środowiskowe (sandbox odtworzony między turami)

- Wheels arcengine 0.9.3 wymaga Pythona ≥3.12 (system: 3.11) → wheel rozpakowany do
  `/tmp/ae` i wstrzyknięty w PYTHONPATH (jak 29.10). Brak `arcengine` = 8 ERRORS winpath
  i 4 ERRORS escalate (import requests/PIL/arcengine) — to ŚRODOWISKO, nie pakiet.
- Kolejność edycji w builderze ma znaczenie: rebrand etykiet psuje kotwicę starego
  alarmu — najpierw dead→alive, potem rebrand (assertion łapie, nie przepuszcza).

## 5. Prognoza i plan

- Względem v13.5: identyczne zachowanie wszędzie oprócz progu eskalacji (lepszy trigger)
  + uczciwy pomiar batchingu. Prognoza szczerze: **w przedziale v13.5 (26–31)**; self-pace
  może dołożyć na grach z długimi przegrywanymi poziomami (mniej marnowanych 20-tek),
  ale to korekta 2–4 akcji/grę — dzwignią nr 1 pozostaje hint openerowy (a/call 4,36→6+;
  stosunek do sporu o eskalację **24:1** wg 7911).
- **Instrumenty na submisji**: bezwarunkowy `a/call` (baza 4,357; bramka 7911 ≥6,0 = granica
  253 akcji/gry = 50 pkt), pokrycie wazone (sufit = score), baseline UKRYTY/ZYWY,
  `[arc3-winpath]`, metering tok/akcję. Bramka Gemmy ≥1,8 jest prożno-przechodząca —
  nie stosujemy (a/call czegokolwiek by nie były, 4,5+ i tak przejdzie).
- Slot 30.10 (do GO): **v13.6-final**. 31.10: powtórka (σ≈2,5–3,9) albo v13.5-kontrola —
  wg druku a/call i pokrycia. 1–2.11: flip wg meteringu, select best.

## 6. Relacja do paczki v17-action-efficiency (upload 283a36b8, obca sesja)

Warstwa oceniona POSYTYWNIE i **ortogonalna** (nie wchodzi do v13.6 dziś):
- PlanCache ≈ nasz win-path replay (0006); ConvergedGuard ma ciekawy pomysł (ban po hashu
  stanu, ttl 40 — łapie pętle dłuższe niż okno anti-loop), ale **bug**: kluczowanie po
  akcji — akcje myszowe (dict) niehashowalne → TypeError w prawdziwym harnessie (a450).
  Poprawny patch = hashowanie klatek, które 0006 już robi — mały patch tam, nie nowa warstwa.
- BudgetLedger.pick_game nie mapuje się na równoległy solver (dead-skip już robi
  abandonment); liczba fal, nie cap, wiąże ogon rosteru.
- HarnessHook = propozycja integracji; **decyzja usera** — nic nie ruszamy bez GO.
- Ich mikro-środowiska i RHAE 40,06 są uczciwe i odtwarzalne (7/7 testów) — wartość
  jako przegląd metodologiczny, nie jako kod do submisji.

## 7. Pochodzenie i uczciwość

- Patch 0009: Gemma duck-v16 (0ef2465) — budowany NA NASZYM v13.4-unified; a450 52b709e
  zweryfikował 9/9 + reprodukcję; docstring patcha mówi 27/16 (w tabeli/testach 22/14) —
  drobna niespójność u źródła, liczba 22/14 jest tą zweryfikowaną przez 3 strony
  (test, a450, nasze uruchomienie).
- Martwy alarm: próg 1,5 pochodził z ery 1,00 akcji/decyzję (MEGA-DIAGNOSIS 7911, r013/15/18);
  przy bazie 4,357 był nieosiągalny — 8. instancja klasy „martwy instrument" (c87).
- Nic do Kaggle bez wyraźnego GO usera. Slug własny: `petersharps/arc3-duck-v13-6-final`.
