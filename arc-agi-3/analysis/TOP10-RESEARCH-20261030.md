# Top 10 ARC-AGI-3: publiczne źródła, 30.10.2026

Odczytano bezpośrednio Kaggle leaderboard oraz listy publicznych notebooków
40 kont należących do obserwowanego top10. Pobrano 12 notebooków i metadane.
Nie ograniczono badania do liderki. Listy są filtrowane po konkursie ARC3;
inne konkursy tych samych osób nie są dowodem ich metody ARC3.

Pełne końcowe artefakty odczytu:
https://github.com/peteraangelic-pixel/Smak-Domu-Konkurs/actions/runs/41139538444

Wcześniejsze odczyty uzupełniające: 41139042043 i 41139320890.
Sekret pozostaje wyłącznie w kroku Actions. Workflow wykonuje leaderboard,
listowanie/pobranie publicznych źródeł oraz odczyt własnych submisji; nie
wykonuje uploadu, zgłoszenia ani zmiany konta Kaggle.

| Pozycja | Zespół | Punkty API | Co udało się ustalić o metodzie |
|---|---|---:|---|
| 1 | Yi-Chia Chen @ Fields Model | 75,56 | Brak publicznego notebooka ARC3 w odczytanej liście. Wypowiedź o niepublikowaniu M2 pozostaje aktualnym śladem; prywatna metoda nieustalona. |
| 2 | Tufa Labs | 70,02 | Publiczny Duck z pierwszego milestone i uproszczona ścieżka submisji. Publiczna stara baza nie wyjaśnia obecnego 70,02. |
| 3 | faster machine is all you need / xz | 58,59 | Brak źródeł w odczytanej publicznej liście ARC3 konta xiaoz259. Nie można wnioskować sprzętu ani algorytmu z nazwy zespołu. |
| 4 | Team Turducken | 56,02 | Keith Tyser opublikował starsze warianty serwowania Qwen3.8. Nie są dowodem kodu aktualnego zespołu. |
| 5 | the last dance | 51,51 | W odczycie czterech kont brak publicznych notebooków przypisanych do ARC3. Metoda nieustalona. |
| 6 | yktori | 51,04 | Brak publicznego źródła ARC3 w odczytanej liście. |
| 7 | mtg | 50,37 | Brak publicznego źródła ARC3 w odczytanej liście michaeltgao. |
| 8 | NVARC3 | 49,54 | Jedyny zwrócony notebook cpmpml to lista plików i próby mkdir. Nie implementuje agenta. Prace NVARC z 2025 nie dowodzą aktualnej metody ARC3. |
| 9 | Grigoriy Zatravkin & co | 47,19 | Sprawdzono grigoriyzatravkin, aizealotwu, deepdreamer, florenciasolange. Brak publicznego notebooka ARC3 w listach. Publiczna dyskusja ujawnia poprawkę uprawnień datasetu, nie algorytm. |
| 10 | 復活の混テキスト | 46,82 | Sześć starszych notebooków tanakaai24: Pathfinder, random, Duck i ledger trajektorii. Nie potwierdzają metody obecnego wyniku 46,82. |

W odpowiedzi CLI `Not found` nie należy traktować returncode=0 jako dowodu,
że konto nie ma żadnego kodu. To wyłącznie brak wyników w danym zapytaniu
publicznym. Nie przejrzano wszystkich komentarzy i wszystkich wersji każdego
notebooka ani prywatnych plików. Wniosków negatywnych nie rozszerzamy na te dane.

## Konkretne materiały i ich przydatność

### Keith Tyser: szybkość ma znaczenie, lecz to stary wariant

Źródło publiczne wskazuje zmianę serwowania na Qwen3.8 Flash Next NVFP4,
MTP, offload do RAM i watchdog procesu. Prompty i polityka Duck pozostają
w nim bazowe. Publiczne komentarze podają wzrost przepustowości ze 114 do
236 tok/s i lokalny wzrost 3,23 do 6,76. To relacja autora o starszym wariancie,
nie kontrolowany pomiar 56,02 i nie przepis do przeniesienia wszystkich flag:
stary notebook wyłącza prefix caching, a nasza linia Franzen/SGLang go używa.

https://www.kaggle.com/code/keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp/comments

### Tanaka: ledger był eksperymentem, później go usunięto

Compact Trajectory dokłada historię akcji i zmian planszy. Autor zapisuje
lokalny wynik 0,83 na 25 grach. Następny publiczny Full Harness explicite
usuwa ledger i wraca do oryginalnej polityki. Safety zachowuje LB1,17.
To szczególnie ważny kontrprzykład dla automatycznego kopiowania każdej
publicznej modyfikacji członka silnego zespołu.

https://www.kaggle.com/code/tanakaai24/arc3-qwen3-6-duck-compact-trajectory-v1
https://www.kaggle.com/code/tanakaai24/arc3-qwen3-6-duck-full-harness-v1
https://www.kaggle.com/code/tanakaai24/arc3-qwen3-6-duck-lb117-safety-v1

Pathfinder v1 i v2 mają identyczny kod wykonywalny w pobranych źródłach.
Różne nazwy nie oznaczają dwóch niezależnych rozwiązań.

### Grigoriy: operacyjna poprawka potwierdzona publicznie

Dyskusja 744659 opisuje prywatny dataset koleżanki nieudostępniony kontu
wysyłającemu submisję. Udostępnienie usunęło ten konkretny problem montowania.
Nie dowodzi to przyczyny naszych innych niskich wyników ani błędów platformy.

https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/744659

## Co wdrożono zamiast samego researchu

- Wykonano porównanie modelu pomocniczego z ewolucją: 507 prób i brak poprawy
  najlepszego wyniku. Szczegóły i surowe dane: SELECTOR-ABLATION-20261030.md.
- Dodano natywną ścieżkę LM Studio do lokalnej polityki JSON i sprawdzono ją
  w rzeczywistym silniku na dwóch grach. Nie jest to ścieżka narzędzi Duck.
- Pełne porównanie Duck v13.7/v18 oraz ablacja pamięci lalalia nadal nie jest
  wykonane. Nie przedstawiamy ich jako ukończonych wdrożeń lub poprawy score.

Ostatni świeży odczyt API w tym badaniu: 57811453 nadal PENDING. W zwróconej
historii własnych submisji najwyższy publicScore to 26,25 (57247568).
Rekonstrukcja r085=26,78146 dotyczy innego zapisanego benchmarku; nie jest
nowym leaderboardowym wynikiem tej sesji.

## Źródła robocze i granice

W katalogu top10-final-20261030 są odpowiedzi API i oryginalne notebooki.
sources-index.json wiąże referencje z hashem kodu i rozmiarem. Roster
top10-roster.json pochodzi z niezależnego agregatora jako pomoc do odkrycia
uchwytów kont; wyniki pochodzą z bezpośredniego leaderboardu Kaggle.
Wnioski techniczne powyżej oparto na samych notebookach i wypowiedziach autorów.

https://arc.markbarney.net/api/kaggle/arc-prize-2026-arc-agi-3/board
https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/742935
