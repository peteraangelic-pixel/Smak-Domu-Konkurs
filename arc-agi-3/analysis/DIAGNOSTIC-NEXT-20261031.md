# Diagnostic continuation,31 October

## Aktualizacja po odzyskaniu najlepszego zgłoszenia

Najpierw przeczytaj `RECOVERY-AND-NEXT-20261031.md`. Stare reasoning-pair i inspection-feedback zakończone: wszystkie zero ukończeń, feedback zero aktywacji. Nie uruchamiaj ich ponownie. Działa nowa, zablokowana przed duplikatami macierz `champion_probe_pair.py` w `champion-probe-pair-20261031`: odzyskana dokładna v3 (26,25 Kaggle) kontra spakowany probe, ft09 i ls20,8192 tokenów,4096/request,thinking OFF. Sprawdź istniejące procesy/wyniki; nie dubluj strumienia serwera. Kod i notebook są przygotowane; po ukończeniu sprawdź faktyczne ukończenia i aktywację, zapisz surowe wyniki i zakomituj na gałęzi Codex. Nie promuj remisu, nie wysyłaj na Kaggle. Gdy próby jeszcze trwają, ustaw kolejne sprawdzenie zamiast zamykać pracę bez kontynuacji.

Known ft09 solution completed level1 in4 actions through the actual Duck Python sandbox and HarnessGameSession; SDK score4.7619 is ORACLE TEST DATA, not an LLM result. Oracle rows are explicitly excluded from quality comparisons.

Current jobs: test_reasoning_pair.py runs on/off reasoning on ft09 with Qwen3.8-27B Q4,2048 tokens,1024/request,1200s. feedback_followup.py waits for both results, then tests inspection_feedback.py with identical settings and the selected reasoning mode (prefer completed levels, tie-break on). It never blocks a snippet; it appends feedback after three actual tool calls without an executed action, even when crops/code differ. Two new tests pass, alongside5 previous router/group tests.

Do not launch duplicate processes. Pending results: analysis/reasoning-pair-20261031 and inspection-feedback-20261031. These are capability/mechanism probes, not hidden-score predictions or full25-game evaluation. No candidate promotion on zero ties.

## PILNE: rzeczywisty wynik Kaggle
Przeczytaj V13-7-SCORE-STATUS-20261031.md: v13.7-final ma13.28, v11 ma23.89, najlepsze26.25. GO wycofane. Nie promuj pochodnych tej bazy na podstawie lokalnych smoke.
