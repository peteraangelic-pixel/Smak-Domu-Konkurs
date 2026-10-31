# Nowy kontroler z obserwacji: 3 poziomy, 25 akcji

## Wynik potwierdzony w rzeczywistym Duck

Spakowany notebook `duck-lab-candidates/template/agent.ipynb` ukończył pierwsze **3 poziomy publicznego ft09 w 4+7+14=25 akcjach**, przez oryginalny ToolAgent, sandbox Python i callback HarnessGameSession. Czas lokalnego testu4,766s, **0 wywołań LLM,0 tokenów,oracle_replay=false**. Nie podawano mu sekwencji rozwiązania. Przy nierozpoznanym czwartym poziomie moduł oddał sterowanie; test controller-only zakończył się przez jawny stop_event,state=cancelled,niecrashed.

Dokładny wynik: `causal-agent-20261031/harness-template-final/result.json`. SHA256 testowanego notebooka: `550eb185aa12efe9450e011c794ff12625adc18db287cf9f8248fa716208d5fa`.

Niezależne ponowne uruchomienie tego samego notebooka dało3 poziomy/25 akcji w4,813s: `harness-template-repro/result.json`. Rzeczywiste25 rekordów akcji,timingi i stan sesji są w `harness-template-repro/game-run.json`. Pusty transcript i brak requests.jsonl w tym trybie są oczekiwane: żaden model nie generował odpowiedzi.

W tym pliku SDK pokazuje28,5714 RHAE **dla jednej publicznej gry ft09 przy ukończeniu3 z6 poziomów**, nie wynik Kaggle ani średnią całego korpusu. `valid_model_run=false` jest prawidłowe: LLM nie był uruchamiany. `valid_agent_run=true` dotyczy rzeczywiście wykonanej polityki obserwacyjnej. Wcześniejszy plik `harness-template/result.json` pochodzi z pierwszego adaptera, który oznaczał abstencję wyjątkiem jako crash; nie stanowi końcowej walidacji. Poprawiono to na jawne zakończenie ewaluatora.

## Co zmieniło się w architekturze

Kontroler sam wyprowadza regułę z widocznych przykładów: wykrywa powtarzalne panele i małe symbole, uczy zależności symbol–kolor z co najmniej dwóch zgodnych przykładów, rozpoznaje panel zadania i wyznacza kliknięcie zmieniające niezgodną komórkę. Potem przenosi regułę na kolejne poziomy: kolor znacznika wyznacza jedną z dwóch barw, a wspólne komórki muszą spełnić ograniczenia wszystkich sąsiadujących symboli.

Nie ma identyfikatorów gier, stałych współrzędnych ani stałej palety rozwiązania. Polityka dostaje tylko piksele, legalne sterowanie i publiczny numer poziomu. Nie czyta kodu/stanu wewnętrznego silnika, baseline'ów, plików rozwiązań; nie klonuje silnika ani nie symuluje go wewnątrz agenta. Każdy przewidziany efekt jest sprawdzany po rzeczywistej akcji. Sprzeczność wyłącza moduł na danym poziomie. Brak rozpoznania oddaje sterowanie oryginalnemu LLM.

To działający moduł dla rozpoznawalnej rodziny mechanik, **nie dowód ogólnego rozumowania ani gotowego wyniku50+**. Opracowano go z obserwacji publicznej gry; testy obrotów i palet są testami odporności, a nie niezależnymi nowymi grami.

## Zakres sprawdzenia

Na25 publicznych grach uruchomiono3 polityki,po256 legalnych akcji maksymalnie,bez klonowania i reset-replay.16 procesów,Python+NumPy C kernels; drugi przebieg używał nowego Rust FFI do ekstrakcji prostokątów. Wszystkie75 śladów obu backendów były identyczne.

| Polityka | Ukończone poziomy łącznie | Zakres |
|---|---:|---|
| uniform | 0 | prosta kontrola cykliczna |
| causal | 1 | lp85,prymitywna eksploracja; nie dołączona do notebooka |
| template | 3 | ft09,25 akcji; abstencja w pozostałych24 grach |

Źródła: `public25-final-portable.jsonl`,`public25-final-rust.jsonl`,`public25-final-comparison.json` w `causal-agent-20261031`. Pozostałe JSONL dokumentują iteracje rozwoju,nie wyniki końcowej wersji. Końcowe ślady mają SHA polityki i ewaluatora.

