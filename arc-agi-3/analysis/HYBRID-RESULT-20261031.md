# Pełna lokalna hybryda: 3 ukończenia wobec 0 kontroli

Przebieg `causal-agent-20261031/hybrid-full-ft09` zakończył się po2464,078s (~41min) wraz z wyczerpaniem8192 tokenów,przed limitem3600s. Normalny tryb hybrydowy,bez `controller-only`,bez oracle/replay. Notebook SHA550eb185aa12efe9450e011c794ff12625adc18db287cf9f8248fa716208d5fa.

| Metryka | Kontrola v3 | Hybryda template |
|---|---:|---:|
| Ukończone poziomy ft09 | 0 | 3 |
| Akcje | 2 | 25 |
| Akcje na kolejnych poziomach | 2,0,0,0,0,0 | 4,7,14,0,0,0 |
| Wygenerowane tokeny | 8192 | 8192 |
| Wywołania API | 47 | 56 |
| Błędy API | 0 | 0 |
| Limit czasu wiążący | nie | nie |

Wszystkie25 akcji hybrydy wykonał kontroler symboliczny przez rzeczywisty sandbox i callback Duck. Następnie nastąpił rzeczywisty fallback do Qwena:56 poprawnych wywołań API,ale **0 dalszych akcji i0 kolejnych ukończeń**. LLM zatrzymał się na analizie czwartego poziomu. Jedna próba kodu narzędzia zwróciła `NameError: name 'json' is not defined`; nie był to błąd API ani crash sesji. Stan końcowy `gave_up` oznacza wyczerpanie budżetu.

Weryfikacja porównania: identyczny model lokalny Qwen3.8-27B Q4,seed731,thinkingOFF,temperatura0,obraz4,8192total/4096request/3600s oraz hashe trzech bazowych patchy odzyskanej v3. Różnica notebooka to moduł template. Sprawdzono hash notebooka i25 prawdziwych rekordów akcji w game-run.json. Porównanie `group_regressions.compare` dało+3 poziomy i brak błędów API/crash/obcięcia czasem; błędy narzędzi raportujemy osobno.

Surowe dane: `result.json`,`manifest.json`,`api.jsonl`,`requests.jsonl`,`transcript.txt`,`game-run.json`. Podsumowania: `paired-comparison.json`,`diagnosis.json` w katalogu przebiegu. Kontrola: `analysis/champion-probe-pair-20261031/control-ft09`.

Uwaga do instrumentu: `controller_abstained=false` w pełnym przebiegu oznacza brak jawnego zatrzymania ewaluatora controller-only. To pole nie liczy przekazań sterowania w trybie hybrydowym; potwierdzeniem fallbacku jest56 rzeczywistych odpowiedzi API w surowym logu.

**Wniosek: potwierdzono lokalną przewagę całej hybrydy na jednej publicznej grze użytej w rozwoju modułu.** To nie ślepy test nowych mechanik,nie wynik ani prognoza Kaggle i nie potwierdzenie50+. Lokalne28,5714 z SDK dotyczy tylko ft09. Na25 publicznych grach moduł działał tylko w ft09; na24 pozostałych przekazuje sterowanie LLM. Nadal nie wykonano pełnego A/B na docelowym Flash-Next/SGLang.

Nie zgłoszono ani nie opublikowano notebooka na Kaggle. Ten pojedynczy test jest zakończony; nie uruchamiamy automatycznie kolejnej macierzy. Monitor należy usunąć po zapisaniu i commicie wyników.
