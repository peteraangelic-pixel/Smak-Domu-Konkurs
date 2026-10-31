# Nocne prace ARC — stan 31.10.2026 około 00:17 Europe/Warsaw

Użytkownik polecił pracować samodzielnie przez noc, nie czekać na jego decyzje,
używać większych modeli/offloadu RAM i przygotować rano sprawdzony notebook.
Przed każdą zmianą modelu wyładować poprzedni. Nie wysyłać Kaggle submisji;
użytkownik chce gotowy plik do samodzielnego przeglądu/wysłania.

## Wznowienie

Utworzono heartbeat tego samego czatu w aplikacji:
arc-wznowienie-nocnych-prac-o-03-00, ACTIVE, jednorazowo o 03:00 lokalnie.
target_thread_id=01a17efc-ace3-7c81-b6f3-03ccd5dcb2ef. To wznowienie po
deklarowanym resecie limitu użytkownika, nie obietnica obejścia limitów.
Harmonogram konkursu sprawdzony ponownie: oficjalnie 2.11, 23:59 UTC, nie 4.11.
https://arcprize.org/competitions/2026

## Aktualnie działające procesy

Sprawdź Get-CimInstance Win32_Process dla run_duck_matrix.py/run_duck_loop.py
oraz lms ps. Nie uruchamiaj drugiej kopii aktywnej macierzy. CLI procesy
uruchomiono przez .venv-local/Scripts/python.exe; launcher Windows może mieć
osobnego rodzica i właściwy interpreter potomny.

Aktywna macierz: analysis/run_duck_matrix.py, wyniki
analysis/duck-loop-pilot-20261031/. Jawny plan matrix-plan.json obejmuje
vc33 (mouse-only) i ls20 (keyboard-only), cztery osobne ramiona:
control, v18, memory, router. Każda próba: Qwen3.8-27B Q4_K_M, temp0,
seed731, maks.1024 wygenerowane tokeny, 512/request, 600s, obraz 256x256.
Zapisuje manifest, request/response, transcript, runtime history i result.json.
To bounded pilot pełnej pętli, nie wynik Kaggle i nie pełna walidacja25 rodzin.

Załadowany WYŁĄCZNIE unsloth/qwen3.8-27b@q4_k_m jako arc-lab-27b,
context16384, GPU offload0.20, parallel1, TTL7200. Qwen4B wyładowano przed
27B. Większy model ma17,39GB pliku, około16,2GiB wag; większość w RAM.
VRAM po korekcie około6,7GB, wolnego RAM około33GB w ostatnim pomiarze.
OpenAI-compatible reasoning_effort=none działa DLA TEGO MODELU: zero tokenów
reasoning i prawidłowe native tool_calls. Wcześniejsza porażka4B dotyczyła
innego modelu/parametru, nie jest zakazem użycia tej ścieżki.

W razie wyładowania TTL: najpierw lms ps; jeśli inny model załadowany, lms
unload <jego_id>; następnie:
lms load unsloth/qwen3.8-27b@q4_k_m --identifier arc-lab-27b --context-length 16384 --gpu 0.20 --parallel 1 --ttl 7200 -y

Nie porównuj starych infrastructure trials w duck-loop-20261031 ani
duck-loop-configured-20261031 z aktualnym pilotem. Pierwsza wersja adaptera
odtworzyła tylko delta-env, pomijając setup_env notebooka. Poprawiono to:
czytamy pełny setup_env przez bezpieczne AST (bez uruchamiania komórek shell).
Profil obrazu640x640/offload0.30 był zbyt wolny i niemal wypełniał VRAM;
przerwano go i rozpoczęto świeży, wspólny profil obrazu256x256/offload0.20.
Nie traktować tych prób infrastruktury jako wyników jakości agentów.

## Co rzeczywiście wdrożono i sprawdzono

1. evolve_search.py --selector surrogate: dopasowanie modelu po każdym
   pokoleniu, na aktualnych wynikach treningowych, z zachowaniem2 rodziców
   i kontroli tak samo jak zwykła ewolucja. adaptive-equal-elite-20261031
   vs ordinary-evolution-20261031: po121 prób, pop6/gen3/screen6,2000nodes/8s,
   16 procesów, Rust FFI. Obie:4 ukończenia treningowe/2 walidacyjne. Brak
   przewagi nad poprzednim najlepszym wariantem. Pierwszy test adaptive-
   evolution-20261031 miał inne zachowanie elit i133 próby; historyczny pilot,
   NIE używać go jako dokładnie równego porównania z121 próbami kontroli.

2. observation_router.py: prompty strategii na podstawie legalnych obserwacji
   i dostępnych akcji. Dodatkowo trzeci identyczny, czysto inspekcyjny snippet
   na niezmienionej obserwacji dostaje informację o powtórzeniu. Akcje,
   nieznane helpery i metody nie są blokowane. Bez game_id, źródeł, baselines,
   klonowania silnika lub gotowych trajektorii. Testy obejmują zmianę poziomu,
   granice poziomów, powtórzenia, ochronę action(). Przewaga w żywej pętli
   pozostaje do odczytania z aktywnej macierzy.

