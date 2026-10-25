# ARC3 Duck v10 — pakiet na slot

`arc3-duck-v10.ipynb` + `kernel-metadata-v10.json`. Baza: zaakceptowany
`duck-c45` (silnik Franzena + harness Tufy). Jedna nowa dźwignia: `commit(plan)`.

## Co ten pakiet naprawia

**1. v9 (i v7) w ogóle by nie ruszyły — i nikt tego nie zauważył.**

Patch harnessu Franzena leżał w notebooku jako jedna komórka `%%writefile`
o długości **498 799 znaków**, a tekst kończy się **w środku hunka**
`segmentation.py`. `git apply` w komórce środowiskowej zwraca
`corrupt patch at line 10086`, `check=True` rzuca wyjątek i notebook umiera
**przed wczytaniem modelu**. Każdy slot na v9 spaliłby się w ~2 minuty, bez
żadnego logu z gry.

498 799 to nie przypadek — to sufit długości komórki. Ogon patcha nigdy nie
trafił do notebooka. v10 odbudowuje patch z **publicznego drzewa Franzena**
(`da-fr/arc-agi-3-solution`, HEAD z 30.09.2026 = wersja z Milestone 2), dzieli
go na kawałki < 400 000 znaków i skleja w runtime, drukując sha256.

**2. `commit(plan)` — plan z weryfikacją każdego kroku.**

Dotąd `action([...])` wysyłało całą listę i nie sprawdzało nic. Jeśli model
mylił się w drugim kroku, reszta planu szła na planszy, której już nie rozumiał.
Teraz:

```python
commit([
    "LEFT",
    {"action": "UP",   "expect": {"level": 2}},
    {"action": "RIGHT","expect": {"cells": {"12,30": "R"}}},
])
```

Każdy krok leci osobno, oczekiwanie jest porównywane z klatką, która realnie
wróciła, a plan **staje na pierwszym rozjeździe** i zwraca `mismatch` z nazwą
pola. Obsługiwane: `level`, `board_changed`, `step`, `digest`
(z `frame_digest()`), `cells`. Stop też na ukończeniu poziomu, game over,
końcu runu i `max_actions` (domyślnie 40).

**3. Eskalacja po utknięciu.**

`ARC3_ESCALATE_ACTIONS=60`: po 60 akcjach na poziomie bez ukończenia kolejny
turn wymaga procedury — retrodikcja z logu → `model_state`/`model_step` →
`check_model()` → `plan()` → `commit()`. To jest przeniesienie planowania
z modelu do kodu; dokładnie to robi czołówka (Retrodict: 99,86% RHAE, 7 703
akcje na 183 poziomy).

## Jak uruchomić

1. Wgraj `arc3-duck-v10.ipynb` i `kernel-metadata-v10.json` na Kaggle.
2. GPU: **RTX Pro 6000** (notebook tego wymaga; preflight sprawdza `nvidia-smi`).
3. Wejścia: `dfranzen/pennyroyal-v253`, `dfranzen/taaf-kaggle-source-bundle-copy`,
   oba modele `dfranzen/*` (są w metadanych).
4. `PROFILE` w komórce 1:

| PROFILE | co robi | koszt |
|---|---|---|
| `c45` | kontrola: dokładnie zaakceptowana konfiguracja, bez nowego promptu i bez `commit()` | 1 slot |
| `plan` | c45 + `commit()` + eskalacja po 60 akcjach | 1 slot |
| `plan-esc` | jak wyżej, eskalacja po 30 akcjach | 1 slot |
| `deep` / `wide` | profile v9 (batching / więcej strumieni) | 1 slot |

Pierwszy slot: `c45`. Nie po to, żeby wygrać, ale żeby mieć **jedną zmierzoną
liczbę** dla tego stosunku na tym koncie. Drugi: `plan`. Trzeci: to, co wygra.

## Bramki

- Smoke (10 gier × 48 min) musi dać `ARC3_SMOKE_OK`.
- `plan` idzie dalej tylko, jeśli `v9 gate` pokaże GO (średnia > 29,02 = smoke v3)
  **i** w logu widać, że `commit()` faktycznie był wołany z oczekiwaniami.
  Brak wywołań = wyłączyć, nie tracić slotu.
- Kill-switch: `ARC3_PLAN_COMMIT` nieustawione = zachowanie identyczne z c45.

## Co jest zweryfikowane offline (i co nie)

Zweryfikowane, odtwarzalne u Ciebie przez `verify.py`:

- patch składa się z kawałków do **bajt w bajt** (sha256 w `ARC3_VARIANT`),
- nakłada się na czyste źródło Tufy (`git apply`, także poza repo git),
- drzewo się kompiluje,
- **12/12 testów** `commit()` przechodzi na tym drzewie, w tym integracyjny
  przez prawdziwy bootstrap sandboxa,
- wszystkie 5 profili rozwiązuje się do oczekiwanego env,
- każda ścieżka `/kaggle/input/...` z notebooka jest zadeklarowana w metadanych.

Zmierzone offline: koszt kroku `commit()` to 4 ms przy pustej historii i 146 ms
przy 200 zarejestrowanych przejściach (plan 20 akcji ≈ 3 s). To nie jest
darmowe, ale mieści się w 30-sekundowym timeoutcie narzędzia.

**Nie jest zmierzone:** zachowanie na żywym gatewayu, zysk punktowy `commit()`,
czy Qwen 3.8 Flash Next napisze poprawny `model_state`/`model_step`. Nikt tego
nie zmierzył — ani ja, ani poprzednie sesje.

## Uczciwie o „45+"

Ten pakiet **podnosi podłogę**: sprawia, że zaakceptowany stos w ogóle się
uruchamia, i dokłada jedną dźwignię z bramką. Nie gwarantuje 45+. Publiczny
sufit tej linii to 38,85 (autor harnessu, to samo podejście). 45+ wymaga
modelu, który realnie pisze symulatory — Retrodict i Tycho robią to na modelach
frontier, nie na 27–30B. Szczegóły i plan slotów: `DECYZJE-I-RYZYKA.md`.
