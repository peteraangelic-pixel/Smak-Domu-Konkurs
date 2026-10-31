# Audyt pakietu `codex/arc-local-lab-v18-20261030` (31.10.2026) i wynik 13,28

Sprawdzone: kod i dane z gałęzi, nie opisy. Klon `--sparse`, uruchomione testy,
odtworzone liczby na `r085`.

---

## 1. Wynik 13,28 — co da się z niego wywnioskować, a czego nie

**Fakt:** `57811453`, COMPLETE, publicScore **13,28** vs v11 **23,89** vs najlepsze **26,25**.

### 1.1 Cap jest wyłączony — i to jest poprawne

Dwie komórki notebooka (`arc3-duck-v13.ipynb`):

```python
# cell 1
ARC3_VARIANT = {"env": {..., "ARC3_LEVEL_TOKEN_CAP": "0", "ARC3_LEVEL_MIN_DONE": "0", ...}}
# cell 17
os.environ.update(_variant_env)          # -> ustawia ARC3_LEVEL_TOKEN_CAP="0"
# cell 29
_prev_cap = os.environ.get("ARC3_LEVEL_TOKEN_CAP")     # == "0"
if _prev_cap in (None, ""):
    os.environ["ARC3_LEVEL_TOKEN_CAP"] = "40000"       # NIE wykonuje się
```

Guard `in (None, "")` jest poprawny: „0" nie jest nadpisywane na 40000.
**Wniosek: spór o arming 20k jest dla tego wyniku bez znaczenia — cap był inertny.**

### 1.2 Nie jest to awaria ani utrata głębokości

Policzone na `r085` (10 gier, oficjalna reguła), score w zależności od tego, jak głębokie
poziomy przetrwały:

| scenariusz | score |
|---|---|
| pełny wynik (wszystkie poziomy) | 26,78 |
| tylko poziomy 1–3 | 17,88 |
| tylko poziomy 1–2 | 9,26 |
| tylko poziom 1 | **3,48** |

**13,28 leży między „1–2" a „1–3"** — czyli ok. **2,5 poziomu na grę**. To **nie jest**
„gry nie wystartowały" (byłoby ≈3,5), to „zahaczyliśmy o 2–3 poziom, dalej brakło budżetu".

### 1.3 Najbardziej prawdopodobny mechanizm: koszt tokenowy patchy przy pełnym rosterze

Ich własny smoke: **22,59** przy 48 min/gra na 10 grach. Submisja: **13,28** na pełnym
rosterze. Różnica ≈ **1 poziom na grę** — a każdy poziom waży `(k+1)`, więc spadek jest
nieproporcjonalnie duży.

Budżet: 9 h × 10 slotów = 5 400 sloto-minut. Przy ~48 min/gra to **~112 gier** — czyli
**submisja dogania wielkość rosteru (≈110)**, a smoke (10 gier × 48 min = 480 min) ma
**11× więcej czasu na grę**.

Ile kosztują patche: r085 (c45, 10 gier, 48 min) = **141,7k tokenów/gra**.
Notatka z gałęzi Smaka (ocena `a/call`): **~186k tok/gra** przy wyższym `actions/call`
po włączeniu hintu batchującego. To **≈ +16%** ruchu przy tym samym zegarze — czyli przy
stałym budżecie **~1 poziom mniej na grę**.

**Hipoteza spójna ze wszystkimi liczbami:** v13.7 z 9 patchami robi więcej akcji
decyzyjnych na token, więc przy rosterze ~110 gier przycina głębokość, a głębokość jest
w RHAE wypukła. **v11 z 0 patchy jest szybszy, nie mądrzejszy** — i dlatego wygrywa.

### 1.4 Konsekwencja metodologiczna, której nikt nie wyciągnął

