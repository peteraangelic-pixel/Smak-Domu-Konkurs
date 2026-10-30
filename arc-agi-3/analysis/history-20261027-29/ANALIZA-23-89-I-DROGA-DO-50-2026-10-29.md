# Dlaczego 23,89 i co realnie daje 50+ (analiza 28/29.10.2026)

## 1. Fakty po slocie A

| Pozycja | Wartość |
|---|---|
| Slot A `57737623` | **23,89** (COMPLETE) |
| c45 `57629847` (przed fixem) | **0,00** → fix concurrency **działa** |
| duck v3 `57247568` | 26,25 (bez capa, inny mózg) |
| v2-think-less `57125322` | 24,66 |
| v11 = v2-think-less + cap45k/r1 | **23,89** |

LB na 28.10 23:01 UTC: **75,56 · 68,91 · 56,02 · 51,51 · 51,04 · 50,37** · 48,84 · 47,19 …
Czyli 50+ robi 6 zespołów, a próg nagród to ~50. My: 23,89. Luka ≈ **+26 pkt**.

Wniosek 1: **cap45k/r1 kosztuje ~2,4 pkt** (23,89 vs 26,25) i ~0,8 pkt vs sam mózg v2 (24,66).
Wniosek 2: 0,00 c45 nie było problemem strategii, tylko `concurrency=120` przy `MAXREQ=10`. To już zamknięte.

## 2. Matematyka wyniku — gdzie naprawdę tracimy

```
s_l        = min( (H_l / A_l)^2 , 1.15 )        # H = mediana człowieka, A = nasze akcje
game_score = min( Σ_{l≤k} l·s_l / Σ_{l≤n} l ,   # jakość na ukończonych
                  Σ_{l≤k} l / Σ_{l≤n} l )       # ile głębokości ukończono
```

Wagi rosną z numerem poziomu, więc **głębokość dominuje**. Dla gry o 8 poziomach sam wskaźnik
ukończenia daje:

| ukończone k/8 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| score (sufit) | 2,8 | 8,3 | 16,7 | **27,8** | 41,7 | 58,3 | 77,8 | 100 |

- Nasze 23,89 ≈ średnio **~3,5 ukończonych poziomów na grę o 8** (albo 2,5 z 6).
- **50 pkt ≈ średnio 5/8** (41,7) **lub 4/8 przy dobrej efektywności** — czyli **~1,4–1,6× więcej
  poziomów** niż dziś, nie 2×. To wciąż skok o klasę, ale mniejszy, niż wygląda.
- Efektywność akcji **nie jest** wąskim gardłem: na ukończonych poziomach mamy 8,6 akcji/poziom
  przy 10,4 człowieka, więc `s_l` siedzi na suficie 1,15. Kara kwadratowa nie boli — **boli brak
  poziomów**.

### 2.1. Gdzie dokładnie tracimy — ogon, nie środek

Smoke v11 (te same 10 gier co zawsze):

| gra | poziomy | % wagi | score |
|---|---|---|---|
| ka59 | 5/7 | 53,6 | 28,66 |
| dc22 | 4/6 | 47,6 | 42,01 |
| sc25 | 4/6 | 47,6 | 46,06 |
| su15 | 5/9 | 33,3 | 33,33 |
| m0r0 | 2/6 | 14,3 | 11,48 |
| s5i5 | 2/8 | 8,3 | 8,33 |
| cn04 | 1/6 | 4,8 | 4,76 |
| tn36 | 1/7 | 3,6 | 3,57 |
| ls20 | 3/7 | 21,4 | 7,25 |
| g50t | **0/7** | 0,0 | **0,00** |

Połowa gier jest już blisko 50% głębokości. Cały wynik zabija **ogon**: g50t 0, cn04 1, tn36 1.
A `ARC3_LEVEL_TOKEN_CAP=45000` + `MIN_DONE=0` **celuje dokładnie w ten ogon** — porzuca grę, która
nie zrobiła jeszcze pierwszego poziomu. Dlatego cap obniżył wynik, mimo że „oszczędza tokeny”.

## 3. Budżet czasu i równoległość — ukryta zmienna, która może tłumaczyć część straty

Z kodu linii Franzena (`duck-c45`, cell 22) i z logu r050 wynika twarde ograniczenie:

