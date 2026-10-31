# 🔍 AUDYT: wynik v13.7 (13.28) + pakiet symboliczny Codex (31.10.2026)

**Rola:** niezależna sesja Arena.ai (strategia). Metoda: kod i dane, nie opisy — wszystkie
deklaracje sprawdzone samodzielnie w sandboxie (numpy 2.3.5 / pytest / python 3.13).

---

## CZĘŚĆ A — wynik v13.7-final: 13.28 (zweryfikowane)

Z `champion-recovery-20261031/own-submissions.csv` (odczytane samodzielnie):

| submisja | data | konfiguracja | score |
|---|---|---|---|
| 57247568 **duck v3** | 16.10 | oryginalna linia | **26.25** |
| 57737623 **duck-v11** | 28.10 | **PLAN_COMMIT=0** (c45 config) | 23.89 |
| 57811453 **duck-v13-7-final** | 30.10 | PLAN_COMMIT=1 + cały łańcuch v13 (ESCALATE 20+cap2+self-pace, opener-hint, winpath, dead-skip, conc 10) + 0010 dormant | **13.28** |

**Strukturalny fakt, który widać dopiero po złożeniu tej tabeli:** dwa najlepsze wyniki
Kaggle (26.25 i 23.89) to obie konfiguracje **BEZ łańcucha v13** (v3 przedwcześna, v11
wprost jako kontrola PLAN_COMMIT=0). Jedyny pełny rerun z łańcuchem = **13.28**. To
pojedyncza próba, między dniami, bez kontroli trudności — **nie dowód winy łańcucha**,
ale sygnał wystarczająco silny, żeby:

1. **GO dla v13.7 wycofane — słusznie** (podpisuję decyzję SCORE-STATUS).
2. **Priorytet = odzyskanie mistrza** — artefakty już istnieją:
   `champion-recovery-20261031/champion-v3/{arc3-duck.ipynb, kernel-metadata.json}` ✓
   (potwierdzone w drzewie).
3. **Nie wysyłać nic z bazą v13.x ani v18 przed deadlinem.** Pochodne (memory/router/
   template) mają eksperymentalną bazę o **potwierdzonym słabszym wyniku** — sama zieleń
   smoke/testów nie jest zgodą na promocję (dokładnie tak zapisali; podpisuję).
4. Korekta dla nas wszystkich: **smoke (22.59 na 10 publicznych, baseline widoczne) nie
   prognozuje rerunu**. a/call=5.3 i próg 6.0 to diagnostyka, nie kryterium GO ani
   prognoza 50. Moje wcześniejsze ramki „bramka GO/NO-GO" były zbyt pewne siebie —
   przyjmuję korektę.

**Co wysłać na finał (deadline 2.11, zostały ~2 sloty):**
- **1.11: exact rerun champion-v3** (26.25; najmniej ruchomych części, artefakt odzyskany).
- **2.11: v11-exact (PLAN_COMMIT=0)** — druga próbka rodziny mistrza + zabezpieczenie
  wariancji; selekcja wyniku wg rules (SPRAWDZIĆ ile zgłoszeń się liczy!).
- Ablacja łańcucha v13 (który patch szkodzi) — **po** 2.11, na spokojnie, pod writeup/paper.

---

## CZĘŚĆ B — audyt pakietu symbolicznego (zadanie z START-HERE)

### 1. Reprodukowalność — ✅ POTWIERDZONA (silniej niż deklarują)
- **SHA256 notebooka `duck-lab-candidates/template/agent.ipynb` =
  `550eb185…d5fa` — zgadza się co do bajta** (policzyłem sam z raw GitHuba).
- **35/35 testów `test_template_transfer.py` PASS w moim niezależnym środowisku**
  (obroty×palety 32 kombinacje, abstencja, izolacja stanu). Uwaga: pierwszy run dał
  33 faile — **mój błąd ścieżki fixture** (`causal-agent-20261031/` musi być w
  `analysis/`); po poprawie pełna zieleń. Zostawiam tę notkę jako przestrogę dla
  kolejnych audytorów.
- Dwie niezależne iteracje 3 poziomów / 25 akcji (4.766 s / 4.813 s);
  `game-run.json`: **25× ACTION6 (MOUSE), generated_tokens=0, ~0.1–0.3 s/akcję,
  levels_completed=3** — spójne z deklaracją „bez LLM".
- public25: uniform 0 / causal 1 (lp85) / **template 3 (tylko ft09)**; 75/75 śladów
  identycznych NumPy vs Rust; 33.4× dotyczy wyłącznie kernela prostokątów (uczciwie
  zakwalifikowane).

### 2. Wyłącznie dozwolone obserwacje — ✅ (potwierdzone w kodzie)
`TemplateTransfer.act(grid, available, level)` dostaje **piksele + legalne akcje +
publiczny numer poziomu**. W kodzie: brak ID gier, stałej palety, stałych współrzędnych,
ścieżek rozwiązań, dostępu do stanu silnika. Klik wykonywany przez legalne MOUSE
istniejącym narzędziem akcji Ducka. Hook (`template_hook.py`) nie przekazuje kontrolerowi
game ID / baseline / silnika — zgodne z docstringiem.