**Dopóki roster jest ~11× większy niż smoke, żaden smoke ani żadna symulacja na zapisach
nie może ranguować wariantów.** Ich własne `ANALIZA-23.md` mówi to poprawnie
(„RHAE jest wypukłe w głębokości... cięcie budżetu o połowę kosztuje więcej niż połowę
wyniku"), ale wniosek operacyjny nie został wyciągnięty:

> **Jedyny pomiar, który rangowuje warianty, to pełny bieg na rosterze.**
> Wszystko inne mierzy inną populację przy innym budżecie.

To wyjaśnia całą serię: 26,25 → 23,89 → 13,28 przy rosnącej liczbie patchy i stałym
budżecie. **Nie „v13.7 jest gorszy" — „v13.7 jest droższy".**

---

## 2. Audyt pakietu symbolicznego (to jest realna nowość)

### 2.1 Co sprawdziłem i co się potwierdza

| kontrola | wynik |
|---|---|
| `template_transfer.py` — zależności | **czysty numpy**, zero `arcengine`, zero `game_id` (potwierdzone `grep` + import) |
| izolacja od niedozwolonych danych | `template_hook.py`: kontroler dostaje tylko `frame.grid`, `controls`, `frame.level` — **nie** dostaje ID gry, baseline'u, silnika, funkcji scoringu. Docstring zgodny z kodem |
| fallback do LLM | `if action is None: return original(...)` — poprawny; `ARC3_TEMPLATE_ONLY=1` daje jawną abstynencję zamiast cichego błędu |
| testy | `pytest tests/test_template_transfer.py` → **35 passed** (0,21 s) |
| abstynencja | `template_coverage = [["ft09", 3, 25]]` — 1 gra z 25, reszta abstynuje. Zgodne z deklaracją |

### 2.2 Co realnie jest warte

`public25-final-comparison.json`, 75 prób, 16 workerów, `identical_traces: 75`:

| backend | poziomy | akcje |
|---|---|---|
| uniform | 0 | 3 248 |
| causal | 1 | 2 879 |
| **template** | **3** | **25** |

**3 poziomy w 25 akcjach** to na tej jednej grze efektywność ~2× lepsza od człowieka
(RHAE cap 1,15). To realny wynik, nie projekcja.

**Ale:** to **1 gra z 25**. Wpływ na średnią Kaggle to
**+28,57 / liczba_gier ≈ +0,3 pkt** przy rosterze 110 — czyli **szum**.

### 2.3 Błąd arytmetyczny w `START-HERE`

> „Potwierdzony wynik: 3 poziomy publicznego ft09 w 25 akcjach, **około 4,8 s** przez
> rzeczywisty Duck bez LLM."

**25 akcji w 4,8 s = 0,19 s/akcję.** To jest czas *wykonania akcji*, nie *znalezienia
rozwiązania*. Rozpoznanie szablonu to praca CPU nad siatką — jeśli cały test trwał 4,8 s,
to albo pomiar obejmuje tylko pętlę akcji, albo rozpoznanie jest darmowe.

**Dlaczego to ważne:** „4,8 s zamiast 48 minut" sugeruje zysk 600×. Realny zysk to
**oszczędność tokenów na jednej grze**, bo kontroler nie woła LLM. Mieszanie tych dwóch
liczb w jednym zdaniu to dokładnie ten typ błędu, który ta kampania już raz wycofywała
(„3,6× luka silnika"). Wymaga jednego zdania sprostowania.

---

## 3. Co z dokumentu jest mocne

* **Sekcja o Qwenie jest uczciwa i warta zachowania**: „temperatura 0.7 ograniczyła
  powtarzanie kodu, ale nadal dała 0 ukończonych poziomów. Nie wytrenowano wag."
  To jest wynik negatywny, który oszczędza dni.
* **Rozdzielenie 3 ukończeń na ft09 od generalizacji** — zrobione wprost, bez marketing.
* **Wycofanie GO dla v13.7** — decyzja poprawna i szybka.
* **`paired-comparison.json` ma sekcję `qualification`** („one development public game/seed,
  not a hidden-game score forecast") — wzorowa dyscyplina.
* **Rust/Rayon: 33× na kernelu prostokątów, nie na grze** — poprawnie zawężone.

## 4. Gdzie dokument jest zbyt optymistyczny

1. **„Konkretny postęp"** — 3 poziomy na 1 znanej grze rozwojowej to nie postęp
   w konkursie, to **prototyp jednej zdolności**. Dokument to przyznaje w przypisie,
   ale nagłówek sugeruje więcej.
2. **Brak kosztu fałszywego rozpoznania.** Testy pokrywają palety, obroty i abstynencję,
   ale nie ma pomiaru: ile razy szablon rozpoznał *źle* na planszy, której nie znał?
   `template_coverage` pokazuje, że abstynuje na 24/25 gier — dobrze. Ale **na ile
   z tych 24 rozpoznał coś fałszywie i wykonał akcję?** Tej liczby nie ma, a to jest
   ryzyko regresji w submisji. **Do zmierzenia przed jakimkolwiek użyciem w konkursie.**
3. **Izolacja pamięci między grami** — `_template_runtime != runtime` resetuje kontroler
   przy zmianie ścieżki stanu. To poprawne, ale nietestowane na przejściu poziomu
   w obrębie tej samej gry (czy `learned` nie przecieka między poziomami o innej mechanice).

---

## 5. Rekomendacja

1. **Nie promować v13.7 przez smoke.** Zmierzone: smoke 22,59 → sub 13,28.
2. **Odzyskać mistrza** (v11 / v3, 23,89–26,25) jako baseline i **zrobić jedną pełną
   submisję kontrolną** — bez tego każda dalsza zmiana jest niemierzalna.
3. **Ablacja po jednym patchu, ale tylko na pełnym biegu** — inaczej znów porównacie
   populacje. Jeśli budżetu wystarczy na 2 biegi: (a) v11 + 0008, (b) v11 + 0009.
4. **Szablon symboliczny trzymać jako osobny eksperyment**, nie w ścieżce submisji,
   dopóki nie ma pomiaru fałszywych rozpoznań.
5. **Priorytet liczbowy:** +0,3 pkt z szablonu vs −10,61 pkt z v13.7. Kolejność jest
   oczywista — **najpierw odzyskać 23,89, potem myśleć o nowych zdolnościach.**

## 6. Czego nie sprawdziłem

* Nie uruchamiałem notebooka ani nie odtwarzałem 25 akcji na ft09 (wymaga silnika + Duck).
* Nie weryfikowałem `agent.ipynb` po SHA256 (`550eb185…`) — nie klonowałem
  `duck-lab-candidates/`.
* Commitów `f730639`, `aec6c3e`, `91f1ce9` nie sprawdzałem osobno (`ls-remote` na gałęzi
  zwraca tip; historia jest w `--depth 1` niedostępna).
