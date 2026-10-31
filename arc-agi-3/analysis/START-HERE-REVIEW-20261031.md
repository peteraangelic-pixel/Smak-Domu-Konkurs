# Aktualny pakiet do niezależnego audytu, 31 października

## Co faktycznie dały prace

Wielogodzinne próby lokalnego Qwena były głównie diagnostyką. Wariant probe i zmiana temperatury nie zwiększyły ukończeń. Temperatura0.7 ograniczyła powtarzanie kodu, ale nadal dała0 ukończonych poziomów. Nie wytrenowano ani nie ulepszono wag modelu. Ta część prac była zbyt czasochłonna względem uzyskanego postępu.

Konkretny postęp powstał przez napisanie kontrolera symbolicznego na CPU, a nie przez samo dalsze liczenie GPU. Z pikseli i przykładów na planszy wyprowadza regułę, przenosi ją między poziomami, sprawdza efekty legalnych akcji i oddaje sterowanie LLM przy braku rozpoznania. Nie ma ID gier, gotowych ścieżek ani dostępu do silnika w polityce.

Potwierdzony wynik:3 poziomy publicznego ft09 w25 akcjach,około4.8s przez rzeczywisty Duck bez LLM. Późniejszy pełny test z Qwenem potwierdził3 ukończenia wobec0 kontroli przy tym samym budżecie8192 tokenów. Qwen po przejęciu sterowania nie dodał ukończeń ani akcji. To jedna znana gra użyta w rozwoju,nie ślepy test generalizacji. Moduł abstynuje na24 innych publicznych grach. Nie ma wyniku Kaggle ani dowodu50+.

Rust/Rayon przyspiesza nowy kernel prostokątów około33x w zapisanym pomiarze,nie całą grę ani LLM. CPU ewaluacja używa16 procesów. Notebook zachowuje przenośny wariant NumPy; DLL Windows jest tylko lokalnym przyspieszeniem.

## Czytać w tej kolejności

1. [HYBRID-RESULT-20261031.md](HYBRID-RESULT-20261031.md) — ostatni zakończony test całej lokalnej hybrydy,warunki porównania i ograniczenia.
2. [SYMBOLIC-CONTROLLER-20261031.md](SYMBOLIC-CONTROLLER-20261031.md) — architektura,benchmark25 gier,Rust/FFI,testy i komendy odtworzenia.
3. [DIAGNOSTIC-FINAL-20261031.md](DIAGNOSTIC-FINAL-20261031.md) — wcześniejsze nieudane próby probe/temperatury; przydatne do unikania ich powtarzania. Nie ocenia późniejszego modułu template.
4. [V13-7-SCORE-STATUS-20261031.md](V13-7-SCORE-STATUS-20261031.md) — kontekst rzeczywistych historycznych zgłoszeń Kaggle; rekomendacja GO dla v13.7 wycofana.

Pliki NIGHT-HANDOFF,NIGHT-UPDATE,MORNING-REPORT,DIAGNOSTIC-NEXT,HYBRID-HANDOFF i wcześniejsze raporty rozwoju traktować jako dzienniki historyczne. Ich instrukcje o oczekujących testach zostały zastąpione wynikami powyżej. Nie uruchamiać z nich ponownie macierzy. Oba monitory zakończonych testów usunięto.

## Audytować kod i dane,nie tylko opisy

- [template_transfer.py](template_transfer.py): rozpoznawanie widocznych przykładów,uczenie relacji,przenoszenie ograniczeń i odrzucanie sprzecznych predykcji.
- [template_hook.py](template_hook.py): połączenie z istniejącym narzędziem akcji Duck i fallback do oryginalnego LLM.
- [agent.ipynb](../duck-lab-candidates/template/agent.ipynb): dokładnie testowany notebook,SHA256 `550eb185aa12efe9450e011c794ff12625adc18db287cf9f8248fa716208d5fa`.
- [test_template_transfer.py](tests/test_template_transfer.py): testy palet/obrotów,abstencji i izolacji stanu. Testy odporności nie zastępują nowych mechanik.
- [paired-comparison.json](causal-agent-20261031/hybrid-full-ft09/paired-comparison.json) oraz [game-run.json](causal-agent-20261031/hybrid-full-ft09/game-run.json): wynik porównania i25 rzeczywistych akcji; w tym samym katalogu pełne API/requests/transcript/manifest/result.
- [public25-final-comparison.json](causal-agent-20261031/public25-final-comparison.json): zakres25 gier i75 zgodnych śladów backendów.
- [rectangles.rs](../rust/src/rectangles.rs),[native_rectangles.py](native_rectangles.py),[structural-verification.json](causal-agent-20261031/structural-verification.json): port Rust/FFI i rzeczywisty zakres przyspieszenia.

## Zadanie dla niezależnego AI

Sprawdź odtwarzalność oraz to,czy kontroler korzysta wyłącznie z dozwolonych obserwacji. Oceń ryzyko fałszywego rozpoznania na nowych planszach,izolację pamięci między grami i poprawność fallbacku. Oddziel3 ukończenia na znanym publicznym ft09 od generalizacji na inne mechaniki. Zaproponuj albo zaimplementuj kolejną zdolność na innej rodzinie gier,sprawdzając ukończenia i regresje na wspólnym korpusie. Nie uznawaj większej liczby akcji ani testów jednostkowych za wzrost wyniku Kaggle. Nie zgłaszaj notebooka bez osobnej zgody użytkownika.

Kod modułu:commit f730639; pełne lokalne wyniki: aec6c3e; doprecyzowanie instrumentów:91f1ce9. Gałąź `codex/arc-local-lab-v18-20261030` w repo Smak-Domu-Konkurs. Nazwa gałęzi jest historyczna i nie oznacza,że notebook template to wcześniej testowana v18. Lokalny checkout publikacyjny znajduje się w `.publish-review`.
