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

## 3. Znalezisko e499c604 (v9/v7 martwe przed serwerem) — POTWIERDZONE, z korektą mechanizmu
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

## 8. PORÓWNANIE: DZISIEJSZA PRACA ARENY vs V11 CODEX-a (~17:30 UTC; ODTWORZONE — pierwotny wpis zgubił reset --hard, zob. CHAT-LOG)
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
