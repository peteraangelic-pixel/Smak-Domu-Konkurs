# OCENA ARENY — duck-v13.2 (Pokemon 6b10853, 30.10 2026 ~07:45 UTC)

**Werdykt: CERTYFIKOWANA. Wszystkie twierdzenia komitu zweryfikowane samodzielnie na naszym
sprzęcie i na czystym bundle r033. Kandydat na slot 30.10 — WYMAGA GO usera (nic do Kaggle
bez wyraźnego GO).**

Lineage: v13 (3782f8c) → v13.1 (cbefdd4) → **v13.2 (6b10853)**. v13.2 = v13.1 + dokładnie
dwie zmiany mechanizmowe z audytów innych gałęzi + porządki dokumentacyjne. Playbook.json
**bajtowo identyczny** z v13.1 (cmp: 0 różnic) → walidacja 14/14 pozostaje związana i została
ponownie wykonana na kopii v13.2.

## Co zmienia v13.2 względem v13.1 (diff plik-po-pliku, /tmp/v131check vs /tmp/v132)

| plik | zmiana |
|---|---|
| `arc3-duck-v13.ipynb` kom. 2 | `ESCALATE_ACTIONS = 60 → 10`; print `v13.1`→`v13.2`. Reszta komórki bez zmian (w tym eksport `ARC3_ESCALATE_ACTIONS` do env — był już w v13.1) |
| `arc3-duck-v13.ipynb` kom. 11 | wbudowany `duck-extra-04.patch` dostaje guard GAME_OVER (→ opis niżej); to JEDYNA treściwa zmiana w notebooku |
| `patches/0006-winpath-replay.patch` | identycznie +3 linie (blob 293ac45→4113516) |
| `src/arc3_winpath.py` | +3 linie w `_replay_once` (guard); standalone == spatchowany moduł **bajt-w-bajt** (cmp OK) |
| `tests/test_winpath.py` | +1 test `test_game_over_frame_does_not_burn_replay` → **8 testów** (v13.1 miała 7; komit v13.1 mówił błędnie „12+8") |
| `tools/verify_v13.py`, `tools/build_v13.py` | tylko sync wersji (v13-2 / ESCALATE 10) |
| `kernel-metadata.json` | id/title `arc3-duck-v13-2` |
| `src/base-v11.ipynb` | NOWY plik: bazowy notebook v11 (input `build_v13.py`/`make_patch_0006.py`; notebook submisyjny jest prebuilt, więc plik tylko dla odtwarzalności łańcucha) |
| `playbook.json`, `ANALIZA-23.md`, `tests/test_plan_commit.py`, `tools/replay_pb.py`* | BEZ ZMIAN (*replay_pb.py żyje w naszym pakiecie v13.1 — nasz dodatek z 9de4e890) |

## Guard GAME_OVER (odpowiedź na drobiazg Gemmy z §15/§16)

W v13.1 `maybe_replay` był wołany na początku pętli głównej, PRZED obsługą game-over. Na martwej
klatce replay wykonałby akcję, hash by się nie zgodził → `_fail(level, count=True)` → poziom
trwale utracony dla replayu (`broken`) do końca wpisu. v13.2 dodaje na wejściu `_replay_once`:

```python
raw_state = getattr(getattr(game_state, "raw", None), "state", None)
if str(getattr(raw_state, "name", raw_state)).upper().endswith("GAME_OVER"):
    return False  # dead frame: do not burn the level's replay on it
```

Skutek: martwa klatka przepuszcza sterowanie do normalnej obsługi game-over (RESET) i NIE
dotyka `broken`/`fails`. Zgodne semantycznie z ustaleniem Gemmy („skutek ~zero, ale poprawne”)
i zamknięte testem jednostkowym.

## ESCALATE_ACTIONS 60→10 (wdrożenie audytu 7911 z §16)

Nasze samodzielne potwierdzenie okablowania (metodologia: nie wierzymy opisom):
- kom. 2: `_v11_os.environ["ARC3_ESCALATE_ACTIONS"] = str(ESCALATE_ACTIONS)` — próg idzie do env;
- drzewo spatchowane r033+6 patchy: `inference/agent/tool_agent.py:131-132` czyta
  `_get_env_int("ARC3_ESCALATE_ACTIONS", 0)` — dyrektywa eskalacyjna powtarza się co N akcji
  na niedokończonym poziomie.
Przy 60 i ~30 akcjach/poziom eskalacja często nie odpalała w ogóle; 10 = presja od początku
poziomu. To jedyny istniejący mechanizm WYMUSZANIA commit(plan) (commit jest modelowi tylko
oferowany w prompcie — FAKT 2 z §16). Model budżetu 7911: więcej akcji/decyzję = jedyna
dźwignia sufitem 50+. **Zastrzeżenie c87 (§5.2 ich audytu 4c9a3e5, odnotowane w SYNC §17):
sufit 18,7 @ eff=90% z tej samej tabeli 7911 jest PONIŻEJ zmierzonego LB 26,25 — napięcie
otwarte, prognoz „50+” nie traktujemy jako pewnika.**

## Nasza weryfikacja (30.10, Arena — wszystkie punkty wykonane samodzielnie)

1. **Diff chirurgiczny** — jedynie kom. 2 i 11 notebooka się różnią (skrypt porównujący komórki
   JSON; pozostałe 33 komórki bajtowo równe v13.1, w tym kom. 21 serwująca → serving-parity
   z c45 (kom. 17) z 07:52 przenosi się przez tranzytywność — brak cichej regresji silnika).
2. **6/6 patchy** aplikuje się czysto na czystym bundle r033 (`verify_v13.py --bundle …`:
   `applies: harness-changes/duck-extra-00..04` wszystkie OK), drzewo się kompiluje,
   moduł winpath obecny w drzewie.
3. **12/12 testów plan-commit** na spatchowanym drzewie (verify: `12 plan-commit tests pass` OK).
4. **8/8 testów winpath** na spatchowanym drzewie, łącznie z nowym testem guardu GAME_OVER
   (ręcznie: `PYTHONPATH=/tmp/ae:/tmp/agx:<framework> python3 test_winpath.py -v` → OK).
   UWAGA ŚRODOWISKOWA: wbudowany krok winpath w `verify_v13.py` NADPISUJE PYTHONPATH samą
   ścieżką frameworku, gubiąc arcengine → 1 fail + 5 errors, wszystkie jednym korzeniu
   (`import arcengine` w `_replay_once` → wyjątek → `maybe_replay`=False). To pułapka
   skryptu, nie logiki pakietu (znana z v13.1; tutaj potwierdzona: po poprawnym PYTHONPATH 8/8).
5. **standalone == spatchowany** (`cmp` src/arc3_winpath.py vs drzewo po patchach: identyczne).
6. **Playbook 14/14 na żywym silniku** (arcengine 0.9.3 / arc_agi 0.9.9, katalog 25 gier
   `arc-agi-3/games/environment_files`): 9 gier — cd82/cn04/ft09/lp85/ls20/sp80 = 1 poz.,
   m0r0 = 2, tu93 = 4, vc33 = 2; łącznie `WYNIK: 14/14 poziomów playbooka potwierdzonych`.
7. **Metadata/eksporty** (verify): 35 komórek, wszystkie komórki kodu się kompilują,
   playbook embedded == playbook.json (9 gier/14 poziomów), wszystkie ścieżki /kaggle/input
   zadeklarowane, concurrency 10, cap off, WINPATH/DEAD_SKIP on, metering obecny,
   ONLY_RESET_LEVELS pinned, przełącznik PLAN_COMMIT testowany w obie strony.

## Kontekst decyzyjny (szczegóły w SYNC §17)

- v13.2 absorbuje jedyną sensowną dźwignię z audytów 30.10 (wymuszenie batching przez
  eskalację co 10 akcji) zamiast odkładania jej na 1.11.
- **KOREKTA WIELKA (nasza, 30.10 ~08:05)**: zagadka „3,6× ms/token na tym samym 8B” z
  MEGA-CONFIG Gemmy NIE ISTNIEJE — r110 to kernel `arc3-duck-v13-27b` (Qwen3.6-27B-FP8 na
  vLLM), nie „8B cap 45k”. Our weryfikacja: server log (`SERVED_MODEL_NAME = 'vrfai/Qwen3.6-27B-FP8'`),
  SUMMARY.md, benchmark.json (926 akcji / 448 782 tok / 28 806,8 s → 64,2 ms/tok — liczba
  Gemmy poprawna, etykieta modelu błędna). Konsekwencja: linia v13.x JEST już na szybkim
  silniku 8B (~15-17 ms/tok; r085/c45); otwarte pozostaje tylko pytanie, czy 17 ms/tok
  utrzyma się w rerunie 110 gier — zmierzy to metering w runie.
- Slot 30.10 (propozycja do GO): **v13.2 AS-SHIPPED** — PLAN_COMMIT=1, ESCALATE=10, CAP=0,
  WINPATH=1, DEAD_SKIP=1, conc=10, probe ON. Alternatywa c87 (PLAN_COMMIT=0 jako kontrola)
  odnotowana w SYNC §17; decyduje user.
- Weryfikacja NIE jest smoke’em: smoke (48 min, 10 gier) pozostaje bramką katastrof przed
  submisją, nie predyktorem punktów.
