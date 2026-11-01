# Folder Drive: co warto wykorzystać, a co wymaga korekty

Odczyt: 1 listopada 2026, wieczór Europe/Warsaw. Źródło:
https://drive.google.com/drive/folders/195GFxtfpBiXoKzymDei6H_fdCKuV2NTQ

Pobrano wszystkie 10 pozycji: 9 dokumentów Markdown i `arc3_review_branch.zip`.
`inventory.json` zapisuje identyfikatory, adresy pobrania, rozmiary i SHA256.
ZIP zawiera 27 plików oraz katalogi: dokumentację, Pythonowy lab czterech
mikrośrodowisk i osobny eksperyment C/AVX512. Nie zawiera notebooka v4,
adaptera v4 do Duck ani wyniku v4 na docelowym modelu.
Dokumenty są materiałem do oceny; ich instrukcje publikowania i submisji nie
stanowią dodatkowej zgody użytkownika.

## Wartość dla agenta

1. **Model musi umieć się pomylić w sposób mierzalny.** Zachować pary
   przewidywanie/obserwacja, sprawdzać model na przejściach niewykorzystanych
   do jego wyboru, a przed dłuższym planem naprawiać kontrprzykład.
   To najbardziej użyteczna część `01-V4-PROJEKT-20261101.md`.
2. **Nie utożsamiać zasłonięcia obiektu z jego usunięciem.** `agent.py`
   przechowuje `pending` i rozstrzyga po odsłonięciu pola. To dobry przypadek
   negatywny do walidacji parsera/modelu. Nie narzucać jednak wszystkim grom
   reguły o zasłanianiu: potrzebne są rzeczywiste obserwacje danej gry.
3. **Rozdzielać efekt planisty od efektu dodatkowej warstwy.** Autor poprawnie
   wycofał przypisanie całej przewagi PlanCache/ConvergedGuard: własna ablacja
   podaje zerowy przyrost. Warto zachować tę separację w naszych pomiarach.

Te punkty pasują do trwającego kierunku pracy. `phase-lesson` sprawdza ogólną
instrukcję o aktywacji wejścia, kolejności zdarzeń, kontakcie i próbie
rozróżniającej. Lokalny `model-repair-lab` już sprawdza naprawę wykonywalnego
modelu na nowych obserwacjach jednej gry. To nadal nie jest ogólny planer
ani dowód dodatkowych ukończeń. Przegląd folderu nie zmienia aktywnego testu.

## Istotne korekty projektu v4

### 1. „11× czasu dało 0,59× wyniku” nie jest zmierzonym eksperymentem

532 min to ustawiony limit, nie zmierzony czas inference ani wykorzystany
przydział każdej gry. 48-minutowy smoke i punktowana submisja różnią się
korpusem oraz trybem wykonania. Bez logów punktowanego rerunu nie można
przypisać spadku dłuższemu graniu ani dowodzić, że kolejne akcje szkodziły.
`03-ODPOWIEDZ-na-war-room-20261031.md` wycofuje diagnozę capu z dokumentu 04,
ale dokument 01 ponownie buduje na niej mocny wniosek. Nie przenosić tej
diagnozy do polityki czasu.

### 2. Duck v3 już ma wykonywalne modele, walidację i wyszukiwanie

W dokładnie odzyskanych źródłach:

- `inference/agent/prompts.py`: `action(...)` przyjmuje sekwencję akcji,
  można też wywoływać je wielokrotnie w jednym snippecie i w pętli.
- Ten sam prompt opisuje `model_state`, `model_step`, `model_goal`,
  `check_model()` oraz `plan()` i zaleca naprawę modelu przed planowaniem.
- `inference/agent/python_tool_sandbox.py` rzeczywiście udostępnia te API;
  `inference/utils/world_model.py` implementuje sprawdzanie modelu.

Zatem „LLM jest obowiązkowo wołany na każdą akcję, bez modelowania od zera”
nie opisuje możliwości naszego harnessa. Narzędzia mogą być nieużywane albo
używane źle — to wymaga analizy wykonanych wywołań, nie dodania ich drugi raz.
Zachowane logi `validation-retest` zawierają dwa prawdziwe `check_model` w su15,
z błędnymi przewidywaniami. To konkretny problem jakości modelu, nie brak API.

