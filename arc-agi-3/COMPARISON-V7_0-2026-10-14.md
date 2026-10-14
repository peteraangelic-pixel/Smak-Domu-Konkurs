# Porównanie: ich v7.0 (@3ad6a47, 14.10 17:37) vs nasz v6.8 (@b3ccca3)

Źródło: `Pokemon/arena/7911f950-pokemon` @3ad6a47. LB (z ich COMPARISON_14X.md):
lider 67.49, Tufa 56.52, mtg 45.00, Majkel1337 42.66, NVARC3 **40.97** (5. miejsce = próg).
Zmierzone wyniki naszego konta: duck v5 = **27.21** (13.10), v2 = **24.66**.
Ich „v5.0 est. 35–42 / v5.1 est. 37–47" to **szacunki, nie pomiary** (sumowanie
sufitów — dokładnie to, czego ich własny V7_PLAN zabrania).

## Co realnie siedzi w ich v7.0

| Komponent | Stan |
|---|---|
| `llm_policy_v7_0.py` (20 KB) | Port ~8–9/12 naszych mechanizmów (notes, game-over, no-op, audyt, batch, raw_decode, temp) + 3 NOWE: counter-picking, ValueGate, drabinka eskalacji. **BRAK: probe opening, lessons-between-games, self-test, cap kolejki.** Brak klienta LLM w pliku (tylko MockLLMClient). |
| `goal_classifier.py` (13.7 KB) | Heurystyczna detekcja 7 klas celu z grida (COVER/REACH/COPY/REDUCE/PLACE/FLOW/ALIGN); **podłączony** do v7_0 (akcja 1 → klasa → strategia). Najcenniejsza nowość. |
| `evolve_parameters.py` (13.3 KB) | CEM po ~14 parametrach HeuristicParams. **MARTWY KOD**: nikt go nie importuje, wymaga `evaluator: Callable`, którego nie ma. |
| ML pipeline (feature_extractor + mlp_value_model + training_data_generator) | Numpy MLP 20→128→64→1. **NIEpodłączony** do polityki (ValueGate celowo heurystyczny). |
| `run_games_fast.py` | Pool MP, ale **importuje llm_policy_v4**, nie v7.0. Runner nie uruchamia v7.0. |
| Testy | Brak testów v7.0 wdiff naszych 87. |

