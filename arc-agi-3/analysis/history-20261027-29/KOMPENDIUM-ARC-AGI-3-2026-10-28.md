# KOMPENDIUM ARC-AGI-3 — cała wiedza projektowa w jednym pliku

**Data:** 28.10.2026
**Autor konsolidacji:** sesja Smak-Domu-Konkurs / Arena
**Zakres:** wszystko, co w tej rozmowie i w dokumentach projektu okazało się cenne, zmierzone, obalone albo decyzyjne — od stanu konkursu, przez architekturę Ducka i naszego agenta, po pomiar L1 (ABANDON), warianty env-only i plan slotów A/B/C.
**Zasada:** ten plik nie zastępuje źródeł, ale ma wystarczyć, by nowa sesja podjęła pracę w kilka minut bez ponownego odkrywania koła.

---

## 0. TL;DR — dziesięć rzeczy, które trzeba wiedzieć

1. **Cel:** ≥50 pkt do 2.11.2026. To **stretch**, nie obietnica. Uczciwe prawdopodobieństwo 50+ ≈ **5%**.
2. **Zmierzone punkty:** best COMPLETE **26,25** (duck v3), c45 #57629847 **0,00**, smoke c45 **26,78** (32/69 poziomów), r019 ~**175k tok/grę**; LB **24,66** (v2-think-less), wewnętrzny mean r019 **27,21**.
3. **Próg nagród (LB 24.10): 49,85**; lider **68,91** (Tufa Labs). Z ~26 brakuje **~+24 pkt**, nie +5. Snapshot 40,97 z 10.10 jest nieaktualny.
4. **Wynik jest zdominowany liczbą ukończonych poziomów**, nie „jakością odpowiedzi”. Sufit z samej efektywności ruchów ≈ **29,0**; **+1 poziom/grę ≈ 44** (ekstrapolacja z r019).
5. **Pula tokenów runu jest w przybliżeniu stała** (~19,7M; przy 110 grach ~175k/gamę). Więcej tokenów na grę podnosi wynik, ale nie ponad sufit poziomów.
6. **L1 ABANDON@60k nie jest kandydatem.** Na realnym trace r085 ubija 6/10 gier, traci 10/32 poziomów i oszczędza 27% tokenów. To **negatywna kontrola**, nie +5–7.
7. **Jedyny nie-destrukcyjny wariant env-only to `cap90`** (`ARC3_LEVEL_TOKEN_CAP=90000`, `RESETS_MAX=1`, `MIN_DONE=0`): 0 resetów, 0 porzuceń, wszystkie zaobserwowane ukończone poziomy zachowane (max 88 114), bezpiecznik ABANDON dopiero przy 180k.
8. **`ARC3_ABANDON_TOKENS` jest martwy** w tym drzewie. Realna dźwignia to `ARC3_LEVEL_TOKEN_CAP` + `ARC3_LEVEL_RESETS_MAX` + `ARC3_LEVEL_MIN_DONE`. `cap=0` wyłącza **cały** patch 0004, łącznie z RESET_LEVEL i ABANDON.
9. **Plan slotów:** A = kontrola `c45fix` (`PLAN_COMMIT="0"`, cap45/r1); B = sam `PLAN_COMMIT="1"` (`duck-v12-plan`, cap45/r1); C = `cap90` (stack, jeśli B ≥ A+3; fallback, jeśli B < A). **Nic nie zostało pushnięte ani zgłoszone — czeka na GO.**
10. **Finalista musi być publicznym notebookiem do 31.10–1.11**, inaczej nagroda przepada niezależnie od wyniku.

---

## 1. Konkurs — twarde fakty

| Pozycja | Wartość |
|---|---|
| Konkurs | ARC Prize 2026 — ARC-AGI-3 (Kaggle) |
| Entry deadline | 26.10.2026 — **zaakceptowany** |
| Finałowa submisja | **2.11.2026** |
| Ogłoszenie wyników | 4.12.2026 |
| Nagrody | **$75 000 dla top-5**: $40k / $15k / $10k / $5k / $5k |
| Aktywne zespoły | **28** (nie 4 494 — to liczba kont) |
| Ocena | wyłącznie wynik leaderboardu; **bez write-upu i bez rozmowy** (inaczej niż Grand Prize ARC Prize Foundation) |
| Limit zgłoszeń | **1 oficjalne zgłoszenie dziennie**, reset 00:00 UTC |
| Konto | `petersharps`; submit **da się zrobić z CLI** przez ops (patrz §13.1) — nie trzeba klikać w UI |
| Sprzęt finałowy | Kaggle **RTX 6000 (96 GB VRAM)**, **9 h**, internet wyłączony |
| Zestaw | **25 gier publicznych + 55 prywatnych** (prywatne dają wynik) |
| Baseline | `Tufalabs/duck-harness` — 55,89 RHAE, 1. miejsce na LB w pewnym momencie |

### 1.1. Leaderboard — dwa snapshoty, nie mieszać

| Data | Lider | Próg top-5 | Uwaga |
|---|---|---|---|
| 10.10.2026 | Yi-Chia Chen **62,96**; Tufa **56,52** | NVARC3 **40,97** (5. miejsce) | snapshot stary; mediana 38,17 |
| 24.10.2026 | **Tufa Labs 68,91** | **49,85** | **ten snapshot jest decyzyjny** |

**Wniosek:** „40,97 = próg” było prawdą tylko 10.10. Próg dryfował do 49,85. Z ~26 luka to ~+24 pkt.

### 1.2. Metryka RHAE — dlaczego liczy się oszczędność akcji

```
score_l = min( (H_l / A_l)², 1.15 )
game_score = min( Σ_l l · score_l / Σ_l l,
                  Σ_completed_l l / Σ_all_l l )
```

- `H_l` = mediana akcji człowieka na poziomie `l`; `A_l` = akcje agenta.
- Późniejsze poziomy ważą więcej (waga `l`).
- Kara jest **kwadratowa**: 2× więcej akcji = 0,25; 5× = 0,04; 10× = 0,01.
- Bycie lepszym od człowieka daje do **1,15** — jest z czego brać.
- **Mniej akcji = wyższy wynik i mniej obliczeń.** To nie kompromis, to jedna i ta sama dźwignia.

### 1.3. Budżet obliczeniowy

- Kaggle finał: RTX 6000 96 GB, 9 h, bez internetu. Qwen3.6-27B FP8 (~27 GB) się mieści.
- Lokalnie: **Ryzen 9 5950X (16C) + 64 GB RAM**, GPU 8 GB VRAM (część warstw w RAM; LM Studio obsługuje modele ~17 GB).
- Lokalnie można iterować **pętlę agenta, logikę, testy, replay, segmentację** — bez GPU.
- **Inferencja 27B wymaga Kaggle.** CPU inference ~1–3 tok/s; to nie jest droga.
- GitHub Actions **nie ma GPU** — tylko CI, testy, analiza artefaktów, commit logów.
- Rust + rayon ma sens wszędzie **poza samą inferencją**: segmentacja, replay, scoring, precompute offline.
- Precompute / cache pre-solve to szara strefa regulaminowa — **potwierdzić na forum przed włożeniem pracy**.

### 1.4. Co realnie oferują publiczne notebooki (pomiar 28.10, r106)

`kaggle kernels list --competition ... --sort-by scoreDescending` (60 pozycji):

| Obserwacja | Wniosek |
|---|---|
| Publiczne notebooki w tytule mają max **31,54** („31.54 in a Single Sub”), 31,21, 28,39, 27,80 | Publiczny „pipe” daje ~30, nie 50 |
| Najwięcej głosów: Franzen M2 (1158), Tufa stock (288) | To są dwie linie, na których stoimy |
| Tufa Labs na LB ma **68,91** i udostępnia swój notebook 27B | **Jedyny publiczny stack z dowodem 50+** — i to jest v13 |
| Zespoły 75,56 / 56,02 / 51,51 / 51,04 / 50,37 nie publikują notebooków | Nie ma gotowego pipe'a na 50+ |

**Konsekwencja decyzyjna:** nie ma skrótu „weź cudzy notebook 50+”. Zostają dwie drogi: (a) odtworzyć
linię Tufy (v13), (b) podnieść naszą fast-line o kilka punktów (cap → nocap, plan-commit).
(a) ma znacznie większy sufit, (b) jest tania i pewna. Dlatego slot B = v13, a `nocap` = fallback.

---

## 2. Oś czasu projektu — co po kolei ustalono

