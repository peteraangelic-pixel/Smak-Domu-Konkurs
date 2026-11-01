# Końcowa decyzja przed02:10: BRAK KWALIFIKUJĄCEJ WERSJI

Wersja2 petersharps/arc3-codex-memory-v3-recovery/2 zakończyła się COMPLETE. Pobrano pełny dostępny artefakt kolektora41251874109. Notebook lokalny ma oczekiwany SHA25632ec0588d81a1b6cb53f50a52e9d38303fcf2cf9bcda8fec9924470061ef549b.

| Próba publiczna | Średni wynik | Ukończenia | Nowa gra z zerem |
|---|---:|---:|---|
| Kontrola v3 |27.49667|33|brak|
| Pamięć v1 |28.39998|32|tn36|
| Pamięć + recovery v2 |17.10526|25|dc22|

**Żaden nowy wariant nie spełnia wszystkich ustalonych warunków. Nie zgłaszać żadnego z nich.** Wyższa średnia wersji1 nie znosi regresji ukończeń i nowego zera. Wersja2 pogarsza również średnią. Nie zmieniono progów i nie uruchomiono trzeciej wersji ani duplikatu GPU.

Wersja2: ARC3_SMOKE_OK; brak crashy;25 rzeczywistych capture,18 pinned,0 błędów pamięci/recovery. **0 aktywacji SLM_V3_RECOVERY.** Nie ma więc pomiaru wpływu samej wskazówki na rozgrywkę; nie przypisujemy jej przyczynowo ani poprawy tn36,ani spadku całości. Ta próba nadal wystarcza do odrzucenia zmierzonego notebooka według ustalonych kryteriów,nie do dowodu,że hipoteza recovery nie może działać.

Per gra ukończenia wersji2:tn36 4,m0r0 3,cn04 3,dc22 0,ka59 2,sc25 3,s5i5 2,ls20 3,su15 3,g50t 2. Dane i maszynowe porównanie: analysis/memory-v3-target-20261031/recovery-result-summary.json. Surowe benchmark/logi/prompty/serve.log/status i historia kolektora: recovery-result/submission-access-20261031/memory-correction-output/ w tym samym katalogu.

To publiczne save-runy,nie wyniki konkursowe. Pojedyncze przebiegi i różne głębokości nie rozstrzygają wpływu konkretnego patcha. Zakres zmienności między próbami jest istotnym ograniczeniem selekcji na podstawie jednego smoke.

SUBMISSION-CANDIDATE.json zachowuje tożsamość wersji1 wyłącznie jako zapis historyczny i ma eligible=false oraz powód BRAK KWALIFIKUJĄCEJ WERSJI. Wykonawca submisji respektuje to oznaczenie i nie wywoła API submit. Automatyzacja02:10 powinna odczytać tę końcową decyzję;nie szukać zastępczego nieprzetestowanego notebooka. Monitor analizy jest zakończony i usuwany. Żadnej submisji konkursowej nie wykonano przez ten monitor.
