# duck-v13.5-consensus — kandydat do zgłoszenia (Arena, 30.10 2026)

**v13.5 = v13.4-unified + fala 08:00–08:12 (korekty 7911, duck-v15 a450, audyt Gemmy
naszego v13.3, 9. korekta c87)** — szczegóły: `OCENA-ARENA-V13-5-CONSENSUS.md`.

| warstwa | element |
|---|---|
| baza | v13.2: PLAN_COMMIT=1, CAP=0, WINPATH=1, DEAD_SKIP=1, conc=10, playbook 14/14 |
| presja batcha | `ARC3_OPENER_COMMIT_HINT=1` (cięcie tok/akcję = dźwignia wg poprawionego modelu budżetu 7911) |
| observability | patch 0007 (`[arc3-winpath]` log replayu/dead-skip) + sonda budżetu + sonda rosteru |
| eskalacja | `ESCALATE_ACTIONS=20` + patch 0008 (`ARC3_ESCALATE_RELATIVE`, cap 2/level); **w submisji baseline'y ukryte → działa absolutna 20 + cap 2 = 42 wstrzyknięć na r085 (2,9% puli)** — degradacja udokumentowana w komórce 2 i mierzona sondą baseline'u |
| NOWE w v13.5 | sonda rosteru loguje **pokrycie wazone** (score ≤ 100×pokrycie, reguła 30/30) + **widoczność baseline'u** w prawdziwym rerunie |

Weryfikacja: **ALL CHECKS PASSED** — 8/8 patchy czysty r033, 12+6+11 testów na
spatchowanym drzewie, sondy na stubach, playbook bajtowo identyczny (14/14 na
silniku), serving nietknięty.

## Wypchnięcie (właściciel konta)

```bash
kaggle kernels push -p arc-agi-3/duck-v13-5-consensus
```
potem UI: Run → **Submit to Competition**. W logu: `v13.5-consensus profile=plan
plan_commit=1 escalate=20 true_concurrency=10`, `ARC3 extra patch applied:
...-05.patch` i `...-06.patch`, `v13.5 budget: ...`, `probe: OK -> ...`,
`v13 playbook: 9 gier, 14 poziomów`, po biegu `v13.5 roster: {...}` z pokryciem
i werdyktem baseline'u.

## Kill-switcze

`"ARC3_ESCALATE_RELATIVE": "0"` (=v14) · `"ARC3_ESCALATE_MAX_PER_LEVEL": "0"` ·
`"ARC3_OPENER_COMMIT_HINT": "0"` (=v14) · `"ARC3_WINPATH_LOG": "0"` ·
`"ARC3_WINPATH": "0"` · `"ARC3_DEAD_SKIP": "0"` · `PLAN_COMMIT = "0"` ·
`"ARC3_LEVEL_TOKEN_CAP": "45000"`.

## Uczciwie

Prognoza rerunu: **26–34** (Gemma dla v15; nasza przewaga = obserwowalność). Jedyna
droga do 50 wg poprawionej matematyki 7911: pokrycie 29%→50% = +1,1 poziomu/grę
(+22% budżetu); mechanizmy w pakiecie celują w tok/akcję (hint) i mierzą wszystko,
co o tym decyduje. Pakiet nie obiecuje 50 — obiecuje pomiar każdej dźwigni w jednym
biegu, z kill-switchami na każdą z nich.