| Data | Wydarzenie / ustalenie |
|---|---|
| 10.10 | Crate Rust (segmentacja, RHAE, replay), CI zielone; most Kaggle przez workflow; LB zmierzony; entry zaakceptowany. |
| 11.10 | Zgłoszenie `57075036` = atrapa, score 0,0. Ówczesny wniosek („API bierze istniejące wyjście notebooka, trzeba klikać w UI”) **obalony 28.10** — poprawna forma to `-k <kernel> -v <ver> -f submission.parquet` → rc=0 i slot zajęty (§13.1). |
| 13.10 | r019: v2-think-less **24,66** LB; duck v5 **27,21** wewnętrznie; linia world-model zamknięta (283/813 przejść, v4 23,11 — gorzej); Duck **`license: null`** — nie kopiować kodu. |
| 14.10 | v6.x: field guide, goal persistence, notatki, stuck protocol, parser `raw_decode`, batch queue, no-op detector, lessons-between-games, goal classifier, ValueGate; testy rosną do 104/104. |
| 15.10 | Autopsja v6: **wszystkie gry `gave_up` na budżet, zero błędów**; „błąd” był w strategii — dokładanie kosztu decyzji na stałej puli obniża LB. v7-abandon zbudowany, nie pushowany. |
| 24.10 | Weryfikacja między-sesyjna: LB 49,85 / lider 68,91; `-f` bug; guard kwoty; `game_weights` to mit; replay +45–50% obalony; `PERSISTENT_FUNCTIONS_SCOPE='game'` żyje. |
| 25.10 | c45 #57629847 = **0,00**; diagnoza concurrency 120 vs MAXREQ 10; v10/v11; certyfikacja v11-Smak później obalona. |
| 27.10 | Przyjęto `v11-ex-c45` (33 komórki, 5 patchy, kill-switch); retrakcje v11-Smak i „v9 dead”; korekta opinii (41,8 to nie pomiar); plan 50+. |
| 28.10 | Pomiar L1 na realnym r085: 60k/r0 ubija 6/10 gier, traci 10/32 poziomów; cap90 = najlepszy env-only; zbudowano i zweryfikowano `abandon`, `nocap`, `cap90`; naprawiono `duck-v12-plan` (był klonem kontroli); testy: Rust 36/36, llm-agent 108/108, patch-chain 5/5 + 9/9 logiki. **Slot A wykonany**: push `arc3-duck-v11` v1 (12:05), smoke COMPLETE 13:06 z `ARC3_SMOKE_OK` (18,54; 27/69), submit **ref 57737623** 13:11 rc=0; submit da się zrobić z CLI (nie trzeba UI); smoke okazał się szumem (§3.3). **Werdykt A = 23,89** (COMPLETE): fix concurrency działa (0,00 → 23,89), cap45k/r1 kosztuje ~2,4 pkt vs v3 26,25. Analiza: `ANALIZA-23-89-I-DROGA-DO-50-2026-10-29.md`. 23:06 push `arc3-duck-v13-27b` v1 jako **save-run** (model = jedyna zmienna). |
| 29.10 | v13 (27B) smoke COMPLETE 00:05: mean **0,73**, 926 akcji, 155,5 tok/s, 4/10 gier z poziomem, wszystkie `cancelled` na `soft_end`. Kluczowe: **20–47 akcji/poziom** na ukończonych poziomach (jak człowiek) — brakuje nie jakości, a budżetu akcji. Bramka smoke uchylona jako nieporównywalna między modelami; **slot B = v13**, submit **ref 57752672** (00:09:51, PENDING). Fallback = `cap90`. Szczegóły: `POMIAR-V13-27B-2026-10-29.md`. |

---

## 3. Zmierzone wyniki — jedyne liczby, które wolno cytować jako fakty

| Metryka | Wartość | Kontekst |
|---|---|---|
| Best COMPLETE (LB) | **26,25** | duck v3 |
| c45 #57629847 (LB) | **0,00** | rerun; smoke był zdrowy |
| Smoke c45 | **26,78** | 32/69 poziomów, 10 gier |
| Smoke v11 (slot A) | **18,54** | 27/69 poziomów; **ten sam kod co c45** → różnica to szum (§3.3) |
| Slot A #57737623 (LB) | **23,89** | `arc3-duck-v11` v1, fix concurrency 120→10; cap45k/r1 **kosztuje ~2,4 pkt** |
| LB top-6 (28.10 23:01 UTC) | 75,56 · 68,91 · 56,02 · 51,51 · 51,04 · 50,37 | 50+ robi 6 zespołów; my 23,89 |
| r019 (wewnętrzny mean) | **27,21** | 10 gier smoke v6, nie LB |
| v2-think-less (LB) | **24,66** | 13.10 |
| r019 ekonomia | 2 065 akcji / 474 wywołania / a-call **4,357** ważone, **5,204** średnia / **841,3** tok/akcję / **3 665,1** tok/wywołanie / **173 726** tok/grę | surowe `requests.jsonl` |
| Sufit ruchów | **~29,0** | ekstrapolacja |
| +1 poziom/grę | **~44** | ekstrapolacja z r019 |
| Próg nagród (24.10) | **49,85** | top-5 |
| Lider (24.10) | **68,91** | Tufa Labs |
| Kalibracja smoke → LB | **~ -2,8** | przybliżenie |

### 3.1. Krzywa tokenów z notatek — **nie jest pomiarem tej rury**

```
100k → 24,7
175k → 27,2   (nasz smoke)
200k → 41,8
300k → 45,7
```

**Nie budować planu na 41,8 / 45,7.** To punkty krzywej Ducka z notatek, nie wynik tego pipeline'u. Nasz realny punkt to ~175k → 24–27. Ewentualny skok na 200k+ wymaga realokacji puli, której **strona korzyści nie została zmierzona**.

### 3.2. Ekonomia r019 — co z niej wynika

- **a/call 4,357 (ważone) / 5,204 (średnia)** — batching działa, ale nie jest magiczny.
- **841 tok/akcję** — tokeny są kosztem, nie tylko „myśleniem”.
- **Pula ~173,7k tok/grę** przy 110 grach.
- Liczba „1,13” **nie istnieje** w danych; 1 417 linii `requests.jsonl` to wszystkie żądania (z analizatorem), nie tylko akcyjne.
- „21/32 poziomów na capie 115” **nie odtwarza się**: **32/32** ukończonych poziomów miało ≤115 akcji. Efekt „wyczerpanej efektywności” jest realny (29,6% budżetu głębokości), ale konkretna liczba 21/32 pochodzi z innej definicji.
- **Bramka profilu deep = liczba poziomów, nie a/call** — w r019 a/call koreluje **odwrotnie** ze score (ls20 13,89 → 3,27 pkt; su15 1,85 → 56,42).

### 3.3. Smoke 10 gier nie rozstrzyga niczego poniżej ±9 pkt (pomiar 28.10)

Ten sam kod (c45 vs v11; `ARC3_VARIANT.env` identyczny, patch 0005 inertny, linia concurrency nieużywana
w smoke) dał dwa smoke'i: **26,78** i **18,54**. Pomiar sparowany po grach:

- poziomy: Δ = **−0,50 ± 0,60** (SD 1,90), t = −0,83
- score: Δ = **−8,24 ± 9,03** (SD 28,54), t = −0,91
- 3 gry lepiej, 3 gorzej, 4 bez zmian (cn04 5→1 poziom, g50t 3→0, ale dc22 3→4, su15 3→5)

Sampling: `LOCAL_ANALYZER_TEMPERATURE=0,7`, `TOP_P=0,95`, brak seeda. Konsekwencje:

1. **„NO-GO poniżej 29,02” nie odrzuca wariantu** i „GO powyżej” nie potwierdza poprawy — pojedynczy smoke
   to loteria. Wszystkie wcześniejsze porównania smoke-vs-smoke są w szumie.
2. Smoke zostaje jako **health-check** (`ARC3_SMOKE_OK`: brak crashy, tokeny > 0, akcje > 0), nie jako gate.
3. Jedynym arbitrem jest LB = **1 slot dziennie**, więc każda bramka typu „B ≥ A + 3” kosztuje dwa dni.
4. Jeśli smoke ma wrócić jako narzędzie decyzyjne: ustawić `LOCAL_ANALYZER_SEED` (determinizm) albo
   liczyć średnią z 3 przebiegów, albo zwiększyć liczbę gier. Szczegóły: `POMIAR-SMOKE-V11-2026-10-28.md`.

### 3.4. Ile poziomów trzeba na 50 pkt (matematyka wyniku)

Wagi poziomów rosną z numerem (`Σ l·s_l / Σ l`), więc **głębokość dominuje**. Dla gry o 8 poziomach
sufit samego wskaźnika ukończenia:

| ukończone k/8 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| score | 2,8 | 8,3 | 16,7 | **27,8** | 41,7 | 58,3 | 77,8 | 100 |

- 23,89 ≈ średnio **~3,5/8**; **50 pkt ≈ 5/8** (41,7) lub 4/8 przy dobrej efektywności → **1,4–1,6×** poziomów.
- Efektywność **nie** jest wąskim gardłem: 8,6 akcji/poziom vs 10,4 człowieka → `s_l` na sufitach 1,15.
- Tracimy **ogon**, nie środek: w smoke v11 połowa gier ma ~50% głębokości, a g50t 0/7, cn04 1/6,
  tn36 1/7 ciągną średnią w dół. `ARC3_LEVEL_TOKEN_CAP=45000` + `MIN_DONE=0` **celuje w ten ogon**
  — dlatego cap obniżył wynik (23,89 vs 26,25).
- Tufa (write-up): „solvability zależy od modelu, koszt od harnessu”. Fast-line ma 528 tok/s,
  linia 27B ~33 tok/s/strumień — kupiliśmy 16× tokenów za cenę mózgu.

---

## 4. Co jest dowiedzione, co hipotezą, co obalone

