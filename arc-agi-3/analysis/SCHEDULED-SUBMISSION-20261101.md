# Warunkowa submisja memory-v3:1 listopada2026,02:10 Warszawa

Użytkownik wyraźnie polecił: „wrzuc go na submisje jesli wynik bedzie okey,zrób to o2:10 w nocy”. Dotyczy memory-v3,nie innego kandydata. Jednorazowa zgoda na submisję po przejściu kryteriów. Nie wymaga ponownego pytania.

Termin: **2026-11-01 02:10 Europe/Warsaw = 2026-11-01 01:10 UTC**. Skrypt odmawia przed tym momentem i innego dnia. Automatyzacja ma wykonać tylko jedno sprawdzenie,zgłosić dokładną wersję1 albo zapisać powód pominięcia. Bez zastępczych wersji i bez ponawiania niejednoznacznego wysłania.

Kandydat: petersharps/arc3-codex-memory-v3-lab/1. Lokalny notebook SHA2561e73906cf1c99d65b17b41e18ecc7633438158aae42bc6383cb8570e97ca5a61. Przed decyzją pobrać opublikowany kod wersji1 i porównać wszystkie komórki kodu.

Kryteria „OK”,wszystkie naraz:

- Status COMPLETE,ARC3_SMOKE_OK,brak crashy i błędów hooka pamięci.
- Te same10 gier i metadata środowisk co świeża kontrola.
- **Więcej niż33 ukończenia i średnia ponad27.496670817884922**.
- Żadnej gry z zerowym ukończeniem (kontrola miała wszędzie co najmniej2).
- Rzeczywiste linie logu potwierdzają SLM_V3_CAPTURE i SOLVED_LEVEL_MEMORY pinned; sam tekst źródła patcha nie jest dowodem aktywacji.
- Istnieje output submission.parquet,wersja nie była wcześniej zgłoszona,API pozwala na zgłoszenie. Nie obchodzić dziennego limitu.

Gotowy wykonawca: analysis/submit_memory_if_good.py. Przetestowano kontrolę bramek: remis odrzucony,poprawa przyjęta,zero/crash/obcy roster/NaN/spadek wyniku odrzucone. Faktyczna komenda submit nie została jeszcze wykonana. Workflow na naszej gałęzi ma osobny tryb memory-submit oraz blokadę równoległych wykonań.

O02:10 uruchomić z dowolnego katalogu:

```powershell
gh workflow run arc3-ops.yml --repo peteraangelic-pixel/Smak-Domu-Konkurs --ref codex/arc-local-lab-v18-20261030 -f mode=memory-submit
```

Przed dispatch sprawdzić,czy automatyzacja nie uruchomiła już tego trybu i czy istnieje wynik poprzedniej próby; po nim odczytać artefakt arc-submission-access-57811453,folder memory-v3-scheduled-submit-20261101. decision.json jest decyzją; competition-submit.txt zawiera ref przyjętego zgłoszenia. attempted.json zapisuje się przed API call. Gdy istnieje próba bez potwierdzenia wyniku,sprawdzić listę zgłoszeń,zamiast automatycznie ponawiać. Wcześniej uruchomiony kolektor memory-watch (Actions41246697654) tylko pobiera wyniki,nie zgłasza.

Po zakończeniu podać wynik testu,ukończenia,aktywację,decyzję i ref zgłoszenia lub konkretny powód pominięcia. Wyniku smoke nie przedstawiać jako wyniku konkursowego. Usunąć jednorazowy heartbeat po zakończeniu.
