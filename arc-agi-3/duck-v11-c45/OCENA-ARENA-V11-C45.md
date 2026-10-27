# OCENA ARENA — v11-ex-c45 (pakiet z gałęzi Pokemon a450/c87/7911f950, komit 6c3e958)
Data weryfikacji: 27.10.2026 ~19:55 UTC, offline (piaskownica, bez GPU), na czystym bundlu r033.

## Wyniki (niezależna reprodukcja)
- verify_v11.py --bundle (czysta kopia r033 z git archive):
  - 12 checków statycznych OK (parse 33 komórki, kompilacja, concurrency fix OBECNY, `concurrency = 120` USUNIĘTY,
    extra-03 zarejestrowany, metering obecny, ONLY_RESET_LEVELS, przełączniki PLAN_COMMIT 0/1, metadata id/title/code_file,
    wszystkie /kaggle/input zadeklarowane, 5 patchy wyekstrahowanych),
  - **łańcuch patchy: 5/5 APLIKUJE SIĘ na czystym bundlu + spatchowane drzewo się kompiluje** (decydujący test, który
    v11-Smak PADŁ — Makefile:40 / README.md:1),
- testy plan-commit: 9/12 offline; 3 błędy = importy środowiskowe piaskownicy (dependencies runtime); wg sesji-rodzica 12/12.
- notebook strict-JSON: OK (folderowa wersja; bez problemów transportowych zipa).
- metadata: petersharps/arc3-duck-v11, GPU RTX6000, źródła c45-proven.
- Konstrukcja: baza = c45 (patch 498 KB bajt-ten-co-grał), port commit(plan) = 19,7 KB / 4 pliki (0005), fix concurrency
  przez env ARC3_TRUE_CONCURRENCY (default 10), PLAN_COMMIT="0" domyślnie = kill-switch (slot A = czysty fix, B = commit).

## RETRAKCJE Arena (27.10) — w trosce na wspólne gałęzie
1. **Mój certyfikat v11-Smak ("git apply PASS na r033") był NIEPRAWIDŁOWY.** Na czystym drzewie (git archive z HEAD)
   sklejka v11-Smak pada na ARC3-Inference/Makefile:40 i README.md:1 — z --include i bez. Mój PASS pochodził z
   zanieczyszczonego drzewa roboczego (stan sprzed recyklingu piaskownicy). Reprodukcja c87f7a48 (POROWNANIE-V11-SMAK.md)
   jest WŁAŚCIWA. v11-Smak as-is = ryzyko śmierci komórki środowiskowej na żywym datasecie; do ratunku wymagałaby
   regeneracji patcha na drzewo bundla albo --exclude Makefile/README.
2. **Claim "v9 umrze przed serwerem" (e499 §1, przeze mnie "potwierdzony") jest OBALONY**: komórka patcha 498 799 znaków
   jest bajt-identyczna w v7/c45/v9 (sha 6fdcd1ae...), a c45 z nią PRZESZŁY pełny smoke i rerun na Kaggle ("harness patch
   applied successfully" w logu, r076). c87 zreplikował pełny potok IPython: `run_cell` z %%writefile dopisuje końcowy
   \n. Moja statyczna reprodukcja (git apply na ekstrakcie z JSON) była prawdziwa jako test tekstu, ale błędna jako
   predykcja runtime. Wniosek: nie wydawano by slotu na "naprawę" działającego patcha.
3. Metodyczna uwaga c87 przyjęta: v9_metrics miesza średnią-z-proporcji (5.204) z agregatami (4.357) — bramek a/call nie
   stawiać na tym narzędziu bez ujednolicenia mianowników.

## Werdykt slotu (rekomendacja Arena, decyzja = GO usera)
**Kandydat nr 1 na następny slot = v11-ex-c45** (jedyny pakiet, którego przeżycie komórki środowiskowej jest dowiedzione
na tym samym drzewie, na którym c45 realnie zagrał; fix concurrency w środku; kill-switch PLAN_COMMIT).
Kolejność wg DECYZJA.md tej sesji: slot A (PLAN_COMMIT="0", czysty test fixa) -> slot B (PLAN_COMMIT="1", commit()).
Uwaga krytyczna: smoke NIE testuje ścieżki TRUE_SUBMISSION (smoke szedł concurrency=liczba gier) — prawdziwy werdykt
fixa da dopiero submit; to jest świadome ryzyko slotu A.
v11-Smak (duck-v11/, Codex) = ARCHIWUM/baza mechanizmów; nie pushować bez naprawy patcha.
