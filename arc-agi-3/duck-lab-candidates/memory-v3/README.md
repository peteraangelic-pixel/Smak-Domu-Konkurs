# v3 + pamięć ukończonych poziomów: eksperyment na docelowym modelu

Notebook SHA256:1e73906cf1c99d65b17b41e18ecc7633438158aae42bc6383cb8570e97ca5a61.

Kontrola: dokładna odzyskana v3,świeży prywatny test27.49667/33 ukończenia na10 publicznych grach. Ten wynik nie jest wynikiem punktowanego rerunu. Nowy wariant ma osobny prywatny slug petersharps/arc3-codex-memory-v3-lab. Nie ma jeszcze zmierzonej jakości i **nie jest prognozą60 punktów**.

## Uzasadnienie

W logu kontroli m0r0 agent na poziomie3 wielokrotnie ponownie analizuje,dlaczego poziom2 został ukończony. To bezpośrednia obserwacja utknięcia,nie dowód utraty danych przez trimmer. Hipoteza eksperymentu: krótka trwała pamięć zweryfikowanego ukończenia oraz własnego opisu reguły może ograniczyć takie powroty.

## Jedna zmiana mechanizmu

Dodano tylko pamięć ukończonych poziomów. Pozostałe komórki v3 (poza nagłówkiem i jedną nową komórką patcha) są identyczne; serwowanie,budżety,roster i temperatura bez zmian. Nie dodano hintu,template,routera ani capa.

Pamięć zapisuje fakty zaobserwowane w tej grze i pyta o krótką regułę po ukończeniu. Wnioski modelu nie są traktowane jako zweryfikowane prawa: instrukcja wymaga sprawdzenia na nowej planszy. Blok jest odświeżany po przycięciu historii,aby ograniczać dodatkowe zmiany prefiksu cache. Oprócz limitu tokenów obsłużono przycięcie limitem liczby wiadomości. Zmiana ścieżki stanu gry czyści rekordy i stary blok. Mechanizm może też pogorszyć wynik przez dodatkowe tokeny lub utrwalenie błędnej hipotezy; właśnie dlatego jest osobnym eksperymentem.

Pochodzenie: publiczny hook lalalia9/vickyfym,adaptowany z rellik13/sirikilohit (CC-BY4.0); lokalny lalalia_compat; nowe opakowanie memory_v3.py obejmuje zdarzenia przycięcia,izolację i telemetrię.

## Weryfikacja przed push

- Pełny łańcuch patchy stosuje się na rzeczywistym r033,źródła inference kompilują się.
- Rzeczywiste ukończenie poziomu ft09 przez silnik jako fixture testu infrastruktury:4 akcje,4 zapisane; żądanie reguły aktywne.
- Pamięć obecna w rzeczywistym promptcie po przycięciu tokenowym i przetrwała drugie przycięcie. Brak wcześniejszej zmiany system promptu.
- Przycięcie samym limitem wiadomości także przypina pamięć; stabilna historia nie zmienia jej ponownie.
- Dwa obiekty agenta i dwie ścieżki stanów nie współdzielą rekordów.

To sprawdzenia infrastruktury ze skryptowaną regułą,nie sukces LLM. Dane analysis/memory-v3-target-20261031/activation-final/result.json i eviction-isolation.json.

## Pomiar Kaggle

Tak jak kontrola:10 publicznych gier,48min/gra,concurrency10,jeden pass,Flash-Next W4A16+drafter. Rzeczywista aktywacja musi być widoczna w logach: SLM_V3_CAPTURE oraz SOLVED_LEVEL_MEMORY pinned. Gdy nie wystąpi,nie interpretować remisu jako testu wpływu pamięci.

Porównanie obejmie ukończenia per gra,średni wynik,nowe zera,czas,tokeny i błędy. Pierwszy próg użyteczności: więcej niż33 ukończenia bez spadku średniej27.49667 i bez nowych zer; analizować także regresje rodzin gier. Pojedynczy przebieg nie dowodzi stabilnej przewagi,przyczyny historycznego13.28 ani wyniku ukrytego rosteru.

Zgoda użytkownika na prywatne uruchomienia jest udzielona. Nie wykonujemy automatycznej submisji konkursowej na podstawie smoke. Zlecenie push: Actions41246641520; sprawdzić artefakt memory-target-push.txt,bo sukces Actions sam nie dowodzi przyjęcia notebooka.

Odtworzenie:

```powershell
& arc-agi-3/.venv-local/Scripts/python.exe -X utf8 arc-agi-3/analysis/build_duck_variants.py --name memory-v3 --base-notebook arc-agi-3/analysis/champion-recovery-20261031/champion-v3/arc3-duck.ipynb --source-output NOWY_KATALOG
```

Aktualizacja: Kaggle potwierdził Kernel version1 successfully pushed. Kolektor: Actions41246697654,tryb memory-watch,maksymalnie100min,bez ponownego pusha i bez submisji.
