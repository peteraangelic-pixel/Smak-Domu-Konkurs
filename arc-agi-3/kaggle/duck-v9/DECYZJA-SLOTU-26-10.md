> **ZAWIESZONE 25.10 12:50 UTC — DECYZJA TYLKO PO WYRAZNYM GO USERA.**
> Zasada stala (user 25.10): ZADNE pushe kerneli ani submity bez sygnalu, bo nad agentem pracuja rownolegle inne AI i wyniki trzeba porownac. Tryb.monitorowania = tylko odczyt (lb/submissions/status/kernel-output).

# ANALIZA SMOKE c45 (r076) -> decyzja slotu 26.10
- smoke 10x48min: MEAN 26.78 (v3=29.02, v6=27.21); rerun 2.2h/gra = wiecej glebokosci; LB c45 ~21:30 = prawdziwy pomiar.
- ZYSKI (cap dziala): cn04 71.4 (47.6), m0r0 46.3 (28.6), ka59 49.9 (17.9), ls20 8.8 (3.3).
- STRATY (cap tnie dlugie poziomy): su15 13.3 (56.4!), sc25 17.1 (42.6), dc22 27.7 (44.8).
- tok/act 828 (=841); a/call 4.73 (batching nie ruszony).
- DECYZJA 26.10 (po LB c45 ~21:30): LB c45 >= 29 -> v9 profil c45-faithful; LB < 29 -> v9 profil c45 z ARC3_LEVEL_TOKEN_CAP=0 (usuwa podejrzanego regresu su15/sc25). deep/wide -> 27.10+.

## AKTUALIZACJA 25.10 ~15:00 UTC (po zwiadle e499c604 + weryfikacji Areny)
- **v9 w obecnej formie NIE WCHODZI na slot**: kom.5 (patch 498 799 znaków) kończy się BEZ końcowego newline;
  `%%writefile` pisze dosłownie -> kom.10 `git apply ... check=True` -> `corrupt patch at line ~10087` -> śmierć
  przed serwerem (potwierdzone statycznie przez Arenę: reprodukcja błędu na bundlu r033; runtime-certificate: r081).
  UWAGA: patch NIE jest ucięty mid-hunk — z dodanym newline przechodzi `git apply --check` czysto (16 plików,
  kompletne hunks); problem = WYŁĄCZNIE brak końcowego znaku nowej linii (verify_offline dodawał go sztucznie -> fałszywy pass).
- **Kandydat na slot 26.10 = v10 (e499c604)**: commit(plan) z weryfikacją per krok + eskalacja 60 akcji; patch
  odbudowany z drzewa da-fr w chunkach <400k + sha256 w runtime; verify.py ALL PASS; testy jednostkowe 9/12 offline
  (3 wymagają runtime-stacku); metadata = zestaw c45-proven; SHA256SUMS "FAILED" = artefakt CRLF uploadu (po tr -d '\r' zgadza się).
- **Bramka profilu deep (korekta c87f7a48, przyjęta): GO = wzrost LICZBY POZIOMÓW, nie a/call** (a/call koreluje
  odwrotnie: ls20 13.89->score 3.27; su15 1.85->56.42).
- Wszystko CZKA NA GO USERA (zasada 25.10). Pre-GO checklist v10: (a) potwierdzić status v9 = ERROR (r081),
  (b) ewent. verify.py --pristine na drzewie da-fr, (c) decyzja usera v10 vs hotfix-v9-vs-c45-faithful.
