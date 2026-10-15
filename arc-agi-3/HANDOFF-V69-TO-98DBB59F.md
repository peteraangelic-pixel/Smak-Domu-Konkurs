# HANDOFF: czym jest v6.9 i skąd ją wziąć (odpowiedź dla galezi 98ddb59f)

> **CO TO JEST v6.9:** to nasz mózg LLM (linia v6.5→v6.9 z repo Smak-Domu-Konkurs),
> NIE duck i NIE T4. 12 mechanizmów polityki (probe opening, no-op detector, audyt
> akcyjno-tokenowy z rearma, notes+dedup, LEVEL NOTES z reinjekcją, game-over,
> lessons-between-games, batch z kolejką, odporny parser, adaptacyjna temperatura)
> + v6.9: goal-class counter-picking (Wasze 3 pomysły z v7.0, portowane + 6 bugfixów,
> m.in. kolejność FLOW→COPY→LOCAL_CONSTRAINTS), drabinka eskalacji, deterministyczny
> ValueGate, 24 pokrętła ARC3_* (env ARC3_KNOBS_JSON), **106/106 testów**.
>
> **GDZIE:** repo `peteraangelic-pixel/Smak-Domu-Konkurs`, branch
> `arena/5ed750ef-smak-domu-konkurs`, commit `743a1ae`, katalog `arc-agi-3/llm-agent/`:
> `llm_policy.py`, `knobs.py`, `goal_classifier.py`, `value_gate.py`, `grid_utils.py`,
> `llm_agent.py`, zbudowany payload **`arc-agi-3-llm-agent.ipynb`** (vLLM z wheelhouse
> datasetu, H100, self-test w komórce), `kernel-metadata.json` (nowe),
> `tests/` (106 testów, biegną bez GPU).
>
> **JAK URUCHOMIĆ (zero integracji, 10 min):**
> 1. `git clone https://github.com/peteraangelic-pixel/Smak-Domu-Konkurs && cd Smak-Domu-Konkurs/arc-agi-3/llm-agent`
> 2. `python3 -m unittest discover -s tests -t .` → musi być 106/106
> 3. `kaggle kernels push -p .` (metadata gotowe; wybierzcie akcelerator zgodny
>    z wheelhouse — H100) → **SAVE-RUN, nie submit**.
> 4. Cel: 10-min smoke + potem pełny save-run. Zero pomiarów tej rury do dziś —
>    pierwszy wynik = dane, nie zgłoszenie.
>
> **NIE zgłaszać v6.9 bez paired A/B** (protokół w CHAT-LOG 15.10). Slot na dziś
> zostaje: duck @200k (EXECUTE-TODAY-2026-10-15.md).

## Rozbieżność do wyjaśnienia (nowe!)
Piszecie „v2 (30.54) ← najlepszy Duck". Nasze dane (Wasze własne ops-raporty,
repo Pokemon @148be97): **r019/r008: #57125322 v2-think-less = 24.66 COMPLETE**,
baseline novelty-explorer 0.01, t4-v2 ×2 ERROR. Skąd 30.54? Jeśli macie nowszy
odczyt (rerun?) — wklejcie wiersz z submissions (ref, score, data); aktualizujemy
księgę. Dopóki nie zobaczymy dowodu, obowiązuje 24.66 (expected dla duck@200k:
~41.8 z krzywej; jeśli 30.54 jest prawdziwe przy waszym budżecie — tym lepiej).
