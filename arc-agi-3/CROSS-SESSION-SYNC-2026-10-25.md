# SYNCHRONIZACJA SESJI — 25.10.2026, ~15:00 UTC (Arena)
Weryfikacja pracy gałęzi c87f7a48/a450b00f (Pokemon), pakietu v10 z folderu e499c604 oraz liczb DeepSeeka — wszystko na surowych danych, bez GPU.

## 1. Spór a/call — ZAMKNIĘTY (trzy sesje zbiegają się)
Niezależne przeliczenie Arena z `r019-benchmark.json` (semantyka: wywołanie akcyjne = wpis historii z generated_tokens>0):
- akcje **2065**, wywołania akcyjne **474**, a/call ważone **4.357**, średnia z gier **5.204**,
- tok/akcje **841.3**, tok/wywołanie **3665.1**, pula **173 726 tok/grę**, score 27.21,
- per gra (a/call): tn36 4.39, m0r0 5.00, cn04 3.46, dc22 4.68, ka59 5.29, sc25 3.85, s5i5 4.83, ls20 13.89, su15 1.85, g50t 4.80 — 1:1 z tabelą c87f7a48.
- **1417 linii requests.jsonl potwierdzone** (wc -l), ale to wszystkie żądania (z analizatorem); 1.13 OBALONE definitywnie.
- Korekta wstawiona do LEPSZA-DROGA.md §2 (baner).

## 2. „21/32 poziomów na capie 115" (DeepSeek) — NIE ODTWARZA SIĘ
Moje przeliczenie: **32/32 ukończonych poziomów** miało <=115 akcji (cap per-level score nigdy nie uciął ukończonego poziomu; nieukończone poziomy mają 0 w actions_per_level). Efekt „wyczerpanej efektywności" jest realny (29.6% budżetu głębokości), ale konkretna liczba 21/32 pochodzi z innej definicji.

## 3. Znalezisko e499c604 (v9/v7 martwe przed serwerem) — ~~POTWIERDZONE~~ **OBALONE 27.10 (zob. §9): patch bajt-identyczny z c45, który przeszedł; IPython %%writefile dopisuje newline** (kontekst historyczny poniżej)
- Reprodukcja Arena: kom.5 v9 (498 799 znaków) bez końcowego newline -> `git apply --check` na bundlu r033:
  `error: corrupt patch at line 10087`; kom.10 ma `check=True` -> CalledProcessError przed startem serwera. **v9-as-shipped = DEAD.**
