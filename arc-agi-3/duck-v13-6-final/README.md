# duck-v13-6-final — slot 30.10 (kandydat, CZEKA NA GO)

**v13.5-consensus + patch 0009 self-pace (Gemma duck-v16, bajt w bajt) + fix martwego
alarmu a/call (c87) + fix testu R085_BENCH (a450) + slug pinned.**
Pełny certyfikat: `OCENA-ARENA-V13-6-FINAL.md`.

## W skrócie

- 40 komórek, 743 616 B; łańcuch **0001–0009** (9 patchy); metadata `petersharps/arc3-duck-v13-6-final`.
- **0009 self-pace**: próg eskalacji z WŁASNYCH ukończonych poziomów gry
  (`clamp(1,5×mediana, 20, 120)`, cap 2) — działa W RERUNIE (baseline human jest ukryty,
  `GameRun.actions_per_level` nie); r085: **22 nudge / 14 przedwczesnych** vs 42/26 dla 20+cap2.
- **Instrument**: bezwarunkowy druk `v13.6 batch: a/call = …` (baza r019 = 4.357; cele
  5,7/7,6; **bramka 7911 ≥6,0** = granica 253 akcji/gry = 50 pkt) zamiast martwego alarmu `< 1.5`.
- Kill-switcze: `ARC3_ESCALATE_SELF_PACE=0`→v13.5 exact; `ARC3_ESCALATE_RELATIVE=0`→floor;
  `ARC3_OPENER_COMMIT_HINT=0`; `ARC3_ESCALATE_MAX_PER_LEVEL=0`; `WINPATH=0`; `DEAD_SKIP=0`;
  `PLAN_COMMIT=0`; `ARC3_LEVEL_TOKEN_CAP=0` (cap OFF); baseline widoczny → relatywny wygrywa (test 3).

## Weryfikacja

`verify_v13.py --bundle r033 --tests` → **ALL CHECKS PASSED**: 9/9 patchy czysty r033,
drzewo kompiluje, 12 plan-commit + 6 escalate + 11 winpath na spatchowanym drzewie,
self-pace 22/14 z kodu patcha (fixtures == shipped), sondy stub, playbook bajt-w-bajt,
serving nietknięty. ENV wymagane do testów: `PYTHONPATH` z rozpakowanym arcengine (Py≥3.12),
`R085_BENCH=…/r085/benchmark.json`.

## Build

```
python3 tools/build_v136_final.py   # prev = ../duck-v13-5-consensus/arc3-duck-v13.ipynb
python3 tools/verify_v13.py --bundle <r033 bundle> --tests
```

## Uwaga o wersjonowaniu

NIE tworzymy „v18" z warstwy action-efficiency (rekomendacja tamtej sesji, podtrzymana):
na dziś warstwa jest ortogonalna i ma bug niehashowalnych akcji w ConvergedGuard —
integracja = osobna decyzja (propozycja: mały patch win-path po hashu klatki, nie nowa warstwa).