### 4.1. Zmierzone / potwierdzone

- best COMPLETE **26,25** (duck v3)
- c45 #57629847 **0,00**
- smoke c45 **26,78** (32/69)
- r019 ~**175k tok/grę**, LB **24,66**
- próg nagród (LB 24.10) **49,85**; lider **68,91** (Tufa Labs)
- sufit ruchów **~29,0**; +1 poziom/grę **≈44**
- `PERSISTENT_FUNCTIONS_SCOPE='game'` akceptowane — pamięć między poziomami w grze działa
- finalista jako publiczny notebook do **31.10–1.11**
- `ARC3_ABANDON_TOKENS` / `ARC3_ABANDON_MIN_LEVELS` **martwe** w tym drzewie
- `cap=0` wyłącza cały patch 0004 (RESET_LEVEL i ABANDON też)
- replay `LevelBudget` odtwarza decyzje kontroli 45k/r1 z dokładnością **0–4 akcji**
- L1 60k/r0: **6/10 gier ubitych, 10/32 poziomów straconych, 384 218/1 417 188 tokenów zaoszczędzonych (27%)**
- cap90: **0 resetów, 0 porzuceń**, max ukończony poziom 88 114 zachowany
- 75k/md1: **2 gry ubite, 0 poziomów straconych, 16 338 tokenów (1,1%)**
- Rust **36/36**; llm-agent **108/108**; patch-chain **5/5 + 9/9 logiki** (3 sandbox skipped na Windows)

### 4.2. Hipotezy — **nie cytować jako faktów**

- fix concurrency (120 → 10) naprawia 0,00 — **brak logu reruna** (dostępny tylko w przeglądarce usera)
- 41,8 / 45,7 — punkty krzywej z notatek, nie pomiar tej rury
- early-abandon +7 pkt — symulacja na założeniach; **strona kosztu obalona pomiarem 28.10**, strona korzyści w kolejce 110 gier nadal niezmierzona
- 7 słabych punktów README (pamięć między passami, transfer poziomów, role temperatur itd.) — **zero A/B**
- pamięć między passami — **martwy end** przy `n_passes=1` / scorecard bez powtórzeń `game_id`; wracać tylko przy powtórzeniach z sondy rosteru
- arXiv 2605.25931 / RHAE 0.30 — niezweryfikowane
- roster prywatny = 25 gier publicznych — niepewne (sonda rosteru w v11 istnieje dlatego)
- „+0,4 / +2,2” z opinii innego AI — to korelacje między pakietami, **nie czyste A/B**

### 4.3. Rejestr retrakcji — nie powtarzać tych błędów

| Twierdzenie | Status | Powód |
|---|---|---|
| v11-Smak „git apply PASS na r033” | **OBALONE** | pada na `Makefile:40` i `README.md:1`; certyfikat z brudnego drzewa. v11-Smak = archiwum, nie kandydat. |
| „v9 umrze przed serwerem” (brak końcowego `\n`) | **OBALONE** | komórka 498 799 znaków jest bajt-identyczna z c45, która przeszła smoke i rerun; IPython `%%writefile` dopisuje `\n`. |
| „21/32 poziomów ≤115 akcji” | **NIE ODTWARZA SIĘ** | 32/32; inna definicja. |
| „1,13” (a/call) | **OBALONE** | 1 417 linii to wszystkie żądania; poprawne 4,357 / 5,204. |
| „game_weights realokuje budżet” | **MIT** | tylko agregacja diagnostyki w `benchmark.py`. |
| „Replay = +45–50% → 45 pkt” | **OBALONE** | efektywność H/A już ~0,95; replay podnosi efektywność, nie sufit; realnie ≤ +1,5. |
| „41,8 dla slotu A” | **BŁĄD** | 41,8 to punkt krzywej z notatek; realne ~25–30. |
| „31–42 i blisko progu” | **BŁĄD** | próg 49,85; luka ~+24 pkt. |
| „Pamięć między passami = największa dźwignia” | **MARTWY END** | `n_passes=1`; scorecard bez powtórzeń `game_id`. |
| „Duck harness jest MIT” | **BŁĄD** | GitHub API: `license: null`; używać jako rury, nie kopiować. |
| „-f submission.parquet blokuje API-submit” | **BŁĄD** | prawdziwą przyczyną było `-f` jako ścieżka repo zamiast nazwy pliku; poprawne `-f submission.parquet` → rc=0. |
| „40,97 to próg nagród” | **NIEAKTUALNE** | to 5. miejsce ze snapshotu 10.10; 24.10 próg = 49,85. |
| „Deadline 26.10 = koniec” | **BŁĄD** | entry zaakceptowany; finał 2.11. |

---

## 5. Architektura Ducka — jak działa rura

```
vLLM (Qwen3.6-27B-FP8, 1 GPU, ctx 32768)
  └─ ToolAgent — jedno narzędzie: `python` (REPL, 30 s limit, output 1024 tok.)
       ├─ Stan wstrzykiwany do REPL-a:
       │    current_frame (.ascii / .segmentation / .step / .level / .shape)
       │    previous_frame, history[], transitions[], last_action_result, valid_actions
       │    action([...]) — wykonuje ruchy w środowisku z poziomu Pythona
       └─ World model: 7 slotów tekstowych przenoszonych między turami
```

**Percepcja (3 kanały):**
1. `current_frame.ascii` — siatka 64×64 jako litery kodujące kolory ARC (prompt zabrania skanowania całości).
2. `current_frame.segmentation` — **główny widok**: obiekty 4-connected, każdy z `id, color, hash, pixels, boundary, children` + `adjacency_list`.
3. Obraz PNG aktualnej siatki (upscale ×4), tylko tryb `current_grid`.

**Zarządzanie kontekstem:**
- Okno 32 768 tokenów; `_trim_messages_for_context` usuwa najstarsze bloki.
- `_keep_recent_history_turns` → ostatnie **30 tur asystenta**.
- `_persistent_history_messages` przenosi to, co przetrwało, do kolejnej tury.

**World model — 7 slotów:**
`world_model` · `goal_model` · `action_model` · `recent_findings` · `open_questions` · `current_plan` · `cross_level_notes`

Model emituje bloki w tekście (`World model: ...`), są parsowane (`_extract_labeled_blocks`) i wstrzykiwane do następnego promptu jako *„Working world model carried from earlier turns:”*.

### 5.1. Siedem słabych punktów Ducka — i co z tym zrobić

| # | Luka | Fakt | Fix | Wpływ |
|---|---|---|---|---|
| A | Brak pamięci między passami | `n_passes: 20`; każdy pass tworzy nowy `_HarnessGameSession` → `_ensure_session()` zeruje `_history_messages` i `_summarized_knowledge`. Wszystkie passy odkrywają grę od zera. | Zapis world modelu do pliku kluczowanego `game_id`, ładowany przy starcie sesji. | **Martwy end przy `n_passes=1`** — nie budować na tym planu. |
| B | Wiedza kasowana przy przejściu poziomu | `tool_agent.py:1113-1126` — przy `level_transition` / `run_complete` / `game_over` kasowane **6 z 7 slotów**; zostaje `cross_level_notes`. | Migrować treść do `cross_level_notes` zamiast kasować + jawna instrukcja w prompcie. | Wysoki, koszt niski — ale **zero A/B**. |
| C | Nadpisywanie zamiast akumulacji | `self._summarized_knowledge[key] = value` — czysty overwrite. | Merge z historią (append + dedup), kasowanie tylko przy jawnej sprzeczności. | Średni. |
| D | Brak pamięci negatywnej | Model nie ma gdzie zapisać „akcja X to no-op” / „hipoteza Y obalona”. | Nowy slot `Ruled out` + instrukcja. | Uderza w RHAE — mniej zmarnowanych akcji. |
| E | Kruchy parser etykiet | `_extract_labeled_blocks` wymaga linii `label:` po zdjęciu `-`/`*`; `**World model:**` **nie zadziała**. | Zdejmować markdown (`*`, `_`, `#`, backticki), akceptować `-` i `=` jako separator. | ~15 min, czysty zysk. |
| F | Percepcja bez sygnału czasowego | Tylko pojedynczy PNG bieżącej siatki; brak delty. | prev\|current obok siebie, overlay delty, tekstowy diff segmentacji. | Do przetestowania; 256×256 tanio. |
| G | Konfiguracja | `temperature 0.6`, `top_p 0.95`, `top_k 20`, `tool_output_tokens 1024`, `max_runtime_minutes 45`, `n_passes 20`. | Rozdzielić role passów: pass 1 wysoka temp. (eksploracja), passy 2–20 niska (~0.2–0.3). | Tanie A/B. |

**Ważne ostrzeżenie Tufa Labs:** *„gains came from multimodality and better base models, not hand-built tools”* — dorabianie specjalistycznych narzędzi szkodzi. Trzymać się czystego, ogólnego interfejsu.

### 5.2. Co z tego realnie weszło do planu

