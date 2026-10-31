# Aktywny test nowego modułu symbolicznego

ZAKOŃCZONE: czytaj HYBRID-RESULT-20261031.md. Hybryda3 poziomy/25 akcji kontra kontrola0 poziomów/2 akcje,przy zgodnych modelu i budżecie8192 tokeny. Fallback do LLM56 wywołań API był rzeczywisty,bez błędów API,lecz nie dodał akcji/ukończeń na poziomie4. Jedna NameError w kodzie narzędzia; brak crasha i limitu czasu. Nie uruchamiać ponownie. Po archiwizacji usunąć heartbeat. Dalsze instrukcje są historyczne.

Czytaj SYMBOLIC-CONTROLLER-20261031.md. Nowy kod i notebook template nie zawierają ID gier,gotowych ścieżek ani dostępu do silnika. W dwóch rzeczywistych przebiegach controller-only przez Duck/sandbox ukończyły3 publiczne poziomy ft09 w4+7+14=25 akcjach,0 tokenów,oracle_replay=false.4,766s i4,813s. Drugi przebieg zachował25 prawdziwych rekordów w game-run.json. Dalej polityka abstynuje. Notebook w trybie normalnym przekazuje wtedy sterowanie oryginalnemu LLM.

Teraz działa JEDEN `run_duck_loop.py` dla `analysis/causal-agent-20261031/hybrid-full-ft09`,na Qwen3.8-27B Q4,16k kontekstu,thinkingOFF,temp0,8192total/4096request/3600s,seed731,image4. Nie dublować ani nie zmieniać załadowanego modelu. Źródło `analysis/causal-agent-20261031/packaged-template-final/ARC3-Inference`,notebook `duck-lab-candidates/template/agent.ipynb`,SHA550eb185aa12efe9450e011c794ff12625adc18db287cf9f8248fa716208d5fa.

Po wyniku:
1. Sprawdzić error,harness_state,API errors,time_limit_binding,liczbę rzeczywistych ukończeń i potwierdzenie fallbacku API do LLM. Nie uznawać `valid_model_run=false` z trybu controller-only za błąd; pełny hybrydowy przebieg powinien użyć LLM po abstencji.
2. Porównać z `analysis/champion-probe-pair-20261031/control-ft09/result.json` (0 levels/2 actions/8192tokens). Model,budżet,seed,skala obrazu,thinking,temp0 są takie same. Zweryfikować manifesty. Inny hash notebooka jest zamierzoną zmianą polityki.
3. Zapisać porównanie poprzez group_regressions.compare,diagnose_tool_loop.py,raw result/manifest/api/requests/transcript/game-run. Jeśli próba niesprawna,opisać przyczynę zamiast promować.
4. Skopiować konkretne pliki do `.publish-review/arc-agi-3`,commit/push na istniejącej osobnej gałęzi Codex. Pełny checkout tego projektu nie jest repo; .publish-review jest repo publikacyjnym.
5. Podać uczciwy wynik lokalny i granice.25-public-game test nowego modułu działa tylko na ft09 (3 poziomy/25 akcji);24 inne gry przekazuje LLM. To nie wynik ani prognoza ukrytego Kaggle i nie dowód50+. Pełnego target Flash-Next A/B nie wykonano. Nie publikować/submittować na Kaggle bez osobnej zgody.
6. Usunąć heartbeat po zakończeniu tego pojedynczego testu. Nie rozszerzać automatycznie macierzy ani nie dublować inference.

Testy:42 Python,36 Rust;64 przypadki zgodności prostokątów,32 identyczne decyzje,75 identycznych śladów portable/Rust. CPU uruchomienia16 procesów,Rayon16 w partiach klatek. Pomiar~33x dotyczy wyłącznie kernela prostokątów. Nowa polityka została przywrócona bajtowo do SHAa948d0877c0324bc0ff213821ac5221c0fef741633e2350ed70c1b025d066332 po nieudanym rozszerzeniu wielokolorowym; to ona jest w zweryfikowanym notebooku. Nie promować niezweryfikowanej wersji z pliku multicolor-constraints.jsonl (inna SHA).
