# Werdykt Arena (25.10 12:45): v9 ZWERYFIKOWANY 43/43 na prawdziwych artefaktach — slot 26.10
- verify_offline --bundle r033 --r019: 43/43 OK (patche aplikuja sie na czysty bundle, drzewo sie kompiluje, formula odtwarza r019 co do 0.0000, mean 27.21).
- v9_metrics dziala na r019: per gra actions/calls/tok/w%/score + GATE vs 29.02.
- Metadata v9 = fast-line Franzen (duck-v7 wzor) — zgodna z notebookiem. title=slug OK.
- **Samo-korekta Arena**: a/call = **5.2** (analizator liczy wywolania produkujace akcje; moje 1.13 = artefakt liczenia LINII w requests.jsonl, tam tez sa wywolania analizatora). T2: bramka ">=3" juz spelniona -> batching testujemy profilem **deep** (dyrektywa 8-15/call) w slot 26.10/27.10 — tanio, mierzalnie.
- Plan: c45 LB ~21:30 dzis -> 26.10 slot: v9 profile deep (jesli c45 smoke/lb OK) -> 27.10: wide albo T2-pelne -> 28+: T3 (paper01 port).
- Pakiet w arc-agi-3/kaggle/duck-v9 (z arc-agi-3/new, user upload 9fb6641).
