# OCENA ARENA — duck-v13-7-final (30.10.2026, ~15:30 UTC)

**Werdykt: CERTYFIKOWANA — ALL CHECKS PASSED (verify --bundle r033 --tests, 10/10 patchy).**
Kandydat na slot 30.10/31.10 (CZEKA NA GO usera). Komit: patrz CHAT-LOG/SYNC §22.

## 1. Co to jest

`duck-v13-7-final` = `duck-v13-6-final` (kom. 3bf4d3e0) + **patch 0010 dyn-level-budget**
(od sesji „strategia", handoff `arc-arena-handoff-30-10.zip` = kom. 999f9194, 14:40;
w ich numeracji 0009, plik `arc-v16-package/patches/0009-dyn-level-budget.patch`,
przeniesiony **bajt w bajt** jako `patches/0010-dyn-level-budget.patch` / `duck-extra-08`).

- **Plik rozłączny**: dotyczy WYŁĄCZNIE `ARC3-Inference/inference/framework/arc3_level_budget.py`
  (moduł 0004); self-pace (0009) siedzi w `tool_agent.py` — zero kolizji; 0001–0008 nietknięte.
- **DORMANT na submisji**: `ARC3_LEVEL_TOKEN_CAP="0"` zostaje → moduł inertny, zachowanie
  **identyczne z v13.6**. Uzbrojenie później = JEDNA wartość (0→60000), decyzja na 1.11 wg GO.
- Mechanizm (po uzbrojeniu): cap poziomu = `clamp(mediana(koszty ukończonych poziomów gry) ×
  ARC3_DYN_CAP_MULT(4), 45k, 150k)`; drabina RESET ×1,5 po każdym resecie; ABANDON tylko
  po wyczerpaniu resetów i ≥1,5× cap oraz ≥ARC3_LEVEL_MIN_DONE — **nigdy ostrzejszy od
  statycznego capa**. Kill: `ARC3_DYN_CAP=0` → wierny statyczny 0004 (gotowy kontrolny A/B).
- Motywacja (ich, zmierzone): statyczny cap ranił drogie prawie-ukończone poziomy (su15
  56,4→13,3 pod 45k), a bez capa gry palą 35–91% tokenów na jednym nieukończonym poziomie
  (tn36 86%, ls20 91%) — scoring jest wypukły w głębokości.
- Notebook: **41 komórek, 758 240 B** (< 1 MB); cell-diff vs v13.6 = **{1,2,12,14,15,33,40}**
  (variant, switch+nota, rebrandy 0007/0009, NOWY writer extra-08, budget/roster labels);
  writer extra-08 == patches/0010 (porównanie True); slug `petersharps/arc3-duck-v13-7-final`.

## 2. Weryfikacja paczki handoffowej PRZED kompozycją (jej „pending" zamknięty przez nas)

