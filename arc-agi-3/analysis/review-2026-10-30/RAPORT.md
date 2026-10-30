# Przegląd sześciu gałęzi ARC i lokalnego warsztatu — 30.10.2026

Przegląd przypięty do commitów w sources.json. Gałęzie rozwijają się równolegle; nazwa „v17” nie identyfikuje jednego agenta. Źródła opinii skopiowano do sources/. Nie zmieniałem notebooków ani nie wykonywałem submission.

## Wniosek

Najbardziej spójna baza pakietowa to Smak duck-v13-7-final (cap=0). To ocena integracji i diagnostyki, nie wykazanej przewagi punktowej. Kandydat do oddzielnego eksperymentu: Gemma 6d081d52 v17-arena-dyn z harmonogramem D′. Brak dowodu, że którykolwiek z tych najnowszych pakietów uzyskuje 50+.

Nie rekomenduję włączania cap=20000 na podstawie samych zapisanych trajektorii. Najnowsze analizy wskazują istotną utratę ukończeń, a nie mierzą nowej trajektorii po RESET ani efektu harmonogramu całego biegu. MIN_DONE=1 ogranicza część strat, lecz nie dowodzi dodatniego bilansu.

## Co wnoszą gałęzie

| Gałąź, badany commit | Najważniejsze osiągnięcie | Ograniczenie |
|---|---|---|
| Pokemon c87, f5e03fc | Audyt żywotności przełączników i diagnostyki, odtworzenie części certyfikatu, wykrycie błędu dict w guardzie oraz brakującego capa punktacji mikro-labu | Własny certyfikat miał błąd środowiskowy arcengine; rekomendacja 20k wyprzedza najnowsze wycofanie tej rekomendacji przez część innych autorów |
| Pokemon a450, 0336731 | Integracja winpath/replay, odtworzenie łańcuchów patchy v13.7 i v17-dyn; najnowsza korekta rekomendacji capa | Wyniki testów patchy nie są wynikami Kaggle |
| Pokemon 7911, 90dfaca | Poprawna metryka na zapisanych runach i symulacja kosztu porzucania; sprostowanie wcześniejszego błędnego twierdzenia o braku v13.4 | „v17” tej gałęzi jest głównie warstwą analityczną; część liczb to projekcje |
| Gemma c4eeb067, 6fcb8d9 | Self-pace eskalacji, local-lab, fastclone, analizator Rust/Rayon, krytyka capa20k | Kalibracja klonowania nie jest dowodem niezależności stanów; wariant v16 ma zgłoszone problemy metadanych notebooka |
| Gemma 6d081d52, e0e5e6d | v17-arena-dyn = baza v13.7 + D′, reprodukowalny symulator armingu z fixtures; autor wycofał bezwarunkową rekomendację20k | Brak wyniku Kaggle dla tego pakietu; 54/54 kontroli to deklarowany wynik weryfikacji innych sesji |
| Smak, de67be4 | v13.7 integruje self-pace, batching hint, winpath, sondy i uśpiony dynamiczny budżet | README nadal rekomenduje20k, ale nowy WERYFIKACJA-opinii-7911.md mówi „nie bez MIN_DONE=1”; dokumentacja nie jest spójna |

