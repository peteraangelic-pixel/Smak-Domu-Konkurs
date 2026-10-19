# PLAN-GENIUS: wersja własna > Option A (na slot 18.10+)

## Baza faktów (dziś, 16.10)
- NB Tufy (June-30 winner): 17 komórek; model NIE jest w NB — w bundle-daciecie
  `jeroencottaar/taaf-kaggle-source-share` (setup_commands.json uruchamia vLLM);
 solver/benchmark: pickle `benchmark_initial.pkl`, kod w bundle.
- **Dźwignia #1 odkryta w kom.14: `bm.game_weights`** (Tufa ustawia None = uniform).
  To jest first-class hook realokacji budżetu między grami — nasza krzywa (100k→24.7,
  200k→41.8, 300k→45.7 tok/ocalałego) mówi, że realokacja ma wartość ~+4-14 pp.
- `target.max_runtime_s` (miękki deadline), `bm.n_passes`, `bm.games` (kolejność/lista).
- Autopsja v6: ogromna wariancja per gra (3.3–56.4) →Games słabe palą budżet.
- Ich insight (STRATEGIA-TOP3): „gains from multimodality and better base models,
  NOT hand-built tools" → NIE dokładamy knobów do promptu; gramy u ich własnej broni.

## Kandydaci (ranking wg (efekt × P(zadziała)) / ryzyko)
1. **game_weights ≠ None** — realokacja budżetu: obetnij gry o niskiej krańcowej
   wartości (daj min. poziomy), przelej resztę na gry środkowe (marginal 200→300k
   nadal +3.9 pp). Semantykę wag potwierdzi r033 (kod benchmarku w bundle).
   Wpięcie: kom.12 hook, aktywny TYLKO przy TRUE_SUBMISSION (rerun), kill-switch env.
2. **Model swap**: setup_commands.json pokaże, czy model idzie przez
   TAAF_KAGGLE_INPUT_PATHS (dynamicznie) czy hardcode. Jeśli dynamicznie →
   podpięcie nowszego snapshotu (np. Qwen3.8-Flash-Next jak u Franzena M2 47.25,
   albo nowszy tufa-model z 68.91) = metadata-only change.
3. **Kolejność/lista gier**: przy miękkim deadline front-load silnych gier
   (autopsja: su15/cn04/dc22/sc25). Mean nie zmienisz kolejnością, ale deadline
   tak — ostatnia gra w kolejce jest ucinana.
4. NIE robimy: hand-tools (ich własny wynik: szkodzą), prompt-engineering (loteria).

## Harmonogram
- 16.10 ~16:30: r033 (recon) → semantyka game_weights + model path + czy jest
  publiczny nowszy Tufa-kernel (68.91?).
- 17.10 noc: chain działa (Option A baseline, expected ~40-56) — NIC nie zmieniamy.
- 17.10 dzień: budowa duck-genius-v1 (base=duck-original + hook rerun-only) →
  push CPU test → save-run smoke po kolei.
- 18.10 00:00 UTC: submit genius-v1 (kolejny slot).

## AKTUALIZACJA 19.10: formuła scoringu POTWIERDZONA (dane r019)
- score/poziom = (H/A)^2 × 100 (H=ruchy człowieka, A=agenta); total = mean per gra.
- Implied H/A v6: śr. 0.697 → replay pass2 (odtwarzanie ścieżek pass1) → 0.95+ = +45-50% pkt/poziom.
- Dźwignie genius-v1: (1) game_weights realokacja, (2) REPLAY-layer w solverze Tufy
  (zapis sekwencji per level w pass1; pass2 odtwarza; wymaga weryfikacji przepływu
  stanu między passami w taaf/benchmark.py — plik w r033-recon-bundle), (3) kolejność
  gier pod deadline, (4) opcjonalnie nowszy fork boristown jako baza.
