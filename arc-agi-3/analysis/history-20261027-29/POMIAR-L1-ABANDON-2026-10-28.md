# POMIAR L1 (ABANDON) — 28.10.2026

> Cel: zastąpić symulację „+5–7 pkt" pomiarem na **realnym trace c45**.
> Źródło: `kaggle/ops/results/r085-kernel_output_pick/output-pick/benchmark.json`
> (10 gier, 1 pass, 11:34:10 → 12:22:16; sumy `generated_tokens` z `history`).
> Narzędzie: `analysis/replay_level_budget.py` — replayuje `LevelBudget` z patcha
> 0004, czyli **ten sam kod, który jedzie w notebooku**, na zaobserwowanych
> sekwencjach tokenów i granicach poziomów (`actions_per_level`).

## 1. Walidacja replayu (zanim wyciągnięto wnioski)

Konfiguracja kontrolna c45 (`cap=45k, resets=1`) przewiduje auto-RESET w:

| gra | przewidziany RESET | rzeczywiste RESET w trace | zgodność |
|---|---|---|---|
| tn36 | 106 | 77, **106**, 168 | dokładna |
| dc22 | 101 | **101** | dokładna |
| s5i5 | 33, 70 | **33**, 68 | 33 dokładna, 70 vs 68 |
| m0r0 | 247 | 249 | ±2 |
| sc25 | 178 | 125, 160, **182** | ±4 |
| ls20 | 148 | **146**, 303 | ±2 |
| su15 | 36 | **34**, 101 | ±2 |
| g50t | 33 | **31** | ±2 |
| cn04 | — | 0 (warmup) | — |
| ka59 | — | — | — |

Pozostałe RESET-y w trace to resety agenta, nie budżetu. **Wniosek: replay
odtwarza decyzje budżetu z dokładnością 0–4 akcji, więc model tokenów jest
dobry.** To nie jest re-run — to kontrfaktyczna symulacja na zaobserwowanym
przebiegu.

## 2. Koszt tokenowy poziomów (realny trace)

| gra | ukończone poziomy (tokeny) | poziom nieukończony | max ukończony |
|---|---|---|---|
| tn36 | 6 776 | 88 977 | 6 776 |
| m0r0 | 18 907 · 13 225 · 34 405 · 29 001 | 48 503 | 34 405 |
| cn04 | 36 741 · 38 214 · 27 200 · 18 364 · 27 453 | 2 291 | 38 214 |
| dc22 | 25 204 · 66 607 · 41 255 | 12 263 | 66 607 |
| ka59 | 10 561 · 30 656 · 27 613 · 38 606 · 20 933 | 18 952 | 38 606 |
| sc25 | 44 441 · 14 207 · 30 524 | 50 806 | 44 441 |
| s5i5 | 14 018 · 65 010 | 78 385 | 65 010 |
| ls20 | 11 875 · 62 017 · 44 369 | 14 151 | 62 017 |
| su15 | 11 857 · 68 648 · 31 963 | 40 634 | 68 648 |
| g50t | **88 114** · 23 941 · 39 521 | 0 | **88 114** |

**Maksymalny ukończony poziom kosztował 88 114 tokenów (g50t L1).** Poziomy,
które „wyglądają na martwe", często są po prostu trudne i później kończone:
su15 L2 68,6k, dc22 L2 66,6k, s5i5 L2 65k, ls20 L2 62k.

## 3. Sweep ABANDON (resets=0)

| cap | min_done | ubite gry | utracone poziomy | zaoszczędzone tokeny | gry |
|---|---|---|---|---|---|
| 45k | 0 | 8 | 10 | 441 067 | tn36 0, m0r0 0, dc22 −2, sc25 0, s5i5 −1, ls20 −2, su15 −2, g50t −3 |
| **60k** | **0** | **6** | **10** | **384 218** | tn36 0, dc22 −2, s5i5 −1, ls20 −2, su15 −2, g50t −3 |
| 75k | 0 | 3 | 3 | 83 843 | tn36 0, s5i5 0, g50t −3 |
| 88 114 | 0 | 2 | 3 | 63 554 | tn36 0, g50t −3 |
| 90k | 0 | 0 | 0 | 0 | — |
| 60k | 1 | 5 | 7 | 299 524 | tn36 0, dc22 −2, s5i5 −1, ls20 −2, su15 −2 |
| **75k** | **1** | **2** | **0** | **16 338** | tn36 0, s5i5 0 |
| 90k | 1 | 0 | 0 | 0 | — |

