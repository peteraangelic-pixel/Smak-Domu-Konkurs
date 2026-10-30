# OCENA ARENA — duck-v13.4-unified (własny wariant „best of all branches", 30.10 2026 ~10:30 UTC)

**Werdykt: CERTYFIKOWANA — ALL CHECKS PASSED (39 komórek, 8/8 patchy czysty r033,
12 plan-commit + 6 escalate-relative + 11 winpath na spatchowanym drzewie, sondy na
stubach, playbook bajtowo identyczny i 14/14 na silniku). Kandydat na slot 30.10.
NIC do Kaggle bez wyraźnego GO usera.**

v13.4-unified skleja WSZYSTKO zmierzone/zaobserwowane z 4 gałęzi (stan 30.10 ~10:00):

| źródło | co wchodzi | status pomiaru |
|---|---|---|
| v13.2 (Pokemon 6b10853, certyfikowana) | PLAN_COMMIT=1, CAP=0, WINPATH=1, DEAD_SKIP=1, conc=10, playbook 14/14 | baza, bajt-w-bajt |
| v13.3-arena (nasza, certyfikowana) | `ARC3_OPENER_COMMIT_HINT=1` (opener batche 3,91–5,43 → 6,73–6,91 — pomiar upstream w docstringu harnessu) + **patch 0007** log zdarzeń win-path `[arc3-winpath] …` | zmierzone upstream / observability |
| **v14 (Gemma b38b82e, 30.10 08:04)** | **ESCALATE 10→20** (zmierzone na 32 ukończonych poziomach r085: @10 = 154 wstrzyknięć = **15,3% puli tokenów gry**, „przestań próbować" odpala **przed ludzkim baseline'em na 31/32 poziomów**; @20 = 60 / 6,0%) · **guard hooka sondy** (w naszym łańcuchu `_orig_play = _S._HarnessGameSession.play` leżało POZA try — AttributeError w innej rewizji bundla = martwy notebook PRZED startem, klasa katastrofy c45-0.00) · **sonda budżetu** (przed biegiem: games/passes/conc/uczciwy udział/cap + ostrzeżenie przy cap/udział > 1,3) · **sonda rosteru** (po biegu, z `bm.game_runs` → werdykt duplicate_bases + alarm `actions_per_call < 1,5`) | **przeliczone niezależnie przez Arenę: 154/12/8 i 31/32, 7/32, 0/32 — identycznie** |
| **NOWE (patch 0008) — to, czego v14 nie mogła wysłać** | **`ARC3_ESCALATE_RELATIVE=1`**: eskalacja odpala dopiero powyżej `max(floor, ARC3_ESCALATE_RATE × base_actions_per_level[poziom])`, z capem `ARC3_ESCALATE_MAX_PER_LEVEL=2`/poziom; fallback na próg absolutny przy braku baseline'u (GameRun.base_actions_per_level jest None, gdy silnik ukrywa). Gemma oznaczyła to jako „lepszy wariant, ale nie mam r033, by zweryfikować patch" — **my mamy r033 i łańcuch zweryfikowany** | na r085: **8 wstrzyknięć / 0 przedwczesnych** vs 60/25-z-32 przy @20 i 154/31-z-32 przy @10; test w pakiecie przechodzi przez SPATCHOWANY `tool_agent._escalate_threshold` na prawdziwych danych r085 (`R085_BENCH`) |

`base_actions_per_level` istnieje w runtime (`taaf/game.py:295`, None gdy ukryte); referencja
gry dowiązana jednym hunkiem w `solver._make_analyzer` (`agent.game = game`, fabryka analyserów
w notebooku nieużywana — sprawdzone). Wykonalność potwierdzona; Gemma samodzielnie odradzała
ten patch bez r033 — my go wysyłamy z testem odtwarzającym pomiar.

## Matryca kill-switchy (każda niezależna)

| switch | off daje |
|---|---|
| `ARC3_ESCALATE_RELATIVE=0` | dokładnie v14 (próg absolutny 20) |
| `ARC3_ESCALATE_MAX_PER_LEVEL=0` | bez capu nudge'ów (domyślne 2/level tylko w wariancie) |
| `ARC3_OPENER_COMMIT_HINT=0` | v14 |
| `ARC3_WINPATH_LOG=0` | cisza (log-only, logika nietknięta) |
| `ARC3_WINPATH=0` / `ARC3_DEAD_SKIP=0` / `PLAN_COMMIT=0` / `CAP=45000` | jak w v13.2 |
| `ESCALATE_ACTIONS` | podłoga progu (20) |

## Co zmieniło się w notebooku vs v13.3-arena (39 komórek; cell-diff potwierdzony)

kom. 1 (env+rejestracja extra-06), kom. 2 (ESCALATE 20 + komentarz z pomiarem + print
v13.4-unified), kom. 12 (rebrand 0007), NOWA 13 (writer extra-06), kom. 27 (guard hooka —
dokładnie fix v14), NOWA 31 (sonda budżetu, przed `bm.run`), NOWA 38 (sonda rosteru po biegu,
plik `roster_probe_runs.jsonl` — celowo INNA nazwa niż `roster_probe.jsonl` hooka c45, by oba
zbiory przetrwały). **Serving nietknięty (stara kom. 21 == nowa 22); playbook i winpath bajtowo.**

## Dlaczego to ma szansę gonić liderów (konwergencja 4 sesji)

Wynik = przepustowość (akcje/grę), a `akcje/grę = 2 945 s / (tok/akcję × ms/tok)`. Jedyna
dźwignia z sufitem >50 to `commit(plan)` (~0,3 s/akcję zamiast ~12,9 — połowa akcji przez
commit = ~450 akcji zamiast 226). v13.2 uzbrajał ją progiem @10, który — jak zmierzyła Gemma
i przeliczyliśmy my — **karze poziomy wygrywane** (31/32 przedwczesnych + 15,3% puli na
dyrektywy i „posłuszność"). v13.4 kieruje nacisk tam, gdzie run realnie traci (relatywnie,
8× na r085), dokłada presję batcha na OTWARCIU tur (hint), a sondy + logi czynią z jednego
biegu pełną diagnozę: roster (duplicates), głodzenie (cap/udział), skuteczność commita
(`actions_per_call`), życie replayu (`[arc3-winpath]`). Realny pułap na 30.10: **26–31**
(zgodnie 4 sesje), z mechanizmem do ~450 akcji/grę, jeśli model zacznie słuchać —
i metrami, które to rozstrzygną niezależnie od σ≈2,5–3,9 hałasu punktowego.

## Weryfikacja (30.10, Arena — wszystko samodzielnie)

1. `tools/verify_v13.py --bundle r033 --tests` → **ALL CHECKS PASSED** (lista OK m.in.:
   39 komórek; extra-05/06 zarejestrowane; ESCALATE=20 (bez śladu po 10); RELATIVE/RATE/CAP
   w wariancie; hook z guardem; obie sondy; playbook embedded == disk; PLAN_COMMIT w obie
   strony; 8/8 patchy w kolejności; drzewo się kompiluje).
2. **12 plan-commit + 6 escalate-relative + 11 winpath** na spatchowanym drzewie.
   `test_r085_reproduces_the_measured_trigger_set` przechodzi przez spatchowany kod na
   prawdziwym benchmarku r085 → dokładnie 8 nudge'ów, 0 przedwczesnych.
3. Sondy: `tools/test_probes.py` (adaptowane z v14): budżet flaguje cap 11× i NIE flaguje
   uczciwego; roster wykrywa duplikaty, werdykt 0 pkt, alarm a/call=1.0; wyjątek w danych →
   „skipped"; hook AttributeError-proof.
4. `standalone == spatchowany` dla winpath (cmp); playbook bajtowo v13.2/v13.3; **14/14 na
   żywym silniku** (przejmowane z certyfikacji v13.2/v13.3 — plik ten sam bajt w bajt).
5. Cell-diff vs v13.3-arena potwierdzony programowo (lista wyżej); serving parity.

## Uczciwie o ryzykach

- **Największe:** eskalacja relatywna + hint zmieniają statystykę tur — kierunek zmierzony,
  ale interakcja nie; dlatego metr (`actions_per_call`, liczba nudge'ów w logu) jedzie w tym
  samym biegu, a każdy element ma kill-switch.
- Próg relatywny na 110 UKRYTYCH grach: `base_actions_per_level` może być None (silnik
  ukrywa baseline) → automatyczny fallback na absolutne 20 (bezpieczne, v14).
- Sondy niczego nie zmieniają i są podwójnie otulone try/except.
- v14 prognozowała dla siebie 26–31 („górna połowa przy @20"); nasza przewaga to ten sam
  kierunek z ostrzejszym spustem + pełną obserwowalnością, nie nowa, niemierzona magia.

## Propozycja slotów (decyduje GO usera)

- **30.10: v13.4-unified** (zamiast v13.2 as-shipped — @10 z v13.2 jest teraz ZMIERZONE jako
  ryzyko: 15,3% puli i 31/32 „przestań próbować" na poziomach wygrywanych;nasze GO#1 nie
  powinno płacić za znalezione ryzyko, skoro mamy wersję z tym samym kierunkiem i lepszym
  spustem).
- 31.10: powtórka v13.4 ×2 (draw) LUB — jeśli user woli czystą atrybucję — v14 (Gemma) jako
  kontrola absolutna @20.
- 1.11: flip najsłabszego komponentu wg meteringu (kandydat: RELATIVE=0 → v14-exact; lub
  HISTORY_ASSISTANT_TURNS 150→48 jeśli sonda budżetu pokaże głodzenie).
- 2.11: select best (sprawdzić w rules liczbę punktowanych submisji).
