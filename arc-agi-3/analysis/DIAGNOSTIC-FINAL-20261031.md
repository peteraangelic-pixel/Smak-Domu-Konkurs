# Wynik końcowy diagnozy lokalnego Duck, 31.10.2026

**Nie uzyskano kandydata z potwierdzoną przewagą w ukończeniach. Nie rekomendujemy notebooka probe do zgłoszenia.**

## Zakończona macierz v3/probe

Qwen3.8-27B Q4,16k kontekstu,thinking OFF,temperatura0,seed731,8192 tokeny/próbę,4096/request,limit3600s. Ta sama gra i budżet w każdej parze.

| Gra | Wariant | Ukończone poziomy | Akcje | Aktywacje feedbacku | Czas s |
|---|---|---:|---:|---:|---:|
| ft09 | odzyskana v3 | 0 | 2 | 0 | 2137,688 |
| ft09 | probe | 0 | 3 | 10 | 2229,922 |
| ls20 | odzyskana v3 | 0 | 0 | 0 | 2382,953 |
| ls20 | probe | 0 | 2 | 19 | 2523,187 |

Wszystkie próby zużyły pełne8192 tokeny, bez błędów API ani osiągnięcia limitu czasu. Były błędy kodu narzędzi w niektórych próbach; są wykazane osobno w plikach diagnosis.json. Kontrola ls20 miała0 takich błędów: problemem było114 wywołań bez akcji, w tym94 powtórzenia identycznego cropu. Sam brak błędów API nie oznacza użytecznej pętli rozwiązywania gry.

Zbiorczy wynik i surowe dane: `champion-probe-pair-20261031/comparison.json` oraz katalogi czterech prób. Feedback rzeczywiście się aktywował29 razy. Nie zwiększył liczby ukończeń ani punktacji w żadnej grupie. Zerowy remis nie jest sukcesem ani dowodem ogólnej równoważności agentów.

## Jedna ablacją temperatury

Odzyskany notebook przewidywał temperaturę0.7; sterownik lokalnych testów jawnie narzucał0. Po zakończeniu macierzy wykonano jedną próbę kontrolną ls20 z temperaturą0.7. Wysłaną wartość sprawdzono w rzeczywistym payloadzie. Pozostałe parametry, notebook i hashe źródeł są zgodne z kontrolą ls20; potwierdzono to w porównaniu.

| Metryka | Temperatura0 | Temperatura0.7 |
|---|---:|---:|
| Ukończone poziomy | 0 | 0 |
| Akcje | 0 | 5 |
| Wywołania API | 114 | 46 |
| Maks. liczba identycznych fragmentów kodu | 94 | 2 |
| Błędy API / narzędzi | 0 / 0 | 0 / 0 |
| Wygenerowane tokeny | 8192 | 8192 |
| Czas s | 2382,953 | 2221,813 |

Próba zakończyła się około13:01:46 czasu polskiego, przed limitem13:25. Zmiana temperatury w tej jednej próbie ograniczyła powtarzanie inspekcji i umożliwiła ruchy, ale **nie poprawiła ukończeń ani punktacji**. Jeden seed nie uzasadnia rekomendacji kandydata ani prognozy wyniku Kaggle.

Surowe dane, diagnoza i porównanie: `capability-sampling-20261031`. Dokładne polecenie: `champion-probe-pair-20261031/capability-command.json`. Wznowienie komendy z istniejącym katalogiem wyników jest celowo blokowane, aby nie nadpisać pomiaru.

## Granice wnioskowania

- To test lokalnego Qwena27B, a nie docelowego Flash-Next/SGLang. Kontekst16k,skala obrazu4 i wyłączone thinking różnią się od oryginalnej konfiguracji konkursowej. Wyniki nie przewidują ukrytego wyniku Kaggle.
- Dokładnie odzyskana wersja3 uzyskała **historycznie**26,25. Nie potwierdzono dzisiejszej odtwarzalności tego wyniku ani codziennego wzrostu trudności konkursu. Różnicy do13,28 dla v13.7 nie przypisujemy wyłącznie zmianom kodu.
- Kontrola pozytywna ft09 sprawdziła działanie sandboxa i akcji z podaną sekwencją testową. To nie wynik modelu i nie trafia do porównań jakości.
- Łącznie pięć zakończonych prób zużyło40960 tokenów i około3h12. Nie prowadzono nowej dużej serii CPU ani nie przyspieszano inference przez Rayon. Po zakończeniu nie uruchomiono kolejnych prób; model LM Studio jest bezczynny.

Diagnoza zamknięta. Artefakty i wyniki zapisano na osobnej gałęzi Codex. Nie opublikowano i nie zgłoszono notebooka na Kaggle. Monitor tej diagnozy należy usunąć.
