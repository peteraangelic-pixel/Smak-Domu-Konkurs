# Odpowiedź na PEER-AUDIT-RESPONSE-20261031 + diagnoza 13,28 i plan

## 1. Najpierw moje błędy — potwierdzone

| mój błąd | ich korekta | weryfikacja |
|---|---|---|
| „141,7k → 186k to ≈ +16%" | **+31%** | **Mają rację.** 186 141/141 719 = **1,314**. Napisałem +16% — czysta pomyłka arytmetyczna. |
| „11× więcej czasu na grę w smoke" | miesza cap, budżet i równoległość | **Mają rację co do formy.** Cap smoke = 48 min, fair share = 48,2 min — praktycznie identyczne. Mój argument był źle zbudowany (choć wniosek okazał się słuszny z innego powodu — patrz §2). |
| `28,57/110 ≈ +0,3 pkt` | nie jest wynikiem, tylko ilustracją | **Mają rację.** To nie estymata. |
| „13,28 = ~2,5 poziomu na grę" | nieznany roster, to ilustracja | **Mają rację co do dowodu** — porównanie do r085 nie odwraca funkcji punktacji. Ale §2 daje odpowiedź niezależną od r085. |
| „35 passed" | 42 = 35 + 5 + 2 z trzech plików | Częściowo: pytest na `test_template_transfer.py` dał 35. Ich suma 42 jest poprawna dla całego katalogu. Sformułowanie powinienem zawęzić. |
| „4,8 s = wykonanie akcji, nie percepcja" | zegar startuje przed `session.play()` | **Mają rację**, mój zarzut był za mocny. Wniosek: 4,8 s obejmuje percepcję, nie obejmuje programowania/importów. |

**Podsumowanie: dwa z moich zarzutów były błędne liczbowo, dwa za mocno sformułowane.
Zostaje jeden, którego nie wycofuję: brak pomiaru fałszywych rozpoznań — i oni sami
potwierdzili go sondą w §„Sonda Gemmy".**

---

## 2. Diagnoza 13,28 — znaleziona w ich własnym kodzie

Nie trzeba żadnego modelu ani porównania z r085. **Mechanizm jest w komórce 33
notebooka v13.7** (`v13.7 budget probe`), którą napisali sami:

```python
_total, _reserve, _conc = 32400.0, 600.0, int(bm.solver.concurrency)   # 10
_fair = max(60.0, (_total - _reserve) * _conc / max(1, _n_games))
_cap  = float(bm.solver.max_runtime_s_per_game)                        # 532*60
print(f"...uczciwy udzial {_fair/60:.0f} min/gra, cap {_cap/60:.0f} min -> {_cap/_fair}x")
if _cap / _fair > 1.3:
    print("UWAGA cap jest {:.1f}x powyzej udzialu - ogon rosteru nie zagra")
```

A w komórce 29:

```python
bm.solver.max_runtime_s_per_game = 48*60     # smoke
bm.solver.max_runtime_s_per_game = 532*60    # TRUE_SUBMISSION  <-- rerun
```

### Liczby

| wielkość | wartość |
|---|---|
| budżet realny (32400 − 600 s rezerwy) | 530 min |
| concurrency | 10 |
| roster (ich notatka) | ~110 gier |
| **uczciwy udział na grę** | **48,2 min** |
| **skonfigurowany cap** | **532 min** |
| **cap / fair** | **11,0×** |

Ich własna obserwacja z tego samego bloku: *„KAŻDY run kończy się dokładnie na capie"*
(czyli gra nie kończy się wcześniej — cap **jest** przydziałem akcji).
Przy capie 532 min jeden slot obsłuży **~1 grę** w całym oknie 530 min.

### Co to daje

| rozegranych gier | score |
|---|---|
| 30/110 | 7,30 |
| **55/110** | **13,39** ← **pasuje do 13,28** |
| 110/110 | 26,78 |

**13,28 = mniej więcej połowa rosteru rozegrana.** Ogon kolejki nie zagrał i policzył się jako 0.
To **nie** jest wina patchy, capa tokenowego, Qwena ani harmonogramu —
to jeden parametr czasu ustawiony 11× powyżej uczciwego udziału.

---

## 3. Poprawka: jedna linia

```python
# cell 29, zamiast:  bm.solver.max_runtime_s_per_game = 532*60
_reserve = 600.0
_conc = max(1, int(bm.solver.concurrency))
_fair = max(60.0, (target.max_runtime_s - _reserve) * _conc / max(1, len(bm.games)))
bm.solver.max_runtime_s_per_game = int(_fair)          # 48 min przy 110 grach i 10 slotach
```

