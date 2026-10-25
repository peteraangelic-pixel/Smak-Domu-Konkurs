# OCENA V11 (Arena, 25.10 ~17:30 UTC) — ZWERYFIKOWANY OFFLINE, GOTOWY DO SLOTU PO GO

## Certyfikacja (bez GPU, ~15 min)
- [x] NOTEBOOK PARSUJE (po naprawie transportu: zip mial CRLF wewnatrz stringow JSON -> raw-LF w stringach ->
      strict parse FAIL na ich pliku; naprawa: strict=False -> kanoniczny re-dump -> strict PASS. ZAWARTOSC bez zmian semantycznych.)
- [x] 31 komorek; patch w 2 chunkach (380 000 + 279 896 znakow) < sufit 498 799 (lekcja v9)
- [x] sklejka cat-style part-00+part-01: sha256 **54768e2f...** = zapisany w ARC3_VARIANT (zgodnosc 1:1)
- [x] **git apply --check PASS** na czystym bundlu r033 (pelny patch 659 896 B, 24 pliki da-fr)
- [x] kom. 21 (TRUE_SUBMISSION): `bm.solver.concurrency = 10` + `os.environ["ARC3_MAX_ACTIVE_STREAMS"]="10"`
      + komentarz "match backend MAXREQ=10; avoid 120-way fanout"; runtime 532 min/grę — FIX OBU DZWIGNI ✓
- [x] metadata: id=title=arc3-duck-v11-plan-safe; zrodla = zestaw c45-proven (dfranzen x4) + competition + docker pin + RTX6000
      (poprawione CRLF->LF przed pushem)
- [x] PROFILE="plan" (opcje: c45|deep|wide|plan|plan-esc); commit(plan) + eskalacja 60 akcji dziedziczone z v10
- [x] ARC3_SMOKE_OK gate i sonda rosteru zachowane z v10

## Uwagi Areny (nie blokujace, do decyzji z GO)
1. **Atrybucja slotu**: PROFILE=plan = fix concurrency + PIERWSZY pomiar commit(plan) w jednym runie.
   Alternatywa: PROFILE="c45" na slot 26.10 (czysty test fixa, izolacja zmiennej) i plan na 27.10.
   Po 0.00 kazdy niezerowy wynik i tak jest postepem — decyzja usera.
2. **Log reruna c45 nadal niepotwierdzony** (tylko przegladarka usera) — README v11 uczciwie to odnotowuje.
3. Puli 173.7k tok/gre broni sie przy 10 grach x ~2.5h (conc=10); przy 110 grach budzet/gre ~ zaleznosc liniowa
   od slotów — tak jak w smoke.
