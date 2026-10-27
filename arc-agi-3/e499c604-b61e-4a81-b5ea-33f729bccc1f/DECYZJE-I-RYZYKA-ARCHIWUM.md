> ⚠️ ARCHIWUM 27.10: diagnoza §1 tego dokumentu ("v9/v7 martwe przed serwerem") OBALONA (patch bajt-identyczny z c45, który przeszedł; %%writefile dopisuje newline). Pakiet v10 jako całość wycofany: jego patch pada na czystym bundlu (Makefile:40/README.md:1), a mechanizmy commit(plan) ŻYJĄ w arc-agi-3/duck-v11-c45/patches/0005-plan-commit.patch (testy tamże). Dokument zostaje wyłącznie jako kontekst decyzji.

# v10 — decyzje, dowody, ryzyka

## 1. Dowód na ucięty patch (najważniejsze znalezisko)

```
duck-v9/arc3-duck-v9.ipynb  →  komórka 5, źródło: 498 799 znaków
duck-v7/arc3-duck.ipynb     →  komórka 4, źródło: 498 799 znaków  (ta sama wartość)
```

Ostatnie 200 znaków komórki:

```
... "pose_hash": signature[3],
    "shape_hash": signature[4],
     "pixels": len(comp["cells"]),
     "boundary": [[r, c] for r, c in boundary],
     "children": children[cid],
```

To środek hunka. `git apply --check` na tak wyekstrahowanym pliku:

```
error: corrupt patch at line 10086
```

Komórka 10 (środowisko) robi `subprocess.run([... "git apply" ...], check=True)`
— czyli `CalledProcessError` **przed** startem serwera i przed pierwszą grą.

Pełny patch z drzewa Franzena ma **660 020 bajtów / 24 pliki**
(ucięta wersja: 498 779 B / 16 plików). Brakuje m.in. końca `segmentation.py`
i całych zmian `viewer/*`.

## 2. Co dokładnie jest w patchu 0010

| warstwa | źródło | rola |
|---|---|---|
| Franzen harness | `da-fr/arc-agi-3-solution` @ 30.09.2026 | silnik, SGLang, scheduler priorytetów, `EXPOSE_UNDO`, no-op guard |
| 0001 | poprzednia sesja | notatki z poziomów, audyt po 60k tokenów, hint „myślenie jest droższe niż akcje" |
| 0002 | poprzednia sesja | wykonywalny model świata: `model_state`/`model_step`/`model_goal`, `check_model()`, `plan()` (BFS) |
| 0004 | poprzednia sesja | cap tokenów na poziom (45k) + limit resetów |
| 0007 | ta sesja | `commit(plan)` + `frame_digest()` + eskalacja |

Kolejność nakładania jest istotna i sprawdzona: 0001 i 0004 nakładają się bez
fuzz na drzewo Franzena; 0002 również (po pełnym patchu, nie po uciętym);
0007 jest już wkomponowany w 0010, więc nie ma osobnego kroku.

## 3. Czego `commit()` NIE naprawia

- **Nie uczy nowych poziomów.** Zmniejsza koszt pomyłki (jeden krok zamiast
  planu), ale jeśli model nie rozumie mechaniki, plan i tak nie powstanie.
- **Nie zwiększa liczby akcji na wywołanie** — to już jest 4,4–5,2 i sufit
  z tego tytułu jest blisko.
- **Nie zastępuje modelu.** Retrodict (99,86% RHAE) i Tycho (100%) używają
  modeli frontier. Na Qwen 3.8 Flash Next nikt tego nie zmierzył.

## 4. Co realnie może dać wynik

Trzy niezależne liczby, wszystkie z repo:

1. **26,25** — najlepszy zmierzony LB (duck v3, 16.10).
2. **38,85** — autor tego harnessu, to samo podejście (15. miejsce).
3. **~30–39** — zakres, w którym powinien wylądować `c45`/v10, jeśli stos
   wystartuje i nie zabije go quota.

Do 45 brakuje warstwy, której w tym repo nie ma zaimplementowanej end-to-end:
model świata pisany przez model + planowanie w nim. Patch 0002 daje mechanikę,
`commit()` daje egzekucję z weryfikacją, eskalacja wymusza użycie — ale
**jakość symulatora zależy od modelu** i to jest jedyna nieusunięta niewiadoma.

## 5. Plan slotów (8 dni do 2 XI)

| slot | profil | pytanie, na które odpowiada | zabić, jeśli |
|---|---|---|---|
| 1 | `c45` | czy stos Franzena w ogóle kończy run na tym koncie | nie ma `ARC3_SMOKE_OK` lub run < 6 h |
| 2 | `plan` | czy `commit()` jest wołany i czy plany przechodzą weryfikację | brak wywołań `commit` z `expect` |
| 3 | wygrany z 1–2 albo `plan-esc` | czy eskalacja ratuje utknięte poziomy | mniej poziomów niż w slocie 1 |

Zasada: jedna zmiana na slot. `deep`/`wide` tylko jako osobny pomiar, nigdy
w połączeniu z `plan`.

## 6. Ryzyka, których nie da się usunąć offline

- **Roster.** Prywatny zestaw może nie być 25 publicznymi grami — wtedy cała
  wiedza o konkretnych grach (playbook, triage budżetu) jest warta zero.
- **Kwota GPU.** 30 h/tyg. Dwa pełne runy po 9 h + smoke 2,5 h = 20,5 h.
  Trzeci slot może nie wejść.
- **Zmienność.** Historycznie: v6 (world model) 23,94 < v2 24,66. Nowa warstwa
  potrafi kosztować. Dlatego `PROFILE="c45"` jest w pakiecie i jest domyślną
  kontrolą.
