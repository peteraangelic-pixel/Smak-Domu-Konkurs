# OCENA pakietu DeepSeek "candidate-45" (SPis.txt + arc3-duck-c45.ipynb) — Arena, 24.10 ~22:00 UTC

## Werdykt: PRZYJETY do pipeline'u (slot 25.10), po 1 wymaganej poprawce (zastosowana)
**Ocena ogolna: 4.5/5** — najlepiej przygotowany pakiet od jakiejkolwiek sesji: kod + testy + kill-switche
+ uczciwe "nie ma tu 45". Do uzycia JUTRO po smoke G1.

## Co zweryfikowalem w kodzie (nie w opisach)
1. **WORLD_MODEL=0/NUDGE=0** (banner+ARC3_VARIANT) — mechanizm, ktory OBIZYL v5(23.94), jest OFF. OK.
2. **LEVEL_TOKEN_CAP=45000 + LEVEL_RESETS_MAX=1** aktywne (kom.21/ARC3_VARIANT); ABANDON_TOKENS=0
   (game-abandon OFF — bezpieczniej niz v7: autopsja v6 = gave_upy od budzetu, nie bugi).
3. **USE_PRIORITY_SCHEDULING=True jest TEZ w duck-v7** — czyli w linii, ktora dala LB 24.66/26.25/23.94
   => to status quo linii, NIE nowa zmienna w G2 (brak konfundowania cap+scheduler).
4. **MAXREQ=10 w launcherze (kom.17)** — NIE podbite do 16 (zgodnie z runbookiem: G3b pozniej). Konservative. OK.
5. **Sonda rosteru (kom.21)**: hook w try/except (nie zabije runu), loguje start/end z hashem 1. ramki;
   analyze_roster.py rozroznia repliki (cross game_id) od passow (same game_id) — madre; w smoke (10 gier,
   n_passes=4) zmierzy tylko passy — prawdziwy werdykt CYCLIC/DISTINCT przyjdzie Z DARMOWO z reruna 110 gier G2.
6. **Smoke ograniczony konfiguracja wariantu** (10 gier x 48 min, concurrency 10) — nie placi kwoty jak
   martwy guard w duck-original. PASSy n_passes=4 w smoke = wiecej sygnalu.
7. **BRAKI złapane** (=> poprawka zastosowana): TAAF_MINIMAL_DIAGNOSTICS warunkowe (0 w smoke) —
   dokladnie ta konfiguracja zabijala v2/v4/v7 (~25-35 min, firehose); v5 z minimal-diag ALWAYS przetrwal
   2h12m. FIX: ustawione ALWAYS (komentarz petersharps w kom.9).
8. **KAGGLE_GPU_TYPE autodetect nieobecny** — akceptowalne, bo metadata pinuje RTX6000 (assert default
   'rtx-pro-6000' przechodzi). Metadata utworzona: petersharps/arc3-duck-c45, title=slug (regula!), pin+docker z v5.

## Dwie korekty do ich twierdzen
- "game_weights tylko diagnostyka" — potwierdzam (benchmark.py), juz wycofane w CROSS-SESSION-VERDICTS.
- "SCOPE przyjmuje tylko turn|levelup|game" — kierunkowo tak (zgodne z korekta z 24.10), ale w moim grepie
  r033 nie zlapalem miejsca walidacji — do potwierdzenia przed G3a (patch pamieci i tak trzeba pisac).

## Bramka decyzyjna na 25.10 (moja korekta runbooka)
Rano ~07:00 UTC LB v5 (#57607527). Potem:
- **LB v5 >= 47 (strefa nagrod)** => G2 z ARC3_LEVEL_TOKEN_CAP=0 (kill-switch z kom.21): score ~v5 chroniony,
  sonda dowozi roster-data za darmo; cap jako osobny pozniejszy pomiar.
- **LB v5 < 45** => G2 z cap=45000 (swing w gore; downside ograniczony — 1 slot).
W obu wariantach: push c45 rano -> smoke (~2h) -> COMPLETE -> submit po 12:00 UTC -> LB ~22:00 UTC.
26.10+: CYCLIC => patch pamieci miedzy replikami (x4.4); DISTINCT => MAXREQ=16.

## Ryzyka resztkowe
- Builder-lineage (format 30-komorkowy) mial 2 crashe ~25 min (v7, v8) — v8 to byl jednak pipeline ducka z
  naszymi hackami, nie czysty build; minimal-diag ALWAYS + smoke G1 strzela ryzyko. Jesli G1 padnie — log
  (teraz maly) da przyczyne w 1 iteracje.
- Patch 498 KB (kom.4) aplikowany runtime — jesli apply padnie, run umiera szybko i tanio (smoke to wyłapuje).
- Sonda: hash 1. ramki zalezny od serializacji stanu — stabilnosc hashy miedzy runami potwierdzi G2;
  analyze_roster i tak liczy repliki per (hash, game_id) tolerancyjnie.