| Parametr | Wartość | Skąd |
|---|---|---|
| Budżet notebooka | **32400 s = 9 h** | asercja `target.max_runtime_s == 32400` w c45 |
| Gier w rosterze | **80 = 25 publicznych + 55 prywatnych** | §1 KOMPENDIUM; komentarz w c45 mówi 110 (nieaktualny) |
| `max_runtime_s_per_game` (stock Tufa) | **7920 s = 2,2 h** | r050: `HarnessSolver(... max_runtime_s_per_game=7920.0)` |
| `concurrency` (stock Tufa) | **28** | r050: `concurrency=28` |
| `concurrency` (nasz v11) | **10** | fix po 0,00 c45 (SGLang `MAXREQ=10`) |

Konsekwencja: przy 80 grach i `concurrency=28` mieszczą się **3 fale × 2,2 h ≈ 6,3 h** — z zapasem
w budżecie 9 h. Przy `concurrency=10` i capie 45k gra kończy się szybciej (cap + RESET), więc 80 gier
też się mieści — ale każda dostaje mniej tokenów, a bez capa 8 fal × 2,2 h = 17,6 h nie zmieściłoby się.

**To jest druga (obok modelu) różnica między nami a Tufą: nie tylko mózg, ale i szerokość
równoległości.** Linia 27B (v13) dziedziczy po stocku 28 równoległych gier i 2,2 h na grę — czyli
~2,8× większy udział GPU na grę niż v11 przy 10 lane'ach. To może być warte więcej niż sam model.

Uwaga pomiarowa: smoke v13 (10 gier, `concurrency=10`, 48 min/grę) daje **podobny budżet na grę**
jak realny rerun (2,2 h przy 28 streamach ≈ 47 min przy 10), więc jest uczciwym estymatorem.

### 3.1. Dwie hipotezy wyjaśniające 23,89 — i dlaczego v13 jest odporne na obie

| Hipoteza | Mechanizm | Co przewiduje |
|---|---|---|
| **H1: pokrycie** | 80 gier, 10 lane'ów, 2,2 h/grę bez capa = 8 fal × 2,2 h = 17,6 h > 9 h → część gier **w ogóle nie jest grana** (score 0) | real ≈ (pokryte gry × ~47) × pokrycie/80 ≈ 24 |
| **H2: jakość** | wszystkie gry zagrane po ~67 min, średnia głębokość ~3,5/8 | real ≈ smoke + trochę czasu ≈ 24 |

Obie dają ~24, więc **samego LB nie da się rozstrzygnąć** — potrzebny log reruna (Submissions →
57737623 → Logs: ile gier, ile akcji na grę). Ale wniosek praktyczny jest ten sam:

