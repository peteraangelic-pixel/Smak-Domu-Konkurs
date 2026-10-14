# Plan pomiaru i zgłoszenia (17–20.10.2026) — ARC-AGI-3

Stan na 14.10 wieczór: oba warianty zbiegły do tej samej warstwy myślącej
(nasza v6.2 = ich v4.1 + delta v6.2). GPU wraca ~17.10 (limit wspólny `petersharps`).
**Wpisy do konkursu: 26.10.** Zgłoszenie: 1/dzień. Wyniki: 4.12.

## Warianty do porównania (jednorazowo, paired A/B)

| wariant | kod | rura | status |
|---|---|---|---|
| baseline | Franzen M2 publiczny | duck (98ddb59f) | zmierzony: 29.48 (10 gier × 4), LB 27.89 |
| v6.2 (nasz) | `Smak-Domu-Konkurs/arc-agi-3/llm-agent` (llm_policy.py) | nasz notebook H100 albo duck | kod gotowy, testy 43/43, nigdy nie grał prawdziwej gry |
| v4.1+delta (ich) | `Pokemon/arena/7911f950-pokemon/llm-agent/llm_policy_v4.py` | duck (Franzen) | kod gotowy |

Delta v6.2 → v4.1: no-op detector + lessons-between-games (`CROSS-SESSION-DELTA-v6.2.md`).

## Procedura 17.10 (kolejność obowiązkowa)

1. **SMOKE najpierw** (nie pełne 2 h): 1 gra × 10 min, marker zdrowia w logu
   (u nich `ARC3_SMOKE_OK`; u nas self-test komórki 6 + pierwsze 2 tury z prawdziwym API).
   Cel: wykryć błędy integracji za 10 min, nie za 2 h. (Lekcja: ich 2 zgłoszenia = ERROR.)
2. **Paired A/B**: te same gry, te same passy, po kolei:
   - v6.2: 10 gier × 1 przebieg ≈ 2 h GPU
   - v4.1+delta: 10 gier × 1 przebieg ≈ 2 h GPU
   - baseline nie wymaga reranu (mamy 4 przebiegi).
3. **Decyzja (reguły z FINDINGS):**
   - max(wariant) ≥ ~29 → zgłaszamy zwycięzcę następnego dnia (limit 1/dzień).
   - 26–29 → też zgłaszamy: potrzebujemy PRAWDZIWEGO wyniku LB przed 26.10.
   - oba < 26 → Plan B: warstwa promptowa do rury Franzena (zgłasza 98ddb59f).
4. **Zgłoszenie**: `make check-output` → klik „Submit to Competition" przez właściciela
   konta (API nie uruchamia gry — postmortem 57075036). Rezerwacja dnia w issue #1
   komentarzem WCZEŚNIEJ (zasada issue: zgłoszenie = 1/dzień, reset 00:00 UTC).

## Szablon rezerwacji do issue #1 (do wklejenia)

> Rezerwacja [data]: smoke 1 gra (~10 min) + paired A/B v6.2 vs v4.1 (2×10 gier ≈ 4 h GPU)
> z limitu `petersharps`. Zgłoszenie zwycięzcy [data+1] po `check-output`. Wyniki:
> `ops/results/r0XX-...` + FINDINGS. — sesja Smak-Domu-Konkurs + 7911f950.

## Ryzyka

- Nasz scaffold nie grał prawdziwej gry → smoke przed wszystkim, self-test w notebooku.
- GPU tygodniowe: A/B kosztuje ~4 h z ~30 h — zostawia zapas na 2–3 iteracje do 26.10.
- Jedna gra = duża wariancja (sd ≈ 3.9 na średniej z 25 gier ×1; na 10 gier gorzej) —
  decyzje tylko na parach per gra, nie na pojedynczych liczbach.
