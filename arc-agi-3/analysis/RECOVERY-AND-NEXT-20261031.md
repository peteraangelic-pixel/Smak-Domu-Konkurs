# Odzyskana kontrola i następny eksperyment, 31.10.2026

## Fakty konkursowe

Odczyt tylko do odczytu przez Actions 41185887950: nasze najlepsze zapisane zgłoszenie 57247568 = 26,25, kernel `petersharps/arc3-duck`, **wersja 3**. Wersja ta została pobrana z Kaggle jawnie przez `kernels pull petersharps/arc3-duck/3`. Nie podstawiono aktualnej wersji kernela. Manifest SHA256 znajduje się w `champion-recovery-20261031/recovery-manifest.json`.

Uściślenie po pytaniu użytkownika:26,25 jest wynikiem historycznym. Nie potwierdziliśmy odtwarzalności dzisiejszego rerunu ani codziennego wzrostu trudności. W publicznej dyskusji738762 pytania o identyczne seedy/podział gier między rerunami pozostają nierozstrzygnięte w sprawdzonym widoku. Różnicy do13,28 nie wolno przypisywać wyłącznie zmianom kodu bez kontroli. Odzyskany notebook stanowi dokładną kontrolę kodu, a nie gwarancję obecnego wyniku. Źródło: https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/738762

Świeży odczyt rankingu: 75,56 / 70,02 / 58,59 / 56,02 / **51,51**. Nagrody końcowe obejmują miejsca 1–5: https://arcprize.org/competitions/2026/arc-agi-3. To zmienna sytuacja rankingowa, a nie gwarantowany próg końcowy. v13.7-final ma 13,28; rekomendacja GO pozostaje wycofana.

## Co ustalono o kodzie

- Bazowy patch Franzen jest identyczny bajtowo w v3 i v13.7 (498799 znaków z nagłówkiem komórki).
- Słownik `setup_env` jest taki sam. W obu wskazano model Flash-Next i drafter; lokalny Qwen27B nie odtwarza tego serwera.
- v3 deklaruje dwa dodatkowe patche, razem trzy warstwy. v13.7 deklaruje dziewięć dodatkowych, razem dziesięć.
- v3 ma `ARC3_WORLD_MODEL=1`; v13.7 ma `0` oraz dodatkowe mechanizmy commit/escalation/self-pace/winpath/dead-skip. Jest to konkretna różnica do ablacjonowania, **nie ustalona przyczyna spadku**.
- Uogólniono materializację źródeł bez wykonywania notebooka. Odtwarza obie wersje. Nowa materializacja v13.7 dała identyczne hashe wszystkich plików Python jak poprzednia.
- Sterownik testów przyjmuje teraz jawny `--notebook`, odczytuje jego konfigurację i nie narzuca mechanizmu commit wersji v3. Zapisuje SHA notebooka w wyniku.

## Zakończone próby diagnostyczne

`reasoning-pair-20261031`: ft09, Qwen3.8-27B Q4, 2048 tokenów, identyczna kontrola v13.7. Thinking ON: 0 ukończeń, 0 akcji, 1845 tokenów reasoning. OFF: 0 ukończeń, 5 akcji, 0 reasoning. To diagnoza budżetu; OFF nie udowodnił przewagi w ukończeniach.

`inspection-feedback-20261031`: ON, 0 ukończeń, 0 akcji, **0 aktywacji feedbacku**, 1844 tokeny reasoning. Mechanizm nie został w tej próbie oceniony. Nie uznajemy zerowego remisu za sukces.

## Konkretny kandydat do badania

`duck-lab-candidates/probe/agent.ipynb` jest oparty na odzyskanej v3. Dodaje jeden patch: po trzech wywołaniach Pythona bez wykonania akcji dołącza do zachowanego wyniku narzędzia przypomnienie o sprawdzalnej hipotezie i legalnej próbie. Nie wybiera akcji, nie blokuje kodu, nie czyta identyfikatorów ani stanu wewnętrznego gry. Serwowanie i budżety notebooka pozostają takie jak w v3.

7 testów routera/grup/feedbacku przeszło. Bazę v3 i spakowany notebook sprawdzono przez rzeczywisty sandbox/Harness z podaną sekwencją testową ft09: 1 poziom w 4 akcjach. To **kontrola infrastruktury bez LLM**, a nie wynik jakości agenta. Takie wiersze są odrzucane przez porównywarkę jakości.

## Uruchomiona para

Polecenie z katalogu projektu:

```powershell
& arc-agi-3/.venv-local/Scripts/python.exe -X utf8 arc-agi-3/analysis/champion_probe_pair.py
```

Wyniki: `analysis/champion-probe-pair-20261031`. Gra myszy ft09 i gra klawiatury ls20, kontrola v3 kontra **rzeczywiście spakowany** probe. Każda próba ma 8192 tokeny łącznie, 4096/request, 3600 s, seed731, thinking OFF, ten sam Qwen27B/16k kontekstu i skalę obrazu4. Jeden strumień inference. Skrypt ma blokadę duplikatów, zachowuje gotowe wyniki, zapisuje komendy/logi i porównanie grup. Nie publikujemy ani nie zgłaszamy na Kaggle.

To zadanie inference LLM, nie CPU sweep: dokładanie 16 procesów lub Rayon nie przyspieszy pojedynczego serwera mieszczącego model częściowo w RAM. Dotychczasowy Rust FFI i 16 procesów pozostają narzędziem do niezależnych prób CPU. Nie opisujemy testów Duck jako symulacji Rust.

Po zakończeniu: sprawdzić błędy, rzeczywiste aktywacje feedbacku, ukończenia i regresje obu grup. Brak wzrostu ukończeń oznacza brak potwierdzonej przewagi. Jeśli mechanizm nadal nieaktywny, nie powtarzać bezmyślnie macierzy. Przy zerowych ukończeniach kontroli najpierw ocenić transkrypt i ograniczenia lokalnego modelu/budżetu. Nawet dodatni wynik dwóch gier wymaga szerszego sprawdzenia i nie przewiduje wyniku ukrytego Kaggle.