Odnośniki do opinii:
- [c87](https://github.com/peteraangelic-pixel/Pokemon/blob/f5e03fc728cd42a605cae800b449afb3f7b3fb6f/arc3-handoff/AUDYT-V13-7-I-CZTERY-OPINIE.md)
- [a450](https://github.com/peteraangelic-pixel/Pokemon/blob/0336731518dcb105176f64dc2192ac85b5f1eb0c/arc-agi-3/AUDYT-V13-4-2026-10-30.md)
- [7911](https://github.com/peteraangelic-pixel/Pokemon/blob/90dfaca727ff88cf4508a6a901955099abb81e36/arc-agi-3/V18-VS-REV2.md)
- [Gemma c4](https://github.com/peteraangelic-pixel/Gemma-konkurs/blob/6fcb8d9c9b8dfe813b2b8f4c3a38761a25de94c5/REVIEWS/2026-10-30-v13-7-rev2-vs-v16.md)
- [Gemma6d](https://github.com/peteraangelic-pixel/Gemma-konkurs/blob/e0e5e6d0aab48a6126bfda4e73deda7635cd4926/arc3_local_candidate/v17-arena-dyn/README.md)
- [Smak, najnowsze zastrzeżenie](https://github.com/peteraangelic-pixel/Smak-Domu-Konkurs/blob/de67be443cf234702af32dce7cfb661fb75d22bb/WERYFIKACJA-opinii-7911.md)

## Wyniki: czego liczby rzeczywiście dowodzą

- Symulacja7911: średnia zapisanych wyników26,44 →18,38 przy20k; MIN_DONE=1 →22,74. To kontrfaktyczny koszt na zapisach, nie wynik uruchomienia zmodyfikowanego agenta. a450 deklaruje reprodukcję1:1.
- SymulacjaGemma6d na innym korpusie:20k usuwa15/65 ukończeń;30k nie usuwa ukończeń w tym korpusie. Nie wynika z tego, że30k poprawi wynik ani że nie zmieni zachowania przez RESET.
- Wynik40,06 z paczki action-efficiency pochodzi z planisty na czterech mikrośrodowiskach. Audyty c87/c4 wskazują brak warstwy action_efficiency w tej ścieżce pomiaru, powtarzające się światy mimo różnych seedów i brak capa ukończenia; skorygowana liczba to36,31. Nie uruchamiałem ponownie całego archiwum mikro-labu; to ustalenia audytów, nie mój pomiar.
- Bramka6 akcji/wywołanie jest hipotezą operacyjną. Nie jest matematyczną gwarancją50 punktów: liczą się ukończenia, wagi poziomów, trafność planów i koszt akcji.
- Stwierdzenie c4 „zysk architektonicznie=0” wymaga ostrożności: trzeba badać cały harmonogram i deadline, nie tylko semafor. Koszt przeciętnego ukończonego poziomu nie jest też ścisłą dolną granicą kosztu następnego poziomu. Straty są mocnym ostrzeżeniem; bilansu nie zamyka sama arytmetyka na średnich.
- Nie łączyć różnych modeli i reżimów w jedną średnią: r110/r118 mają bardzo inne koszty i ukończenia niż produktywne runy8B. Wcześniejsza teza o luce silnika3,6× została przez autorów wycofana.

## Lokalny folder i poprzedni Codex

Folder jest kopią bez .git. Zawiera wcześniejszą linię v11/v12 i ulepszenia lokalnego Rusta, ale nie jest checkoutem aktualnego zdalnego v13.7. Sprawdzony lokalny ZIP ma2002 wpisy; nie znalazłem w nim osobnego arc3_lab/fastclone.

Lokalny rust/src/score.rs ma już cap1,15 na poziom i ważony cap ukończenia na grę — to istotna wcześniejsza poprawka Codexa. cargo test:36 PASS. Cargo.toml nie ma cdylib ani PyO3; CLI oferuje segment/bench/score. Lokalny sweep2.py nadal robi copy.deepcopy(state) przy każdym rozwinięciu i używa multiprocessing.

Potwierdzony zapis wcześniejszego sweepa:24 gier,14 rozwiązanych poziomów w9 grach,270265 węzłów. To liczba rozwiniętych stanów, nie270tys. niezależnych pełnych gier. Dodatkowy ograniczony przebieg lf52 jest osobnym plikiem. Nie zrobiłem teraz nowego pełnego sweepa.

Przejrzałem też historię sesji „Oceń projekt konkursowy ARC”: jej ostatni artefakt to v12 jako kontrola c45, bez wyniku Kaggle. Inna sesja z masowymi symulacjami Rust dotyczyła Kaggriculture; jej liczb nie przenoszę na ARC.

## Co naprawdę wykonuje Rust / FFI / multiprocessing

1. Lokalny arc3: natywna segmentacja, punktacja, analiza. Nie port silnika wszystkich gier.
2. Gemma c4 arc3lab: Rayon zarządza procesami Python worker.py (Command::new). To rzeczywista równoległość między zadaniami, ale przejścia gry pozostają w Pythonie.
3. Pokemon7911 rust_bridge.py: transport subprocess+JSONL do segmentacji. To nie FFI do biblioteki w tym samym procesie. Metoda click_candidates wywołuje proces dla pojedynczej klatki. Przy braku binarki/błędzie przechodzi na Python.
4. Ten bridge nie pasuje bezpośrednio do lokalnego arc3: oczekuje poleceń segment-batch/clicks, których lokalny CLI nie ma; domyślne ścieżki binarki pomijają .exe. Przed użyciem konieczny jawny test backendu, inaczej można mierzyć fallback.
5. a450 pc-sweep-pack: Python multiprocessing i realny arcengine. Dokumentacja zaleca14 workerów; dla preferowanego przez użytkownika profilu należy jawnie ustawić16.
6. Samo FFI nie gwarantuje przyspieszenia. Warto przenosić ciężkie obliczenia na zwartym stanie do Rusta i przekraczać granicę języków partiami. Uruchomienie kodu gry Python z wątku Rayon nie usuwa kosztu interpretera ani kopiowania.

Nie ma podstaw, by mnożyć przyspieszenie segmentacji200× przez16 rdzeni i traktować to jako przyspieszenie całego searcha.

## Własne sprawdzenia30.10 na tym PC

- Skopiowano źródło arc3lab Gemmy do izolowanego podfolderu gemma-rust. Build release udany,3 ostrzeżenia.
- Jego score na lokalnym r085:10/10 wyników zgodnych, max różnica drukowana0,0000, średnia26,78. To lokalny zapis smoke, nie leaderboard.
- Lokalny Rust:36 testów przechodzi.
- Źródło action_efficiency_layer z aktualnego Smaka: ConvergedGuard.filter z akcją dict rzuca TypeError: unhashable type: 'dict'. Potwierdzone wykonawczo. Nie integrować tej kopii bez poprawki i testu realistycznych akcji.
- fastclone Gemmy:42 prób zgodności na grę w jego własnej kalibracji;30 kopii każdego wariantu do orientacyjnego czasu:

| gra | deepcopy ms | fastclone ms | przyspieszenie kopiowania |
|---|---:|---:|---:|
| ft09 |3,569|1,484|2,40×|
| ls20 |16,122|8,774|1,84×|
| tu93 |1,645|0,608|2,71×|

Szczegóły: clone_measurements.json. Te liczby nie mierzą pełnego searcha ani16 procesów pod obciążeniem.

Kalibracja wybrała share_levels_and_camera także dla ls20. Autor dokumentuje, że ls20 mutuje _clean_levels. Może to wynikać z wersji silnika/gry lub z niepokrytych przejść; bez dodatkowej próby nie rozstrzygam. Z kodu wynika jednak, że kalibracja porównuje jedną trajektorię i nie sprawdza osobno niezmienności rodzica ani wzajemnej izolacji dwóch dzieci, zwłaszcza przez reset/przejście poziomu.42 prób nie jest dowodem bezpieczeństwa BFS.

## Najbardziej opłacalne następne prace na5950X/64GB

1. Bazować na najnowszym v13.7 z cap=0 i zbierać ukończenia, punkty, akcje/wywołanie, tokeny/ukończony poziom oraz udział mechanizmów w realnym biegu.
2. Rozbudować test lokalnego klonowania: rodzic→dwoje dzieci, przeplatanie różnych akcji, RESET, GAME_OVER, przejście poziomu, porównanie ze świeżym replayem. Fallback na pełną kopię przy rozbieżności.
3. Zastosować16 procesów do niezależnych zadań game×wariant×seed; zapisywać hash wersji gry i agenta, błędy, backend, szczyt RAM i węzły/s. Seed agenta nie musi zmieniać planszy; liczyć unikalne konfiguracje.
4. Limit RAM globalny i timeout procesu są ważniejsze niż samo podniesienie frontier_cap.16×8000×0,19MB daje około24GB samych stanów tylko dla przykładowego rozmiaru; nie jest gwarancją dla innych gier. Nie dodawać16 wątków Rayon w każdym z16 procesów.
5. Rust/Rayon wykorzystać do dużych partii oceny replayów, heurystyk i wyszukiwania w zweryfikowanych, zwartych modelach świata. Portować najdroższe przejścia dopiero po pomiarze i z porównaniem krok-po-kroku do arcengine.
6. Osobny eksperyment D′ jest bardziej czytelny niż jednoczesna zmiana harmonogramu i capa. Cap/reset potrzebuje aktywnego A/B z nowymi trajektoriami; replay potrafi oszacować koszt utraty ukończeń, lecz nie wygeneruje korzyści nowego zachowania.

Ten audyt nie stanowi certyfikatu całego v13.7 ani dowodu50+. Nie odtwarzałem wszystkich patchy i wszystkich testów sześciu gałęzi. Własne wykonania są wymienione powyżej; pozostałe wyniki przypisano autorom.