Ich llm_policy.py (23.4 KB, „vLLM + plan cache + anti-loop") = ich STARY baseline, nie
port naszego v6.7 — różni się od naszego v6.8 o 489 linii, zero KNOBS.

## Nasz v6.8 vs ich v7.0 — werdykt

- **Kompletność polityki**: my 12/12 mechanizmów + 22 pokrętła okablowane w 12 miejscach
  + testy 87/87. Oni ~8–9/12 + 3 nowe pomysły, bez klienta, bez runera, bez testów.
- **Ewolucja**: nasz CEM jest spięty z realnym ewaluatorem (local_eval.make_fitness,
  e2e przetestowane w sandboxie). Ich CEM = moduł bez konsumenta.
- **Runner**: nasz run_local/local_eval rozmawia z arcengine bezpośrednio (API z ich
  play.py) + mock + LM Studio env. Ich run_games_fast uruchamia v4, nie v7.0.
- **ML**: oba domyślnie OFF — zgodnie z ich własną lekcją z PTCG („ML płytkie ±0pp").
- **Zmierzone wyniki**: żaden z nowych policy (nasz v6.7/v6.8-mózg w duck ani ich v7.0)
  nie ma jeszcze wyniku Kaggle. Najlepszy zmierzony = duck v5 27.21.

## Co ukradnąć z ich v7.0 (kandydaci na nasz v6.9)

1. **goal_classifier.py** → wstrzykiwanie wykrytej klasy celu do naszego system prompta
   i audytów (counter-picking). Czyste heurystyki grida, tania, ortogonalna do 12 mechanizmów.
2. **Drabinka eskalacji**: audyt #2+ = „wybierz INNĄ klasę celu z FIELD GUIDE" — ładniejsze
   sformułowanie do naszego AUDIT prompta (v6.5 ma gate+eskalację, ale bez klasy celu).
3. **ValueGate feedback**: deterministyczny oceniany stan pokazywany modelowi w prompcie
   — dodać jako knob-gated eksperyment (ARC3_VALUE_GATE, default OFF).

Czego NIE brać: ich szacunków 35–47, MLP bez danych, run_games_fast (v4), martwego CEM.

---

## DODATEK (14.10 wieczór): nasza v6.9 vs ich v7.0 — porównanie po fakcie

v6.9 zbudowana (port ich najlepszych 3 pomysłów + nasze 12 mechanizmów + poprawki
ich błędów). Porównanie wymiar po wymiarze:

| Wymiar | Nasz v6.9 (`goal_classifier.py` + wiring) | Ich v7.0 (`llm_policy_v7_0.py`) |
|---|---|---|
| Mechanizmy bazowe | 12/12 (v6.1–v6.7) + 24 pokrętła KNOBS | ~8–9/12 (brak probe opening, lessons-between-games, self-test, cap kolejki) |
| Goal classifier | ich port + 4 bugfixy; detekcja 1. klatka gry, UNKNOWN→retry | oryginał: fałszywe COPY na rzadkich planszach (zero-vs-zero), puste wzorce, REDUCE konflikt z COVER |
| Counter-picking | poziom promptu: STRATEGY_HINTS (8 klas) → system prompt + audyty | StrategyParams (wagi heurystyki) — martwy kod, brak konsumenta |
| ValueGate | deterministyczny (novelty+change−loop), knob `VALUE_GATE` default 0, zero martwego ML | heurystyczny w polityce (działa), ale bez kalibracji; ich MLP ML dalej niepodłączony |
| Drabinka eskalacji | w naszych audytach akcyjno-tokenowych (40 akcji/50k tok. + rearm): ✗ FALSIFIED → DIFFERENT | stały próg 40 akcji, bez tokenów i rearmu |
| Klient LLM | realny OpenAI-compat (vLLM **i** LM Studio) + tryb mock + temperatura adaptacyjna knobowa | tylko MockLLMClient w pliku |
| Runner + MP | run_local.py / local_eval.py: arcengine bezpośrednio, Pool, knobs per worker | run_games_fast.py importuje **v4**, nie v7.0 |
| Ewolucja | evolve_knobs (CEM 8 EVOLVABLE) → local_eval.make_fitness, spięte e2e, przetestowane | evolve_parameters.py — martwy (wymaga evaluator, brak) |
| Testy | 104/104 (+76/76 baseline), w tym 17 nowych v6.9 | brak testów v7.0 |
| Payload Kaggle | notebook przebudowany; self-test: parser+probe+goal-class; FIX copy-listy TRUE_SUBMISSION | notebooki v2/v3/v4 z OLDER politykami |
| Wynik Kaggle | linia v6.x: brak (zmierzone: v2 24.66, duck v5 27.21) | brak |

**Werdykt**: v6.9 dominuje v7.0 na każdim wymiarze inżynierskim (kompletność, testy,
runner, ewolucja, payload) ORAZ naprawia 3 realne błędy ich klasyfikatora. Ich
unikalny wkład, który u nas teraz żyje: goal-class detection, drabinka, ValueGate
feedback. Co dalej bez zmian: prawda jest na Kaggle — paired A/B (GOAL_CLASS 0/1)
po 17.10 zdecyduje, czy v6.9 startuje jako zgłoszenie.

## AKTUALIZACJA (14.10 wieczór): ich v7.0 @740a993 — weryfikacja po fixach

| Ich twierdzenie | Weryfikacja kodem @740a993 |
|---|---|
| Fix 1: fałszywe COPY (density>0.1 + brak 0-vs-0) | ✅ REALNE (L87, L100); 0/200 fałszywych na naszych testach |
| Fix 2: puste wzorce | ✅ REALNE (ten sam mechanizm) |
| Fix 3: REDUCE próg 20 | ✅ REALNE (L287); 12 pionków → COVER (nie REDUCE) |
| Fix 4: hinty w system prompcie | ⚠️ NIE — wstrzykiwana sama etykieta klasy; `get_strategy_hint()` bez konsumenta; 13 testów testuje słownik, nie wiring |
| Runner | ❌ nadal `llm_policy_v4` |
| Ewolucja | ❌ nadal bez konsumenta |
| Detekcja UNKNOWN | bez retry (nasza: retry na kolejnych klatkach) |

Werdykt: ich klasyfikator jest teraz **równy naszemu** (na identycznych testach).
Różnice jakościowe zostały: wiring hintów (u nas żyje), retry UNKNOWN, runner,
ewolucja, 104 vs 13 testów. Szacunki 40–50 nadal traktujemy jako sumowanie
sufitów — pomiary mają pierwszeństwo (24.66 / 27.21).

## AKTUALIZACJA 2 (14.10 21:30, @cc1b657): runner/adapter/notebook

| Wymiar | @740a993 | @cc1b657 (teraz) |
|---|---|---|
| Runner | ❌ v4 | ✅ run_games_v7 → v7_0 + realny OpenAI klient (sekwencyjnie, bez MP) |
| Adapter Kaggle framework | ❌ brak | ✅ llm_agent_v7 (Agent subclass, coords clamp, budżet, auto-RESET) |
| Notebook z v7 | ❌ stare | ✅ v7.ipynb (3 pliki osadzone; bez self-testu) |
| Hints w prompcie | ❌ | ❌ nadal import bez wywołania |
| Ewolucja | ❌ | ❌ nadal martwa |
| MP | — | ❌ sekwencyjnie |

Zostaje u nas przewagą: 12/12 mechanizmów, 24 knobsy + CEM spięty z ewaluatorem,
MP w runnerze, retry UNKNOWN, self-test w payloadze, fix TRUE_SUBMISSION,
104 testy. ich unikalny żywy wkład: etykieta klasy w prompcie + ValueGate feedback.
