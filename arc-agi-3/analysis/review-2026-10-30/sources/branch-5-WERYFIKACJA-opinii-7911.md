# Weryfikacja opinii `arena/7911f950-pokemon` o `v13.7 rev2` (30.10.2026)

**Metoda:** nie przyjąłem twierdzeń na słowo. Odtworzyłem te, które da się policzyć na
`r085-kernel_output_pick/output-pick/benchmark.json` (32 ukończone poziomy z 10 gier,
prawdziwe `generated_tokens` per akcja, `actions_per_level`, `base_actions_per_level`),
a twierdzenia o artefaktach sprawdziłem w drzewach gałęzi.

## Werdykt

**Opinia jest rzetelna i jej najważniejszy wniosek jest poprawny.** Trzy twierdzenia
potwierdziłem niezależnie, jedno potwierdzam z zastrzeżeniem co do mechanizmu, jedno
(najciekawsze) **nie da się rozstrzygnąć** na dostępnych danych — i oni sami to przyznają.

---

## 1. CO POTWIERDZAM — arytmetyka capa

Policzone na 32 ukończonych poziomach z r085:

| próg capa | ucięłoby ukończonych poziomów | % | mediana uciętych |
|---|---|---|---|
| arming **20k** (bez drabinki) | **23 / 32** | **71,9%** | 37k |
| cap 45k | 5 / 32 | 15,6% | 67k |
| @20k z drabinką ~65k | 4 / 32 | 12,5% | 68k |
| @60k z drabinką ~195k | **0 / 32** | 0,0% | — |

Mediana kosztu ukończonego poziomu: **30k tokenów**.

To jest dokładnie to, co piszą: *„cap jest inertny tam, gdzie jest marnotrawstwo
(@60000 = 195k nie wiąże), i destrukcyjny tam, gdzie jest pokrycie"*. Przy armingu 20k
**7 z 10 ukończonych poziomów** przekracza próg. Ich wniosek „@20000 bez
`ARC3_LEVEL_MIN_DONE=1` kosztuje ~8 punktów" jest wiarygodny, a mechanizm
(MIN_DONE chroni wczesne poziomy) — spójny z danymi.

## 2. CO POTWIERDZAM — retrakcja o `v13.4` i standard weryfikacji

`v13.4` **istnieje**: `arc-agi-3/duck-v13-4-unified` jest w drzewie Smaka. Retrakcja
(„sprawdziłem `gh api trees | grep | head -20`, `head` uciął wynik") jest słuszna,
a zaproponowany warunek — `git cat-file -e <rev>:<path>` zamiast listy z `head` — jest
poprawny i wart wpisania do zasad wszystkich sesji.

To druga retrakcja w tej kampanii (pierwsza: „3,6× luka silnika nie istnieje").
**Retrakcje są tu mocniejszym sygnałem jakości niż jakikolwiek wynik.**

## 3. POTWIERDZAM Z ZASTRZEŻENIEM — „metric.py z testem 30/30, którego oni nie mają"

Testy reguły `min(115, …)` + cap ukończenia **istnieją u dwóch sesji**, nie tylko u 7911:
* `7911` — `metric.py` (deklarowany test 30/30),
* **Gemma `c4eeb067`** — `ARC3/local-lab/test_lab.py`: `test_per_level_cap_is_115`,
  `test_completion_cap`, `test_partial_level_not_credited`, `test_depth_dominates`
  + `verify_scoring.py` (34/34 zgodnych z harnessem).

Smak rzeczywiście **nie ma** testu tej reguły — to trafna obserwacja. Ale „jedyna rzecz,
której nikt inny nie ma" to **nieprawda**: Gemma ma to samo, niezależnie. Wniosek
praktyczny bez zmian (warto mieć test), tylko atrybucja szersza.

## 4. NIE DA SIĘ ROZSTRZYGNĄĆ — czy RESET obniża koszt poziomu

Ich symulacja zakłada **niezmieniony koszt poziomu po resecie**. Sprawdziłem, co da się
wyciągnąć z r085: w historii 10 gier jest **16 akcji RESET**. Koszt pierwszej akcji po
resecie = mediana **3 397 tok** vs **1 787 tok** dla pozostałych (1,90×), ale **n = 15**.

To **nie jest** pomiar kosztu poziomu po resecie — tylko pierwszej akcji (re-prefill
kontekstu), która z definicji jest droższa. **Hipotezy nie da się rozstrzygnąć na
zapisanych danych**, bo r085 jest runem bez capa, więc resetów jest za mało.

Konsekwencja, którą sami uczciwie zasygnalizowali: **znak bilansu jest niepewny**.
Strona straty (−8,06) jest skwantyfikowana, strona zysku (czy reset kupuje tańszy
poziom) — nie. To jest właściwe ustawienie problemu, nie błąd.

## 5. Rekomendacja, którą podpisuję bez zastrzeżeń

> **Nie uzbrajać 20000 bez `ARC3_LEVEL_MIN_DONE=1`.** Sam `MIN_DONE=1` przy 60000 nic
> nie zmienia, więc jest darmowym bezpiecznikiem.

Do tego moja uwaga z `co_next.py`: cap/eskalacja to nadal **jedna dźwignia**. Nawet
naprawiony, nie zmienia tego, do których gier idzie budżet — a dokończenie poziomu
w `cn04` jest warte **+28,57**, gdy w `ls20` **+3,29**. Cap decyduje *jak długo*, nie
*na co*.

## 6. Co dorzuciłbym do ich metodologii

Zasada z ich incydentu pushowego (lokalna gałąź cofnięta → commit objął całe drzewo →
naprawa bez force-push) zasługuje na regułę: **przed commitem `git status` + `git diff --stat`
względem `origin`, nie względem lokalnego HEAD.** Ten sam gatunek błędu co `head -20`:
narzędzie zwróciło sukces, więc uznano wynik za prawdziwy.

---

## Podsumowanie w trzech liniach

1. **Mają rację co do capa 20k** — potwierdzone na 32 poziomach: ucięłoby 72% ukończonych.
2. **Mają rację, że nie da się tego domknąć bez pomiaru resetu** — i mówią to wprost.
3. **Ich „jedyne, co wnoszę" jest warte więcej niż sami przyznają**, bo wskazuje
   mechanizm (cap trafia w zły punkt), a nie tylko liczbę.