- **Pamięć między poziomami w grze** działa (`PERSISTENT_FUNCTIONS_SCOPE='game'`) — to nie jest luka do naprawy.
- **Pamięć między passami** — nie używać przy `n_passes=1`.
- **Parser etykiet** — tani zysk, ale nie był osobnym slotem.
- **Transfer między poziomami** — mechanizm istnieje, praktycznie wyłączony; kandydat na później.
- **Ruled out / no-op** — w naszym `llm-agent` v6.x; integracja z Duckiem to nowy, nieprzetestowany kod.

---

## 6. Nasz agent (`llm-agent` v6.x) — co zbudowano i co naprawiono

### 6.1. Architektura

```
arc-agi-3/llm-agent/
├── grid_utils.py       # ASCII, segmentacja, kolory
├── llm_policy.py       # LLM client, prompt, anti-loop, parsowanie akcji
├── llm_agent.py        # adapter do ARC-AGI-3-Agents framework
├── knobs.py            # 24 pokrętła ARC3_* (env ARC3_KNOBS_JSON)
├── goal_classifier.py  # detekcja 8 klas celu
├── value_gate.py       # learned ValueGate (bez wag = OFF)
├── build_notebook.py   # generator notebooka Kaggle
└── notebook/           # katalog push na Kaggle
```

- Start vLLM z Qwen3.6-27B-FP8.
- Stan gry jako ASCII + segmentacja.
- LLM odpowiada JSON-em: `{"action": "UP", "reasoning": "..."}`.
- Action batching do 15 akcji; anti-loop; fallback heurystyczny.

### 6.2. Mechanizmy, które przetrwały

- **Field guide** — wygrana to prawie zawsze „wszystko z X”; kontury/kropkowane obrysy = cele; duży niereagujący obszar = wzorzec do skopiowania (~40% gier); CONFIRM tylko po ustawieniu wszystkiego; malejący licznik = limit kroków/żyć, 0 = przegrana.
- **Goal persistence** — jedna gra = jeden warunek wygranej; po rozwiązaniu poziomu cel znany, zapisany; nowy poziom dokłada mechanikę, nie zmienia klasy celu.
- **Notatki gry** — model może dodać `"notes"` do pierwszej akcji; polityka trzyma ostatnie 4 i wstrzykuje co turę; czyszczone w `reset_game`, trzymane między poziomami.
- **Stuck protocol + audyt** — po 40 akcjach bez ukończenia poziomu i co 15 potem prompt żąda rejestru sfalsyfikowanych hipotez (✗) i najtańszego eksperymentu 1–2 akcje.
- **Anty-dysertacja** — max ~60 słów uzasadnienia; „act more, deliberate less”.
- **No-op detector** — dokładne równanie krotek; w grach z animowanym HUD milczy (zero fałszywych pozytywów); progi 6/3.
- **Lessons-between-games** — uczenie runa in-context; max 8 lekcji.
- **Goal classifier** — 8 klas: dotrzyj, umieść, pokryj, kopiuj wzorzec, ograniczenia lokalne, zredukuj, przepływ, wyrównaj.
- **ValueGate** — deterministyczny (novelty + change − loop), knob `VALUE_GATE` default 0; bez wag = OFF.
- **CEM po knobs** — spięty z realnym ewaluatorem, ale przy braku fitness (0 GPU quota, 1 LB/dzień) jest ślepy; nie priorytet.

### 6.3. Błędy, które naprawiono (i które warto pamiętać)

| Błąd | Skutek | Fix |
|---|---|---|
| Parser `re.search(r'\{.*?\}')` / `r'\[.*?\]'` (non-greedy) | Zagnieżdżony `reasoning` urywa JSON → akcja odrzucona → fallback. | `json.JSONDecoder.raw_decode` (`_extract_action_objects`). |
| Batch czyta tablicę, ale `get_action` zwraca `actions[0]` | Akcje 2..N wyrzucane; batching nie działa. | Kolejka `_action_queue` do 15. |
| `load_mlp_weights` fallback = losowe wagi | Gate na losowych wagach = szum. | Brak pliku = gate całkiem OFF. |
| `training_data_generator.py` używa Mock policy | Nie wygenerowano prawdziwych danych. | Prawdziwe dane z przebiegów albo lokalnych gier. |
| Split 80/20 po wierszach | Wyciek (kolejne stany identyczne); „acc 0.913” zawyżone. | Split per GRA + ostrzeżenie przy acc ≤ base rate + 10pp. |
| Adaptive temperature bez gate'a | `ml_value=0.5` → temperatura zawsze 0.6 (martwe). | Deterministyczny wyzwalacz. |
| `pattern_library` / `multi-hypothesis` bez wywołań | Martwy kod. | Usunąć albo podłączyć. |
| `verify_v11.py` `Path.write_text` LF→CRLF na Windows | Fałszywy negatyw patchy. | `write_bytes` z LF. |
| `duck-v12-plan` miał `PLAN_COMMIT="0"` mimo komentarza „1” | Klon kontroli, zero testu planu. | Ustawiono `"1"`, zweryfikowano `V11_PROFILE=plan`, `ARC3_PLAN_COMMIT=1`, `ARC3_ESCALATE_ACTIONS=60`; różnią się tylko komórki 1/2. |

### 6.4. Testy (stan 28.10)

- **Rust:** 36/36.
- **llm-agent:** **108/108** (wcześniej 107/108; jedyny fail to Windows `cp1250` `UnicodeEncodeError` na `→`; `PYTHONUTF8=1` go usuwa).
- **Patch-chain v11:** 5/5 patchy, drzewo kompiluje, **9/9 testów logiki** `commit(plan)`; 3 testy sandboxu **SKIP** na Windows (sandbox nie startuje — ograniczenie środowiska, nie logiki).
- **Warianty env-only:** `ALL CHECKS PASSED` dla `cap90`, `abandon`, `nocap` (33 komórki, tylko komórki 0/1 różne od kontroli, 5/5 patchy bajtowo identycznych, stan maszyny budżetu).

---

## 7. c45 #57629847 = 0,00 — diagnoza

### 7.1. Łańcuch dowodów

1. Interaktywny smoke c45 był **zdrowy**: 26,78, 32 poziomy, log „harness patch applied successfully”.
2. `submission.parquet` ma **2 648 B** — identyczny stub jak r019, który wziął 27,21. **Scoring czyta wyniki reruna, nie parquet.**
3. W komórce solvera: `if TRUE_SUBMISSION: bm.solver.concurrency = 120` przy serwerze **MAXREQ=10**.
4. Smoke szedł 10 gier na 10 slotów; rerun cisnął ~110 gier przez 10 slotów.
5. Komentarze patcha dokumentują patologię: „refused connection… wait it out”, „fourteenth of the rate”.

**Hipoteza nr 1:** głód slotów / storm połączeń / eksmisja prefiksów → zero poziomów.

### 7.2. Czego to **nie** dowodzi

- **Brak logu reruna.** API go nie serwuje; log jest tylko w przeglądarce usera: `Submissions → #57629847 → log`.
- Alternatywy: crash SGLanga na starcie, inne zachowanie gier z gatewaya.
- **Smoke nie testuje ścieżki TRUE_SUBMISSION.** Prawdziwy werdykt fixa concurrency da dopiero submit. To świadome ryzyko slotu A.

### 7.3. Fix

`concurrency = 10` **oraz** `ARC3_MAX_ACTIVE_STREAMS=10` (match backend MAXREQ=10; avoid 120-way fanout). W `duck-v11-c45` fix jest domyślny; `concurrency = 120` usunięte.

**Stan testu (28.10):** fix jest w `arc3-duck-v11` v1 (`ARC3_TRUE_CONCURRENCY=10`, linia
`bm.solver.concurrency = int(os.environ.get("ARC3_TRUE_CONCURRENCY", "10"))`), submit `57737623`.
Hipoteza nr 1 jest teraz **testowana na LB**; smoke jej nie dotyka (w smoke `concurrency = len(games) = 10`).

---

## 8. Pakiet `duck-v11-c45` — kandydat nr 1

**Lokalizacja:** `arc-agi-3/duck-v11-c45/`
**Kaggle:** `petersharps/arc3-duck-v11`
**Baza:** `duck-c45` — notebook, który realnie zadziałał na Kaggle (smoke COMPLETE, 10 gier).

### 8.1. Co zawiera

| Zmiana | Gdzie | Domyślnie |
|---|---|---|
| fix `concurrency=120` → `ARC3_TRUE_CONCURRENCY` | komórka solvera | **10** |
| `commit(plan)` + eskalacja (patch `0005-plan-commit`, 4 pliki, 19,7 KB) | `duck-extra-03.patch` | **OFF** (`PLAN_COMMIT="0"`) |
| komórka pomiarowa (jak v9, zero tokenów) | koniec notebooka | zawsze |

### 8.2. Statystyka

- **33 komórki**, 18 code cells.
- **5 patchy:** `harness-changes.patch`, `duck-extra-00.patch`, `duck-extra-01.patch`, `duck-extra-02.patch`, `duck-extra-03.patch`.
- Patch 0005 to **19,7 KB / 4 pliki** — minimalny port `commit(plan)`, nie przebudowa 660 KB.
- Metadata: `petersharps/arc3-duck-v11`, `is_private: true`, GPU RTX6000, `enable_internet: false`, docker pin `57e612b4…`.
- Źródła: `dfranzen/pennyroyal-v253`, `dfranzen/taaf-kaggle-source-bundle-copy`; modele `albucino-qwen3-8-flash-next-drafter`, `intel-qwen3.8-flash-next-w4a16-autoround`.

