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
