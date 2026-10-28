# v12 = c45 (bajt-proven 26.78 smoke) + WYLACZNIE fix concurrency (2 linie, kom. 21)
- Powstanie 29.10 ~00:20 UTC. Motywacja: v11 (slot A 28.10, #57737623) = LB 23.89, jej smoke 18.55 vs c45 smoke 26.78
  -> rekonstrukcja build_v11/patch 0005/ONLY_RESET dala regresje (cn04 -66.7, m0r0 -34.8, g50t -21.4; wiecej tokenow,
  mniej punktow). v12 = ZERO zmian poza: `concurrency = 10` + `ARC3_MAX_ACTIVE_STREAMS=10` w galezi TRUE_SUBMISSION.
- Oczekiwanie: zachowany smoke ~26.8; LB wg dwoch kalibracji: v3 (29.02->26.25, -2.8) i v11 (18.55->23.89, +5.3)
  => przedzial ~24-32; najbardziej prawdopodobne ~27-31. To NIE jest wersja "50+" — to przywrocenie linii do zdrowia.
- Weryfikacja diff: 1 komorka rozna vs c45 (dokladnie 3 linie). Metadata: id=title=arc3-duck-v12.
- Dalsze lewarki (v13+, PO danych z tego slotu): playbook miedzy grami (110 = klony 25 publicznych wg official_110();
  wymaga potwierdzenia z logu reruna w przegladarce), otwieracze z zrodel gier, deep batching, commit(plan) na c45.