Albo bezpieczniej — **zostawić 532 jako sufit, ale dodać harmonogram:**
`min(_fair, 532*60)` to to samo, więc realnie chodzi o **obniżenie capa do `_fair`**.

**Oczekiwane:** 13,28 → **~26,78** (+13,5 pkt), czyli powrót do poziomu v3/r085.
To jest **największy pojedynczy zysk dostępny w tej kampanii** i zajmuje jedną linię.

### Czego potrzebuję, żeby to potwierdzić

Jeden plik: **`budget_probe.json`** z prawdziwego rerunu. Zawiera `games`, `fair_share_s_per_game`,
`configured_cap_s`, `cap_over_fair`. Jeśli `cap_over_fair ≈ 11` — diagnoza domknięta.
Jeśli ≈ 1 — mylę się i wracamy do hipotezy kosztu tokenowego.

---

## 4. „Jaka wersja będzie w TOP-5?" — uczciwie: żadna

TOP-5 to **51,51 – 75,56**. Z pozycji 13,28 w **2 dni** (deadline 2.11) to nie jest realne.
Nie dlatego, że brakuje pomysłu, ale z powodów, których nie da się obejść:

| co trzeba | dlaczego nie w 2 dni |
|---|---|
| +1,7 poziomu na grę ponad r085 | leverage: +1 poziom = 43,20; +2 = 59,67. Potrzeba ~1,7 poziomu **na każdej grze**, nie na wybranych |
| nieznany roster | 110 gier, których nikt nie widział; każda poprawka mierzona na 10 grach publicznych |
| budżet submisji | 2 sloty dziennie; każda hipoteza to 9 h i jeden slot |
| baza | startujecie z 13,28, nie z 43. Każdy punkt trzeba najpierw odzyskać |

**Co jest realne:** 13,28 → ~26,8 (jedna linia), a potem, jeśli zostanie slot —
jeden patch zamiast dziewięciu, po jednym na bieg.

**Czego bym nie robił:** nie budował kolejnej wersji (v14/v18/router/memory).
Przy rosterze 110 i budżecie 9 h każda dodatkowa warstwa **zmniejsza** szansę, bo zjada
tokeny, a zysk z warstwy jest mierzony tylko na 10 publicznych grach.

---

## 5. Co zrobić w pozostałe godziny (kolejność)

1. **Wypchnąć poprawkę capa** (jedna linia) i sprawdzić `budget_probe.json`.
2. **Jeden slot na v3/v11 jako kontrola** — żeby mieć zmierzony punkt odniesienia 26,25,
   zamiast porównywać z historią.
3. Jeśli 1–2 zadziałają: **jeden patch**, np. `0009 self-pace`, ale **z capem = fair share**.
   Nie dziewięć patchy.
4. **Szablon symboliczny zostawić poza submisją** dopóki nie ma pomiaru fałszywych
   rozpoznań — ich własna sonda pokazuje, że problem jest realny (patrz §6).
5. **Nie robić** nowych warstw, nowych modeli, nowych harmonogramów przed 2.11.

---

## 6. Ich sonda — i co z niej wynika (to jest realna wartość tego audytu)

Odtworzone 300 syntetycznych plansz na rodzinę:

| rodzina | oryginał: rozpoznane/trafne | single-mismatch |
|---|---|---|
| copy | 149/149 | 149/149 |
| rotate | 299/**18** | 17/3 |
| invert | 300/**0** | 0/0 |
| random | 297/**23** | 8/1 |

**To jest dokładnie ten pomiar, którego brakowało** — i pokazuje, że ryzyko jest duże:
na `invert` polityka rozpoznaje **300/300** przypadków i **myli się w 100%**.
`single-mismatch` to naprawia (0 rozpoznań), ale kosztem 88% poprawnych rozpoznań na `rotate`.

Wniosek: **bez tej sondy szablon byłby niebezpieczny w submisji.** Oni to zmierzyli —
i to jest najmocniejszy element ich całego pakietu, mocniejszy niż 3 poziomy na ft09.

## 7. Co uznaję za ich najlepsze odkrycie

**Kontrprzykład pętli oscylacji (c87, 60 akcji, 0 sprzeczności predykcji).**
To pokazuje, że „sprawdzenie koloru po akcji" nie dowodzi realizacji celu. Mój własny
`ConvergedGuard` adresuje ten sam problem inaczej (hash stanu + ban), ale ich
`template_guarded.py` z limitem 32 propozycji/poziom to **prostsze i lepiej przetestowane**
rozwiązanie tego konkretnego przypadku. Uznaję.
