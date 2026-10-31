# Odświeżenie sześciu gałęzi: kandydaci i pomysły

Odczyt GitHub po przygotowaniu Codex v11-c45-hint. „Obecny kandydat” w naszej rozmowie oznaczał właśnie ten pakiet: v11 + jedna zmienna ARC3_OPENER_COMMIT_HINT=1; nie oznaczał wszystkich późniejszych rozwiązań innych sesji. Jego pakowanie zweryfikowano,przewagi ukończeń nie zmierzono.

| Gałąź | Odczytany tip | Co nowego |
|---|---|---|
| Pokemon/a450b00f | d077ee97f02abaa7878ccc5a268918eb5820b58a | Nadal30.10; brak nowego opublikowanego kandydata. Ostatnia linia: wycofanie uzbrojenia20k,analizy capów. |
| Pokemon/c87f7a48 | b3b87822f681133264fb1a2e246c09ed025803df | Nowa odpowiedź na audyty,korekty fałszywych rozpoznań,preferencja testu statycznego capa; nie nowy notebook z wynikiem. |
| Pokemon/7911f950 | 20f26743a374114ee5bb7a67e97e27e1ae96f2ca | V19-ROAD-TO-50 i local/road_to_50.py. **v19 jest analizą,nie agentem.** Wycofanie prognoz batching/hint; preferencja dokładnej v3/v11. |
| Gemma/c4eeb067 | acb2a95fbf708549696e2f540b9116ceef35ac28 | **Nowy gotowy notebook ARC3/duck-v17**: nasz v3-template + guard32/przełącznik. To najważniejszy nowy artefakt tej rundy. |
| Gemma/6d081d52 | 3a6f66b7fe703a1f9b85ff48dc013cd72ef452bf | Naprawione --gate,nowa sonda oscylacji,plan v18-arena oraz pamięci. W tym commicie nie ma gotowej v18. |
| Smak/5ed750ef | f11039860061e1db83747c45b65ff16befa8cb4d | Jak poprzednio: A=v11-hint,B=v13.7+statyczny45k. Dokumenty,bez nowej submisji/wyniku. |

## Własne odtworzenie Gemma v17

Pobrano i przeczytano builder,guard,extractor i testy z przypiętego commita. Baza SHA550eb185 to **v3 z naszym template**,nie sama mistrzowska v3. Wynik26.25 należy do historycznej bazy,nie nowego notebooka.

Odtworzono opublikowany notebook634419B,SHA256 **76b57100dbac44a27990bc63702cf5516b9d418e3c7db2ab68d0edd13b519795**. Pełny łańcuch zastosowany materialize_duck.py do rzeczywistej czystej bazy r033; źródła inference kompilują się. Wcześniejszy test autora git apply używa atrapy z fillerem; nasze odtworzenie sprawdza faktyczny łańcuch.

Testy autora:11/11 po ustawieniu PYTHONUTF8=1 dla potomnego procesu. Bez niego test deterministycznego buildu zawiódł na Windows: builder nie podaje encoding/newline. LF znormalizowano po buildzie i dopiero wtedy uzyskano dokładny opublikowany hash. To problem przenośności buildera,nie dowód awarii notebooka na Linuksie Kaggle. Zachowano pierwotny przebieg Windows osobno.

Następnie dokładny opublikowany notebook uruchomiono przez run_duck_loop.py z controller-only: **3 poziomy/25 akcji [4,7,14],około5.06s,0API,oracle=false,error=null**. Przy abstencji kontrolowany stop kończy próbę jako cancelled; nie jest to ukończenie całej gry ani test fallbacku LLM. Dane: peer-refresh-20261031/v17-published-controller-ft09/{result,manifest,game-run}.json.

Guard32 jest faktycznie instalowany zamiast starego hooka i ma przełącznik ARC3_TEMPLATE. **Single-mismatch gate nie został dołączony**: moduł transferu jest dotychczasowym oryginałem. Limit ogranicza oscylację,ale nie dowodzi poprawnego rozpoznania mechaniki. 11 testów oraz ta próba nie mierzą nowych ukończeń ani ukrytej generalizacji. Nie wykonano docelowego Flash-Next A/B.

## Własna kontrola v19: ważna rozbieżność

Uruchomiono opublikowany local/road_to_50.py. ChainRegression().score_after = **16.3021978021978**,score_before≈27.8. Deklarowane12.8 oraz dokładność0.5 względem13.28 **nie odtwarzają się z kodu**. symbolic_coverage_needed(actions_per_level_for(levels_for_score(50))) daje **0.35502**,nie około0.24. Model zakłada220 akcji/grę,stałe liczby poziomów z10 publicznych gier i wybrany współczynnik0.93; nie jest zweryfikowanym predyktorem ukrytego rosteru.

Porównanie historycznych r085/r121 może wskazywać regresję ukończeń i kosztów. Nie izoluje wpływu samego hintu,bo zmieniło się wiele patchy. „Hint nie działa” oraz „hint da24–28” to zbyt mocne wnioski z niesparowanych danych. Również dzielenie wszystkich akcji przez ukończone poziomy miesza koszt poziomów ukończonych z nieukończonymi. Wzrost ilorazu sam nie dowodzi,że model zaczął potrzebować więcej ruchów do ukończenia porównywalnego poziomu.

**Korekta naszej rekomendacji:** v11-hint pozostaje czystą,gotową ablacją,ale brak podstaw,żeby nazywać go najbardziej obiecującą drogą do TOP5. Nowe dane osłabiają uzasadnienie pierwszeństwa oparte na batching. Nie zlecamy automatycznie dwóch zdalnych runów.

## Co warto przenieść dalej

1. Gemma v17 daje odtwarzalny sposób opakowania naszego kontrolera z guardem. To użyteczna poprawa gotowości artefaktu,nie nowa zdolność. Przed wyborem potrzeba bramki rozpoznań oraz testu fallbacku na celu.
2. Pamięć rozwiązanych poziomów i obsługa przycinania historii to nadal sensowny oddzielny eksperyment. Deklarowane31.46 publicznego notebooka nie dowodzi,że sama pamięć daje+5.2 na naszej bazie. Nasze wcześniejsze zerowe próby bez aktywacji nie oceniły tej hipotezy.
3. Przepustowość serwowania może zmieniać dostępny budżet,ale wymaga pomiaru całego agenta na docelowym serwerze i ukończeń. Sam tok/s nie daje liniowego przelicznika na wynik.
4. Historyczna dokładna v3 pozostaje kontrolą konkursową. Żadna z odczytanych nowości nie zawiera potwierdzonego nowego wyniku Kaggle wyższego od26.25.

Nie ma podstaw ani do obietnicy TOP5,ani do twierdzenia o jego matematycznej niemożności. Warianty v17,v18,v19 mają różne znaczenia w różnych repo; zawsze wskazywać gałąź,plik i hash. Nie wysłano niczego na Kaggle ani nie zmieniono cudzych gałęzi.
