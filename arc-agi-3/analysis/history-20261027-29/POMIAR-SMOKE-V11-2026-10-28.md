# Slot A (v11) — smoke, submit, i ile wart jest smoke

Data: 28.10.2026. Autor: sesja DeepSeek. Status: slot A **wysłany**, wynik LB w toku.

## 1. Co dokładnie poszło na Kaggle

| Element | Wartość |
|---|---|
| Kernel | `petersharps/arc3-duck-v11`, wersja **1** (push 12:05:54 UTC) |
| Konfiguracja | env **identyczny z c45**: `ARC3_LEVEL_TOKEN_CAP=45000`, `RESETS_MAX=1`, `MIN_DONE=0`, `LEVEL_NOTES=1`, `EXPERIMENT_HINT=1`, `STUCK_AUDIT_TOKENS=60000`, `WORLD_MODEL=0`, `PLAN_COMMIT` nieustawiony |
| Jedyna różnica vs c45 | `bm.solver.concurrency` w TRUE_SUBMISSION: **120 → 10** (`ARC3_TRUE_CONCURRENCY=10`, bo serwer ma `MAXREQ=10`) |
| Smoke | 10 gier × 48 min, start 12:05:54, koniec 13:06:36 UTC, `KernelWorkerStatus.COMPLETE` |
| Werdykt smoke | **`ARC3_SMOKE_OK`** (10 gier, 1 521 961 tok, 2 297 akcji, `crashed=[]`) |
| Średnia smoke | **18,54** (waga 23,4%, 27/69 poziomów, 232/718 akcji = 32,3% pełnego przejścia) |
| Gate w notebooku | `v11 gate: NO-GO (below v3 smoke 29.02)` |
| Submit | **ref `57737623`**, 13:11:56 UTC, rc=0, „0 submissions remaining today” |
| Stan | `SubmissionStatus.PENDING` (13:13:25 UTC) |

Hipoteza slotu A (z planu): *czy fix concurrency naprawia 0,00 c45?* Smoke tej ścieżki **nie dotyka** —
w smoke `concurrency = len(games) = 10`, więc linia `ARC3_TRUE_CONCURRENCY` nigdy się nie wykonuje.
Dlatego werdykt A daje wyłącznie leaderboard.

## 2. Smoke v11 vs smoke c45 — ten sam kod, dwa różne wyniki

Oba pakiety mają **identyczny `ARC3_VARIANT.env`**; c45 nie ma patcha 0005 (plan-commit), a w v11 patch 0005
jest inertny przy `ARC3_PLAN_COMMIT` nieustawionym. Smoke nie używa też linii concurrency.
Wniosek: to **dwa przebiegi tego samego kodu**.

| gra | c45 lv | c45 score | v11 lv | v11 score | Δlv | Δscore |
|---|---:|---:|---:|---:|---:|---:|
| tn36 | 1 | 3,57 | 1 | 3,57 | 0 | 0,00 |
| m0r0 | 4 | 46,26 | 2 | 11,48 | −2 | −34,78 |
| cn04 | 5 | 71,43 | 1 | 4,76 | −4 | −66,67 |
| dc22 | 3 | 27,68 | 4 | 42,01 | +1 | +14,33 |
| ka59 | 5 | 49,87 | 5 | 28,66 | 0 | −21,21 |
| sc25 | 3 | 17,12 | 4 | 46,06 | +1 | +28,94 |
| s5i5 | 2 | 8,33 | 2 | 8,33 | 0 | 0,00 |
| ls20 | 3 | 8,79 | 3 | 7,25 | 0 | −1,54 |
| su15 | 3 | 13,33 | 5 | 33,33 | +2 | +20,00 |
| g50t | 3 | 21,43 | 0 | 0,00 | −3 | −21,43 |
| **suma / średnia** | **32/69** | **26,78** | **27/69** | **18,54** | **−5** | **−8,24** |

Statystyka różnic (10 gier, pomiar sparowany):

