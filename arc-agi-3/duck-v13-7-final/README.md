# duck-v13-7-final — kandydat na slot 30.10/31.10 (CZEKA NA GO)

**v13.6-final + patch 0010 dyn-level-budget (handoff sesji „strategia"; u nich 0009)
— DORMANT**: na submisji zachowuje się DOKŁADNIE jak v13.6 (`ARC3_LEVEL_TOKEN_CAP="0"`),
uzbrojenie później jedną wartością (60000), kill `ARC3_DYN_CAP=0` → wierny statyczny 0004.
Certyfikat: `OCENA-ARENA-V13-7-FINAL.md`.

## W skrócie

- 41 komórek, 758 240 B; łańcuch **0001–0010** (10 patchy); metadata `petersharps/arc3-duck-v13-7-final`.
- 0010 dotyka TYLKO `framework/arc3_level_budget.py` (plik rozłączny od self-pace w tool_agent.py).
- Po uzbrojeniu: adaptacyjny cap z mediany koszów ukończonych poziomów gry
  (clamp 45k–150k, ×4), drabina RESET ×1,5, ABANDON nigdy ostrzejszy od statycznego.
- Dziedziczy z v13.6: 0009 self-pace (22/14 na r085, działa w rerunie), hint openerowy,
  bezwarunkowy druk `v13.7 batch: a/call` (baza 4.357, bramka 7911 ≥6,0 = granica 50 pkt),
  pokrycie wazone, win-path logi, metering.

## Weryfikacja

- Paczka handoffowa przed kompozycją: 16/16 testów, verify_v16 ALL LOCAL CHECKS PASSED,
  **pending-gate r033 zamknięty przez nas** (9/9 patchy czysty r033, kompilacja, 12+6+11
  naszych testów na ich drzewie, 11/11 winpath), rekonstrukcja == bajty łańcucha (cmp).
- v13.7: `verify_v13.py --bundle r033 --tests` → **ALL CHECKS PASSED** — 10/10 patchy,
  0010: cmp rekonstrukcji z drzewem + 16/16 na bajtach wysyłkowych, self-pace 22/14 1:1,
  dormancja w wariancie, playbook bajt, serving nietknięty.

## Build

```
python3 tools/build_v137_final.py   # prev = ../duck-v13-6-final/arc3-duck-v13.ipynb
python3 tools/verify_v13.py --bundle <r033 bundle> --tests
```

## Uzbrojenie (TYLKO wg GO, proponowany termin 1.11)

`ARC3_LEVEL_TOKEN_CAP: "0" -> "60000"` w komórce ARC3_VARIANT. Wtedy moduł aktywny;
kontrola A/B: `ARC3_DYN_CAP=0` przy uzbrojonym capa = exact statyczny 0004.