3. group_regressions.py: wymaga tego samego game/seed/model/budżetu/korpusu
   i grup. Wykrywa stratę grupy mimo poprawy średniej. engine-group-regressions-
   20261031.json sprawdza25 REALNYCH gier offline:8 mouse-only,6 keyboard-only,
   11 mixed; weighted_completion jest UPPER BOUND pokrycia, NIE RHAE. Nowy
   najlepszy search vs pierwotna kontrola: +2 poziomy, bez strat grup. Nie
   oznacza to poprawy LLM ani przewagi nad już znanym najlepszym searcherem.

4. materialize_duck.py i run_duck_loop.py: rzeczywiste ToolAgent +
   _HarnessGameSession + TAAF Game + arcengine, a nie polityka JSON.
   Lokalny adapter konwertuje FrameData do FrameDataRaw z tablicami int8;
   baselines ukryte przed agentem, punktacja liczona po runie przez SDK.
   Windows bootstrap zapisuje te same bajty skryptu do pliku, omijając32K
   limit linii poleceń. Inference1 strumień, CPU sweeps16. Już potwierdzono
   pełną pętlę27B -> Python sandbox ->3 rzeczywiste kliknięcia ->nowa ramka.

5. lalalia_compat.py i verify_memory_hook.py: wykryto i naprawiono realną
   kolizję. Publiczny hook lalalia podpina pamięć w _note_history_evicted,
   po czym ARC3_LEVEL_NOTES z naszej v13.7 nadpisuje system prompt i usuwa
   ten blok. Kompatybilny hook podpina pamięć PO całym bazowym trimie.
   Zweryfikowano rzeczywiste ukończenie ft09 czterema akcjami testowej
   trajektorii, zapis4 akcji, pytanie o regułę, brak zmiany systemu przed
   trimem, pamięć w aktualnym request po pierwszym i drugim trimie. Tekst
   reguły był SCRIPTED TEST DATA, nie wynikiem uczenia LLM. Oryginał: oba
   sprawdzenia obecności bloku false. Poprawiony i zapakowany: true.

6. GOTOWE osobne artefakty do przeglądu (NIE wysłane na Kaggle):
   duck-lab-candidates/memory/agent.ipynb i kernel-metadata.json;
   duck-lab-candidates/router/agent.ipynb i kernel-metadata.json.
   Oba na v13.7, cap0, konfiguracja Kaggle zachowana, po1 dodatkowym patchu.
   Builder analysis/build_duck_variants.py. Atrybucje lalalia9/vickyfym i
   rellik13/sirikilohit zachowane. Pamięć i router NIE są połączone.

7.119 testów przechodzi (112 polityki JSON,2 izolacji selekcji,5 regresji i
   routera). Zweryfikowano też import routera Z ODTWORZONEGO NOTEBOOKA:
   obie metody faktycznie podmienione. Materializer poprawiono, bo wcześniej
   pomijał patch zaczynający się --- /dev/null; teraz go uwzględnia.
   Stare drzewo packaged-router-ignored-extra-ARCHIVE zachowane do audytu.

## Co robić dalej przez noc

1. Dokończ macierz, odczytaj rzeczywiste ukończenia i błędy. Nie porównuj
   samych czasów prób z różnym kosztem prefillu; podstawą jest wspólny budżet
   tokenów, kontrola czasu i zgodność manifestów.
2. Uruchom group_regressions.py na tych samych2 grach dla każdego ramienia.
   Gdy memory_levels/pinned_chars=0, pamięć nie została aktywowana; nie
   wnioskuj wtedy o skuteczności pamięci. Gdy v18 nie używa plan(), także
   nie uznawaj tego za mocny test jej nowej możliwości.
3. Zwiększ sparowany budżet do4096 tokenów i czasu1800–2400s dla kontroli
   i najlepszego obiecującego ramienia (albo routera, jeśli pilot daje remis
   i pokazuje zablokowanie jałowych inspekcji). Zachowaj model, kwantyzację,
   obraz4x, seed, wszystkie pozostałe parametry. Nowy katalog wyników.
   Nie wymuszaj16 jednoczesnych żądań do jednego27B w RAM;16 jest dla silników
   offline, backend w tym profilu ma1 slot.
4. Jeśli wyniki pokazują regresję lub błędy, popraw przyczynę i ponów tylko
   właściwe kontrole. Nie promuj na podstawie zerowych remisów lub smoke.
5. Zapisz sprawozdanie i artefakt poranny z uczciwym statusem. Wypchnij kod,
   testy, surowe pomiary i notebook na codex/arc-local-lab-v18-20261030.
   Repo publikacyjne: arc-agi-3/.publish-review; główny folder nie jest git.
   Nie nadpisuj najnowszej głównej gałęzi innych AI.

## Weryfikacja

W głównym katalogu:
```powershell
$env:PYTHONUTF8='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:PYTHONPATH=(Resolve-Path .\arc-agi-3\llm-agent).Path
& .\arc-agi-3\.venv-local\Scripts\python.exe -m pytest arc-agi-3/llm-agent/tests arc-agi-3/analysis/tests/test_selector_integrity.py arc-agi-3/analysis/tests/test_groups_and_router.py --import-mode=importlib -q
```

Nie zapisywać plików pamięci Codex bez osobnego polecenia użytkownika.


## Aktualizacja03:00
Przeczytaj NIGHT-UPDATE-0300-20261031.md; pilot zakończony, rozszerzona macierz działa.
