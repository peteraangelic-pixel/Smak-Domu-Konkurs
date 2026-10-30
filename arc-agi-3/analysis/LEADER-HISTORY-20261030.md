# Starsze wyniki i wypowiedzi Yi-Chia Chen — przegląd 30.10.2026

Sprawdzono publiczne wyniki API Kaggle, publiczną listę notebooków konta
threerabbits, pobrane źródło submission-32b-fix4, indeksowane wypowiedzi
z dyskusji konkursowej i datowane relacje z rankingu. Bezpośrednie strony
dyskusji nie zwracają tekstu w narzędziu web. Próba otwarcia profilu w
przeglądarce narzędziowej zakończyła się błędem inicjalizacji środowiska.
Nie jest to pełny eksport wszystkich komentarzy konta.

## Datowane ślady wyników

| Data relacji | Wynik | Rodzaj źródła |
|---|---:|---|
| 8.10 | 55,77 | datowana relacja z publicznego rankingu |
| 9.10 | 59,17 | relacja i odnotowane ogłoszenie ARC Prize |
| 10.10 | 62,96 | datowana relacja z publicznego rankingu |
| 12.10 | 67,49 | datowana relacja z publicznego rankingu |
| 25.10 | 71,48 | datowana relacja z publicznego rankingu |
| 30.10, odczyt API | 75,56 | bezpośredni Kaggle CLI leaderboard |

Daty oznaczają odnotowane obserwacje. Nie dowodzą dokładnego czasu pierwszego
osiągnięcia wyniku. W sprawdzonych materiałach okolice60 występują na początku
października. Nie znaleziono opisu algorytmu przypisanego do tych wyników.

W dyskusji742935 liderka napisała, że nie zdecydowała jeszcze o publikacji,
a następnie zrezygnowała z publikowania rozwiązania na drugi milestone.
Sama decyzja o niepublikowaniu nie wyklucza częściowych wcześniejszych porad.
Przeprowadzone wyszukiwania takich porad dotyczących ARC nie ujawniły.

Publiczny notebook submission-32b-fix4 dotyczy AIMO Proof Pilot. Pokazuje
doświadczenie autorki z modelami32B, kwantyzacją, SGLang i speculative decoding.
Nie ustala modelu ani techniki użytej w jej rozwiązaniu ARC.

## Użyteczne techniczne źródła zastępcze

Publiczne rozwiązanie Franzena pozwala badać faktyczny kod serving/cache,
narzędzi i harmonogramu. Notebook lalalia opisuje pamięć rozwiązanych poziomów
aktualizowaną przy przycinaniu historii, z deklarowanym wynikiem31,46. Są to
konkretne mechanizmy do porównania z bazą, z zachowaniem rozróżnienia między
deklaracją autora, naszym testem lokalnym i wynikiem konkursowym.

Na zdalnej gałęzi Smak o tipie03ae156 zapisano zgłoszenie57811453 i smoke22,59,
a/call5,3. Zapis tego zgłoszenia wskazuje PENDING i0 pozostałych zgłoszeń
30.10. To stan zapisany w repo, a nie nowy odczyt bieżącego statusu z Kaggle.

## Źródła

- https://arc3.markbarney.net/news/2026-10-08-evening-arc-3
- https://arc.markbarney.net/news/2026-10-10-evening-arc-3
- https://arc.markbarney.net/news
- https://arc.markbarney.net/news/2026-10-25-evening-arc-3
- https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/742935
- https://github.com/da-fr/arc-agi-3-solution
- https://github.com/peteraangelic-pixel/Smak-Domu-Konkurs/actions/runs/41131379942