### 8.3. Przełącznik

- `PLAN_COMMIT = "0"` → profil **`c45fix`**: zachowanie identyczne z c45 poza fixem concurrency. **Slot A.**
- `PLAN_COMMIT = "1"` → profil **`plan`**: `commit(plan)` z `expect` per krok + dyrektywa eskalacyjna co **60 akcji** na niedokończonym poziomie. **Slot B.**

### 8.4. `commit(plan)` — co dokładnie robi

Plan to lista kroków; krok to akcja (`"UP"`, `{"action": "MOUSE", "row": r, "col": c}`) albo dict z `expect={...}`. Po każdym kroku oczekiwanie jest porównywane z faktyczną ramką; plan zatrzymuje się na pierwszym mismatch i zwraca `mismatch` z nazwą pola.

Obsługiwane oczekiwania:
- `level` (int)
- `board_changed` (bool)
- `step` (int, absolutny)
- `digest` (z `frame_digest()`)
- `cells` (`{'row,col': symbol}` albo `[[row, col, symbol], ...]`)

Zatrzymuje się też na: ukończeniu poziomu, game over, run complete, `max_actions` (default 40).

**Po co:** zły model świata kosztuje **jedną akcję** i zwraca diff, zamiast marnować resztę planu na planszy, która już nie pasuje.

### 8.5. Weryfikacja offline (28.10, powtórzona)

```
OK   notebook parses (33 cells)
OK   code cells compile (18)
OK   concurrency fix present
OK   concurrency 120 gone
OK   extra-03 registered
OK   metering cell present
OK   ONLY_RESET_LEVELS pinned
OK   switch PLAN_COMMIT=0
OK   switch PLAN_COMMIT=1
OK   metadata id/title/code_file
OK   all /kaggle/input paths declared
OK   all five patches extracted
OK   applies: harness-changes.patch
OK   applies: duck-extra-00.patch
OK   applies: duck-extra-01.patch
OK   applies: duck-extra-02.patch
OK   applies: duck-extra-03.patch
OK   patched tree compiles
OK   9 plan-commit logic tests pass
SKIP 3 sandbox tests (Windows sandbox cannot start; documented limitation, not a logic failure)
ALL CHECKS PASSED
```

### 8.6. Czego to nie dowodzi

- Zachowania na żywym gatewayu.
- Zysku punktowego `commit(plan)`.
- Że fix concurrency naprawia 0,00 — to nadal hipoteza bez logu reruna.

---

## 9. L1 — budżet poziomu i ABANDON: pełny pomiar

### 9.1. Semantyka patcha 0004 (`arc3_level_budget.py`)

- `ARC3_LEVEL_TOKEN_CAP` — limit tokenów **na poziom**.
- `ARC3_LEVEL_RESETS_MAX` — ile darmowych RESET_LEVEL przed ABANDON.
- `ARC3_LEVEL_MIN_DONE` — ile ukończonych poziomów trzeba mieć, żeby w ogóle móc porzucić grę.
- `cap=0` → **cały patch inertny**: `peek`/`step` zwracają KEEP_GOING; **RESET_LEVEL i ABANDON też nie działają**.
- `resets=0` → pierwsze przekroczenie capa to ABANDON, nie darmowy RESET.
- `min_done=0` → można porzucić nawet grę z 0 ukończonymi poziomami.

**Martwe zmienne:** `ARC3_ABANDON_TOKENS`, `ARC3_ABANDON_MIN_LEVELS` — należą do patcha 0003, który 0004 zastąpił. Zostawione dla proweniencji.

### 9.2. Walidacja replayu — zanim wyciągnięto wnioski

Replay `LevelBudget` z patcha 0004 na realnym trace r085 (`benchmark.json`, 10 gier, 1 pass, 11:34:10 → 12:22:16). Konfiguracja kontrolna c45 (`cap=45k, resets=1`) przewiduje auto-RESET w:

| Gra | Przewidziany RESET | Rzeczywiste RESET w trace | Zgodność |
|---|---|---|---|
| tn36 | 106 | 77, **106**, 168 | dokładna |
| dc22 | 101 | **101** | dokładna |
| s5i5 | 33, 70 | **33**, 68 | 33 dokładna, 70 vs 68 |
| m0r0 | 247 | 249 | ±2 |
| sc25 | 178 | 125, 160, **182** | ±4 |
| ls20 | 148 | **146**, 303 | ±2 |
| su15 | 36 | **34**, 101 | ±2 |
| g50t | 33 | **31** | ±2 |
| cn04 | — | 0 (warmup) | — |
| ka59 | — | — | — |

Pozostałe RESET-y w trace to resety agenta, nie budżetu. **Wniosek: replay odtwarza decyzje budżetu z dokładnością 0–4 akcji — model tokenów jest dobry.** To kontrfaktyczna symulacja na zaobserwowanym przebiegu, nie re-run.

### 9.3. Koszt tokenowy poziomów (realny trace)

| Gra | Ukończone poziomy (tokeny) | Poziom nieukończony | Max ukończony |
|---|---|---|---|
| tn36 | 6 776 | 88 977 | 6 776 |
| m0r0 | 18 907 · 13 225 · 34 405 · 29 001 | 48 503 | 34 405 |
| cn04 | 36 741 · 38 214 · 27 200 · 18 364 · 27 453 | 2 291 | 38 214 |
| dc22 | 25 204 · 66 607 · 41 255 | 12 263 | 66 607 |
| ka59 | 10 561 · 30 656 · 27 613 · 38 606 · 20 933 | 18 952 | 38 606 |
| sc25 | 44 441 · 14 207 · 30 524 | 50 806 | 44 441 |
| s5i5 | 14 018 · 65 010 | 78 385 | 65 010 |
| ls20 | 11 875 · 62 017 · 44 369 | 14 151 | 62 017 |
| su15 | 11 857 · 68 648 · 31 963 | 40 634 | 68 648 |
| g50t | **88 114** · 23 941 · 39 521 | 0 | **88 114** |

**Maksymalny ukończony poziom kosztował 88 114 tokenów (g50t L1).** Poziomy, które „wyglądają na martwe”, często są po prostu trudne i później kończone: su15 L2 68,6k, dc22 L2 66,6k, s5i5 L2 65k, ls20 L2 62k.

### 9.4. Sweep ABANDON (`resets=0`)

| cap | min_done | Ubite gry | Utracone poziomy | Zaoszczędzone tokeny | Gry |
|---|---|---|---|---|---|
| 45k | 0 | 8 | 10 | 441 067 | tn36 0, m0r0 0, dc22 −2, sc25 0, s5i5 −1, ls20 −2, su15 −2, g50t −3 |
| **60k** | **0** | **6** | **10** | **384 218** | tn36 0, dc22 −2, s5i5 −1, ls20 −2, su15 −2, g50t −3 |
| 75k | 0 | 3 | 3 | 83 843 | tn36 0, s5i5 0, g50t −3 |
| 88 114 | 0 | 2 | 3 | 63 554 | tn36 0, g50t −3 |
| 90k | 0 | 0 | 0 | 0 | — |
| 60k | 1 | 5 | 7 | 299 524 | tn36 0, dc22 −2, s5i5 −1, ls20 −2, su15 −2 |
| **75k** | **1** | **2** | **0** | **16 338** | tn36 0, s5i5 0 |
| 90k | 1 | 0 | 0 | 0 | — |

Suma trace: **32 poziomy, 1 417 188 tokenów**.

### 9.5. Sweep RESET (`resets=1`, tryb kontrolny)

| cap | Resety | Porzucenia |
|---|---|---|
| 45k (kontrola) | 9 | 0 |
| 60k | 7 | 0 |
| 75k | 3 | 0 |
| 88 114 | 2 | 0 |
| **90k** | **0** | **0** |
| 105k | 0 | 0 |

Podniesienie capa przy `resets=1` **nie porzuca żadnej gry** — tylko usuwa resety. To czysta subtrakcja mechanizmu, nie nowy mechanizm.

### 9.6. Wnioski

1. **L1 ABANDON@60k nie jest kandydatem.** Na realnym trace ubija 6/10 gier i traci 10/32 poziomów, oszczędzając 27% tokenów. Koszt jest zmierzony; korzyść (realokacja w kolejce 110 gier) **nie** — smoke ma 10 gier = 10 slotów, więc nie ma do kogo realokować.
2. **Założenie „martwe gry” jest na tym trace fałszywe.** Najdroższe poziomy są często kończone (g50t L1 88k, su15 L2 68,6k, dc22 L2 66,6k, s5i5 L2 65k, ls20 L2 62k). Cap per poziom nie odróżnia „trudny, ale postępuje” od „beznadziejny”. To ta sama klasa błędu (zła populacja), którą opinia innego AI słusznie zarzuciła modelowi capa.
3. **Jedyny nie-destrukcyjny abandon to 75k/min_done=1:** 2 gry ubite, 0 poziomów straconych, 1,1% tokenów. Za mało, by samodzielnie uzasadnić slot.
4. **Cap90/resets=1 to najlepszy wariant env-only:** zachowuje wszystkie zaobserwowane ukończone poziomy (max 88 114), usuwa wszystkie 9 resetów, nie porzuca nikogo, a bezpiecznik ABANDON zostawia dopiero przy 180k.
5. **`ARC3_ABANDON_TOKENS` jest martwy** — realna dźwignia to CAP + RESETS_MAX + MIN_DONE.