- poziomy: średnia **−0,50 ± 0,60** (SD 1,90), **t = −0,83** → nieistotne
- score: średnia **−8,24 ± 9,03** (SD 28,54), **t = −0,91** → nieistotne
- kierunek: 3 gry lepiej, 3 gorzej, 4 bez zmian

**Wniosek: 18,54 vs 26,78 to szum, nie regresja.** Sampling: `LOCAL_ANALYZER_TEMPERATURE=0.7`,
`TOP_P=0.95`, brak seeda → przebieg jest stochastyczny, a 10 gier to za mała próba.

## 3. Co to znaczy dla decyzji (ważniejsze niż sam slot)

1. **Smoke przestał być gate'em.** Przy efekcie, którego szukamy (±3 pkt), pojedynczy smoke 10 gier ma
   SE ≈ 9 pkt na score. „NO-GO poniżej 29,02” **nie odrzuca** wariantu — i odwrotnie, smoke 30 nie
   potwierdza poprawy. Wszystkie wcześniejsze porównania smoke-vs-smoke (26,78 vs 29,02 itd.) są w szumie.
2. **Jedynym arbitrem pozostaje LB**, czyli 1 slot dziennie. To ogranicza tempo eksperymentów do 1/dzień
   i czyni plan A/B/C bardzo kosztownym: każda bramka „B ≥ A + 3” wymaga **dwóch** pomiarów LB.
3. **Żeby smoke miał moc**, trzeba albo (a) ustalić `LOCAL_ANALYZER_SEED` i grać deterministycznie,
   albo (b) uruchamiać ten sam wariant 3× i porównywać średnie, albo (c) zwiększyć liczbę gier w smoke.
   Bez tego nie warto płacić 48 min GPU za smoke przed każdym slotem — wystarczy `ARC3_SMOKE_OK`
   (health: brak crashy, tokeny > 0, akcje > 0).
4. **c45 = 0,00 ma teraz nazwaną przyczynę**: `concurrency=120` przy serwerze `MAXREQ=10`. To nie była
   zła strategia, tylko przeciążenie serwera — dlatego smoke (concurrency=10) wyglądał zdrowo.

## 4. Czego pilnować dalej

- `57737623`: PENDING → COMPLETE/ERROR + publicScore. To werdykt slotu A.
- Bramka z planu: A = 0,00 → **stop**, diagnoza logu reruna przed slotem B; A > 26,25 → zielone światło na B.
- `kernels status` **nie pokazuje** reruna konkursowego (po submit nadal `COMPLETE`) — stan czytamy
  wyłącznie z `competitions submissions`.
- Slot B (`duck-v12-plan`, `PLAN_COMMIT="1"`, `ARC3_ESCALATE_ACTIONS=60`) czeka gotowy lokalnie;
  push dopiero po werdykcie A, bo obowiązuje 1 zgłoszenie dziennie.

## 5. Reprodukcja

```powershell
# log smoke v11 (JSONL -> tekst)
.venv-local\Scripts\python.exe - <<'PY'
import json, urllib.request
u = ("https://raw.githubusercontent.com/peteraangelic-pixel/Smak-Domu-Konkurs/"
     "arena/5ed750ef-smak-domu-konkurs/arc-agi-3/kaggle/ops/results/"
     "r093-kernel_output_pick/output-pick/arc3-duck-v11.log")
raw = urllib.request.urlopen(u).read().decode("utf-8", "replace")
out = [json.loads(l.strip().lstrip(",")).get("data", "") for l in raw.splitlines()
       if l.strip().lstrip(",").startswith("{")]
print("".join(out)[-2500:])
PY
```

- smoke v11: `kaggle/ops/results/r093-kernel_output_pick/smoke.log`
- smoke c45: `kaggle/ops/results/r085-kernel_output_pick/c45_smoke.log`
- submit: `kaggle/ops/results/r095-submit/SUMMARY.md`
- status: `kaggle/ops/results/r096-submissions/SUMMARY.md`
