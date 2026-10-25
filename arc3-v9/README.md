# ARC-AGI-3 — pakiet `v9` (25.10.2026)

Notebook gotowy do wypchnięcia na Kaggle, zbudowany na przyjętym `duck-c45`
(a nie od zera), z naprawioną metadaną i pomiarem, który po każdym runie mówi,
co ten slot faktycznie kupił.

**Najpierw jedno zdanie prawdy:** ten pakiet nie gwarantuje 45+. Gwarantuje,
że slot nie przepadnie na błędzie, który nie ma nic wspólnego z algorytmem —
a takich w tym projekcie było w ostatnich dniach pięć.

---

## 1. Co jest w środku

| plik | rola |
|---|---|
| `arc3-duck-v9.ipynb` | notebook do wypchnięcia (32 komórki, 661 KB) |
| `kernel-metadata.json` | metadana z **prawdziwymi** źródłami danych i modeli |
| `tools/build_v9.py` | odtwarza notebook z `src/base-c45.ipynb` (jeden plik, cztery edycje) |
| `tools/v9_metrics.py` | analiza `benchmark.json` / `v9_metrics.json`: sześć liczb decyzyjnych |
| `tools/test_v9_metrics.py` | 7 testów analizatora (bez GPU) |
| `tools/verify_offline.py` | 43 sprawdzenia offline: notebook, metadana, łańcuch patchy, kompilacja |
| `OCENA-I-PLAN.md` | co zweryfikowałem w kodzie wszystkich gałęzi, arytmetyka luki, plan slotów |
| `examples/r019-benchmark.json` | prawdziwy `benchmark.json` z r019 — na nim analizator odtwarza 27,21 |
| `src/base-c45.ipynb` | kopia `duck-c45` — punkt odniesienia, żeby build był odtwarzalny |
| `verify.sh` | jedno polecenie: `./verify.sh [bundle] [benchmark.json]` |

## 2. Co dokładnie różni v9 od c45

Cztery rzeczy, wszystkie widoczne w `git diff` notebooka:

1. **Komórka `V9`** (druga w notebooku) — jeden przełącznik `PROFILE`
   (`c45` / `deep` / `wide`), który ustawia trzy wartości i nic więcej.
   Domyślnie `c45` = zachowanie przyjętego pakietu.
2. **`LOCAL_ANALYZER_MAX_OUTPUT`, `ARC3_SYSTEM_PROMPT_PREFIX`,
   `ARC3_MAX_ACTIVE_STREAMS`** czytane z `V9` zamiast wpisane na sztywno.
3. **`MAXREQ` / `CTX` / `CUDAGRAPH_MAXBS`** w launcherze sglang czytane
   z `V9_MAXREQ` / `V9_CTX` (domyślnie bez zmian: 10 i 136k).
4. **Komórka pomiarowa na końcu** — wypisuje per gra: `actions`, `actions_need`,
   `calls`, `actions/call`, `tok/action`, `tok/call`, `w%`, `score`, i zapisuje
   `v9_metrics.json`. W smoke i w prawdziwym submitcie. Zero tokenów, zero GPU.

Patch 498 KB, trzy patche dodatkowe, ścieżki modeli, `TRUE_SUBMISSION`,
pin `ONLY_RESET_LEVELS` i logika smoke/submit są **nietknięte**.

## 3. Dlaczego metadana to nie kosmetyka

`duck-c45/kernel-metadata.json` deklaruje:

```
dataset_sources: jeroencottaar/taaf-kaggle-source-share,
                 driessmit1/arc3-vllm-h100-wheelhouse-v3,
                 driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot
```

a komórka 9 tego samego notebooka czyta:

```
/kaggle/input/datasets/dfranzen/pennyroyal-v253
/kaggle/input/models/dfranzen/intel-qwen3.8-flash-next-w4a16-autoround/...
/kaggle/input/models/dfranzen/albucino-qwen3-8-flash-next-drafter/...
/kaggle/input/datasets/dfranzen/taaf-kaggle-source-bundle-copy
```

Czyli c45 w wersji z repo **nie ma zamontowanych katalogów, których używa**.
Metadana to kopia linii wolnej (v5), podmieniono tylko `id`/`title`.
`kernel-metadata.json` w tym pakiecie ma źródła z `duck-v7` — tej wersji,
która faktycznie się uruchomiła.

## 4. Jak to wypchnąć

Przez Wasz kanał ops (request w `arc-agi-3/kaggle/ops/request.json`):

```json
{"id": "r071", "op": "push", "args": {
  "kernel": "petersharps/arc3-duck-v9",
  "dir": "arc-agi-3/kaggle/duck-v9"
}}
```

Po wgraniu plików `arc3-duck-v9.ipynb` + `kernel-metadata.json` do
`arc-agi-3/kaggle/duck-v9/`. Push = Save & Run (smoke: 10 gier × 48 min,
≈2,5 h GPU). Bramka przed slotem submisyjnym:

```
python3 tools/v9_metrics.py <pobrany benchmark.json>   # albo v9_metrics.json
```

- `MEAN score > 29.02` → kandydat bije v3 na smoke; kalibracja smoke→LB to −2,8…−6,7,
- `a/call` i `tok/action` mówią, który profil ma sens w następnym slocie,
- `depth budget used` (np. 28,8%) mówi, czy gra jest ograniczona głębokością,
  czy umiejętnością.

## 5. Weryfikacja offline (to, co da się zrobić bez GPU)

```
./verify.sh <ścieżka>/r033-recon-bundle/bundle examples/r019-benchmark.json
# albo bez artefaktów repo (34 sprawdzenia):
./verify.sh
```

Wynik u mnie: **43 sprawdzenia, 0 błędów**. Co jest sprawdzane:

- notebook parsuje się, 32 komórki, wszystkie komórki Pythona się kompilują,
- trzy profile `V9` rozwiązują się do zamierzonych wartości,
- każda ścieżka `/kaggle/input/...` z notebooka ma pokrycie w metadanej,
- cztery patche wyciągnięte z notebooka aplikują się na czysty bundle
  (r033) po kolei, a spatchowane drzewo się kompiluje,
- `ARC3_SYSTEM_PROMPT_PREFIX`, `ARC3_MAX_ACTIVE_STREAMS`,
  `ARC3_LEVEL_TOKEN_CAP` istnieją w kodzie po patchach,
- analizator odtwarza `final_score` z `r019` co do 0,0000 i średnią 27,21.

Uwaga praktyczna: patch 498 KB musi kończyć się znakiem nowline. Jeśli
wyciągniesz go z notebooka narzędziem, które go obetnie, `git apply` powie
`corrupt patch at line 10086` i notatnik umrze w komórce 9 po ~minucie.
`verify_offline.py` robi to poprawnie — może służyć jako test regresji.

## 6. Czego tu nie ma (świadomie)

- **replay poziomów kluczowany `game_id`** (a450) — w prawdziwym scorecardzie
  nie ma powtórzonych `game_id`, a `PERSISTENT_FUNCTIONS_SCOPE` zna tylko
  `turn|levelup|game`, więc nie ma gdzie mnożyć pamięci przez repliki;
- **pamięć między replikami ×4,4** (Gemma §5, c87) — klonowanie 25 gier do 110
  to funkcja **lokalnego symulatora** smoka, nie prywatnego scorecardu;
- **`game_weights`** — nie realokują budżetu (potwierdzone w `benchmark.py`);
- **nowe patche behawioralne** — po historii v6 (23,94 < 24,66) i v2 (24,66)
  każdy niezmierzony patch to zakład, a nie ulepszenie.

Szczegóły i liczby: `OCENA-I-PLAN.md`.