### 9.7. Czego ten pomiar **nie** rozstrzyga

- **Strony korzyści abandon w kolejce 110 gier.** Smoke nie ma kolejki. Dopiero slot na żywym rosterze może pokazać, czy wcześniejsze zwolnienie slotu daje więcej poziomów, niż zabiera.
- **Kontrfaktu bez resetów.** Replay zakłada tę samą sekwencję tokenów; bez resetu agent mógłby zachować się inaczej. To ograniczenie każdego replayu.
- **Wpływu na score.** Podajemy poziomy i tokeny, nie punkty: score nie jest liniowy w poziomach.

### 9.8. Skąd wzięło się „+5–7” i dlaczego jest obalone

15.10 hipoteza: pula runu ~19,7M tokenów; ~30 martwych gier × 60k = ~3,4M uwolnione; 80 ocalałych dostaje ~+43k każdy → ~205–220k → krzywa mówi 41+ → mean ≈ (80×41 + 30×6)/110 ≈ **31 (+7)**.

**Co z tego zostało:**
- Mechanizm realokacji jest realny matematycznie.
- **Założenie „spora frakcja gier to 0–10 / martwe” nie zostało potwierdzone na r085.** Wręcz przeciwnie: 6/10 gier miało ukończone poziomy, a najdroższe poziomy były kończone.
- **Smoke 10 gier = 10 slotów** — nie ma kolejki, więc nie da się zmierzyć strony korzyści.
- To była **symulacja na założeniach**, nie pomiar LB. Traktować jak hipotezę do testu na żywym rosterze, nie jak fakt.

---

## 10. Warianty env-only — co jest czym

Wszystkie zbudowane z `duck-v11-c45` przez `tools/build_env_variant.py`; **zero nowych patchy** — tylko `ARC3_VARIANT["env"]` w komórce preflight. Wszystkie pięć komórek patchy jest **bajtowo identyczne** z kontrolą. Weryfikacja: `tools/verify_env_variant.py`.

| Pakiet | cap | resets | min_done | PLAN_COMMIT | Rola | Status |
|---|---|---|---|---|---|---|
| `duck-v11-c45` | 45 000 | 1 | 0 | "0" | **Kontrola / slot A** | kandydat, nie wysłany |
| `duck-v12-plan` | 45 000 | 1 | 0 | **"1"** | **Slot B — plan-commit** | kandydat, nie wysłany |
| `duck-v11-c45-cap90` | **90 000** | 1 | 0 | "0" | **Slot C — najlepszy env-only** | kandydat, nie wysłany |
| `duck-v11-c45-abandon` | 60 000 | **0** | 0 | "0" | **Negatywna kontrola** | **NIE wysyłać** |
| `duck-v11-c45-nocap` | **0** | 0 | 0 | "0" | Fallback „czysta subtrakcja capa” | nie wysłany |

**Wspólny env kontroli** (z `ARC3_VARIANT["env"]`; `PLAN_COMMIT` jest osobno, w komórce 3):

```text
ARC3_ABANDON_MIN_LEVELS=0
ARC3_ABANDON_TOKENS=0
ARC3_EXPERIMENT_HINT=1
ARC3_LEVEL_MIN_DONE=0
ARC3_LEVEL_NOTES=1
ARC3_LEVEL_RESETS_MAX=1
ARC3_LEVEL_TOKEN_CAP=45000
ARC3_STUCK_AUDIT_TOKENS=60000
ARC3_WORLD_MODEL=0
ARC3_WORLD_MODEL_NUDGE=0
```

Warianty zmieniają **tylko** `ARC3_LEVEL_TOKEN_CAP` / `ARC3_LEVEL_RESETS_MAX` / `ARC3_LEVEL_MIN_DONE`; patch cells pozostają bajtowo identyczne.

### 10.1. `cap90` — dlaczego 90k

- Najdroższy ukończony poziom w trace: **88 114** (g50t L1).
- 90k jest powyżej niego → **nie może ubić żadnego zaobserwowanego postępu**.
- Resety znikają, bo żaden poziom nie przekracza 90k.
- ABANDON zostaje jako bezpiecznik dla poziomu, który zje **180k** (po jednym darmowym resecie) — na trace nieosiągalny.
- Testy stanu maszyny: KEEP przy 88 114, RESET przy 90k, KEEP przy 179 999, ABANDON przy 180k.

### 10.2. `abandon` — dlaczego NIE wysyłać

- 60k/r0/md0: 6/10 gier ubitych, 10/32 poziomów straconych, 27% tokenów zaoszczędzonych.
- Żadna gra nie zyskała poziomu.
- To pomiar **kosztu**, nie korzyści.
- **Nie wysyłać bez nowej hipotezy i świeżego pomiaru.**

### 10.3. `nocap` — kiedy używać

- `cap=0` → patch 0004 całkowicie inertny: brak capa, brak RESET_LEVEL, brak ABANDON.
- Fallback w slocie C, jeśli plan-commit okaże się gorszy od kontroli.
- Uwaga: A i C to różne dni i różne warunki (limit 1 slot/dzień), więc to nie jest idealne A/B. `cap90` jest lepszy, bo zachowuje bezpiecznik ABANDON.

---

## 11. Plan slotów A/B/C — harmonogram i bramki

### 11.1. Harmonogram (6 okien: 28.10–2.11)

| Slot | Data | Wariant | Pytanie decyzyjne | Oczekiwanie | Kill / keep |
|---|---|---|---|---|---|
| **A** | 28.10 | `PLAN_COMMIT="0"` (c45fix, cap45/r1) | czy fix concurrency naprawia 0,00? | ~25–30 | **wynik: 23,89** — fix działa (0,00 → 23,89), ale cap45k/r1 kosztuje ~2,4 pkt |
| **B** | 29.10 | **model**: `arc3-duck-v13-27b` (stock Tufa, 27B FP8) **albo** `nocap` (jeśli smoke v13 < 30) | czy 27B bije fast-line? | 27B: 30–55 (nieznane); nocap: ~26,3 | keep jeśli ≥ 26,3 (A + ~2,4) |
| **C** | 30.10 | zwycięzca B + `PLAN_COMMIT="1"` (`duck-v12-plan`) | czy plan-commit dokłada? | B + 2–6 (hipoteza) | keep jeśli ≥ B + 2; inaczej zamroź B |
| **D** | 31.10 | finalista + publiczny notebook | czy kandydat jest prize-eligible? | — | **must: publiczny do 1.11** |
| **E** | 1.11 | finalna submisja | — | — | — |
| **F** | 2.11 | bufor | — | — | — |

**Uwaga:** smoke nie testuje ścieżki TRUE_SUBMISSION — werdykt każdego slotu daje dopiero submit. To świadome ryzyko; dlatego A jest czystym testem jednej zmiennej.

### 11.2. Bramki decyzyjne (twarde)

1. **Slot A = 0,00** → **stop**: concurrency to nie przyczyna; diagnoza logu reruna (przeglądarka usera) przed B.
2. **Slot A ≤ 26,25** → **nie awansować B bez diagnozy**: najpierw sprawdzić, czy fix concurrency w ogóle działa; L1 odrzucony pomiarem 28.10.
3. **Slot B < A + 3** → **C = `cap90`** (czysta subtrakcja), nie dokładanie L1.
4. **Slot B ≥ 35** → **C = B + `cap90`** (stack) albo tuning planu; cel 32–40. Nie wracać do abandonu.
5. **Slot C < B + 2** → **zamrozić B jako finalistę**, nie ryzykować regresji.
6. Zawsze: **finalista jako publiczny notebook do 31.10–1.11** — inaczej nagroda przepada niezależnie od wyniku.

### 11.3. Stan wykonania (aktualizacja 28.10, 23:15 UTC)

- **Slot A: ROZSTRZYGNIĘTY — 23,89.** `petersharps/arc3-duck-v11` v1, submit **ref `57737623`**, 13:11:56 UTC,
  `SubmissionStatus.COMPLETE`, publicScore **23,89**. Smoke: `ARC3_SMOKE_OK` mean 18,54 (27/69) — w szumie.
  - **Fix concurrency działa**: c45 (`concurrency=120`) = 0,00 → v11 (`=10`) = 23,89.
  - **Cap45k/r1 kosztuje ~2,4 pkt**: v11 23,89 vs duck v3 (bez capa) 26,25. Diagnoza: cap + `MIN_DONE=0`
    ubija ogon (g50t 0/7, cn04 1/6, tn36 1/7) — dokładnie ten ogon, który decyduje o średniej (§3.4).