Nie wykonano pełnego A/B hybrydowego Duck z docelowym Flash-Next. Nie wiadomo, czy w ukrytych grach ten wzorzec występuje ani ile wniesie do punktacji. Nie rekomendujemy zgłoszenia wyłącznie na podstawie tego wyniku. Notebook jest gotowym artefaktem do przeglądu i dalszego testowania,nie został wysłany na Kaggle.

Zakończono jeden pełny lokalny przebieg hybrydowy `causal-agent-20261031/hybrid-full-ft09`: normalny fallback do Qwena27B,bez controller-only,8192 tokeny/4096request/3600s,temp0,thinkingOFF,seed731,obraz4. Hybryda ukończyła3 poziomy,istniejąca kontrola przy tych samych limitach0. Fallback miał56 wywołań API,ale nie wykonał dalszych akcji i nie ukończył poziomu4. To wynik jednej znanej publicznej gry,nie ukrytego Kaggle. Szczegóły i błędy narzędzi: HYBRID-RESULT-20261031.md. Nie uruchamiać drugiej kopii.

## Rust,Rayon i sprawdzenie poprawności

Dodano `rust/src/rectangles.rs` z C ABI `arc3_rect_batch` i wrapper `analysis/native_rectangles.py`. Budowanie używa osobnego `target/structural`,aby nie nadpisać DLL poprzedniego benchmarka. Lokalne partie używają16 procesów i pojedynczego kernela na proces; partie klatek mogą korzystać z Rayon16 bez uruchamiania256 wątków. Notebook zachowuje przenośną implementację NumPy i nie wymaga DLL z Windows.

Porównanie64 klatek (szum,obroty,permutacje palet),32 decyzji i75 pełnych śladów gier potwierdziło zgodność backendów. Pomiar256 klatek,z alokacją buforów ctypes i konwersją wyniku: NumPy/Python0,29244s,Rust serial0,01548s,Rust+Rayon160,00875s,około33,4x dla **tego kernela**,nie całej gry ani inference. Surowy pomiar: `structural-verification.json`.

42 testy Python przeszły (w tym32 kombinacje obrotów/palet,odrzucenie sprzecznej predykcji,abstencja i izolacja stanu między plikami).36 testów biblioteki Rust przeszło. Nowy port FFI dodatkowo porównano z referencją NumPy w `verify_structural.py`.

## Odtwarzanie z katalogu projektu

```powershell
# Kompilacja lokalnego backendu Rust:
cargo build --manifest-path arc-agi-3/rust/Cargo.toml --release --lib --target-dir arc-agi-3/rust/target/structural

# Testy i zgodność FFI:
& arc-agi-3/.venv-local/Scripts/python.exe -X utf8 -m pytest arc-agi-3/analysis/tests/test_template_transfer.py -q
& arc-agi-3/.venv-local/Scripts/python.exe -X utf8 arc-agi-3/analysis/verify_structural.py

# Nowy przebieg CPU,16 procesów; użyć świeżej nazwy pliku:
& arc-agi-3/.venv-local/Scripts/python.exe -X utf8 arc-agi-3/analysis/benchmark_causal_explorer.py --workers 16 --actions 256 --rect-backend rust --out arc-agi-3/analysis/new-public25-run.jsonl

# Odtworzenie źródeł notebooka bez wykonywania komórek Kaggle:
& arc-agi-3/.venv-local/Scripts/python.exe -X utf8 arc-agi-3/analysis/materialize_duck.py arc-agi-3/duck-lab-candidates/template/agent.ipynb arc-agi-3/analysis/template-review-fresh

# Kontroler przez rzeczywisty Duck,sandbox i callback; brak LLM:
& arc-agi-3/.venv-local/Scripts/python.exe -X utf8 arc-agi-3/analysis/run_duck_loop.py --source arc-agi-3/analysis/template-review-fresh/ARC3-Inference --notebook arc-agi-3/duck-lab-candidates/template/agent.ipynb --game ft09 --variant template --controller-only --seconds 60 --out arc-agi-3/analysis/template-harness-fresh
```

Istniejące katalogi wyników nie są nadpisywane. Repozytorium nie zawiera lokalnego venv ani targetów Rust; na tym PC są już przygotowane. Serving,budżety i pozostałe patche notebooka zachowano z odzyskanej wersji3,której26,25 jest wynikiem historycznym.
