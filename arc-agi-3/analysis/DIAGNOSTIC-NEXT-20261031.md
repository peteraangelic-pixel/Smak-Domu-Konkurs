# Diagnostic continuation,31 October

Known ft09 solution completed level1 in4 actions through the actual Duck Python sandbox and HarnessGameSession; SDK score4.7619 is ORACLE TEST DATA, not an LLM result. Oracle rows are explicitly excluded from quality comparisons.

Current jobs: test_reasoning_pair.py runs on/off reasoning on ft09 with Qwen3.8-27B Q4,2048 tokens,1024/request,1200s. feedback_followup.py waits for both results, then tests inspection_feedback.py with identical settings and the selected reasoning mode (prefer completed levels, tie-break on). It never blocks a snippet; it appends feedback after three actual tool calls without an executed action, even when crops/code differ. Two new tests pass, alongside5 previous router/group tests.

Do not launch duplicate processes. Pending results: analysis/reasoning-pair-20261031 and inspection-feedback-20261031. These are capability/mechanism probes, not hidden-score predictions or full25-game evaluation. No candidate promotion on zero ties.

## PILNE: rzeczywisty wynik Kaggle
Przeczytaj V13-7-SCORE-STATUS-20261031.md: v13.7-final ma13.28, v11 ma23.89, najlepsze26.25. GO wycofane. Nie promuj pochodnych tej bazy na podstawie lokalnych smoke.