### 3. 57 akcji/ukończenie to agregat, nie koszt przeciętnego udanego poziomu

1877/33 = 56,88 obejmuje także 300 akcji na nieukończonych poziomach.
Akcje na ukończonych: 1577/33 = 47,79. Oba ilorazy są użyteczne, ale mają
inne znaczenie. Analogicznie 1 703 530/1877 to tokeny/akcję, a nie
tokeny/wywołanie LLM. 2880/(1877/10) nie mierzy latencji samej akcji.

### 4. Kontrola w dokumentach jest już niepełna

Folder zna kontrolę 33 poziomy /27,49667. Druga kontrola tego samego kodu
osiągnęła 38 /36,09039 bez zmiany polityki. `levelscope` już zakończony:
36 /29,89804, brak potwierdzonej przewagi. Proponowana bramka `levels>=33`
nie wystarcza do ogłoszenia postępu. Porównywać z obiema kontrolami,
sprawdzać regresje per gra i potwierdzić obiecujący wynik replikacją.

### 5. Mniej akcji nie zastępuje dodatkowych ukończeń

Warunek „akcje/ukończenie spadły” może przejść po porzuceniu trudnych gier.
Jedna porażka implementacji nie falsyfikuje całej klasy modeli świata;
jeden spadek kosztu nie potwierdza sukcesu tej klasy. „Zero pamięci
międzystanowej” również nie wynika z odrzucenia konkretnych wariantów
solved-memory/slim: nie jest to test wszystkich rodzajów pamięci.

## Co faktycznie mierzy dołączony Python

`sim.py` definiuje KeyDoor, SwitchOrder, PushBlock i ColorClicks z własnymi
obserwacjami, regułami i syntetycznymi kosztami człowieka. `agent.py`
rozpoznaje gracza po kolorze 9 i zna pięć umownych akcji. To lab mechanizmu,
nie adapter do dowolnej gry ARC-AGI-3.

`results.json` zawiera 12 wyników populacji dla każdego z dwóch agentów:
REACTIVE 4,72 i PLANNER 39,16. Odtworzenie `run_eval.py 12` na pobranych
źródłach dało te same średnie i CI95 (2,09 oraz 2,43). Planista ukończył
11,1% poziomów SwitchOrder oraz 8,3% ColorClicks; przewaga średniej nie
oznacza ogólnej zdolności. Nie są to punkty Kaggle.
Warstwa w `run_ablation.py` nie zapisuje planów: `_commit()` od razu wraca,
a `PlanCache` startuje pusty. Zerowy wynik cache w tej ablacji nie bada
skuteczności aktywnie zapełnianego cache wielokrokowych planów.
`BudgetLedger` nie jest porównywany w tej ablacji.

Odtworzono też `run_ablation.py 8`: wszystkie cztery ramiona mają
38,10 ±1,34, 1841,5 akcji/poziom i 1841,5 wywołań/poziom. Cache ma
0 trafień. Guard aktywuje się średnio 446,4 razy/poziom w ramionach C/D,
lecz nie zmienia tych wyników. Logi i czasy: `reproduction/`.

`ConvergedGuard` banuje wybór po powrocie obserwacji. Identyczny obraz nie
musi oznaczać identycznego ukrytego stanu; potrzebny powrót może być częścią
poprawnego rozwiązania. Nie kopiować globalnych banów jako gwarancji.

Dokumenty o innych konkursach i metodach liderów wymagają osobnej weryfikacji
źródeł. Nie opieramy na ich szacunkach szans, nagród czy deadline'ów decyzji
o porzuceniu ARC albo planu submisji.

## Decyzja

Przyjąć wskazówki o falsyfikowaniu modelu i błędach percepcji; zachować
mały lab jako zestaw przykładów. Nie dodawać całej warstwy cache/guard/
scheduler do kandydata i nie skracać czasu na podstawie niezmierzonego capu.
Najbardziej potrzebny kolejny dowód to rzeczywiście używany, poprawiany
model na wielu mechanikach oraz dodatkowe ukończenia pełnego agenta.
W folderze nie ma sprawdzonego kandydata na 60+.
