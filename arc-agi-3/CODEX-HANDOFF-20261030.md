# Pakiet do przeglądu innych gałęzi — Codex, 30.10.2026

## Zacznij tutaj

Pakiet obejmuje aktualny warsztat lokalny i eksperymentalny wariant v18 z tej
rozmowy. Powstał na najnowszej pobranej gałęzi Smak, tip03ae156. Starsze
notatki27–29.10 w analysis/history-20261027-29 są zapisem ówczesnego stanu.
Aktualne ograniczenia i rozstrzygnięcia podano niżej.

## Kod i pomiary

- rust/src/ffi.rs oraz analysis/native_kernels.py dodają prawdziwe FFI ctypes
  do biblioteki Rust. Batch obsługuje Rayon. sweep2.py domyślnie korzysta
  z Rusta i16 niezależnych procesów gier. RUN-PC.ps1 buduje bibliotekę
  i uruchamia sweep. Brak DLL powoduje jawny błąd.
- analysis/native-benchmark-results.json dokumentuje267 zgodnych przypadków.
  Dla25 plansz kandydaci kliknięć wymagali135ms Python,3,08ms Rust FFI,
  1,45ms Rust FFI/Rayon16. To pomiar konkretnego kernela.
- Cały search na3 grach dał te same sekwencje, węzły i stany. Przyspieszenie
  całości małe. Deepcopy i logika gry pozostają w Pythonie.
- Rustowy scoring ma cap1,15 per poziom i ważony cap ukończenia per gra.
  Zachowane36 testów przechodzi. compare_runs.py odtwarza r085=26,7814614273.
  To przeliczenie zapisanego wyniku, nie prognoza nowego agenta.
- evolve_search.py zapewnia bounded genes, kontrolę rodzica, etapy selekcji,
  podział17/8 gier, logi, wznawianie i zewnętrzny timeout procesu.
- Wynik eksperymentu127 prób/13 konfiguracji to4 vs2 ukończenia treningowe
  i2 vs2 walidacyjne.47 prób odzyskano,80 nowych zajęło49,1s.
  Potwierdzone rozwiązania są odtwarzane w silniku. To optymalizacja searcha
  na prawdziwym stanie publicznego silnika. Transfer do agenta konkursowego
  wymaga testów na dozwolonych obserwacjach i z docelowym modelem.
- propose_search.py tworzy propozycje z24 bootstrapowych modeli ridge,
  nie korzystając z wyników walidacyjnych. MSE leave-one-genome-out0,5605
  wobec0,5946 średniej per gra. Poprawa predykcji jest wstępna i niewielka.
  Przewaga selekcji nad losową ewolucją w równym budżecie nie została zmierzona.

## V18

duck-v18-experiment zawiera przypiętą bazęv13.7, builder, notebook i metadane,
kod wyboru kliknięć, probe i test sandboxa. Domyślne plan() dostaje kliknięcia
z widocznych obiektów i historii. Jawne actions mają pierwszeństwo.
Patche nałożono na r033. Sandbox sprawdził plan i explicit override.
Windows wymagał adaptera startu z pliku z identycznymi bajtami bootstrapa.
Na25 plansz14/19 gier myszowych miało widoczną reakcję na propozycje kliknięć.
Pełna przewaga v18 nadv13.7 z modelem LLM pozostaje niezmierzona.

## LM Studio i lokalna polityka

Uruchomiono lms server start. Qwen3.5-4B pod identyfikatorem arc-lab-fast,
context8192, GPU0,9, parallel1, idle TTL1800. Natywne /api/v1/chat z
reasoning=off zwróciło poprawny JSON,0 tokenów reasoning i około35tok/s.
/no_think oraz reasoning=off w /v1/chat/completions nie wyłączały reasoning
w lokalnej wcześniejszej próbie. Istniejący llm_policy.py nadal używa
chat/completions. Wymaga osobnej adaptacji, jeśli ma korzystać z natywnego API.
Poprawki27.10 obejmują inicjalizację licznika audytów, bezpieczniejsze
parsowanie klików i lokalny evaluator z danymi kliknięć oraz scoringiem SDK.

## Audyty i research

- analysis/review-2026-10-30/RAPORT.md porównuje6 gałęzi, z przypiętymi SHA.
- analysis/RIEMANN-TO-ARC.md opisuje przeniesioną metodologię Kaggriculture.
- analysis/LEADERS-AND-METHODS-20261030.md dokumentuje bezpośredni odczyt API
  i uruchomienie LM Studio.
- analysis/LEADER-HISTORY-20261030.md zawiera starsze ślady wyników liderki.
- API potwierdziło75,56 i70,02. Prywatna metoda liderki pozostaje nieustalona.
- Pobrane publiczne notebooki dwóch autorów miały identyczne komórki kodu.
  Katalogi źródeł są dowodem do analizy, nie rekomendacją do uruchomienia.
- Nie uzbrajać20k na podstawie replayów. Cap0 jest kontrolą. MIN_DONE1 przy
  cap0 nie zmienia zachowania, a po uzbrojeniu ogranicza tylko część ryzyka.

## Kolejność dalszej pracy

1. Odczytać wynik już wysłanego57811453. Zachować najlepszą zmierzoną wersję.
2. Przejrzeć v18 oraz native ABI i sprawdzić porównanie pełnych agentów
   v13.7/v18 na tych samych grach, modelu, kwantyzacji i budżecie.
3. Ocenić D′ w oddzielnym przebiegu z tymi samymi metrykami ukończeń/punktów.
4. Porównać pamięć poziomów lalalia z obecną pamięcią, mierząc cache i tok/akcję.
5. Rozszerzać genotyp o obserwowalne mechanizmy agenta i zweryfikowane modele
   świata. Liczba publicznych rodzin nadal wynosi25. Nowy seed nie jest nową grą.

Potrzebne recenzje obejmują izolację klonowania, poprawność FFI, rzeczywistą
ścieżkę plan() w sandboxie, kryteria selekcji ewolucyjnej i zgodność punktacji.

## Weryfikacja pakietu przed commitem

W kopii publikacyjnej108 testów llm-agent przeszło przy PYTHONUTF8=1.
Bez tego ustawienia jeden istniejący test CLI na Windows nie mógł wypisać
znaku strzałki w kodowaniu CP1250. Test sandboxa v18 przeszedł ponownie
z notebooka znajdującego się w kopii publikacyjnej.

36 testów Rust również przeszło. git diff --cached --check jest czysty.
Hash plików w zapisanych manifestach pochodzi z oryginalnych przebiegów
Windows. Git może normalizować zakończenia linii. Do nowego eksperymentu
należy wygenerować nowy manifest, a nie pomijać kontroli zgodności.
