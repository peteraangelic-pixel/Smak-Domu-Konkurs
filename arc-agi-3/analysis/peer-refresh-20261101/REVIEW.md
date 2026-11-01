# Najnowsze opinie i wersje z6 gałęzi — 01.11.2026

Przeczytano listy12 ostatnich commitów wszystkich6 gałęzi,pliki zmienione w najnowszych audytach oraz pełne odpowiedzi. SHA i daty:SNAPSHOT.json. Oryginalne opinie zachowane obok. Tytuł commita nie jest dowodem zmiany agenta.

| Gałąź | Najnowsza praca innych sesji | Wniosek |
|---|---|---|
| Pokemon/a450 | d077ee97; później tylko nasze pakiety | Brak nowego własnego agenta lub pomiaru po poprzednim odczycie. |
| Pokemon/c87 | dc15143f; nowy audyt kontroli i slim | Odtworzone33/27.49667; negatywny test reguły3 identycznych akcji. Bez zmiany notebooka/GPU. |
| Pokemon/7911 | 26f2898c,V20-CODEX-FILES.md i kalkulator | V19 (20f26743) także zmieniał wyłącznie dokument i road_to_50.py/testy. V20 koryguje mianowniki. Żaden nie jest nowym agentem. |
| Gemma/c4 | dd714e98; audyt i STATUS | Starszy agent duck-v17 pozostaje v3+template/guard. Nowy commit nie zmienia agenta;wycenia scenariusze nowych ukończeń. |
| Gemma/6d | 82727342; skrypt niezależnego audytu | Starszy v18-arena to guarded/gated template. Nowe:odtworzenie liczb,bootstrap po grach,uwagi do pakietu. Bez GPU. |
| Smak/5ed | 4edd44cb; SYNC §30 | Rekomendacja ponownego zgłoszenia dokładnej v3. Bez nowego notebooka/testu;decyzja wymaga osobnej zgody na konkurs. |

## Co przyjmujemy

1. Odrzucenie prostej reguły „3 identyczne akcje→stop” (c87). Wymagane wielokrotne ruchy występują także w wygranych poziomach. Nie wdrażać takiego guardu. Ewentualna przyszła telemetria musi wiązać akcję z obserwowanym stanem i postępem;sam hash z HUD może także mylić,więc wymaga walidacji.
2. Surowe źródła slim powinny być łatwe do znalezienia. Są już opublikowane na naszej gałęzi w analysis/v3-slim-20261101/completed-download/submission-access-20261031/slim-target-output:benchmark.json,serve.log,notebook.log oraz10 promptów. W paczce peer-review był tylko skrót;zarzut braku w paczce jest trafny,brak w repo nie.
3. Trzeba mierzyć zmienność kolejnych kontroli. Aktywnego levelscope nie przerywamy ani nie dublujemy;obiecujący wynik będzie wymagał świeżej kontroli. Bootstrap po grach nie mierzy zmienności rerunów.
4. Udział akcji na niedokończonych poziomach jest statystyką wynikową,nie samodzielnym dowodem przyczyny. Wszystkie nowe rekomendacje opierać na rzeczywistych ukończeniach i regresjach.

## Co wymaga korekty w opiniach

- verification.json był wynikiem rzeczywistego renderera ToolAgent,nie wyszukiwaniem stringów w notebooku. Dodano odtwarzalny verify_slim_sections.py;przeszedł. To fixture infrastruktury. Dowód aktywacji LLM to rzeczywiste logi promptów,już opublikowane.
- Model V20: akcje×(1−udział_niedokończonych)/koszt_ukończenia odtwarza liczbę ukończeń algebraicznie,gdy wszystkie3 parametry pochodzą z tego samego zakończonego przebiegu. Weryfikacja własna:33.0. To nie niezależna walidacja prognozy nowego agenta. Także score z podanej już liczby ukończeń nie przewiduje,czy nowy kod je uzyska.
- Gemma/c4: porównanie48min smoke z historycznym532min maksimum i innym rosterem rerunu nie dowodzi braku wpływu czasu/kolejki. Maksimum to nie zmierzony czas każdej gry. Nie zamykać tej hipotezy bez logów.
- „60+ = +2 poziomy/gra i−30% akcji” to jeden scenariusz na publicznym rosterze i założonym koszcie nowych poziomów,nie konieczny warunek dla dowolnego agenta ani prognoza ukrytego wyniku. Przy aktualnych ukończeniach sam sufit efektywności wynosi29.19,co odtworzono z danych.
- „Efektywność slim lepsza” w6d jest zbyt mocne:różnica bezwzględnej straty1.54 vs1.69 dotyczy innej populacji ukończonych poziomów;relative loss jest większe. Nie izoluje poprawy polityki.

## Dalsza praca

Kontrola v3 pozostaje bazą. Trwa już prywatny levelscope/1,collector41298108920;nie dublować. Nie znaleziono nowego kandydata z zakończonym pomiarem60+. Nie scalamy opinii,kalkulatorów i niezmierzonych patchy pod nową numeracją. Nowa wartość z audytów:odrzucenie błędnego guardu,poprawa dostępności dowodów i wymóg test–retest przed uznaniem przewagi.