- **Slot B: WYSŁANY — `petersharps/arc3-duck-v13-27b` v1, ref `57752672`** (29.10 00:09:51 UTC, PENDING).
  Stock Tufa 27B-FP8, 28 lane'ów, 2,2 h/grę, bez capa. Smoke: COMPLETE 00:05:46, mean **0,73**,
  926 akcji, 448 782 tokenów, **155,5 tok/s** (batch 10), 4/10 gier z poziomem, wszystkie `cancelled`
  przez `soft_end`.
  - **Smoke nie jest porównywalny między modelami o różnym throughput** — v13 dostał 93 akcje/grę,
    v11 ~450. Dlatego bramka „≥ 25” została uchylona: liczy się **akcje/poziom** (v13: 20–47,
    czyli jak człowiek) i **tokens/game** (v13: 45k vs realne 120–200k). Szczegóły:
    `POMIAR-V13-27B-2026-10-29.md`.
  - Rachunek pokrycia: 80 gier / 28 lane'ów = 2,9 fali × 2,2 h = **6,3 h < 9 h** → wszystkie gry
    mieszczą się w budżecie (inaczej niż `nocap` na 10 lane'ach: 17,6 h).
- **Fallback (jeśli B < 26) = `cap90`**, nie `nocap`: cap90 (~28 min/grę) daje ~190 slotów w 9 h,
  więc pokrycie jest bezpieczne; `nocap` na 10 lane'ach grozi H1 (część gier w ogóle nie grana).
- **Slot C (30.10), jeśli B ≥ 26**: v13 + `max_runtime_s_per_game` 2,2 h → **3 h** (80/28 = 2,86
  fali × 3 h = 8,6 h < 9 h) — czysta dźwignia budżetu, zero zmian w zachowaniu agenta.
- Nie wysyłać `duck-v11-c45-abandon`.
- L3 (probe opening) odłożone — bottleneckiem są trudne poziomy, nie ślepe otwarcia.
- **Smoke nie jest gate'em decyzyjnym i nie jest porównywalny między modelami o różnym
  throughput** — mierzy „ile poziomów w stałym czasie”, a nie „jak dobry jest model”. Do decyzji
  służą: akcje/poziom, tokens/game i pokrycie w 9 h. Decyzje wariantowe: LB (1/dzień).
- **Rust + rayon**: sens tylko dla replay/scoringu > 10 wariantów; nie podnosi wyniku (polityka nie tworzy
  nowych rozwiązań poziomów). Odłożone do momentu, gdy wariantów będzie > 10.

---

## 12. Opinia innego AI — co przyjąć, co odrzucić

### 12.1. Co było dobre

- Proces: mierzyć, nie zgadywać; rozdzielać fakty od hipotez; nie kumulować zmian bez pomiaru.
- Trafna diagnoza, że model capa/abandonu opiera się na **złej populacji** („martwe gry”).
- Trafne wskazanie, że **„+0,4 / +2,2” to korelacje między pakietami, nie czyste A/B**.
- Trafne wskazanie, że **„+5–7 abandon” ma tę samą wadę**, którą sama diagnozowała w modelu capa.

### 12.2. Co było błędne

- Traktowanie korelacji między pakietami i symulacji jako pomiarów.
- „41,8” jako oczekiwanie slotu A — to punkt krzywej z notatek.
- „31–42 i blisko progu” — próg to 49,85, luka ~+24.
- „+5–7 abandon” — symulacja na założeniach; strona kosztu obalona pomiarem, strona korzyści niezmierzona.
- Opis pakietu jako „PROFILE=plan, 31 komórek, patch w 2 chunkach” — to dotyczy odrzuconej linii v10/v11-Smak, nie kandydata.

### 12.3. Poprawiony jednolinijkowiec (do wklejania)

> Kandydat na slot A to `arc-agi-3/duck-v11-c45` (`petersharps/arc3-duck-v11`, commit 6c3e958): **33 komórki, 5 patchy aplikujących się na czysty bundle r033**, domyślnie **`PLAN_COMMIT="0"` → profil `c45fix`** (tylko fix `concurrency=120` → `ARC3_TRUE_CONCURRENCY=10`); `PLAN_COMMIT="1"` włącza `commit(plan)` + eskalację 60 akcji (profil `plan`); realne oczekiwanie slotu A to **~25–30 pkt** (best COMPLETE 26,25; c45 0,00; smoke 26,78), a nie 41,8; próg nagród **49,85** (LB 24.10) oznacza lukę **~+24 pkt**, więc slot A ma wartość diagnostyczną, nie nagrodową.

---

## 13. Operacje, CI i zasady bezpieczeństwa

### 13.1. Kaggle

- **1 oficjalne zgłoszenie dziennie**, reset 00:00 UTC.
- **Submit NIE wymaga kliknięcia w UI** — działa z CLI w Actions (sekret `KAGGLE_API_TOKEN` = konto `petersharps`). Dowody: r069 → ref `57607527` (PENDING→ERROR), r075 → ref `57629847` (c45, COMPLETE 0.00). Wcześniejsza teza „tylko właściciel może kliknąć” była **błędna** (wynikała z dwóch nieudanych prób, r011 bez `-f`, r015 z `-f` = ścieżka repo → 400).
- Poprawna forma (op `submit` w `kaggle/ops/ops.py`): `competitions submit -c arc-prize-2026-arc-agi-3 -k <kernel> -v <wersja> -f submission.parquet -m "<opis>"`; guardy: `confirm=true`, max 1/dzień, `file` to **nazwa pliku wyjściowego**, nie ścieżka.
- Nadal otwarte: czy CLI submit **rerunuje** wersję kernelu (hipoteza: tak — stąd PENDING→ERROR/COMPLETE po godzinach), czy tylko bierze ostatnie wyjście. Test empiryczny: po submit sprawdzić `kernels status` — jeśli kernel wraca w RUNNING, rerun leci.
- `-f submission.parquet` (nazwa pliku) działa; `-f` ze **ścieżką repo** daje 400. Bug kosztował 8 dni.
- `submission.parquet` 2 648 B to **stub**; scoring czyta rerun.
- Guard kwoty był martwy: `soft_end` nadpisywany później; fix = cap re-applied po nadpisaniu.
- `is_private: true` domyślnie; finalista musi być **publiczny** do 31.10–1.11.

### 13.2. GitHub Actions / sandbox

| Kanał | Działa? |
|---|---|
| `gh run view <id>` → ANNOTATIONS (`::notice`) | ✅ najlepszy |
| `gh api .../runs/<id>/jobs` | ✅ status per krok |
| Workflow commituje wyniki na branch | ✅ trwałe |
| `gh run view --log` / job logs | ❌ host poza allowlistą |
| Artefakty `upload-artifact` | ❌ `*.blob.core.windows.net` |
| `gh workflow run` / API dispatch | ❌ 403 |
| Checks API | ❌ `total_count: 0` |
| Listowanie sekretów | ❌ 403 |

**Wzorzec:** `touch <trigger>.trigger && git push` → workflow robi robotę → commituje wyniki do `arc-agi-3/kaggle/results/` → agent czyta po `git pull`.

**Pułapka:** `cmd 2>&1 | tee log` maskuje status wyjścia — każdy krok ma `set -o pipefail`.

**Workspace potrafi się zresetować** — push po każdym kroku, nie na koniec sesji.

### 13.3. Zasady użytkownika (obowiązują)

- **Nie ruszać plików GitHub starszych niż 2 dni** (dziś 28.10.2026).
- **Jedno oficjalne zgłoszenie dziennie.**
- **Submit idzie z ops/CLI** (działa, sprawdzone r069/r075); klikanie w UI nie jest wymagane, ale decyzja o spaleniu slotu należy do użytkownika.
- **Nie zgłaszać niezmierzonych wariantów.**
- **Nie prowadzić dwóch torów submisji naraz.**
- **Nie kopiować kodu Ducka** (`license: null`) — używać tylko jako rury; poprawki clean-room.
- **Finalista jako publiczny notebook do 31.10–1.11** albo nagroda przepada.

---

## 14. Czego NIE robić — lista anty-pułapek

1. **Nie budować planu na 41,8 / 45,7** z notatek ani na „+5–7” z symulacji abandonu.
2. **Nie opierać się na pamięci między passami** — martwy end przy `n_passes=1`.
3. **Nie integrować v6.9 z Duckiem przed L2** — nowy, nieprzetestowany kod; zero pomiarów.
4. **Nie zgłaszać dwóch wariantów w jednym dniu** ani dwóch torów naraz.
5. **Nie ruszać plików starszych niż 2 dni** na gałęzi GitHub.
6. **Nie kopiować kodu Ducka** — tylko jako rura; poprawki clean-room.
7. **Nie wysyłać `duck-v11-c45-abandon`** — to negatywna kontrola.
8. **Nie ufać `ARC3_ABANDON_TOKENS`** — martwe; używać cap/resets/min_done.
9. **Nie ustawiać `cap=0`, jeśli chce się zachować ABANDON/RESET** — cap=0 wyłącza cały patch.
10. **Nie traktować smoke jako testu TRUE_SUBMISSION** — to inna ścieżka.
11. **Nie stawiać bramek na a/call** — w r019 koreluje odwrotnie ze score; bramka = liczba poziomów.
12. **Nie mieszać snapshotów LB** — 40,97 (10.10) vs 49,85 (24.10).
13. **Nie cytować „21/32”, „1,13”, „replay +45–50%”, „game_weights realokuje”** — obalone.
14. **Nie zakładać, że roster prywatny = 25 gier publicznych** — niepewne.

---

## 15. Odtworzenie — komendy

### 15.1. Replay L1 / sweep

```powershell
$env:PYTHONUTF8="1"
python analysis\replay_level_budget.py --sweep
python analysis\replay_level_budget.py --cap 60000 --resets 0 --min-done 0
```

### 15.2. Weryfikacja wariantów env-only

```powershell
$env:PYTHONUTF8="1"
python duck-v11-c45\tools\verify_env_variant.py --pkg duck-v11-c45-cap90
python duck-v11-c45\tools\verify_env_variant.py --pkg duck-v11-c45-abandon
python duck-v11-c45\tools\verify_env_variant.py --pkg duck-v11-c45-nocap
```

Oczekiwane: `ALL CHECKS PASSED` (33 komórki, tylko komórki 0/1 różne od kontroli, 5/5 patchy, stan maszyny budżetu).

### 15.3. Pełny łańcuch patchy + testy logiki

```powershell
$env:PYTHONUTF8="1"
python duck-v11-c45\tools\verify_v11.py `
  --bundle kaggle\ops\results\r033-recon-bundle\bundle --tests
```

Oczekiwane: 5/5 patchy, drzewo kompiluje, 9/9 testów logiki; 3 testy sandboxu SKIP na Windows.

### 15.4. Testy projektu

```powershell
# Rust
cd rust; cargo test

# llm-agent
$env:PYTHONUTF8="1"
python -m pytest llm-agent -q
```

Oczekiwane: Rust 36/36; llm-agent 108/108.

### 15.5. Build wariantu env-only

```powershell
$env:PYTHONUTF8="1"
python duck-v11-c45\tools\build_env_variant.py --help
```

---

## 16. Mapa plików — co gdzie leży

### 16.1. Dokumenty decyzyjne (korzeń `arc-agi-3/`)

| Plik | Co zawiera |
|---|---|
| `KOMPENDIUM-ARC-AGI-3-2026-10-28.md` | **ten plik** — cała wiedza w jednym miejscu |
| `PLAN-50PLUS-2026-10-27.md` | plan agenta 50+, sloty A/B/C, bramki, prawdopodobieństwa |
| `POMIAR-L1-ABANDON-2026-10-28.md` | pełny pomiar replayu L1, walidacja, rekomendacja |
| `POMIAR-SMOKE-V11-2026-10-28.md` | slot A: smoke v11 vs c45, szum ±9 pkt, submit `57737623`, tabela per-gra |
| `KOREKTA-OPINII-2026-10-27.md` | korekta błędnego opisu pakietu, 41,8, starego LB |
| `CROSS-SESSION-SYNC-2026-10-25.md` | synchronizacja sesji, retrakcje, stan slotów |
| `CROSS-SESSION-VERDICTS-2026-10-24.md` | co potwierdzone/obalone/przyjęte 24.10 |
| `STATUS.md` | handoff infrastruktury, CI, Kaggle |
| `STRATEGY.md` | wczesna strategia LLM-agent (5–15 pkt) |
| `README.md` | architektura Ducka + 7 słabych punktów + RHAE |
| `FINDINGS-2026-10-13.md` | duży dziennik ustaleń 13–15.10 |
| `MY-WORK-STATUS.md` | status pracy drugiej gałęzi, usunięte błędy |
| `PRIOR_WORK.md` | historia repo `riemann`, twarde wyniki negatywne |
| `INTEGRATION-V69-DUCK.md` | plan integracji v6.9 z Duckiem (pisany na ślepo; korekta na górze) |
| `CROSS-SESSION-DELTA-v6.2.md` | delta no-op + lessons-between-games |
| `COMPARISON-V7_0-2026-10-14.md` | porównanie v6.8/v6.9 vs v7.0 |
| `MEASUREMENT-PLAN-2026-10.md` | plan pomiaru 17–20.10 |
| `CHAT-LOG-2026-10-14.md` | długi log czatu |

### 16.2. Pakiety

| Katalog | Rola |
|---|---|
| `duck-v11-c45/` | **kandydat nr 1 / slot A** (33 komórki, 5 patchy, `PLAN_COMMIT="0"`) |
| `duck-v12-plan/` | **slot B** (`PLAN_COMMIT="1"`, cap45/r1) |
| `duck-v11-c45-cap90/` | **slot C / najlepszy env-only** (90k/r1/md0) |
| `duck-v11-c45-abandon/` | **negatywna kontrola** (60k/r0/md0) — nie wysyłać |
| `duck-v11-c45-nocap/` | fallback (cap=0) |
| `duck-v11/` | archiwum v11-Smak — nie kandydat bez naprawy patcha |
| `baseline/` | baseline, check_submission |
| `llm-agent/` | nasz agent v6.x (108/108 testów) |
| `rust/` | crate Rust (36/36 testów) |
| `games/` | 25 gier demo, kod źródłowy, katalog celów |
| `analysis/` | replay, sweep, statystyki transkryptów |
| `kaggle/ops/results/` | wyniki runów (r019, r033, r085, …) |

### 16.3. Kluczowe narzędzia

| Plik | Rola |
|---|---|
| `duck-v11-c45/tools/verify_v11.py` | pełny łańcuch patchy + testy logiki; LF fix |
| `duck-v11-c45/tools/build_env_variant.py` | buduje warianty env-only |
| `duck-v11-c45/tools/verify_env_variant.py` | weryfikuje warianty + stan maszyny budżetu |
| `analysis/replay_level_budget.py` | replay `LevelBudget` na r085 |
| `analysis/sweep2.py` | sweep gier/parametrów |
| `analysis/transcript_stats.py` | statystyki transkryptów, multiprocessing |

---

## 17. Otwarte pytania — co naprawdę może zmienić plan

1. **Log reruna c45 #57629847** — czy to na pewno głód 120 vs MAXREQ 10? Bez niego slot A jest testem hipotezy, nie pewnika.
2. **Skład rosteru prywatnego** — czy to 25 gier publicznych, czy inne mechaniki? Od tego zależy, czy playbook/triage budżetowy jest coś wart.
3. **Strona korzyści abandon w kolejce 110 gier** — czy wcześniejsze zwolnienie slotu daje więcej poziomów, niż zabiera? Smoke tego nie rozstrzyga.
4. **Wynik `PLAN_COMMIT="1"`** — czy `commit(plan)` realnie ratuje poziomy, czy tylko dodaje koszt?
5. **Wynik `cap90`** — czy usunięcie 9 resetów przekłada się na punkty, czy tylko na niższy koszt?
6. **KYC przy wypłacie** — czy dyskwalifikuje? Write-up/rozmowa na Kaggle nie występują, ale KYC to osobne pytanie.
7. **Precompute / cache pre-solve** — czy regulamin pozwala wnieść jako artefakt? Potwierdzić na forum.
8. **Czy finalista publiczny do 31.10–1.11** — potwierdzić w rules; jeśli tak, to twardy deadline.
9. **Czy 9 h wystarczy** na pełny przebieg 110 gier z plan-commit? Bez pomiaru czasu passu nie ma planu dni 13–22.

---

## 18. Uczciwa ocena szans

| Scenariusz | Wynik | Prawdopodobieństwo (subiektywne) |
|---|---|---|
| A działa, B/C dokładają plan + cap90 | 28–33 | **~35%** |
| A działa, ale plan/cap90 nie wnoszą | 26–29 | **~40%** |
| A = 0,00 (concurrency to nie przyczyna) | 0–26 | **~20%** |
| Stack + odkrycie mechaniki (commit + cap90) skacze poziomy | **50+** | **~5%** |

**Wniosek:** plan maksymalizuje szansę, ale 50+ w 6 dni jest mało prawdopodobne bez skoku w liczbie rozwiązywanych poziomów. Najbardziej wartościowe w tej chwili: **nie stracić kolejnych okien** i **mieć finalistę publicznego do 1.11**.

---

## 19. Jak zacząć nową sesję

Wklej:

```
Przeczytaj arc-agi-3/KOMPENDIUM-ARC-AGI-3-2026-10-28.md,
PLAN-50PLUS-2026-10-27.md i POMIAR-L1-ABANDON-2026-10-28.md.
Pracujemy nad ARC-AGI-3 na Kaggle (deadline 2 XI 2026, konto petersharps).
Obowiązuje: 1 submit/dzień, GO usera przed push/submit, nie ruszać plików
starszych niż 2 dni, nie kopiować kodu Ducka, finalista publiczny do 1.11.
Aktualny krok: slot A = duck-v11-c45 (PLAN_COMMIT="0", cap45/r1) — czeka na GO.
```

---

## 20. Jedno zdanie podsumowania

**Mamy wiarygodny, offline zweryfikowany kandydat (`duck-v11-c45`), tanią subtrakcję env-only (`cap90`) i uczciwy pomiar, który obala „+5–7 z abandonu”; brakuje nie pomysłów, a okien submisji i jednego prawdziwego wyniku, który powie, czy fix concurrency w ogóle punktuje.**
