# Raport poranny ARC — 31.10.2026,06:00 Europe/Warsaw

Nie uzyskano potwierdzonej lepszej wersji do submisji. Zachowujemy dotychczasową kontrolę. Notebooki memory/router są artefaktami eksperymentalnymi, a nie kandydatami z udowodnioną przewagą. Submisji ani publikacji Kaggle nie wykonano.

## Ukończone testy pełnej pętli

Model Qwen3.8-27B Q4_K_M, częściowy offload GPU0.20/RAM, kontekst16384, obrazy4x, seed731, temperature0, reasoning wyłączony. Faktyczny Duck ToolAgent, sandbox Python, HarnessGameSession, silnik arcengine i scoring SDK. To inny model/kwantyzacja/kontekst niż konkursowy Flash-Next/SGLang; wyniki nie przewidują punktów Kaggle.

| Budżet | Wariant | Gra | Ukończenia | Akcje | Sekundy |
|---|---|---|---:|---:|---:|
| 1024 | control | ls20 | 0 | 4 | 338.2 |
| 1024 | control | vc33 | 0 | 5 | 372.9 |
| 1024 | memory | ls20 | 0 | 4 | 338.4 |
| 1024 | memory | vc33 | 0 | 6 | 330.9 |
| 1024 | router | ls20 | 0 | 0 | 320.7 |
| 1024 | router | vc33 | 0 | 5 | 333.4 |
| 1024 | v18 | ls20 | 0 | 4 | 333.1 |
| 1024 | v18 | vc33 | 0 | 6 | 325.5 |
| 4096 | control | ls20 | 0 | 5 | 1142.5 |
| 4096 | control | vc33 | 0 | 5 | 1127.8 |
| 4096 | memory | ls20 | 0 | 5 | 1132.1 |
| 4096 | memory | vc33 | 0 | 12 | 1248.5 |

Łącznie12 zamkniętych prób pełnego agenta:8 pilotowych i4 rozszerzone. Brak błędów API i nieobsłużonych wyjątków. W rozszerzonym przebiegu nie zadziałał limit czasu: zużyto pełne4096 tokenów. Wszystkie próby zakończyły się bez ukończeń. Zwiększenie budżetu nie wykazało poprawy na tych dwóch grach.

## Interpretacja i decyzja

- Pamięć miała memory_levels=0 i memory_pinned_chars=0 we wszystkich żywych próbach. Nie testuje to jej korzyści po ukończeniu poziomu. Zero remisów nie oznacza, że pamięć jest dobra ani zła. Naprawiona kompatybilność z istniejącymi notatkami jest niezależnie potwierdzona testem realnego przejścia ft09 i dwóch przycięć historii.
- Router na ls20 w pilocie nie wykonał akcji przy1024 tokenach; brak podstaw do promocji routera. Na vc33 wykonał5 akcji i nie ukończył poziomu.
- Raporty group_regressions wymagają identycznego korpusu, modelu, budżetu i obrazu. Tutaj grupy mouse-only/keyboard-only mają zerową różnicę score, lecz po jednej rodzinie na grupę i jeden seed: to mało informacyjne badanie, nie dowód generalizacji.
- W logach rozszerzonej kontroli ls20 model wielokrotnie wypisuje regiony tej samej planszy i opisuje geometrię bez nowych działań. Większa liczba parametrów sama nie usunęła jałowych inspekcji. Nie przypisujemy tego wyniku konkursowemu modelowi ani wszystkim grom ARC.
- Adaptacyjna ewolucja została wdrożona z ponownym dopasowaniem po pokoleniu. Równe zachowanie elit,121 prób na metodę: obie metody4 ukończenia treningowe/2 walidacyjne. Brak przewagi nad znanym najlepszym searcherem.

## Artefakty do przeglądu

- duck-lab-candidates/memory/agent.ipynb — osobny patch pamięci z poprawką kolizji. Zachowane attribution lalalia9/vickyfym i rellik13/sirikilohit.
- duck-lab-candidates/router/agent.ipynb — osobny eksperyment routera obserwacji.
- analysis/duck-loop-pilot-20261031 i duck-loop-extended-20261031 — manifesty, surowe odpowiedzi API, transkrypty i wyniki.
- analysis/memory-packaged-20261031/result.json — pamięć faktycznie obecna w request po1. i2. trimie; reguła jest scripted test data, nie wynikiem LLM.
-119 testów przeszło przed nocnymi próbami; nocne modyfikacje kontrolera dotyczą parametryzacji budżetu i zostały wykonane w czterech zakończonych procesach.

Na poranny slot nie rekomendujemy zastąpienia zmierzonej kontroli tymi eksperymentami. Potrzebny kolejny eksperyment aktywnie zmieniający eksplorację/uczenie mechaniki oraz test przy docelowym modelu. Nie deklarujemy50+ ani poprawy leaderboardu.

Nocne procesy zakończyły się. Jednorazowy heartbeat zostaje usunięty po raporcie; nie uruchamiamy kolejnych automatycznych prób bez końca.
