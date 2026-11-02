# Small non-Qwen reactive prototype

User-authorized separate experiment. Google Gemma4E4B loaded locally;model catalog reports7.5B total with effective4B naming,6.33GB including vision asset in lms. No downloaded weights or competition submission. No other model was loaded beforehand.

Policy sees pixels,public controls and current level only;no engine state/gameID/routes. Chooses a single validated JSON action,predicts up to3cell colors,checks them next observation and switches among3tactics after2consecutive prediction failures. Contract fixtures prove switching and level isolation;they do not prove useful adaptation.

Initial JSON-grid OpenAI-compatible requests failed400;compact grid fixed size,but default thinking exhausted256outputtokens and truncated JSON. Originals preserved in small-reactive-20261102 and small-reactive-20261102-compact. Native API reasoning=off verified0reasoning tokens.

Final feasibility screen:ft09 4actions/22.09s/0levels;ls20 4actions/43.05s/0levels.8valid model-selected actions,no runtimeerrors. Four moves per game is insufficient to evaluate solving quality. No matched baseline,no speedup claim,no Kaggle-score forecast.

Observed weakness:checks of unchanged/background cells can pass without gameplay progress;actual tactics did not switch in this short screen. A useful next version must track informative predicted effects and retain/revise causal hypotheses,not merely change tactic labels. Larger training or GPU sweeps are not justified by this feasibility result alone. V3 unchanged.

Reproduction: lms load google/gemma-4-e4b --identifier arc-small-reactive --context-length8192 --parallel1 --gpu max -y (use separate argument/value tokens). Then .venv-local/Scripts/python.exe -X utf8 analysis/run_small_reactive.py --out NEW_DIRECTORY --decisions4 (separate --decisions and4).