Suma trace: **32 poziomy, 1 417 188 tokenów**.

## 4. Sweep RESET (resets=1, czyli tryb kontrolny)

| cap | resety | porzucenia |
|---|---|---|
| 45k (kontrola) | 9 | 0 |
| 60k | 7 | 0 |
| 75k | 3 | 0 |
| 88 114 | 2 | 0 |
| **90k** | **0** | **0** |
| 105k | 0 | 0 |

Podniesienie capa przy `resets=1` **nie porzuca żadnej gry** — tylko usuwa
resety. To czysta subtrakcja mechanizmu, nie nowy mechanizm.

## 5. Wnioski

1. **L1 ABANDON@60k nie jest kandydatem.** Na realnym trace ubija 6/10 gier
   i traci 10/32 poziomów, oszczędzając 27% tokenów. Koszt jest zmierzony;
   korzyść (realokacja w kolejce 110 gier) **nie** — smoke ma 10 gier = 10
   slotów, więc nie ma do kogo realokować.
2. **Założenie „martwe gry" jest na tym trace fałszywe.** Najdroższe poziomy
   są często kończone (g50t L1 88k, su15 L2 68,6k, dc22 L2 66,6k, s5i5 L2 65k,
   ls20 L2 62k). Cap per poziom nie odróżnia „trudny, ale postępuje" od
   „beznadziejny". To ta sama klasa błędu (zła populacja), którą tamta opinia
   słusznie zarzuciła modelowi capa.
3. **Jedyny nie-destrukcyjny abandon to 75k/min_done=1:** 2 gry ubite,
   0 poziomów straconych, 1,1% tokenów. Za mało, by samodzielnie uzasadnić slot.
4. **Cap90/resets=1 to najlepszy wariant env-only:** zachowuje wszystkie
   zaobserwowane ukończone poziomy (max 88 114), usuwa wszystkie 9 resetów,
   nie porzuca nikogo, a bezpiecznik ABANDON zostawia dopiero przy 180k.
5. **`ARC3_ABANDON_TOKENS` jest martwy** w tym drzewie: należy do patcha 0003,
   który 0004 zastąpił. Realna dźwignia to `CAP` + `RESETS_MAX` + `MIN_DONE`.

## 6. Czego ten pomiar NIE rozstrzyga

- **Strony korzyści abandon w kolejce 110 gier.** Smoke nie ma kolejki.
  Dopiero slot na żywym rosterze może pokazać, czy wcześniejsze zwolnienie
  slotu daje więcej poziomów, niż zabiera.
- **Kontrfaktu bez resetów.** Replay zakłada tę samą sekwencję tokenów; bez
  resetu agent mógłby zachować się inaczej. To ograniczenie każdego replayu.
- **Wpływu na score.** Podajemy poziomy i tokeny, nie punkty: score nie jest
  liniowy w poziomach.

## 7. Rekomendacja slotów (na podstawie pomiaru)

- **A:** kontrola `c45fix` (cap 45k/resets 1, `PLAN_COMMIT="0"`) — czy fix
  concurrency w ogóle punktuje.
- **B:** **sam `PLAN_COMMIT="1"`** (cap 45k/resets 1) — jedyna dźwignia
  celująca w liczbę poziomów, nie w redystrybucję tokenów.
- **C:** jeśli B ≥ A + 3 → dołóż `cap90`; jeśli B < A → `cap90` jako fallback.
- **Nie wysyłać** `duck-v11-c45-abandon` (60k/r0) — to negatywna kontrola.
- **L3 probe:** odłożyć — nowy kod w pętli agenta, a pomiar wskazuje, że
  bottleneckiem są trudne poziomy, nie ślepe otwarcia.

## 8. Odtworzenie

```powershell
$env:PYTHONUTF8="1"
python analysis\replay_level_budget.py --sweep
python analysis\replay_level_budget.py --cap 60000 --resets 0 --min-done 0
python duck-v11-c45\tools\verify_env_variant.py --pkg duck-v11-c45-cap90
# pełny łańcuch patchy na czystym r033 + testy logiki commit(plan):
python duck-v11-c45\tools\verify_v11.py `
  --bundle kaggle\ops\results\r033-recon-bundle\bundle --tests
```

Ostatnia komenda: **5/5 patchy aplikuje się, drzewo kompiluje, 9/9 testów
logiki przechodzi**; 3 testy sandboxu są pomijane na Windows (sandbox nie
startuje — ograniczenie środowiska, nie logiki).
