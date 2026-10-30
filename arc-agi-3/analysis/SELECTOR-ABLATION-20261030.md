# Zrealizowane porównanie selektorów, 30.10.2026

## Wynik

Model pomocniczy nie znalazł wariantu z większą liczbą ukończeń niż zwykła
ewolucja lub dotychczasowy najlepszy wariant. To zamyka wcześniejszą lukę:
poprawa MSE o 5,7% nie była dowodem lepszej selekcji agentów.

| Selekcja kolejnych prób | Najlepsze ukończenia: trening 17 gier | Walidacja 8 gier |
|---|---:|---:|
| Dotychczasowy najlepszy wariant | 4 | 2 |
| Model pomocniczy, każde z 3 ziaren | 4 | 2 |
| Krzyżowanie i mutacje, każde z 3 ziaren | 4 | 2 |
| Oryginalna kontrola searcha | 2 | 2 |

507 fizycznych prób gry/konfiguracji, 27 konfiguracji treningowych, 0 błędów
wykonania, 214,39 s. 16 niezależnych procesów silnika, kandydaci kliknięć przez
Rust ctypes FFI. Wewnętrzne wątki Rayon ustawione na 1 przy 16 procesach, by
nie uruchamiać 256 konkurujących wątków. Rayon16 służy osobnym partiom kernela.

## Protokół i ograniczenia

- Obie metody dostają identyczny zamrożony punkt startowy: historyczne wyniki
  treningowe i dwóch rodziców. Po 8 nowych konfiguracji na ziarno/metodę.
- Każda konfiguracja dostaje wszystkie 17 gier treningowych, 2000 węzłów,
  8 s i maksymalnie pierwszy poziom. Budżet jednej metody to 136 nowych prób
  treningowych na ziarno. Rodzic pozostaje wspólnym zabezpieczeniem.
- Dla 3 ziaren daje to 816 rozliczonych miejsc prób. Identyczne zadania są
  współdzielone między metodami, a kolejność nowych zadań jest przemieszana.
  Wykonano faktycznie 459 prób treningowych i 48 walidacyjnych.
- Nie odczytujemy starych wyników walidacji do dopasowania ani selekcji.
  Wybrane konfiguracje zapisano w frozen-selection.json przed nową walidacją.
- To porównanie **wyboru następnej partii**, nie pełnej adaptacyjnej kampanii
  Bayesowskiej lub wielopokoleniowej ewolucji. Powtarzane ziarna używają tych
  samych rodzin gier i współdzielą próby; nie są niezależnymi replikacjami.
- Model skierował 21/24 miejsc do konfiguracji z 4 ukończeniami treningowymi,
  ewolucja 15/24. Jednak model wybrał tylko 9 różnych nowych konfiguracji,
  ewolucja 19. To opis eksploracji, nie test istotności.
- 27 genotypów miało tylko 5 różnych sygnatur ukończeń i rozwiązań. Sygnatura
  nie zawiera pełnego śladu searcha, więc nie dowodzi identyczności zachowań.
- Publiczne rodziny były wcześniej przeglądane. To nie jest nowy niezależny
  holdout ani prognoza wyniku Kaggle. Search ma dostęp do silnika offline;
  konkursowy agent musi działać przez dozwolony interfejs obserwacji.

## Odtworzenie

Uruchom w głównym katalogu projektu, na oryginalnym korpusie Windows:

```powershell
$env:PYTHONUTF8='1'
$env:OPENBLAS_NUM_THREADS='1'
& .\arc-agi-3\.venv-local\Scripts\python.exe arc-agi-3\analysis\compare_search_selectors.py arc-agi-3\analysis\evolution-watchdog-20261030 --out arc-agi-3\analysis\selector-ablation-new --count 8
```

Manifest odrzuca inne bajty gier i inną implementację workerów. Normalizacja
CRLF/LF przy pobraniu repo może zmienić hashe; w takim przypadku trzeba wykonać
nowy warm start i nowy manifest, a nie ignorować kontrolę zgodności.

## LM Studio: wdrożona integracja

LLM_API_STYLE=lmstudio_native w lokalnym llm-agent/llm_policy.py włącza
/api/v1/chat z reasoning=off. Domyślny protokół OpenAI pozostaje dostępny.
Brak treści lub reasoning mimo wyłączenia powoduje jawny błąd. Liczniki
reasoning i błędów są zapisywane przez lokalny evaluator. Naprawiono także
końcowy stan gry i numer poziomu przekazywany polityce.

smoke_native_policy.py uruchamia prawdziwe ft09 i ls20 przez mały Qwen3.5-4B,
po 6 akcji, jeden strumień inference. Potwierdzono 12 wywołań modelu, 0 tokenów
reasoning, 0 błędów API, 0 niepoprawnych akcji. Ukończeń: 0. Wyniki surowe są
w native-policy-smoke-20261030.json. 112 testów lokalnej polityki przechodzi.

Ten adapter serializuje historię jako tekst JSON, bo natywne API nie przyjmuje
listy ról OpenAI w tym samym formacie. Nie obsługuje obrazów ani narzędzi Duck.
Nie zastępuje pełnego porównania v13.7/v18 z docelowym Flash-Next i jego
kwantyzacją. To porównanie nadal jest niezrealizowane; test małego modelu nie
może być przedstawiany jako dowód przewagi kandydata konkursowego.

## Decyzja

Nie promować żadnej konfiguracji jako poprawy Kaggle na podstawie tego testu.
Nie zwiększać skali ewolucji tych samych sześciu parametrów bez nowych
mechanizmów i dokładniejszego sygnału jakości. Zachować kontrolę oraz v18
jako oddzielny eksperyment. Nie wykonano nowego uploadu ani submisji Kaggle.

## Weryfikacja pakietu

W kopii publikacyjnej przeszło razem 114 testów. Dwa istniejące katalogi
testów nazywają się `tests`, więc zbiorcze uruchomienie wymaga importlib
i jawnej ścieżki lokalnego pakietu:

```powershell
$env:PYTHONUTF8='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:PYTHONPATH=(Resolve-Path .\arc-agi-3\llm-agent).Path
& .\arc-agi-3\.venv-local\Scripts\python.exe -m pytest arc-agi-3/llm-agent/tests arc-agi-3/analysis/tests/test_selector_integrity.py --import-mode=importlib -q
```
