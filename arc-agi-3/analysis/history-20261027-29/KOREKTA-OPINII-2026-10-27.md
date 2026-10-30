# KOREKTA OPINII — 27.10.2026

> Plik utworzony 27.10.2026. Nie modyfikuje żadnego pliku starszego niż 2 dni.
> Cel: inne sesje mają przestać cytować błędny opis pakietu kandydującego
> („duck-v11-c45 PROFILE=plan, 31 komórek, patch w 2 chunkach").

## 1. Co było błędne w opinii AI z 27.10

| # | Błędne twierdzenie | Stan faktyczny (dowód) |
|---|---|---|
| 1 | „duck-v11-c45 ma PROFILE=plan domyślnie, 31 komórek, patch w 2 chunkach <498 799" | **33 komórki** (`arc3-duck-v11.ipynb`, parser JSON). Domyślnie **`PLAN_COMMIT="0"` → profil `c45fix`**; `V11_PROFILE = "plan" if PLAN_COMMIT == "1" else "c45fix"`. **5 patchy** aplikuje się w całości na czysty bundle r033 (`OCENA-ARENA-V11-C45.md`, `README.md`). Opis „plan/31/2 chunki" należy do odrzuconej linii v10/v11-Smak, nie do kandydata. |
| 2 | „expected ~41.8 dla slotu A" | 41,8 to punkt krzywej Ducka @200k z notatek, **nie pomiar tej rury**. Zmierzone: best COMPLETE **26,25**, c45 **0,00**, smoke **26,78** (32/69 poziomów), r019 ~175k tok/grę → LB **24,66**. Realistyczne oczekiwanie slotu A: **~25–30**. |
| 3 | „realistyczne 31–42 i blisko progu" | Próg nagród (**LB 24.10**) = **49,85**; lider **68,91**. Z ~26 luka to **~+24 pkt**, nie +5. Przy ~6 okienkach do 2.11 slot A ma wartość **diagnostyczną**, nie nagrodową. |

## 2. Poprawiony jednolinijkowiec (do wklejania)

> Kandydat na slot A to `arc-agi-3/duck-v11-c45` (`petersharps/arc3-duck-v11`, commit 6c3e958): **33 komórki, 5 patchy aplikujących się na czysty bundle r033**, domyślnie **`PLAN_COMMIT="0"` → profil `c45fix`** (tylko fix `concurrency=120` → `ARC3_TRUE_CONCURRENCY=10`); `PLAN_COMMIT="1"` włącza `commit(plan)` + eskalację 60 akcji (profil `plan`); realne oczekiwanie slotu A to **~25–30 pkt** (best COMPLETE 26,25; c45 0,00; smoke 26,78), a nie 41,8; próg nagród **49,85** (LB 24.10) oznacza lukę **~+24 pkt**, więc slot A ma wartość diagnostyczną, nie nagrodową.

## 3. Fakty vs hipotezy (tylko to wolno cytować)

### Zmierzone / potwierdzone
- best COMPLETE: **26,25** (duck v3)
- c45 #57629847: **0,00**
- smoke c45: **26,78** (32/69 poziomów)
- r019: ~**175k tok/grę**, LB **24,66**
- próg nagród (LB 24.10): **49,85**
- lider (LB 24.10): **68,91** (Tufa Labs)
- sufit ruchów: ~**29,0**; +1 poziom/grę ≈ **44** (ekstrapolacja z r019)
- `PERSISTENT_FUNCTIONS_SCOPE='game'` akceptowane (pamięć między poziomami w grze działa)
- finalista jako publiczny notebook do **31.10–1.11** (inaczej nagroda przepada)

### Hipotezy — NIE cytować jako fakty
- fix concurrency (120 vs MAXREQ=10) naprawia 0,00 — **brak logu reruna** (tylko przeglądarka usera)
- 41,8 / 45,7 — punkty krzywej z notatek, nie pomiar tej rury
- early-abandon +7 pkt — symulacja na założeniach, nie pomiar LB
- 7 słabych punktów README (pamięć między passami, transfer poziomów, role temperatur itd.) — **zero A/B**
- pamięć między passami — **martwy end** przy n_passes=1 / scorecard bez powtórzeń game_id (CROSS-SESSION-SYNC §8); wracać tylko przy powtórzeniach z sondy rosteru
- arXiv 2605.25931 / RHAE 0.30 — niezweryfikowane
- roster prywatny = 25 gier publicznych — niepewne (sonda rosteru w v11 istnieje dlatego)

## 4. Liczby decyzyjne (nic więcej)

**26,25** (best COMPLETE) · **0,00** (c45) · **26,78** (smoke) · **49,85** (próg LB 24.10)

## 5. Źródła

- `duck-v11-c45/OCENA-ARENA-V11-C45.md` — 33 komórki, 5/5 patchy, PLAN_COMMIT=0, fix concurrency
- `duck-v11-c45/README.md` — przełącznik, domyślne wartości, czego to nie dowodzi
- `duck-v11-c45/DECYZJA.md` — 26,25 / 0,00 / 26,78 / próg 49,85 / sufit 29 / +1 poziom ≈ 44
- `duck-v11-c45/arc3-duck-v11.ipynb` — `PLAN_COMMIT = "0"`, `V11_PROFILE = ... "c45fix"`
- `CROSS-SESSION-SYNC-2026-10-25.md` §8–§10 — retrakcje, martwy end pamięci między passami
- `duck-v11/OCENA-V11-ARENA.md` — retrakcja v11-Smak (archiwum, nie kandydat)