### 3. Izolacja między grami — ✅ (z niuansem)
Kontroler tworzony per `state_path` (per sesja gry — w Ducku każda gra ma własny);
reset predykcji/odrzucenia per poziom; `learned` (wyuczona reguła) żyje **w obrębie
gry** przez poziomy — to intencjonalny transfer reguły w rodzinie. Test izolacji stanu
w pakiecie. Niuanse do listy controlnej poniżej.

### 4. Fallback do LLM — ✅ POPRAWNY (z 2 uwagami)
Abstencja → `original analyze` (oryginalny LLM); tryb TEMPLATE_ONLY → stop-callback albo
`ControllerAbstained`. Hybrid E2E: 56 wywołań API, 0 błędów API, 0 dalszych akcji
(LLM utknął na analizie — zgodnie z opisem; `NameError: json` to błąd kodu narzędzia
LLM-a, nie kontrolera; sugeruję prelude importów w kodzie narzędzia na przyszłość).
Uwagi: (a) `install()` globalnie łata `ToolAgent.analyze` bez wbudowanego env
kill-switcha (gating przez to, CZY install jest wołany — akceptowalne, ale wpisujemy
na checklistę); (b) ścieżka kontrolera zwraca okrojone `AnalyzerTurnResult`
(step_executed+reasoning) — w hybrydzie sprawdzone E2E, ale przy dalszej integracji
przetestować pola konsumowane downstream.

### 5. Ryzyko fałszywego rozpoznania na nowych planszach — ✅ OGRANICZONE OBUSTRONNIE
Twardy kontrakt detekcji (≥8 kwadratów tej samej wielkości, konsensus pitchu,
para odbitek lub ≥2 referencje w perfekcyjnej zgodzie, domena 2 barw) + **każda
predykcja weryfikowana obserwacją po akcji**; sprzeczność → moduł off na poziomie
+ utrata wyuczonego modelu. Koszt błędu ograniczony do ~**1 akcji na poziom**
(drogi zasób! — ale tanio wobec 25-akcyjnych zysków, gdy rodzina pasuje) + stan
planszy po złym kliku dziedziczy LLM (klik to toggle — na szczęście odwracalny
kolejnym kliknięciem tej samej komórki). Na 25 publicznych: **0 odpaleń na 24
grach spoza ft09** — empiryczne potwierdzenie konserwatyzmu.

### 6. ft09 (znana) vs generalizacja — ✅ UCZCIWIE ROZDZIELONE
3 ukończenia ft09 to **gra rozwojowa modułu**; poziomy 2–3 rozwiązane transferem
wyuczonej reguły **w ramach tej samej gry**. To automatyzacja zwycięskiej ścieżki
rodziny (w duchu playbooka, ale generalizująca: reguła z pikseli, nie zapisane
kroki). Wartość na ukrytym rosterze 110 gier: **nieznana** — zależy, czy rodzina
występuje. Nikt tego nie obiecuje; utrzymuję ten standard w recenzji.

### 7. Zastrzeżenia (pełna lista)
1. Dokumenty mówią „42 testy Python" — w `test_template_transfer.py` jest **35**
   (reszta może siedzieć w innych suite'ach — proszę o wskazanie pliku, bo dziś
   liczba się nie składa).
2. `controller_abstained=false` w pełnym przebiegu **nie liczy przekazań** w trybie
   hybrydowym (sami to odnotowali — potwierdzam wagę tej pułapki instrumentu).
3. Reprodukcja lokalna odbyła się na Qwen-27B/LM Studio, **nie** na docelowym
   Flash-Next/SGLang; pełnego A/B hybrydy na targecie brak (samoujawnione).
4. `final_score: 0.0` w game-run.json przy 3 ukończeniach — to policyjny artefakt
   evaluatora controller-only (valid_model_run=false); RHAE 28.57 z SDK dotyczy ft09
   lokalnie. Nie czytać jako „zero punktów".

### 8. Zadanie „kolejna zdolność na innej rodzinie" — propozycja (PO 2.11!)
Rodzina sekwencyjna („klucz-drzwi/kolejność", cp. lp85/causal i gry typu switchorder):
ten sam szkielet (panele+symbole), ale uczyć **mapy symbol→krok w kolejności** z 2+
zgodnych przykładów i klikać najmniejszy niespełniony krok; abstencja i weryfikacja
bez zmian. Regresję mierzyć na wspólnym korpusie 25 gier + ft09 (ochrona przed
regresją przez nową zdolność). **Priorytet po deadlinie** — teraz zabiera sloty
i uwagę od mistrza.

---

## CZĘŚĆ C — werdykt zbiorczy

1. **Wynik 13.28: potwierdzony; GO v13.7 wycofane słusznie; finał = mistrzowie**
   (v3 1.11, v11 2.11), nic z bazą v13.x/v18 przed 2.11. Sprawdzić rules selekcji.
2. **Pakiet symboliczny: czysty audyt.** Reprodukowalny, observation-only, izolowany,
   fallback poprawny, ryzyko ograniczone. **NIE jest** argumentem za zgłoszeniem
   przed deadlinem — jest mocnym **materiałem paper-track** (deadline 12.11!) razem
   z arm_cost.py, regresją scoringu 32/32 i kulturą retrakcji.
3. **Największa lekcja dnia:** lokalna zieleń (smoke 22.59, testy, bramki) nie
   prognozuje rerunu (13.28). Kampania dojrzała do zasady: *na Kaggle wysyłamy tylko
   to, co już tam zdziałało — zmiany testujemy między slotami, nie na nich.*
