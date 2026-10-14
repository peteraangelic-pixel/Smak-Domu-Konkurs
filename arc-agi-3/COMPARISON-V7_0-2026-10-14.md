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