- KOREKTA ich §1: patch NIE jest ucięty mid-hunk. Z dodanym `\n` przechodzi `git apply --check --include='ARC3-Inference/*'` CZYSTO
  (16 plików, kompletne hunks; pełny patch da-fr = 660 020 B / 24 pliki — v9 embarca podzbiór 16/24, spójny wewnętrznie).
  Czyli: sufity długości komórki mogły ściąć OGON (pliki viewer/* itd.), ale ostatni hunk segmentation.py jest kompletny.
  Praktycznie i tak: **fix v10 (odbudowa z drzewa da-fr, chunki <400k, sha256 w runtime) jest rozwiązaniem właściwym.**
- verify_offline.py fałszywy pass: dodawał `\n` przy ekstrakcji (linia 218) — maskował dokładnie ten błąd. Odnotowane.

## 4. Pakiet v10 (e499c604) — ocena Arena
- `verify.py`: ALL PASS (profil, chunky, reassembly bajt-w-bajt, sha256, brak dotarcia do sufitu 498 799, metadata id/title/code_file).
- `test_plan_commit.py`: **9/12 offline**; 3 błędy = importy runtime-stacku (`requests`, agent deps) — nie logika; pełny bieg w smoke kernela.
- SHA256SUMS „FAILED" = artefakt CRLF z uploadu GitHub web; po `tr -d '\r'` hash kernel-metadata-v10.json zgadza się 1:1 (788165fc...). Zawartość nietknięta.
- `arc_agi_3_wheels` jedzie na montowaniu kompetycji (jak w c45, który przeżył smoke) — brak metadata-mismatch.
- Higiena: `arc-agi-3/new/tools/__pycache__/*.pyc` usunięte z gita (sygnalizowane przez c87f7a48).

## 5. Odpowiedź na pytanie (B) c87f7a48 — dźwignia #4 ŻYJE
Walidator `PERSISTENT_FUNCTIONS_SCOPE` w patched drzewie (2 wystąpienia w c45 notebook) przyjmuje `turn|levelup|game`
(accessTokenScope check zweryfikowany przez nas 24.10 i przez verify_offline: „PERSISTENT_FUNCTIONS_SCOPE accepts 'game'").
Run z SCOPE='game' jest akceptowany — dźwignię #4 wykreślić NIE trzeba.

## 6. Przyjęte od c87f7a48 (bez zmian)
- §1bis: pula ~175k tok/grę = własność linii SZYBKIEJ (603 vs 29.2 tok/s = 20.7x) — nie traktować jako stałej konkursowej.
- Bramka profilu deep: GO = liczba poziomów, nie a/call (odwrotna korelacja a/call<->score w r019).
- (A) wykonane powyżej; (B) wykonane wcześniej przez nas (pkt 5).

## Stan lotu (15:00 UTC)
- c45 #57629847: rerun trwa, LB ~21:30-22:00 UTC (PENDING; status w r081+).
- v9: push 12:44, smoke wg statystyki powinien być MARTWY (cell 10) — potwierdzenie runtime: r081 kernel_status.
- Kwota: 0 submitów do północy UTC. ZASADA: zero push/submit bez GO usera.

## 7. WYNIK c45: 0.00 — diagnoza (15:05 UTC)
- c45 #57629847 COMPLETE 0.00; smoke zdrowy; parquet = stub (r019: identyczny 2648 B, 27.21) -> scoring z reruna.
- Podejrzany nr 1: kom. 21 TRUE_SUBMISSION concurrency=120 przy serwerze MAXREQ=10 (głód slotów / storm połączeń /
  eksmisja prefiksów -> zero poziomów). r019 (default 16) = 27.21; Franzen 38.85 = własna konfiguracja.
- v10 dziedziczy 120 -> PRZED jakimkolwiek runem: `bm.solver.concurrency = 10` (albo <= ARC3_MAX_ACTIVE_STREAMS).
- Szczegóły + alternatywy: duck-v9/DECYZJA-SLOTU-26-10.md (sekcja DIAGNOZA). Log reruna = tylko przez przeglądarkę usera.

## 8. PORÓWNANIE: DZISIEJSZA PRACA ARENY vs V11 CODEX-a (~17:30 UTC; ODTWORZONE) — ⚠️ certyfikacja z tej sekcji OBALONA 27.10 (zob. §9: patch pada na Makefile/README na czystym drzewie; v11-Smak = archiwum)
Context: Codex przeczytał nasze notatki (DECYZJA-SLOTU-26-10.md + ta synchronizacja) i zbudował v11 = v10 + fix concurrency.
v11 wgrana przez usera (ac096de, arc3-duck-v11.zip), certyfikowana offline przez Arenę -> arc-agi-3/duck-v11/ (komit 0e485c6).

### Certyfikacja v11 (bez GPU)
- [x] parse-repair: zip miał CRLF wewnątrz stringów JSON -> strict parse FAIL (u nich OK — test na lokalnej kopii LF);
      naprawa: strict=False -> kanoniczny re-dump -> strict PASS (semantyka bez zmian)
- [x] 31 komórek; patch w 2 chunkach (380 000 + 279 896 zn.) < sufit 498 799 (lekcja v9)
- [x] sklejka cat-style part-00+part-01: sha256 54768e2f94e99b33... = zapisany w ARC3_VARIANT (zgodność 1:1)
- [x] git apply --check PASS na czystym bundlu r033 (pełny patch 659 896 B / 24 pliki da-fr)
- [x] kom. 21 (TRUE_SUBMISSION): bm.solver.concurrency = 10 ORAZ os.environ["ARC3_MAX_ACTIVE_STREAMS"]="10"
      (+ komentarz "match backend MAXREQ=10; avoid 120-way fanout") — fix OBU dźwigni ✓; runtime 532 min/grę
- [x] metadata: id=title=arc3-duck-v11-plan-safe; źródła = zestaw c45-proven (dfranzen x4 + competition + docker pin 57e612b4 + RTX6000); CRLF poprawione
- [x] zachowane z v10: commit(plan) (weryfikacja per krok), eskalacja 60 akcji, ARC3_SMOKE_OK gate, sonda rosteru; PROFILE="plan" (opcje: c45|deep|wide|plan|plan-esc)

### Head-to-head
- Codex: konwersja naszej diagnozy na kompletnego kandydata slotu; uczciwy README (bez obietnic 50+, jawnie: commit(plan) niezmiierzony, 0.00 niepotwierdzone logiem, nic nie wysłał); strategia zbieżna (najpierw fix + pełny bieg, potem strojenie; mierzyć POZIOMY nie a/call; cel >=53 z buforem na ruchomy próg top-5 = 50.37; 6. miejsce 47.19 — zgodne z naszym snapshotem LB).
- Arena (poza diagnozą, którą Codex zaadoptował): łańcuch dowodów 0.00 (smoke 26.78/32 poziomy zdrowy -> parquet 2648 B = STUB identyczny z r019=27.21 -> scoring z RERUNA -> głód 120 vs MAXREQ=10 -> 0 poziomów); przeliczenie surowe 474/4.357/5.204/841.3/173 726 (koniec sporu 1.13); 32/32<=115 (korekta "21/32"); v9-dead potwierdzony z korektą mechanizmu (nie mid-hunk; 16/24 plików spójnych; winny newline+check=True); infra ops (kernel_output_pick 68 KB zamiast 598 MB, .gitignore outputów, bezpiecznik GO, r083-r085).

### Trzy korekty do treści Codex-a
1. "Pamięć między passami obiecująca" = nasz MARTWY END: prawdziwy scorecard nie powtarza game_id (n_passes=1) -> 0 pkt; pamięć między poziomami w grze już działa (PERSISTENT_FUNCTIONS_SCOPE='game', walidator zweryfikowany). Wracamy tylko przy powtórzeniach z sondy rosteru.
2. "47 nie wystarczy" — racja; precyzja: 5. miejsce 50.37, nagrody = top-5; cel >=53 to zdrowy bufor (ruchomy próg + dryf prywatnej połowy).
3. "Wewnętrzny test nie jest wynikiem LB" — dokładnie; nasza kalibracja: smoke->LB ~ -2.8.

### WARIANTY SLOTU 26.10 (CZEKAJĄ NA GO USERA — zasada 25.10; nic nie wysyłać)
- Wariant A (porządek naukowy): v11 PROFILE="c45" -> czysty test fixa concurrency; commit(plan) mierzymy 27.10.
- Wariant B (as-shipped, wyższy sufit): v11 PROFILE="plan" -> fix + pierwszy pomiar commit(plan) razem (po 0.00 każdy niezerowy wynik = postęp; atrybucja rozmyta).
- Rekomendacja Areny: z potwierdzonym logiem reruna (przeglądarka usera: submissions -> #57629847 -> log; API tego nie serwuje) -> B; bez loga -> A.
- Stan kwoty: 0 submitów do północy UTC 25.10; slot 26.10 wolny; best nadal v3 = 26.25.

## 9. KOREKTA WIELKA (27.10 ~19:55) — zwiad gałęzi a450/c87: dwie retrakcje Areny + przyjęcie v11-ex-c45
Pełne treści: duck-v11-c45/OCENA-ARENA-V11-C45.md. W skrócie:
1. Certyfikat v11-Smak OBALONY na czystym drzewie (Makefile:40, README.md:1; moja wina: brudne drzewo pre-recycling).
   v11-Smak = archiwum mechanizmów, NIE kandydat slotu bez naprawy patcha.
2. "v9 martwy przed serwerem" OBALONE (patch bajt-identyczny c45≡v9, c45 przeszedł; IPython %%writefile dopisuje \n
   — replikacja c87 + log produkcyjny). Status kernela v9 pozostaje nieściągnięty (op kernel_status padl) — ale to
   już nie blokuje niczego.
3. PRZYJĘTO pakiet v11-ex-c45 (Pokemon 6c3e958) -> arc-agi-3/duck-v11-c45/: moja weryfikacja na czystym bundlu:
   5/5 patch chain + kompilacja + 12 checków + kill-switch PLAN_COMMIT. KANDYDAT NR 1 na slot.
4. Stan slotów: 26.10 i 27.10 NIEZUŻYTE (ostatni submit = c45 #57629847 25.10, 0.00). Pozostaje ~7 okien
   (27.10 do 23:59 UTC + 28..31 + 1..2.11). Uwaga c87: finalista (publiczny notebook) do 31.10–1.11 inaczej nagroda
   przepada — do potwierdzenia w rules przez usera.
5. Rekomendacja: slot A = v11-c45 PLAN_COMMIT="0" (czysty test fixa concurrency), potem slot B = "1" (commit()).
   Wszystko CZEKA NA GO.

## 10. SPRZĄTANIE DRZEWA (27.10 ~20:10)
Usunięte z tipa (historia zachowana): outputy r019/r072/r076 (GB!; wnioski w §1/§7 + r085 output-pick), new/ (duplikat v9),
zepsuty zip v11-Smak, kernel v9 (notebook/metadata/src), v11-Smak (notebook/metadata), e499/v10 (banerowana notka arch. zostaje).
ŻYWE: duck-v11-c45 (kandydat), duck-c45 (baza), ops (r086 read-only), r033-bundle, dokumenty decyzyjne z banerami.
Dla sesji czytających repo: KANDYDAT = arc-agi-3/duck-v11-c45 (slot A: PLAN_COMMIT=0 -> slot B: =1). Wysyłka = PO GO usera.

## 11. NOC 28/29.10: ANALIZA 23.89 + LOKALNY SILNIK + v12 (Arena)
- v11 slot A #57737623 = 23.89 (fix concurrency DZIALA — linia znow punktuje; best wciaz v3 26.25).
- REGRESJA SMOKE v11: 18.55 vs c45 26.78 (per-gra: cn04 -66.7, m0r0 -34.8, g50t -21.4; wiecej tokenow, mniej poziomow
  => side-effect patch 0005/ONLY_RESET w rekonstrukcji). Wniosek: rekonstrukcje bazy NIOSA ryzyko; minimal-delta wygrywa.
- LB vs smoke niespójne kierunkowo (v3 -2.8 vs v11 +5.3) => kalibracja slaba, nie przegrywac slotow na "strojenie smoke".
- LOKALNY SILNIK (arcengine 0.9.3 + arc-agi 0.9.9 z PyPI na py3.11 przez sys.path + kody 25 gier w repo): dziala (local-engine/).
  official_110() = klon 110 gier = pelna symulacja reruna lokalnie. Null-vuln z papera AERA: reprodukowana (camera
  TypeError), na 0.9.9 nie daje WIN — i TAK NIE UYWAMY (etyka/ryzyko DQ).
- v12 WYPUSZCZONA: duck-v12/ = c45 bajt + 2 linie fix (jedyne diff). Do decyzji GO: push+smoke (ranek 29.10).
- Droga do 50+ (szczerze): (1) potwierdzic strukture 110-klonow (log reruna w przegladarce!), (2) playbook miedzy grami
  (replay sekwencji per hash-startu klatki), (3) otwieracze z zrodel (parser placements), (4) ew. 27B (v13-27b innej
  sesji w smoke), (5) deep/commit na c45. Bez (1)-(3) sufit linii ~30-40; z (2)+(3) realnie 45-55. Nic nie wysylane bez GO.

## 12. WYNIKI 28-29.10 i REWIZJA OPCJI GO (Arena, 29.10 ~17:00 UTC)
Tabela slotow: v3=26.25 (best) | c45=0.00 (glod 120) | v11 slotA=23.89 (fix conc dziala; regresja patchy rekonstrukcji:
smoke 18.55 vs c45 26.78) | **slot B = stock 27B-FP8 (conc28, no cap) = 1.18** | **v14-27b-long smoke = 0.27** (2 poziomy/10 gier).
- Wniosek 1: **linia 27B w konfiguracji v13/v14 MARTWA** (duzo wolniejsza: ~83k tok/1.5h vs 8B ~150k/0.8h; zero poziomow).
  Model-size lever bez kopi konfiguracji Tufy M1 = spalenie slotu. Wstrzymac 27B do replikacji konfiguracji 1:1 (kosztowne, niski EV).
- Wniosek 2: minimal-delta wygrala z wszelkimi rekonstrukcjami: c45 bajt + 1 fix (v12) = jedyny kandydat z pewna baza (26.78).
- Wniosek 3: dwa nieudane eksperymenty z rzedu (0.00, 1.18) => dalsze sloty tylko dla variantow o dowiedzonym smoke>=26.
OPCJE GO (rewizja):
- GO#1 (aktualne, wzmocnione): v12 push+smoke -> submit slotu 30.10 (29.10 zajety przez slot B 1.18). Oczekiwany LB ~27-31.
- GO#2 (aktualne): log reruna z przegladarki — teraz podwojnie: (a) struktura 110-klonow -> playbook, (b) diagnoza 1.18 (conc28 vs MAXREQ 27B?).
- GO#3 (zmienione): nie "koordynacja 27B", tylko **WSTRZYMANIE 27B** + propozycja podzialu: druga sesja = output-pick/logi i ew. replikacja
  konfiguracji M1; Arena = v12 + playbook (110 klonow) + otwieracze z zrodel + Rust precompute.
Pozostale sloty: 30.10, 31.10, 1.11, 2.11 (4). GPU: reset sobota 00:00 UTC.

## 13. V13-MEGA ZWERYFIKOWANA I PRZYJETA (30.10 ~07:20 UTC) — szczegoly: duck-v13-mega/OCENA-ARENA-V13.md
- Pokemon 3782f8c: 6/6 patchy na czystym r033, testy 12/12+6/6 (po doinstalowaniu PIL/arcengine w piaskownicy),
  standalone winpath == spatchowany, playbook 14/14 POTWIERDZONY przez Arene na PRAWDZIWYM silniku (replay_pb).
- ROSTER: potwierdzony w kodzie Tufy: 110 = round-robin klonow 25 gier (n_passes=1, ~4.4x/gra) — nie 20 passow.
- REWIZJA GO: slot 30.10 = v13-MEGA (sufit 45-55; kill-switche), fallback 31.10 = v12 (c45+fix). PC sweep 600s przed submitem.
- Pakiet skopiowany do naszego repo: arc-agi-3/duck-v13-mega/ + pc-sweep-pack/ (RUN-NA-PC.md dla 5950X).

## 14. V13.1 CERTYFIKOWANA — ZASTĘPUJE v13 JAKO GO#1 (30.10 ~07:35 UTC) — szczegoly: duck-v13-1/OCENA-ARENA-V13-1.md
- Pokemon cbefdd4: diff chirurgiczny (kom. 2+11 notebooka; playbook identyczny -> 14/14 na silniku dalej wazne);
  base_key = wspolny magazyn winpath dla ~4.4 klonow/gra; dead-skip na licznikach magazynu (pass_index martwy przy
  n_passes=1 — nasza korekta przyjeta); 6/6 patchy czysty r033; testy 12/12 + 7/7 (u verify padało na braku
  arcengine/PIL w srodowisku — reczny bieg zielony); standalone==spatchowany.
- Slot 30.10: **v13.1** (duck-v13-1); fallback 31.10: v12. Wysylka PO GO.

## 15. OPINIE POZOSTAŁYCH GAŁĘZI O V13/V13.1 + RETRAKCJA ARENY (30.10 ~07:45 UTC)
Źródła: c87f7a48 (2561cfd, a5432da, 2d8645c), Gemma c4eeb067 (cded50d0, cytowana w 2d8645c), 7911f950 (3269393, 53eab27, 0050174).

### RETRAKCJA (3. w projekcie, po v11-Smak i v9-dead): „roster = 110 klonów 25 gier POTWIERDZONY W KODZIE" — FAŁSZYWE
- Weryfikacja osobiście w repo: `competition_arcade.py` L1-8: „**Local** competition-mode ARC-AGI Arcade simulator (R11.13).
  The **real Kaggle submission path talks to a gateway-backed Arcade** with competition constraints: one scorecard,
  **hidden baselines**, and **no repeated game IDs within that scorecard**."
- Czyli `official_110()` = KSZTAŁT submisji na symulatorze LOKALNYM (przed-submisyjne repro failów), NIE roster punktowany.
- Wnioski: (a) playbook EV ≈ 0 na ukrytym rosterze (Gemma: 72.61 TYLKO gdyby roster=publiczne-25; 7911: +2.3 na naszych 10 smoke;
  c87/Gemma: ~+2.9) — „sufit 45-55" RETRAKTOWANY; (b) replay między wpisami / dead-skip między wpisami = martwe
  (brak powtórzeń w scorecardzie); (c) lekcja c87, trzeci raz: czytać DOCSTRING, nie nazwę funkcji.
- Zostaje formalna szczelina („no repeated IDs" ≠ wprost „gry mechanicznie różne"), ale 3 niezależne pomiary zewnętrzne
  (source-introspection 0.20 „Game sources don't exist in the rerun"; held-out 0/113 vs 7/70; „110 hidden games" przez gateway:8001).
  **ROZSTRZYGNIĘCIE ZA DARMO**: probe z outputu dzisiejszego runa (roster_probe.jsonl) albo log reruna #57737623 z przeglądarki.

### Opinie — konwergencja 3-4 sesji (PRAWDA)
- „Dwie z trzech dźwigni 0006 martwe w submisji": Gemma + c87 niezależnie ✅ (n_passes=1 + brak powtórzeń; dead-skip wymagał passa ≥4).
- „23.89 = draw, nie regresja": 7911 (sd=2.47; -1.3 sd) + c87 (σ=3.93) ✅ → metoda: TA SAMA konfiguracja 2× z rzędu.
- „Głębokość/pokrycie = ~96% brakujących punktów; efektywność 86-90%; sufit przy tym budżecie 18.7-31.9": Gemma+7911+c87 ✅.
- „50+ = PRZEPUSTOWOŚĆ (~300 akcji/grę z ~213), nie mądrzejszy model (27B: 0.27 przy 47 s/akcję — za wolny)": 3 niezależne modele ✅.
- „Cap per-poziom = 1.15, nie 1.0": c87 ✅ (metodologia arcprize + taaf/game.py min(115,…) + regresja 32/32 Gemmy); i tak prawie
  zawsze wiąże cap UKOŃCZENIA — szybszość od człowieka płaci tylko w wąskiej klasie (+3.0 pkt).
- „Playbook 14/14": 3 niezależne reprodukcje (Arena na silniku; Gemma 184/184 hashy + seedy 1/2/7/42; 7911 krzyżowo 2 ścieżki).

### Korekty przyjęte
- **7911: commit(plan) tylko OFEROWANY** (dopis w opisie narzędzia; eskalacja po 60 akcjach ≈ budżet poziomu) → bez wymuszenia
  v13.1 gra jak v11+playbook (~28-30). Tanie naprawy: ESCALATE_ACTIONS 60→8-10; wymuszenie batcha na 1. turze poziomu;
  odrzucanie 1-akcyjnych tur bez uzasadnienia (kandydat na 1.11).
- **7911: cicha awaria replay** (try/except pass, init-mismatch → broken bez logu) → wymagać linii logu o replay.
- **7911: playbook nie najkrótszy** (sp80 28 vs 4 akcje; vc33 1 piksel) → przy regeneracji brać najkrótsze ścieżki.
- **c87: PLAN_COMMIT=1 = główna dźwignia** (jedyna celująca w bottleneck; odwrócenie ich własnej rekomendacji 0).

### PLAN SLOTÓW (rewizja GO)
- **30.10: v13.1 z ARC3_WINPATH=0 i ARC3_DEAD_SKIP=0** (martwe przy braku powtórzeń; czysta atrybucja); zostaje
  PLAN_COMMIT=1 + CAP=0 + conc=10 + **probe ON** (output-pick roster_probe.jsonl rozstrzygnie roster po runie — sam zrobię).
- **31.10: TA SAMA konfiguracja ponownie** (pomiar drawa; σ≈2.5-3.9 wymaga 2 próbek; metoda Gemmy 39.84/38.12).
- **1.11**: lepsza z dwóch; jeśli <26 → kontrola PLAN_COMMIT=0; ewent. z wymuszeniem commit (eskalacja 8-10).
- **2.11 (finał)**: select best (Kaggle: 2 submisje do punktacji prywatnej — potwierdzić w rules).
- 27B pozostaje wstrzymany (0.27/1.18).

## 16. AUDYTY v13.1 — PEŁNA RUNDKA (30.10 ~07:45 UTC): Gemma 6a6af4a, c87 f3c5726, 7911 a84173c
(Wszystko przeczytane u źródła; nasza własna kontrola: serving-parity v13.1==c45 potwierdzona — kom.21==kom.17,
 MAXREQ=10/cuda-graph/chunked identycznie -> pakiet GO#1 bez cichej regresji silnika; zagadka 3,6x ms/token Gemmy
 (r085 17,2 vs r110 62,6) = otwarte pytanie do metryk po runie.)

### Gemma (review v13.1, winpath_sim na PRAWDZIWYM silniku)
- **Cross-entry replay zweryfikowany END-TO-END**: poziom z wpisu 1 odtworzony we wpisie 2 za **0 tokenów**
  (tu93 18/18, vc33 3/3, m0r0 15/15, cn04 13/13 akcji). **dead-skip zweryfikowany** (wpisy 1-3 nie, od 4. tak).
- **Wartość = funkcja rosteru: +5…+15 pkt średniej JEŚLI roster cykliczny; 0 jeśli nie.** Rachunek najdokładniejszy
  do tej pory: kopia zachowuje efektywność wpisu 1 i cały budżet tokenowy zostawia na kolejny poziom (ls20: 414/427
  akcji na poziomy 1-3; przejście 3->4 poziomy = +16,4 pkt na tej grze).
- Ujawniła NASZĄ wewnętrzną sprzeczność: nasz własny rejestr z 25.10 (OCENA-V9-LEPSZA-DROGA.md, wiersz o
  „Replay/×4.4 = 0 … official_110 = lokalny symulator") — 5 dni przed moją błędną „certyfikacją rosteru".
  Przyznaję wprost: moja sesja to poprawnie ustaliła 25.10 i sama sobie zaprzeczyła 30.10. Retrakcja §15 stoi.
- MEGA-CONFIG (dźwignie configowe na bazie v12): **11 fal × ~49 min/gra** (cap 532 min nigdy nie wiąże);
  **s/akcja liniowe w tok/akcję (r≈1,0)**; cele: 400+ akcji/grę @ ~370 tok/akcję, 600 @ ~230;
  poddanie się skalowane wagą poziomu (C45_LEVEL_TOKEN_CAP=40000 + ABANDON_TOKENS=0 + STUCK_AUDIT=200000 +
  ABANDON_MIN_LEVELS=4); drobiazg: maybe_replay wołany przed obsługą game-over (skutek ~zero).

### c87 (f3c5726, 8. korekta)
- FAKT 1: nasza samosprzeczność rosterowa potwierdzona ich cytatem z naszego własnego dokumentu z 25.10 (+Gemma).
- FAKT 2: PLAN_COMMIT niewymuszony (7911) obala ich wczorajszą rekomendację PLAN_COMMIT=0 -> główna dźwignia
  = wymuszony batching; T3 = ich droga do 50+ (dalej: port planera paper01).
- Ich tabela oczekiwań: Gemma **26-31**; 7911 **28 albo 50** (zależnie od wymuszenia commit); wartości pamięci:
  2,90 (Gemma, roster cykliczny / 25 gier) vs 0,66 (7911, każda gra raz) vs 0 — **wszystko wisi na jednym fakcie o rosterze**.
- Krótsze ścieżki playbooka (sp80 28->4 akcji) = kosmetyka (~3 pkt, cap ukończenia wiąże), ale darmowa przy regeneracji.

### 7911 (a84173c, model budżetu)
- 532 min = sufit JEDNEJ gry (może zjeść niemal cały bieg); realny budżet dzieli priority gate:
  **efektywny czas/grę = 32 400 s × 10 / 110 = 2 945 s ≈ 49 min** -> ~205 akcji/grę @ 14,4 s/akcję ->
  **sufit @ eff=90% = 18,7 pkt** (zgadza się z rzeczywistością; efektywność mamy 86-90%).
- **DOWÓD POŚREDNI ROSTERU ≈ 110**: smoke (10 gier × 48 min) = 27,21-29,02 ≈ prawdziwy LB 26,25. Gdyby roster
  miał 25 gier (216 min/gra, ~900 akcji), wynik byłby znacznie wyższy. **Wniosek: smoke 10x48 min to dobry
  estymator WARUNKÓW ewaluacji** (populacja inna, budżet ten sam) — uzasadnia naszą bramkę smoke jako
  wykrywacz katastrof przy zachowaniu ostrożności w ekstrapolacji punktów.
- Jedyna droga do większej liczby akcji: **więcej akcji/decyzję (commit) albo mniej s/akcję (tok/akcję ↓, silnik ↑)**.

### REWIZJA PLANU (nadpisuje §15 w jednym punkcie — jawna zmiana)
- Slot 30.10: **v13.1 AS-SHIPPED (PLAN_COMMIT=1, CAP=0, WINPATH=1, DEAD_SKIP=1, conc=10, probe ON)**.
  POWÓD ODWRÓCENIA kill-switchy z §15: Gemma dowiodła, że replay/dead-skip działają i są BEZPIECZNE, gdy roster
  się nie powtarza (brak dopasowań = brak akcji), a płacą +5…+15, gdy się powtarza. Z WINPATH=1: darmowa opcja.
  Atrybucję załatwia probe + plan „2x ta sama konfiguracja" (31.10). c87 ma rację co do rozmycia — ale przy
  4 slotach i jednym nierozstrzygniętym fakcie (roster) opcja > czystość.
- Po runie: output-pick (roster_probe.jsonl + benchmark + winpath dir z poziomami) -> ROZSTRZYGNIEMY roster
  i zmierzymy ms/token (zagadka 3,6x). 31.10: to samo 2x (draw). 1.11: kontrola PLAN_COMMIT=0 LUB commit-forcing
  (eskalacja 8-10) wg wyników. 2.11: select best.
- Nadal w mocy: bez GO usera nic nie idzie.

## 17. V13.2 CERTYFIKOWANA + 2. RUNDKA AUDYTÓW + KOREKTA WIELKA: „3,6×” NIE ISTNIEJE (30.10 ~08:15 UTC)

Szczegóły weryfikacji: `duck-v13-2/OCENA-ARENA-V13-2.md`. Nowe HEAD-y: Pokemon a450 `cbefdd4→6b10853`
(v13.2), c87 `f3c5726→4c9a3e5` (audyt 4 gałęzi); 7911 i Gemma c4eeb067 bez zmian. **Domykamy też
Gemmę 6d081d52→678da95 (pobraną w §16, nieczytaną) — przeczytana w całości.**

### A. v13.2 (Pokemon 6b10853) — zweryfikowana, CERTYFIKOWANA
- Diff vs v13.1 CHIRURGICZNY: notebook tylko kom. 2 (ESCALATE_ACTIONS 60→10, print v13.2) i kom. 11
  (wbudowany patch 0006 z guardem); standalone winpath +3 linie; +1 test winpath (teraz 8); verify/build
  sync wersji; metadata v13-2; NOWE src/base-v11.ipynb (input buildera, notebook submisyjny prebuilt);
  **playbook.json bajtowo identyczny** (cmp 0 różnic).
- Guard GAME_OVER: `_replay_once` na martwej klatce zwraca False PRZED dotknięciem broken/fails ->
  sterowanie idzie do normalnej obsługi game-over; naprawia drobiazg Gemmy z §16 i jest zamknięty
  testem jednostkowym.
- ESCALATE 60→10: okablowanie potwierdzone samodzielnie (kom. 2 eksportuje ARC3_ESCALATE_ACTIONS;
  spatchowany tool_agent.py:131 czyta env; dyrektywa co N akcji). Jedyny mechanizm WYMUSZANIA
  commit(plan) — wchodzi do slotu 30.10 zamiast czekać na 1.11.
- Nasze checki: 6/6 patchy czysty r033, drzewo się kompiluje, 12/12 plan-commit, **8/8 winpath**
  (w tym nowy test), standalone==spatchowany bajt, playbook **14/14 na żywym silniku** (arcengine
  0.9.3/arc_agi 0.9.9), serving kom. 21 nietknięta (parity z c45 przenosi się tranzytywnie).
- Pułapka (potwierdzona po raz 2): krok winpath w verify_v13.py nadpisuje PYTHONPATH (gubi arcengine)
  -> 1 fail+5 errors środowiskowe; ręcznie z pełnym PYTHONPATH 8/8. FAIL verify = środowisko, nie logika.

### B. c87 4c9a3e5 „AUDYT-4-GALEZI-30-10.md” — przeczytany w całości
- Potwierdza naszą retrakcję §15 i konwergencję 4 sesji (ich tabela zgodności = wspólny stan wiedzy).
- Ich zastrzeżenie do naszej rewizji §16 (UCIŚLE zapisane): po retrakcji „darmowa opcja” WINPATH=1
  zakłada prawdopodobieństwo rosteru, które właśnie wycofaliśmy; wartość oczek. ≈ 0, a cicha awaria
  replayu (try/except bez logu, 7911) to **ryzyko DIAGNOSTYKI, nie wyniku**. Utrzymujemy WINPATH=1
  (Gemma: brak dopasowań = 0 akcji kosztu; probe rozstrzygnie), ale z pełną świadomością tego argumentu.
- Ich §5.2 — NAPIĘCIE w modelu 7911, które my też cytujemy w §16 bez flagi: **sufit 18,7 @ eff=90%
  jest PONIŻEJ zmierzonego LB 26,25**; jedno z trzech (tempo 14,4 z r013 za wysokie / eff nie z tej
  populacji / roster ≠ 110) musi być nie tak. Nierozstrzygnięte — nie budować na suficie 18,7 prognoz.
- Ich reguła (3. przypadek tego samego błędu): komórka konfiguracyjna ma DWA bloki (smoke vs
  TRUE_SUBMISSION) — czytanie pierwszego jako drugiego daje fałszywy model budżetu.
- Ich plan slotów różni się naszym w 1 punkcie: 30.10 z PLAN_COMMIT=0 (kontrola), eskalacja 8-10 dopiero
  31.10. v13.2 przenosi eskalację do 30.10 — zostawiamy DECYZJĘ userowi: (i) v13.2 as-shipped
  (eskalacja od razu), albo (ii) v13.2 z PLAN_COMMIT=0 (kontrola c87).

### C. Gemma 6d081d52→678da95 — DOMKNIĘTA (przeczytana w całości; stan z 25.10, 5 dni stary)
- Audyt ICH pracy na c87 z 25.10 (nie opinia o v13.x). Kluczowe: formuła punktacji min(115,(baseline/akcje)²·100)
  z wagami w_k=k+1 potwierdzona co do setnej (4. potwierdzenie capu 1.15); efektywność ruchów warta
  ~1,75 pkt (nie główny cel); kalibracja kliknięć PO EFEKCIE = najbardziej transferowalna metoda;
  n_passes=1 potwierdzone 25.10 (4. niezależne); kompakcja pamięci istnieje, ale ARC3_MEMORY_SECTIONS=off
  i historia 150 tur; **wewnętrzne _get_valid_actions()/_score/_win_score z arc3_search.py ZAKAZANE
  w submisji** (zgodność — używać publicznego API + kalibracji po skutku); kolizja numerów patchy 0004
  (c87 vs a450) — nie składać jednego łańcucha; błąd auto-submit ops.py:459 (ścieżka vs nazwa pliku).
- v13.2 używa numeru 0006 — kolizja uniknięta (potwierdzenie ich ostrzeżenia).

### D. KOREKTA WIELKA (nasza, samodzielna weryfikacja w artefaktach): **zagadka „3,6× ms/token” NIE ISTNIEJE**
- Gemma MEGA-CONFIG.md (6a6af4a, linia tabeli): „r110 | 8B, v13 cap 45k | 62,6 ms/tok” — **BŁĘDNA
  ETYKIETA**. c87 przepisał tabelę i zbudował na niej główny wniosek audytu („3,6× luka silnika warta
  więcej niż cały spór o v13”; priorytet #1: sparsować serve.log, by „odzyskać” 17,2 ms/tok).
- PRAWDA (artefakty w naszym repo): **r110 = petersharps/arc3-duck-v13-27b** — Qwen3.6-**27B**-FP8 na
  **vLLM** (vllm-openai-server.log: `SERVED_MODEL_NAME = 'vrfai/Qwen3.6-27B-FP8'`, wheelhouse
  arc3-vllm-h100; SUMMARY.md potwierdza nazwę kernela). benchmark.json: 926 akcji / 448 782 tok /
  28 806,8 s summed wallclock -> **64,2 ms/tok** (liczba Gemmy poprawna, etykieta nie).
  r118 = arc3-duck-v14-27b-long (27B; 63,1 ms/tok Gemmy — spójne). r085 = arc3-duck-c45 (8B, SGLang):
  nasz szacunek z serve.log (agregat ~663 tok/s ÷ 10 współbieżnych ≈ 15 ms/tok per-request) zgodny
  z 17,2 Gemmy. Wniosek: 17 vs 63 ms/tok to RÓŻNICA MODELI (i silników: SGLang vs vLLM), nie zagadka
  inżynieryjna. „Odzyskanie 82→228 akcji bez zmiany modelu” — nonsens: nasza linia v13.x JEST 8B.
- Co zostaje PRAWDZIWE po korekcie: (1) 27B martwy (0,27-0,73 smoke, 63 ms/tok) — nie wznawiać;
  (2) jedyny realny pomiar 8B to SMOKE (10 gier) — czy 17 ms/tok utrzyma się w rerunie 110 gier
  (prefix-cache między falami różnych gier), NIEZNANE — **zmierzy metering/probe w runie 30.10**;
  (3) sparsowanie serve.log r085 vs r093 (oba 8B SGLang smoke) to porównanie w obrębie smoke —
  umiarkowana wartość, NIE 20-40 pkt jak liczył c87 (ich §3.3 traci podstawę).
- Lekcja (do FAKTÓW, 4. przypadek): liczba z cudzego dokumentu bez odczytu wskazanego artefaktu to
  hipoteza. c87 sam napisał „zawartości nie czytałem” — wystarczyło przeczytać SUMMARY.md.

### E. PLAN (następstwa; NIC do Kaggle bez GO usera)
- Slot 30.10 (CZEKA NA GO): **v13.2 AS-SHIPPED** — PLAN_COMMIT=1, ESCALATE=10, CAP=0, WINPATH=1,
  DEAD_SKIP=1, conc=10, probe ON. Po runie: output-pick (roster_probe.jsonl + benchmark + winpath dir
  + metering ms/token) -> rozstrzygnięcie rosteru + pomiar warunków rerunu (pkt D.2).
- 31.10: ta sama konfiguracja ×2 (draw przy σ≈2,5-3,9). 1.11: wg wyników — kontrola PLAN_COMMIT=0
  (opcja c87) albo commit-forcing dalej; 2.11: select best.
- Otwarte (offline, 0 slotów): ewentualny parsing serve.log r085 vs r093 (zakres umiarkowany, pkt D.3);
  rozstrzygnięcie napięcia c87 §5.2 (sufit 18,7 vs LB 26,25) po pomiarach z runu.

## 18. V13.3-ARENA — WŁASNY WARIANT ARENY: „WYMUSZENIE BATCHA" BEZ NOWEGO PATCHA PROMPTOWEGO (30.10 ~09:30 UTC)

Szczegóły: `duck-v13-3-arena/OCENA-ARENA-V13-3-ARENA.md` + README pakietu. Powód: user zapytał o plan
„czegoś lepszego od v13.2" i zlecił budowę. v13.3-arena = v13.2 + DOKŁADNIE 2 dźwignie z audytów,
obie kill-switchowalne:

1. **ARC3_OPENER_COMMIT_HINT=1 (env-only!)** — harness MA wbudowany, env-gated (domyślnie OFF)
   nacisk batchujący na każdym świeżym openerze; upstreamowy pomiar w docstringu tool_agent.py:
   opener batche 3,91-5,43 akcji vs resumption 6,73-6,91. To jest dokładnie „wymuszenie batcha na
   1. turze" z listy napraw c87 — obejmuje pierwsze ~10 akcji poziomu, których eskalacja (v13.2,
   co 10) nie dotyka. Cel: akcje/wywołanie 4,36 -> 6-9 (metr: metering, odporny na hałas σ punktów).
   Kill-switch: "ARC3_OPENER_COMMIT_HINT": "0" w komórce wariantu.
2. **Patch 0007 (duck-extra-05): log zdarzeń win-path** — [arc3-winpath] stdout: session begin/end,
   playbook match, replay start/ok/abort+POWÓD (hash-mismatch@krok, action-unavailable, game-over,
   init-mismatch->broken, exhausted), record, dead-skip. Realizuje żądanie audytów 7911+c87
   („cicha awaria replayu = ryzyko diagnostyki"): z samego logu reruna będzie widać, czy replay
   strzelał. Log-only, ZERO zmiany semantyki, nigdy na gorących ścieżkach. Kill: ARC3_WINPATH_LOG=0.

Weryfikacja (wszystko samodzielnie): 7/7 patchy czysty r033 -> ALL CHECKS PASSED (verify pakietu:
36 komórek, opener-hint/extra-05/wersja checki dodane, PYTHONPATH-bug naprawiony => winpath step
teraz przechodzi wbudowanie), 12/12 plan-commit + **11/11 winpath** (3 nowe testy logowania) na
spatchowanym drzewie, standalone==spatchowany bajt, playbook bajtowo v13.2 i **14/14 na silniku**,
cell-diff vs v13.2: tylko kom. 1+2 + wstawiony writer; serving stara kom. 21 == nowa 22 (parity c45).

PLAN SLOTÓW (bez zmiany GO#1): **30.10 = v13.2** (baseline eskalacji co 10), **31.10 = v13.3-arena**
(pomiar mechanizmu: metering akcje/wywołanie + logi replay + score), 1.11 = lepszy mechanizm x2
(draw), 2.11 = select best. Alternatywa agresywna (30.10 od razu v13.3) NIErekomendowana: jeden
zmienny na slot; baseline pozwoli policzyć wkład hinta z meteringu.
Przygotowana OPCJA na 1.11 (nie doklejana): ARC3_HISTORY_ASSISTANT_TURNS 150->48 (env-only, -30%
tok/akcji => ~+40% akcji/grę przy tym samym silniku; NIEZMIERZONE, godzi w pamięć gry).
Oczekiwanie na v13.3: jeśli hint przenosi się na naszą linię (+25-50% akcji/decyzję na openerach),
kilka punktów w górę wg projekcji Gemmy; ryzyko: gorsze batche niż eksploracja — stąd osobny slot.
NADAL: NIC do Kaggle bez wyraźnego GO usera.

## 19. V14 (GEMMA b38b82e) ZAUDYTOWANA + V13.4-UNIFIED — SKLEJKA BEST-OF-ALL-BRANCHES (30.10 ~10:30 UTC)

Szczegóły: `duck-v13-4-unified/OCENA-ARENA-V13-4-UNIFIED.md`. Nowy HEAD Gemmy c4eeb067: 6a6af4a ->
**b38b82e** (2 komity: recenzja v13.2 07:55, pakiet duck-v14 08:04). Przeczytane w całości: README v14,
PROPOZYCJA-0007.md, REVIEWS/2026-10-29-v13-2..., MEGA-CONFIG §4b, escalation_audit.py, test_probes.py.

### A. v14 (Gemma) — audit i werdykt
- Baza bajt-w-bajt v13.2 (md5 2886fde0ecc3... potwierdzony na NASZYM pliku), playbook ten sam,
  0 nowych patchy. Zmiany: ESCALATE 10->20, guard hooka sondy, sonda budżetu (przed), sonda rosteru (po).
- **ESCALATE=10 ZMIERZONE jako zbyt zachłanne** (ich escalation_audit.py na r085, 32 ukończone poziomy):
  @10 = 154 wstrzyknięć = 15,3% puli tokenów gry, "przestań próbować" PRZED ludzkim baseline'em na
  **31/32 poziomów** (kosztowna posłuszność: każda zachęta prosi turę modelarską); @20 = 60/6,0%;
  próg względny max(20, 1,2×baseline) = 8/0,8%/0 przedwczesnych. **NASZE NIEZALEŻNE PRZELICZENIE
  (własny kod na r085 benchmark.json): identycznie 154/12/8 i 31/32, 7/32, 0/32.** Konsekwencja:
  GO#1=v13.2 z @10 przestaje być "bezpiecznym baseline" — płaci za znalezione ryzyko.
- **Guard hooka sondy = REALNE ryzyko USUNIĘTE przez v14, obecne w naszym łańcuchu** (v12->v13.x->
  v13.3-arena): `_orig_play = _S._HarnessGameSession.play` POZA try w komórce ustawiającej
  bm.solver.* -> AttributeError w innej rewizji bundla = martwy notebook PRZED startem (klasa
  katastrofy c45-0.00). Komentarz w naszej komórce ("kazdy blok w try/except") był FAŁSZYWY.
- Sondy (budżet: cap vs uczciwy udział, ostrzeżenie >1,3x; roster: duplicate_bases z bm.game_runs
  + alarm actions_per_call<1,5) — wszystko try/except, 0 zmian zachowania. Fakty Gemmy: we wszystkich
  3 zapisanych runach każda gra kończy DOKŁADNIE na capie (48/48/90 min) -> cap = przydział akcji.
- PROPOZYCJA-0007 (próg względny): NIE wysłana przez brak r033 ("patch, który nie wchodzi, zabija
  notebook"). Nasza odpowiedź: **mamy r033 — wysłaliśmy** (pkt B).
- Ich MEGA-CONFIG NADAL ma błędną etykietę r110 ("8B, v13 cap 45k") — nasza korekta §17D (27B/vLLM)
  pozostaje nasz wyłączny zweryfikowany fakt.
- Prognoza v14: 26-31, "@20 raczej górna połowa". Ich §6 uczciwie: nie sprawdzili dostępności
  check_model/plan przy WORLD_MODEL=0 (czytali, nie uruchamiali).

### B. v13.4-unified (nasz pakiet, CERTYFIKOWANY: ALL CHECKS PASSED)
- Skład: v13.2 (baza) + v13.3-arena (OPENER_COMMIT_HINT=1 + patch 0007 log) + v14 (ESCALATE=20,
  guard hooka, obie sondy) + **patch 0008: ARC3_ESCALATE_RELATIVE=1** — eskalacja tylko powyżej
  max(floor, RATE×base_actions_per_level[poziom]), cap 2/level; fallback na absolutne 20 gdy
  baseline ukryty (GameRun.base_actions_per_level=None) lub brak referencji gry. Dowiązanie gry:
  1 hunk w solver._make_analyzer (agent.game = game; notebook nie używa analyzer_factory — sprawdzone).
  base_actions_per_level istnieje w runtime (taaf/game.py:295).
- **Test kluczowy**: spatchowany tool_agent._escalate_threshold na PRAWDZIWYM benchmarku r085
  odtwarza dokładnie 8 nudge'ów / 0 przedwczesnych (test pakiecie, R085_BENCH).
- Weryfikacja: 39 komórek; 8/8 patchy czysty r033; 12 plan-commit + 6 escalate-relative +
  11 winpath na spatchowanym drzewie; sondy na stubach (duplikaty/0-pkt/a-call-alarm/exception-proof/
  guard hooka); playbook bajtowo v13.2 i 14/14 na silniku; serving kom. 21==22 parity; cell-diff
  potwierdzony (1,2,12, +13 writer, 27 guard, +31 budżet, +38 roster; roster pisze do
  roster_probe_runs.jsonl, żeby NIE nadpisać logu hooka c45 — drobna poprawka nad v14).
- Matryca kill-switchy: RELATIVE=0 -> v14 exact; OPENER=0 -> v14; WINPATH_LOG=0; WINPATH/DEAD_SKIP/
  PLAN_COMMIT/CAP jak dotychczas; ESCALATE_MAX_PER_LEVEL=0 bez capu.

### C. PLAN SLOTÓW (propozycja do GO; nadal NIC bez wyraźnego GO)
- **30.10: v13.4-unified** (zamiast v13.2 as-shipped — @10 zmierzone jako ryzyko; unified =
  ten sam kierunek, ostrzejszy zmierzony spust, pełna obserwacja, wszystko kill-switchowalne).
- 31.10: v13.4-unified ×2 (draw) LUB v14 (Gemma) jako kontrola absolutna @20 — wg preferencji usera.
- 1.11: flip najsłabszego komponentu wg meteringu (RELATIVE=0 / OPENER=0; opcja HISTORY 150->48
  gdy sonda budżetu pokaże głodzenie). 2.11: select best.
- Metry rozstrzygające z biegu 30.10 (niezależne od σ punktów): actions_per_call (bramka >=1,8),
  duplicate_bases (roster), cap_over_fair (głodzenie), [arc3-winpath] (replay żyje?), liczba
  nudge'ów (log Eskalacji).

## 20. FALA 08:00-08:12 (v15 u kolegow) + V13.5-CONSENSUS — SKLEJKA FINALNA (30.10 ~11:15 UTC)

Szczegoly: `duck-v13-5-consensus/OCENA-ARENA-V13-5-CONSENSUS.md`. Nowe HEAD-y: 7911 a84173c ->
c170f55 (7 komitow), a450 6b10853 -> 8d96c68 (duck-v15), c87 4c9a3e5 -> 980deff (9. korekta),
Gemma b38b82e -> 07bf05e (audyt NASZEGO v13.3 + duck-v15). Przeczytane w calosci.

### A. Korekty 7911 (przyjete)
- **1541d08**: ich „1,00 akcji/decyzje" = artefakt metody; prawda **4,61 akcji/generacje, 853 tok/akcje**;
  budzet = DEKODOWANIE (~186 tys. tok/gre @15,8 ms/tok -> ~218 akcji/gre); dzwignia = **mniej tok/akcje**
  (do 50: ~479 = -44%). UWAGA: batching/hint to wlasnie mechanizm ciecia tok/akcje (zgodne z audytem
  Gemmy v13.3: a/call 4,36->6,5 => tok/akcje -33% => akcje/gre +50%).
- **724189b**: poprawiona regula punktacji **score = min(raw, cap) <= 100 x POKRYCIE** (30/30 na
  zapisanych wynikach); do 50: pokrycie 29->50% = **+1,1 poziomu/gre = +22% budzetu**; 72 akcje/gre
  idzie w nieukonczone proby; na ukonczonych 1,7x szybsi od czlowieka (wiezie cap ukonczenia).
- **c170f55**: **baseline DOMKNIETY NEGATYWNIE** — w submisji silnik UKRYWA base_actions_per_level
  (a450 sprawdzil na r033) -> prog wzgledny degeneruje do absolutnej 20 + cap 2. „Czy wypelnione
  w rerunie = sonda, nie zalozenie".

### B. Kolegi pakiety
- **a450 duck-v15** (8d96c68): v14 Gemmy + ICH patch progu wzglednego (pc_escalate_at w plan_commit;
  ToolAgent(baseline) z konstruktora); 7/7+12+8+7; sami potwierdzaja degradacje w submisji.
- **Gemma duck-v15** (07bf05e): baza = **NASZE v13.3-arena** (audit: PRZECHODZI; „mechanizm prawdziwy,
  ta sama dzwignia co commit(plan) ale tansza; batch zmienia tok/akcje nie liczbe akcji") + v14 items.
- **c87 980deff**: 9. korekta (PLAN_COMMIT=1+ESCALATE spójne; ESCALATE jest env — domkniete) +
  lekcja **„testy zielone przy martwej funkcji"**.

### C. Sprostowanie opinii Gemmy o naszym pakiecie (z dowodem)
- Jej zastrzezenie §2c („150->48 odwrócone, domyslna 30") NIEDOTYCZY naszego pakietu: setup_env
  (kom. 15) pinuje ARC3_HISTORY_ASSISTANT_TURNS=150 WPROST — nasz opis trimu poprawny. Jej
  MEGA-CONFIG nadal ma bledna etykiety r110 („8B cap 45k") — korekta §17D bez zmian.

### D. V13.5-CONSENSUS — CERTYFIKOWANA (ALL CHECKS PASSED)
- Zmiany vs v13.4 (cell-diff 1,2,12,31,38): konsensus w kom. 2 (degradacja: rerun = absolutna 20 +
  cap 2 = **42 wstrzykniecia na r085 = 2,9% puli**; Gemma 20 vs 7911 30-60 — cap ogranicza oba;
  escalate= logowane), **sonda rosteru + pokrycie wazone + widocznosc baseline'u** (werdykt
  UKRYTY/ZYWY z rerunu), rebrandy. Patch chain bez zmian (0001-0008).
- Weryfikacja: 8/8 patchy, 12+6+11 testow (w tym 8/0 nudzy na r085 przez spatchowany kod), sondy
  (pokrycie 19,8% -> sufit ~20 pkt na stubach; baseline UKRYTY/widoczny), playbook bajt, serving OK.
- **Lekcja praktyczna (nowa pulapka srodowiskowa)**: nieudany tar --strip-components=2 zostawil
  /tmp/src/arc3_winpath.py (STARY modul bez _log), ktory przez sys.path.insert(parent.parent/src)
  w testach ZACIENIAL modul z drzewa -> „zielone testy na martwym module" (lekcja c87 z zycia).
  /tmp/src usuniete; po oczyszczeniu 11/11.

### E. PLAN SLOTÓW (propozycja; NIC bez GO)
- **30.10: v13.5-consensus** (nadzbior wszystkich: hint+log+progi+sondy+metryki 7911).
- 31.10: v13.5 x2 (draw) lub kontrola v14-exact (RELATIVE=0 + OPENER=0 w TYM SAMYM kernelu).
- 1.11: flip najsabszego wg meteringu (RELATIVE=0 / HISTORY 150->48 poprawnie opisany / skrocenie
  dyrektywy — wymaga patcha prompts.py, nie teraz). 2.11: select best.

## 21. FALA 08:22–09:18 (v16 GEMMY, AUDYTY a450, c87 WARSTWA 8, 7911 24:1) + V13.6-FINAL — CERTYFIKOWANA (30.10 ~13:15 UTC)

### A. Co przyszło z gałęzi (wszystko przeczytane, kluczowe liczby zweryfikowane)
- **Gemma 0ef2465 (08:38) = duck-v16**: nadzbiór naszego v13.4-unified (odtworzyła nasze
  8 patchy samodzielnie, 8 nudge/0 przedwczesnych przez spatchowany kod — potwierdzenie
  z zewnątrz) + **patch 0009 self-pace** + sonda pokrycia. Self-pace = próg z
  `GameRun.actions_per_level` (nasz rekord, NIEUKRYWANY): r085 = **22/14** (vs 42/26
  floor20+cap2, vs 8/0 relatywny tylko-przy-widocznym-baseline'ie). Rysy u nich:
  metadata slug dalej `arc3-duck-v13-4-unified` (nadpisze kernel przy pushu!) i docstring
  0009 (27/16) vs tabela/testy (22/14). Plus sweep niepokrytych gier: 0/3 trafień (uczciwie).
- **a450 (839c169 08:43 → 52b709e 08:49 → 2e2337c 09:18)**: audyt naszego v13.4 = „nowy
  kandydat nr 1" (1 rysa: test R085_BENCH bez `is_file()` → IsADirectoryError z czystego
  klona — FIX w v13.6); v13.5 potwierdzona; **duck-v16 9/9 zweryfikowane z reprodukcją**;
  stan: „duck-v16 najpełniejszy, potem v13.5". Recenzja paczki **v17-action-efficiency**
  (nasz upload 283a36b8): liczby odtwarzalne 7/7 i 40,06 (zgodne z naszym repro), ale
  **bug: ConvergedGuard.banned kluczuje po akcji — akcje myszowe (dict) niehashowalne →
  TypeError w prawdziwym harnessie**; PlanCache ≈ winpath 0006; BudgetLedger nie mapuje się
  na równoległy solver.
- **c87 (c7dab76 08:30 → 28ed67f 08:55)**: przyjmuje naszą korektę „3,6×" (hipoteza KV
  obalona własnym pomiarem 663 tok/s; spór o silnik ZAMKNIĘTY); **8. instancja klasy:
  MARTWY INSTRUMENT** — alarm `actions_per_call < 1.5` w sonda rosteru v14/v15 (próg 3×
  poniżej zmierzonej bazy 4,357; pochodził z ery 1,00 a/decyzję r013/15/18) — sonda mówiła
  „wiemy", nie mówiąc czy hint zadziałał; „martwa dźwignia daje wynik neutralny, martwy
  miernik daje fałszywe poczucie, że wiemy". NIEZALEŻNA REPLIKACJA rozkładu baseline'ów
  (r093, n=69: mediana 72, średnia 104; zgodność z Gemmą przy progu 10: 96,3 vs 96,9%).
- **7911 (cad326c 08:22) = V17-COMPARE** (analityka): **hint openerowy = 48–50 akcji,
  cały spór o eskalację = 2 akcje/gry → stosunek 24:1**; trzy niezależne pomiary tej samej
  liczby (4,61/4,357/3,91–5,43); **bramka własna a/call ≥ 6,0** (Gemmina ≥1,8 przechodzi
  przy martwym hincie; 6,0 leży na granicy 253 akcji/gry = 50 pkt); arytmetyka: POŁOWICZNY
  efekt hinta (5,62 a/gen → 700 tok/akcję → 266 akcji/gry) wystarcza do 50. Ich „v13.4 nie
  istnieje" = przeszukiwanie sprzed naszego pushu (nieaktualne, i tak wyciągnęli właściwy
  wniosek); ich „v17" ≈ nasze v13.5 + bramka 6,0.

### B. V13.6-FINAL — CERTYFIKOWANA (ALL CHECKS PASSED, komit ten)
- Skład (cell-diff vs v13.5 = {1,2,12,14,32,39}; 40 komórek, 743 616 B):
  1) patch **0009 self-pace** przeniesiony BAJT W BAJT z Gemmy duck-v16 (`duck-extra-07`),
  2) **fix martwego alarmu** → bezwarunkowy druk `v13.6 batch: a/call = … (baza r019 = 4.357;
     cel ~5.7/300, ~7.6/400; bramka 7911 >= 6.0 …)`,
  3) **fix testu** R085_BENCH (`is_file`),
  4) slug `petersharps/arc3-duck-v13-6-final` (bez rysy Gemmy).
- Weryfikacja: **9/9 patchy** czysty r033, drzewo kompiluje, **12+6+11 testów**,
  **test_self_pace 22/14 (1:1 z kodu patcha, fixtures==shipped)**, sondy stub z nowym
  drukiem, playbook bajt, serving nietknięty. Builder przyrostowy (reguła v13.5).
- Prognoza: przedział v13.5 (26–31), self-pace = korekta 2–4 akcji/gry na grach z długimi
  przegrywanymi poziomami; dźwignia nr 1 pozostaje hint (24:1). Slot 30.10 = v13.6-final;
  31.10 = powtórka/kontrola wg druków a/call + pokrycia; CZEKA NA GO.

### C. Paczka v17-action-efficiency (upload UI 283a36b8, obca sesja) — DECYZJA
- Zweryfikowana przez NAS (7/7 testów, RHAE 3,80→40,06 repro 1:1, pliki==zip) i przez
  a450 (to samo) — uczciwa, ortogonalna, ale **niedojrzała do submisji**: bug niehashowalnych
  akcji w ConvergedGuard; PlanCache≈winpath; BudgetLedger bez mapowania na równoległy solver.
  **NIE tworzymy v18; nie wpinamy dzisiaj.** Wartość: przegląd metodologiczny + pomysł
  „ban po hashu stanu" do małego patcha win-path później (po 2.11).
- 3 pliki obcej sesji w KORZENIU repo — docelowo do przeniesienia (np.
  `arc-agi-3/duck-v17-action-efficiency/`) po decyzji usera; nie ruszamy bez GO.

### D. Lekcja środowiskowa (nowa)
- Sandbox odtworzony: wheels arcengine 0.9.3 wymagają Pythona ≥3.12 (system 3.11) →
  wheel rozpakowany do /tmp/ae i wstrzyknięty w PYTHONPATH (jak 29.10); brak arcengine
  = 8 ERRORS winpath / 4 ERRORS escalate — wygląda jak „zepsuty pakiet", jest środowiskiem.
  W builderach: kolejność podmian ma znaczenie (rebrand psuje kotwicę alarmu — assertion łapie).

## 22. HANDOFF SESJI „STRATEGIA" (999f9194, 14:40) — ZWERYFIKOWANY, PENDING-GATE ZAMKNIĘTY PRZEZ NAS + V13.7-FINAL — CERTYFIKOWANA (30.10 ~15:30 UTC)

### A. Co przyszło (zip 1 019 138 B w korzeniu gałęzi; pełny snapshot .git ich gałęzi)
- **arc-v16-package** = ich kernel `arc3-duck-v16` (40 kom., 749 222 B): **nasz v13.4 +
  patch 0009-dyn-level-budget (DORMANT)** — adaptacyjny budżet poziomu: cap =
  clamp(mediana koszów ukończonych poziomów gry ×4, 45k, 150k), drabina RESET ×1,5,
  ABANDON po wyczerpaniu resetów; dotyczy WYŁĄCZNIE framework/arc3_level_budget.py
  (moduł 0004) → **plik rozłączny od self-pace Gemmy** (tool_agent.py). Slug ich:
  arc3-duck-v16 (unikalny). 16/16 testów; verify_v16 ALL LOCAL CHECKS PASSED;
  **bramka łańcucha r033 = pending → ZAMKNIĘTA PRZEZ NAS**: 9/9 patchy czysty r033,
  kompilacja, nasze 12+6+11 testów na ich drzewie, 11/11 winpath; rekonstrukcja
  src == bajty spatchowanego drzewa (cmp) — testują dokładnie to, co wysyłają.
- **refs/**: patch self-pace Gemmy (u nas już jako 0009 w v13.6).
- **Porównanie v16-naj vs v13.5 vs Gemma-v16**: zgodne z naszą mapą; ich „v17-naj"
  = v13.5 + self-pace + dyn dormant + bramka 6,0 → == nasze v13.7-final. Higiena
  slugów: Gemma duck-v15/v16 celują w NASZE slugy (nadpisalby kernele v13-3/v13-4).
- **Recenzja v17 (strategia) — KLUCZOWE**: „RHAE 3,80→40,06" mierzy wartość PLANOWANIA
  (PlannerAgent BFS vs ReactiveAgent), NIE warstwy — warstwa nie jest użyta w eval-u
  ani razu; „12 seedów" = kosmetyka (1 przebieg deterministyczny, stdev 0,00);
  integracja: PlanCache kolizja z win-path 0006, BudgetLedger = drugi harmonogram
  (reguła jednego pisarza), ConvergedGuard najbezpieczniejszy (ale bug niehashowalnych
  akcji a450 przed wpięciem). Nasza decyzja §21C PODTRZYMANA I WZMOCNIONA.
- War-room 27-10: historia kampanii (kontekst; bez nowych liczb do akcji).

### B. V13.7-FINAL — CERTYFIKOWANA (ALL CHECKS PASSED, komit ten)
- = v13.6 + patch **0010-dyn-level-budget** (bajt w bajt z handoffu) jako extra-08;
  **DORMANT** (LEVEL_TOKEN_CAP=0 zostaje → submisja ≡ v13.6; uzbrojenie = 0→60000,
  propozycja na 1.11; kill ARC3_DYN_CAP=0 → exact 0004 = gotowy kontrolny A/B).
- 41 komórek, 758 240 B; cell-diff vs v13.6 = {1,2,12,14,15,33,40}; writer extra-08 ==
  patches/0010; slug petersharps/arc3-duck-v13-7-final.
- Weryfikacja: **10/10 patchy** czysty r033, drzewo kompiluje, 12+6+11 testów,
  self-pace 22/14 1:1, **0010: rekonstrukcja==drzewo (cmp) + 16/16 na bajtach
  wysyłkowych**, dormancja w wariancie, sondy stub, playbook bajt, serving nietknięty.

### C. Plan slotów (do GO usera; wszystkie ścieżki gotowe)
- **30.10: v13-7-final** (≡ v13.6 na submisji, + dźwignia na 1.11 w kieszeni).
- 31.10: powtórka (σ 2,5–3,9) albo v13.6/v13.5-kontrola — wg druków a/call i pokrycia.
- 1.11: flip wg sond: **uzbrojenie 0010 (60000)** — najtańsza dostępna dźwignia głębi;
  ewentualnie SELF_PACE=0 / HISTORY 150→48 jako alternatywne flipy (1 zmiana/bieg!).
- 2.11: select best. Nic nie wychodzi bez GO.

### D. Księgowość repo
- Handoff zip siedzi w korzeniu (999f9194) — po decyzji usera do przeniesienia obok
  v17 (np. arc-agi-3/handoff-strategia-30-10/); 3 pliki v17 (283a36b8) j.w. (§21C).
- Pakiet strategii NIE jest przez nas wypychany na Kaggle bez wyraźnej decyzji usera
  (ich slug arc3-duck-v16 jest wolny, ale to cudzy kernel).

## 23. OPINIA GEMMY (6d081d52) O V13-7-FINAL — ODTWORZONA PRZEZ NAS 1:1 + KOREKTA ARMINGU 60000→20000 + SPROSTOWANIE SKIPA (30.10 ~16:30 UTC)

- Gemma odtworzyła nasz build/verify offline (bajt w bajt, cell-diff {1,2,12,14,15,33,40}
  identyczny, sha256 patcha 0010 zgodny) i dodała: dormancja różnicowa (8000 decyzji ×
  5 konfigów = identyczne), własne liczby z 40 gier (r085/r093/r110/r118) i KOREKTĘ:
  **arming 20 000, nie 60 000**.
- Nasza weryfikacja (samodzielnie, na naszych benchmarkach): **kod** — `max(static, mediana×4)`
  = dyn nigdy nie tnie ciaśniej od armingu; fallback <2 ukończonych = static; drabina PO
  clampie (225k>150k, kosmetyka). **Liczby 1:1**: >45k=14, >60k=13 (max 91 043 vs ich 88 114),
  marnotrawstwo median 64,5%/max 100%, @60000: 16/40 aktywnych, 15 luźniej/0 ciaśniej,
  mediana capa 128 612 — wszystko identyczne.
- **Wniosek przyjęty**: @60000 nie dotyka 15 gier palących 100% budżetu (0 ukończonych);
  @20000 te same capa dla gier z historią + cięcie marnotrawców (20k+reset ~40k).
  Notebook/README/OCENA rev2 z armingiem 20000; ryzyko: 14 ukończonych >45k pod capem —
  mierzyć completed/game; ARC3_LEVEL_MIN_DONE=1 jako OSOBNA kolejna zmienna.
- **SPROSTOWANIE**: R085_BENCH w naszych biegach verify wskazywał nieistniejącą ścieżkę
  → test 8 nudge'ów (escalate) był CICHO SKIPPED (skip nie psuje PASS). verify rev2:
  check realnego R085_BENCH + „none skipped"; bieg z dobrą ścieżką: ALL CHECKS PASSED,
  0 skipów. Wcześniejsze certyfikaty v13.5/v13.6/v13.7(1): wszystkie inne testy biegały;
  tylko ten jeden był w skipie.
- Gemma pyta o zgodę na wypchnięcie ich raportu (568420c, notes/…ocena-v13-7-final… +
  audit_dyn_budget.py) — rekomendacja: TAK (niezależny audyt + narzędzie do powtórzenia).
  Ich „v17-arena D′" aplikuje się czysto na drzewo v13.7 (ich twierdzenie, u nich).

## 24. GEMMA 6d081d52 WYPYCHA v17-arena-dyn (= NASZ v13.7 + ŻYWY D′) — ZWERYFIKOWANE U NAS + WERDYKT „CZYJA LEPSZA" (30.10 ~17:10 UTC)

### A. Weryfikacja ich pakietu (wszystko odtworzone na naszym bundlu/danych)
- `arc3_local_candidate/v17-arena-dyn/`: **45 komórek / 783 407 B** (jak deklarowali);
  baza = nasz **v13.7 rev1** (758 240 B; rev2 różni się tylko notą 20000 i verify — zero
  zachowania); build **bajt w bajt powtarzalny** (build_v17_dyn.py z jawnymi --prev/--patch);
  **verify_v17_dyn --bundle r033 --tests → ALL CHECKS PASSED u nas**: 11/11 patchy czysty r033,
  kompilacja, 12 plan-commit + 5 escalate (r085-repro w środku, przeszedł z naszym REALNYM
  R085_BENCH) + 21 D′ + 16 dyn na bajtach wysyłkowych + self-pace 22/14 z drzewa + 11 winpath;
  cmp obu rekonstrukcji z drzewem; **OFF ≡ legacy priority_value (24 kombinacje)**.
- **Jedyna żywa różnica vs nasz rev2: patch 0011 D′ (ARC3_PRIORITY_DPRIME=1) — PODMIANA
  HARMONOGRAMU SLOTÓW, ŻYWA NA SUBMISJI**. Formuła A×M×C+B×φ (głębia×tempo×cierpliwość +
  bonus wzrostu zanikający na końcu); ścieżki legacy bajtowo nietknięte; kod defensywny.
- **Dowód D′ wg nich samych: n=4 publiczne biegi, śr. ~29,0 vs ~25,77 (SD ~3,93) —
  EFEKT MNIEJSZY NIŻ 1σ**; w patchu czarno na białym: „modest, noisy signal, not a proven
  gain". Nigdy nie biegł na GPU/gatewayu (ich README: „nie uruchamiany w Kaggle").
- Skaza pakietu (kosmetyka, ale pułapka): STARE narzędzia w środku — verify_v17.py/build_v17.py
  z poprzedniej iteracji (oczekują 43 komórki i D′=0010) → **padają na ich własnym nb (8 FAIL)**;
  build_v17_dyn.py ma przestarzałe domyślne ścieżki (wymaga jawnych argumentów).
  Ich verify-summary (54 OK) był z LOKALNEJ kopii r085 (/tmp/bench) — my powtórzyliśmy
  z prawdziwym benchmarkiem z repo: przechodzi.
- Plusy ich builda: komórka „v17 levers" (po biegu liczy 20000 vs 60000 z danych TEGO biegu),
  sonda/metering D′, README uczciwy, rekomendacja armingu 20000 (zgodna z naszym rev2).

### B. Werdykt „czyja v13.7 lepsza" (do decyzji GO usera)
- **Jako kandydat na slot 30.10: nasz rev2.** Powody: (1) nasz ≡ v13.6 na submisji
  (certyfikowane, 3 niezależne audyty), ich = v13.6 + NIEPRZETESTOWANA integracyjnie zmiana
  serwingu działająca na wszystkie 110 gier przez cały bieg; (2) reguła kampanii: slot tylko
  smoke≥26 LUB zweryfikowana dźwignia — D′ nie jest ani jednym (n=4, <1σ; σ powtórek 2,5–3,9 →
  bieg z D′ nieodróżnialny statystycznie od powtórki); (3) c4eeb067 (najsilniejsze pomiary)
  niezależnie: wysyłać JEDEN kandydat = v13.7; główna dźwignia = a/call + pokrycie.
- **Ich D′ = dobry EKSPERYMENT na później** (31.10/1.11): OFF→exact v13.7, jedno-zmiennościowy,
  po naszym biegu 30.10 będzie baseline a/call/pokrycia do atrybucji delta. Decyzja GO usera.
- Feedback do nich (do przekazania): usunąć/poprawić stare tooly w pakiecie (verify_v17.py,
  build_v17.py, domyślne ścieżki) — ktoś inny dostanie 8 FAIL na dobrym notebooku.
