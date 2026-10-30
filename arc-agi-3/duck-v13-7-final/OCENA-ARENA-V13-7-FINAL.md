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

---

## 7. KOREKTA po niezależnej opinii Gemmy (gałąź 6d081d52) — 30.10 ~16:30, zweryfikowana przeze mnie 1:1

Gemma odtworzyła nasz build/verify (bajt w bajt, cell-diff identyczny) i wnieśli TRZY rzeczy.
Wszystkie sprawdziłem samodzielnie:

1. **Semantyka kodu (potwierdzona w patchu 0010)**: `base = max(static_cap, mediana×4)`
   → dyn **nigdy nie tnie ciaśniej niż arming**; poniżej 2 ukończonych poziomów fallback =
   static_cap; drabina mnoży **po** clampie (150k×1,5=225k możliwe — kosmetyka, nie bug).
   Ich „dormancja różnicowa" 8000 decyzji × 5 konfigów → identyczne decyzje: spójne.
2. **Liczby z 40 gier (r085/r093/r110/r118) — ODTWORZONE PRZEZE MNIE 1:1**:
   ukończone poziomy >45k: **14** (oni: 14), >60k: **13** (oni: 13), max koszt 91 043
   (oni: 88 114 — drobny rozjazd cięcia segmentów); marnotrawstwo na poziomy nieukończone:
   median **64,5%**, max **100%** (identycznie); sim @60000: dyn aktywny **16/40**,
   **15 luźniej / 0 ciaśniej**, mediana capa **128 612** — WSZYSTKO identycznie.
3. **Rekomendacja armingu 20 000 zamiast 60 000 — PRZYJĘTA**. Uzasadnienie (kod+liczby):
   @60000 gry z historią dostają ≥60k, a **15 gier palących 100% budżetu (0 ukończonych,
   >40k tok) pozostaje nietkniętych** — „utnij marnotrawstwo" nie działa; @20000 gry z
   historią mają TE SAME capa (mediana×4 ≥ 46k; mediana 128 612 bez zmiany), a
   marnotrawcy bez historii są cięci na 20k + darmowy RESET (~40k). Nota w komórce 2
   i README poprawione na 20 000 (rev2). **Ryzyko do pomiaru na 1.11**: te 14 poziomów
   >45k może nie ukończyć się pod capem 20k+reset — metryka ochronna: completed/game
   przed/po; opcja `ARC3_LEVEL_MIN_DONE=1` (nie porzucaj gier z ≥1 ukończonym) jako
   OSOBNA kolejna zmienna, nie w tym samym biegu.

## 8. SPROSTOWANIE własnej usterki certyfikatu

Ścieżka R085_BENCH w moich wcześniejszych biegach verify (`…/r085/benchmark.json`)
**nie istniała** (prawdziwa: `…/r085-kernel_output_pick/output-pick/benchmark.json`),
więc test reprodukcji 8 nudge'ów (escalate) był **cicho SKIPPED** (skip nie zmienia
returncode). verify rev2: check na realny R085_BENCH + zakaz skipa („none skipped");
bieg z dobrą ścieżką: **ALL CHECKS PASSED, 0 skipów**. Wniosek o 8/0 nudge'ach
reprodukuje się z realnych danych (bieg obecny), nie tylko z kodu patcha.

Ich raport (notes/ARC-AGI-3-ocena-v13-7-final-2026-10-30.md, commit 568420c lokalnie)
+ narzędzie audit_dyn_budget.py: warto wypchnąć na ich gałąź (rekomendacja do ownera).

---

## 9. ADJUDYKACJA (30.10 ~18:40): ARMING 20000 WYCOFANY — Gemma c4eeb067 (6fcb8d9) ma rację

Nasza §25 zakończyła się rekomendacją „arming 20000 potwierdzony" z argumentem
„pewna strata / nieumierzalny zysk". **Logika była odwrócona** — pewna strata i
nieumierzalny zysk argumentują PRZECIW. Gemma (REVIEWS/2026-10-30-v13-7-rev2-vs-v16.md)
odtworzyła nasz sweep 1:1 (20 gier AB / 15 utraconych / 667 937 tok; per-run 3/7/0/10 —
identycznie) i pokazała arytmetykę konwersji. Nasza niezależna weryfikacja
(/tmp/adjud_arm.py, prawdziwy moduł, per-akcja):

| run | uwolnione tok. | utracone poz. | koszt/uk. poz. (tylko ukończone) | uwolnione = X poz. | konwersja do zera |
|---|---|---|---|---|---|
| r085 | 154 460 | 5 (dc22 3→1, g50t 3→0) | 33 195 (ich pesymistycznie: 44 287=total/32) | 4,65 | **107%** (ich: 143%) |
| r093 | 374 898 | 9 | 35 342 | 10,61 | 85% (ich: 136%) |
| r118 | 138 579 | 1 (run 0/2-ukończonych) | 37 542 | 3,69 | 27% |
| Σ | 667 937 | 15 | ~34k | ~19,6 | **76–101%** |

Czyli: **nawet przy doskonałej konwersji arming jest najwyżej na granicy zera**; a
konwersja przez kolejkę jest według Gemmy ≈0 — solver.py:898/917 (zweryfikowane u nas:
Semaphore(10)=MAXREQ, `create_task` dla WSZYSTKICH gier naraz) — uwolniony slot od razu
lapie następna gra, a uwolniony czas **skraca bieg**, nie wydłuża cudzych budżetów
(ich zastrzeżenie: to odczyt kodu, nie pomiar; rozstrzygną logi 30.10 — czy globalny
deadline 532 min tnie ogon). Utracone poziomy trafiają w gry, które DOWOZIŁY (dc22, g50t,
ka59) — ryzyko skoncentrowane, EV ≤ 0, σ powtórek 2,5–3,9: **flip slotu lepiej wydać
na powtórkę/dźwignię niż na arming**.

DECYZJA (rejestr): **0010 zostaje DORMANT na obu pozostałych slotach; arming 20k
wycofany z rekomendacji** (nota w kom. 2 notebooka jest historyczną propozycją —
nadrzędna jest niniejsza §9; przebudowa notebooka tylko przy najbliższej zmianie
funkcjonalnej). Sonda „v17 levers" w notebooku i tak przeliczy 20k/60k z danych
własnego biegu. Pozytywne od Gemmy: rev2 ≡ v16 na submisji; nasz druk a/call lepszy
od ich martwego progu (wpinają u siebie wraz z poprawką sluga — po GO ich ownera).