Ich pakiet przyjechał z „ALL LOCAL CHECKS PASSED" i bramką łańcucha r033 **pending**.
Odtworzyliśmy wszystko samodzielnie:
- ich `tests/test_arc3_dyn_budget.py`: **16/16 PASS** (czysta logika, bez silnika),
- ich `tools/verify_v16.py`: **ALL LOCAL CHECKS PASSED** (10/10, w tym dormancja i uzbrojenie
  oraz cell-diff „czysty przesuw" komórek 15..39 vs baza v13.4),
- **zamknięcie pending-gate**: 9/9 patchy (ich łańcuch) `git apply` na **czystym r033**,
  drzewo się kompiluje, **nasze** 12 plan-commit + 6 escalate + 11 winpath testów
  **na ich spatchowanym drzewie** — PASS,
- `src/arc3_level_budget_v13_2.py` (rekonstrukcja, na której siedzą ich testy) == bajty
  modułu po pełnym łańcuchu r033 (**cmp identyczne** → testują dokładnie to, co wysyłają),
- writer w ich notebooku == plik patcha w pakiecie (cmp).

## 3. Weryfikacja v13.7 (kompozycja)

- verify_v13.py --bundle r033-recon-bundle --tests: **ALL CHECKS PASSED**, w tym:
  **10/10 patchy** czysty r033 (0001–0007 + 0008 + 0009 self-pace + **0010 dyn**),
  drzewo się kompiluje, 12+6+11 testów na spatchowanym drzewie, self-pace **22/14** 1:1,
  **0010: rekonstrukcja == bajty spatchowanego drzewa (cmp) + 16/16 testów na bajtach
  wysyłkowych**, sondy stub (z nowym bezwarunkowym drukiem a/call), playbook bajt,
  serving nietknięty, dormancja checkowana w wariancie (`"ARC3_LEVEL_TOKEN_CAP": "0"`).

## 4. Sloty (propozycja; DECYDUJE GO usera)

- **30.10: v13-7-final** — na submisji zachowawczo ≡ v13.6 (0010 dormant), więc ryzyko
  jak v13.6; pakuje już jedyną dostępną dźwignię „głębi" na 1.11.
- **1.11: uzbrojenie 0010** (LEVEL_TOKEN_CAP 0→60000) jeśli 30.10 pokaże pokrycie/a/call
  zgodne z planem; alternatywnie kontrola.
- Opcja wspólnej sesji strategii (SYNC §22): ich pakiet można też wypchnąć 1:1 na ich slug
  `arc3-duck-v16` — my NIE wysyłamy cudzego kernela bez wyraźnej decyzji usera.

## 5. Ocena reszty handoffu (przeczytane: HANDOFF, porównanie, recenzja v17; war-room przegląd)

- **Recenzja v17 (strategia) — KLUCZOWE**: „RHAE 3,80→40,06" mierzy wartość **planowania**
  (PlannerAgent BFS vs ReactiveAgent), a NIE warstwy action-efficiency — warstwa nie jest
  ani razu użyta w eval-u (agent.py/run_eval.py jej nie importują). „12 seedów" = kosmetyka
  (fabryka ignoruje seed → 1 przebieg deterministyczny, stdev 0,00). Uczciwe deklaracje
  2/4 przegranych potwierdzone. Nasza decyzja §21C (nie wpinamy warstwy) — **podtrzymana
  i wzmocniona**: przyrost warstwy nad harnessem jest NIEZMIERZONY; jedyna uczciwa miara
  pozostaje Δ mediany akcji/ukończony poziom na r085 (przed/po).
- Integracja warstwy wg nich: PlanCache kolizja filozofii z win-path 0006 (cache'uje też
  niezweryfikowane plany); BudgetLedger = drugi harmonogram → reguła jednego pisarza;
  **ConvergedGuard najbezpieczniejszy** (additive, po modelu). Zgodne z a450 (bug
  niehashowalnych akcji do naprawy przed jakimkolwiek wpięciem).
- Porównanie potwierdza mapę: v13.7-final == ich „v17-naj" (v13.5 + self-pace + dyn dormant)
  + nasz fix alarmu a/call + slug bez kolizji.
- Higiena slugów: Gemma duck-v15/v16 celują w NASZE slugi (arc3-duck-v13-3-arena /
  arc3-duck-v13-4-unified) — gdyby ich kernele kiedyś szły na Kaggle, nadpiszą nasze wersje.
  Nasze pakiety: wszystkie slugi własne (v13-3-arena, v13-4-unified, v13-5-consensus,
  v13-6-final, v13-7-final).

## 6. Uczciwość pochodzenia

- Patch 0010: sesja „strategia" (handoff 30.10 ~12:00); docstring modułu mówi „patch 0007/
  v13.2" — ich wewnętrzna etykieta, bajty nietknięte (zasada: cmp zamiast kosmetyki).
- Patch 0009: Gemma duck-v16 (0ef2465). Baza: nasz łańcuch v11→v13.6. Wszystkie liczby
  cudze zweryfikowane samodzielnie (reguła stała). Nic do Kaggle bez GO.
