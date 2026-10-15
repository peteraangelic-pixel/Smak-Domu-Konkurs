# ⚠️ KOREKTA (15.10): TEN DOKUMENT BYŁ PISANY NA ŚLEPO

Napisałem go, NIE czytając kodu ducka — po sklonowaniu duck-harness okazało się,
że duck to własny framework Tufa (tool-agent, Solver, TAAF), **bez punktu wpięcia
dla naszych plików**. „Integracja krok po kroku" = napisanie adaptera Solver =
NOWY, NIETESTOWANY KOD. Dokument zostaje jako PLAN pracy po 17.10 (wtedy adapter
zrobi się w save-runie, nie na slocie). Ścieżka zero-kodu dla v6.9 DZIŚ: własny
notebook (kernel-metadata.json w llm-agent/) jako SAVE-RUN, nie submit.

---

# Integracja v6.9 (nasz mózg) w rurę duck — instrukcja dla gałęzi 98ddb59f

Cel: **bieg A/B w rurze duck** — dziś: v4.1 @200k (bezpiecznik), jutro: v6.9 @200k.
Paired per gra (ta sama lista gier, ten sam budżet tokenów) → czysty odczyt wkładu
mózgu. Stan v6.9: commit `dc9b2a8` w `Smak-Domu-Konkurs/arc-agi-3/llm-agent/`,
testy 104/104, smoke A/B lokalnie zielone.

## Pliki do skopiowania (cały mózg, spójny zestaw)

```
llm_policy.py          # polityka v6.9 (12 mechanizmów + goal-class + drabinka + ValueGate)
knobs.py               # 24 pokrętła ARC3_* (env ARC3_KNOBS_JSON)
goal_classifier.py     # detekcja 8 klas celu (NOWY w v6.9)
value_gate.py          # learned ValueGate (v6.5; bez wag = OFF, nic nie kosztuje)
grid_utils.py          # format grida
llm_agent.py           # wrapper notebookowy (jeśli duck go używa)
```

Wszystkie używają **relative importów** (`from .knobs import KNOBS`) → działają w
dowolnym pakiecie (u was `llm_agent` z podkreślnikiem, u nas alias `llmagent` —
nazwa pakietu nie gra roli; nie wolno tylko odpalać plików jako skrypty top-level).

## Env (vLLM na H100, API zgodne z OpenAI — te same co do tej pory)

```
LLM_BASE_URL, LLM_MODEL_ID, LLM_API_KEY, LLM_CONTEXT_WINDOW, LLM_MAX_OUTPUT,
LLM_TEMPERATURE, LLM_TIMEOUT   # bez zmian vs wasz bieg v5/duck
ARC3_KNOBS_JSON                # OPCJONALNIE — nie ustawiać = defaults = v6.7/v6.8 zachowanie
```

UWAGA: po stronie Kaggle w notebooku **musi dojść** `goal_classifier.py` + `knobs.py`
(nasza lekcja z buga TRUE_SUBMISSION — lista plików do skopiowania w build_notebook.py
jest już u nas naprawiona; u was zwrócić uwagę na własną listę kopiowania).

## Walidacja PRZED odpaleniem rury (5 min, bez GPU)

1. W katalogu z plikami: `python3 -m unittest discover -s tests -t .` z naszego repo
   (104 testy; katalog `llm-agent` ma myślnik, testy robią alias same).
2. Kontroli markera w pliku polityki: `grep -c GOAL_CLASS llm_policy.py` ≥ 3,
   `grep -c "KNOBS\[" llm_policy.py` ≥ 12.
3. U nas smoke pełne: mock e2e (run_local.py --mock) + A/B knobów — zielone.

## Protokół A/B

- **Bieg 1 (dziś)**: mózg v4.1 (wasz obecny staging) @200k tokenów/grę.
- **Bieg 2 (jutro)**: mózg v6.9 @200k. Identyczna lista gier i seedów (duck).
- Porównanie **paired per gra** (nasz protokół z MEASUREMENT-PLAN): per gra delta
  score, potem suma/średnia; decyzja ≥+2 łącznego → v6.9 na kolejne zgłoszenie.
- Opcjonalne trzecie ramię (19.10+): v6.9 + `ARC3_KNOBS_JSON={"VALUE_GATE":1}`
  (deterministyczna linia wartości w prompcie) albo knob-gated warianty z CEM.

## Czego NIE robić

- Nie wrzucać v6.9 bez punktów 1–3 (nasza reguła po ich martwych mechanizmach).
- Nie mieszać plików z różnych wersji (llm_policy v6.9 wymaga knobs.py v6.9 +
  goal_classifier.py v6.9 — stary llm_policy z nowym knobs spowoduje brak pól).
- Nie podnosić budżetu w biegu 2 (paired znaczy też ten sam budżet).