- v13 (stock 28 lane'ów, 2,2 h/grę, bez capa) → 80/28 = **2,9 fali × 2,2 h = 6,3 h < 9 h**,
  czyli **wszystkie gry mieszczą się w budżecie niezależnie od tego, czy scheduler rotuje**.
- `nocap` na fast-line (10 lane'ów, bez capa) → 17,6 h → **ryzyko H1 w najgorszej formie**.
- `cap90` (90k/r1) → ~28 min/grę → ~190 slotów w 9 h → pokrycie bezpieczne.

Dlatego fallbackiem nie powinien być `nocap`, tylko **`cap90`**; a v13 jest jedynym wariantem, który
poprawia **i model, i pokrycie** bez dodatkowego ryzyka.

## 4. Trzy dźwignie i ile są warte

| Dźwignia | Mechanizm | Oczekiwany efekt | Koszt | Status |
|---|---|---|---|---|
| **M — model** (27B FP8 zamiast małego fast-line) | więcej „rozumienia” na token; Tufa robi 68,91 na 27B | **+10…+30** (nieznane) | 1 slot + ~1 h smoke | **test w toku (v13)** |
| **N — brak capa** (`cap=0`, stock) | nie zabija ogona; wraca do poziomu v3 | **+2,4** (23,89 → ~26,3) | 1 slot | gotowe (`nocap`) |
| **P — plan-commit / world model** | mniej zmarnowanych akcji po błędnej hipotezie; RGB Agent tak doszedł do 58,12% na preview | **+2…+6** (hipoteza) | 1 slot | gotowe (`duck-v12-plan`) |

Tufa w swoim write-upie pisze wprost: **„solvability zależy od modelu, koszt od harnessu”**.
Nasza fast-line ma 528 tok/s, linia 27B ~33 tok/s na strumień — i to jest cała różnica: my
kupiliśmy 16× więcej tokenów za cenę mózgu, a wynik płaci się za **głębokość**, nie za tokeny.

## 5. Eksperyment v13 (27B) — co dokładnie leci

- Pakiet: `arc-agi-3/kaggle/duck-v13-27b/` → kernel **`petersharps/arc3-duck-v13-27b`** v1.
- Baza: **stock notebook Tufa Labs** (Qwen3.6-27B-FP8, vLLM, REPL + obrazy siatki, kontekst evict).
- Zmiany **tylko** smoke'owe: filtr 10 znanych gier, 48 min/grę, `concurrency=10`.
  Zero capa, zero world-model, zero plan-commit — **jedna zmienna: model**.
  W realnym rerunie (`TRUE_SUBMISSION=1`) wracają ustawienia stock: `concurrency=28`, 2,2 h/grę.
- Tryb: **Save & Run** (bez submitu, bez slotu).
- Odczyt: `summary.txt` w outpucie (`mean score`, per-game), plus `V13_SMOKE_BEGIN/END` w logu.
- Bramka (zrewidowana, bo smoke ma ±9 pkt szumu i mierzy tylko 10 gier preview):
  - smoke ≥ 25 **i** zero crashy → **B = v13** (model + 28 lane'ów; jedyna droga do 50+);
  - smoke 15–25, run czysty, ≥3 gry z poziomem → **B = v13** mimo wszystko: to jedyny stack
    z dowodem 68,91, a `nocap` daje ~26,3 (czyli max +2,4);
  - smoke < 15, crash albo `levels=0` w większości gier → **B = `nocap`**, 27B odłożone.
- Uczciwie: v13 mierzy 10 gier preview, a LB liczy prywatny roster 110 gier — smoke nie jest
  doskonałą próbką, jest tylko kontrolą „czy stack żyje i ile robi poziomów na grę”.

## 6. Plan slotów po A = 23,89 (bramki z planu, zaktualizowane)

| Slot | Data (UTC) | Wariant | Pytanie | Keep jeśli |
|---|---|---|---|---|
| **B** | 29.10 | v13-27b **albo** `nocap` (wg smoke) | czy model 27B bije fast-line? | ≥ 26,3 |
| **C** | 30.10 | zwycięzca B + `PLAN_COMMIT=1` (i `cap90` tylko jeśli B ma cap) | czy plan-commit dokłada? | ≥ B + 2 |
| **D** | 31.10 | finalista + **publiczny** notebook | eligibility | must |
| **E** | 1.11 | finalna submisja | — | — |
| **F** | 2.11 | bufor | — | — |

Bramka twarda: **nie wysyłać wariantu, który na smoke jest gorszy o > 9 pkt** (to już nie szum).

## 7. Uczciwa ocena 50+

- 50 pkt wymaga ~1,4–1,6× więcej poziomów na grę. Model 27B to jedyna dźwignia tej skali,
  jaką mamy, i **nie wiemy, czy zadziała na tym sprzęcie** (33 tok/s/strumień, 9 h, 110 gier).
- Realny scenariusz: **B 26–32, C 28–35**. 50+ tylko jeśli 27B okaże się jakościowo tak dobry
  jak u Tufy — wtedy B może wskoczyć na 40–55 i wtedy C z plan-commit ma sens.
- Prawdopodobieństwo ≥ 50 do 2.11: **~10–15%** (wzrost z ~5%, bo mamy nazwany, testowalny powód
  straty 45 pkt: model, nie harness). To nie obietnica — to jedyna droga, jaka została.

## 8. Rust + rayon — gdzie ma sens, a gdzie nie

- **Ma sens**: replay/scoring po `*_events.jsonl` (segmentacja, RHAE, symulacja cap/reset/abandon
  na tysiącach wariantów w sekundach) — 16 rdzeni 5950X wystarczy z zapasem. Zastąpiłby
  `analysis/replay_level_budget.py`, który dziś chodzi w minutach.
- **Nie ma sensu**: inferencja (CPU ~1–3 tok/s) i „przeszukiwanie” gier bez modelu — polityka nie
  tworzy nowych rozwiązań poziomów, tylko przesuwa tokeny. Przy naszej diagnozie (ogon + model)
  replay w Rust **nie podniesie wyniku**; podniesie tempo decyzji, gdy wariantów będzie > 20.
- Decyzja: włączamy dopiero, gdy będzie > 10 wariantów do przeliczenia; wcześniej to strata czasu,
  którego zostało 4 dni.
