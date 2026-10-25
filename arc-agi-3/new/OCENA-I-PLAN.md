# ARC-AGI-3 — ocena po przejrzeniu wszystkich gałęzi i plan do 2 XI

Stan: 25.10.2026, po odczytaniu `Smak-Domu-Konkurs@arena/5ed750ef`, `Pokemon@arena/a450b00f`,
`Pokemon@arena/c87f7a48`, `Gemma-konkurs@arena/6d081d52` i `@arena/c4eeb067`, oraz po
przeliczeniu Waszych własnych artefaktów (`r019`, `r033`, `r070`, `r069`).

## 0. Odpowiedź w trzech zdaniach

1. Submity **działają** (`-f` poprawione, r069 → ref 57607527, rc=0) — bloker operacyjny z 16 X jest zamknięty.
2. Dźwignie, na których stał plan „+45–50% z replaya” i „×4,4 z pamięci między replikami”,
   **nie istnieją w prawdziwym scorecardzie** — sprawdziłem to w kodzie, nie w opiniach.
3. 45+ nie jest dziś osiągalne tym stosem: autor tego harnessa (Franzen, ten sam model, ten
   sam kod) ma **38,85**, a próg nagród to **49,85**. Realny cel na 8 dni to 33–42 i publiczny
   notebook; 45+ to ~30% szans, pieniądze — nie w tym roku.

---

## 1. Stan faktyczny (same liczby z repo)

| co | wartość | źródło |
|---|---|---|
| najlepszy Wasz wynik | **26,25** (v3, ref 57247568, 16 X) | r069 `submissions` |
| ostatni submit | **57607527**, 24 X 21:44, rc=0, `PENDING` | r069 |
| leaderboard (24 X 21:45) | Tufa 68,91 · Chen 68,21 · Turducken 56,02 · mtg 50,37 · **the last dance 49,85** | r070 |
| autor harnessa (Franzen) | **38,85**, 15. miejsce | r070 |
| smoke v3 | 29,02 → LB 26,25 (kalibracja −2,8) | CHAT-LOG |
| budżet GPU | 30 h/tydz., smoke 2,5 h, pełny rerun 9 h | workflow + r050 |

Wniosek z tabeli: **płaci top-5, czyli 49,85.** 45+ nie jest progiem nagrody — to było 40,97
w snapshocie z 10–11 X. Od 24 X próg to ~50.

## 2. Co zweryfikowałem w kodzie (i co z tego wypada)

### 2.1 Formuła wyniku — odtworzona co do zera
`taaf/game.py:381–413`: poziom `k` ma wagę `k+1`, ukończony daje
`min(115, (baseline/actions)²·100)`, nieukończony 0, wynik to suma ważona przez sumę wag,
dodatkowo cap na procencie ukończonej wagi.

Przeliczyłem nią **wszystkie 10 gier z `r019`**: maksymalna różnica między moim wynikiem
a `final_score` z `benchmark.json` to **0,0000**. Czyli rozumiemy metrykę; każdy dalszy spór
„czy to już cap, czy jeszcze nie” jest rozstrzygalny offline (robi to `tools/v9_metrics.py`).

### 2.2 Gdzie naprawdę idzie budżet (`r019`, 10 gier × 48 min, wszystkie `gave_up`)

```
gra            poziomy  %wagi  score  akcje/base   wywołań  akcji/wyw.  tok/akcję
su15            7/9      62,2   56,42   157/361        85       1,85       1176
cn04            4/6      47,6   47,62   166/789        48       3,46       1100
dc22            4/6      47,6   44,77   304/1228       65       4,68        565
sc25            4/6      47,6   42,62   285/350        74       3,85        584
m0r0            3/6      28,6   28,57   215/1107       43       5,00        792
ka59            3/7      21,4   17,85   259/730        49       5,29        652
s5i5            3/8      16,7   16,67   116/638        24       4,83       1591
g50t            2/7      10,7   10,71   168/879        35       4,80       1006
tn36            1/7       3,6    3,57   145/317        33       4,39       1199
ls20            1/7       3,6    3,27   250/776        18      13,89        661
----------------------------------------------------------------------------
ŚREDNIA                  29,0   27,21   206/718       42,2      5,2         933
```

Trzy rzeczy, których w repo nie było policzonych w ten sposób:

1. **Budżet akcji to 28,8% tego, co trzeba na pełne przejście** (206 z 718 akcji).
   Wszystkie 10 gier zakończyło się na czasie (`gave_up`, 48,0 min), nie na śmierci.
2. **`tok/akcję` ≈ 841–933** przy 173,7 tys. tokenów na grę. Ten sam iloczyn na linii wolnej
   (r050: 1337 tok/decyzję) i szybkiej (3665) tłumaczy, dlaczego 24,66 i 26,25 są tak blisko.
3. **Głębokie batche nie są dźwignią.** `ls20` ma 13,9 akcji na wywołanie i 3,27 pkt;
   `su15` ma 1,85 i 56,42 (najlepsza gra). To korelacja, nie dowód — ale wystarczy, żeby
   **nie** stawiać slotu na „głębszym batchowaniu” (rekomendacja Gemmy c4eeb067 §3).
   Średnio model robi już 5,2 akcji na wywołanie; nie ma tam 4× zapasu.

### 2.3 Replay i „×4,4 pamięci między replikami” — nie w prawdziwym runie

`taaf/competition_arcade.py:1–6` mówi wprost:

> „The real Kaggle submission path talks to a gateway-backed Arcade with competition
> constraints: one scorecard, hidden baselines, and **no repeated game IDs within that scorecard**.”

A `official_110()` (linie 56–98) to **lokalny symulator**: klonuje 25 publicznych gier do
110 runów po to, żeby smoke miał kształt scorecardu. W prywatnym rerunie `bm.games` pochodzi
z żywego gatewaya (`_competition_games()` w komórce 25) i każdy `game_id` jest inny.

Do tego `ARC3_PERSISTENT_FUNCTIONS_SCOPE` przyjmuje **tylko** `turn|levelup|game`
(`tool_agent.py:2413` w drzewie po patchach) — nie ma zakresu „cały run”, więc pamięci
między grami nie da się włączyć zmienną env, trzeba by pisać patch.

**Skutek:** plan „klucz replaya sygnaturą ramki → ×4,4 darmowych poziomów” (Gemma §5, c87)
opiera się na mechanizmie, który w ocenianym runie nie występuje. Nie ma z tego ani punktu.
Sonda rosteru z c45 i tak odpowie na to jednym runem — ale jej wynik będzie `DISTINCT`.

### 2.4 `PERSISTENT_FUNCTIONS_SCOPE='game'` jest poprawny
W ocenie c45 (24.10) padło „kod przyjmuje tylko turn|levelup, więc `game` po cichu spada do
levelup”. To nieprawda: walidator to `("turn", "levelup", "game")`. Nic tu nie jest zepsute.

### 2.5 Główny błąd c45: metadana nie pasuje do notebooka
`duck-c45/kernel-metadata.json` deklaruje zbiory linii **wolnej** (`jeroencottaar/taaf-kaggle-source-share`,
`driessmit1/arc3-vllm-h100-wheelhouse-v3`, `driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot`),
a komórka 9 czyta zbiory i modele **Franzena**:

```
/kaggle/input/datasets/dfranzen/pennyroyal-v253
/kaggle/input/models/dfranzen/intel-qwen3.8-flash-next-w4a16-autoround/transformers/default/1
/kaggle/input/models/dfranzen/albucino-qwen3-8-flash-next-drafter/transformers/default/1
/kaggle/input/datasets/dfranzen/taaf-kaggle-source-bundle-copy
```

Czyli pakiet „przyjęty na slot 25.10” nie miałby zamontowanych katalogów, których używa —
padłby w komórce 17 (launcher sglang), zanim cokolwiek zagralibyście. Metadana w tym pakiecie
ma źródła z `duck-v7` (wersja, która faktycznie ruszyła).

### 2.6 Łańcuch patchy — aplikuje się, kompiluje, i jest kompletny
Cztery patche wyciągnięte z notebooka (`harness-changes` 498 757 znaków + `duck-extra-00/01/02`)
aplikują się po kolei na czysty bundle z `r033`, a spatchowane drzewo się kompiluje.
Ostrzeżenie na przyszłość: ostatni hunk patcha 498 KB jest krótszy niż deklaruje nagłówek,
więc plik **musi** kończyć się znakiem nowej linii — bez niego `git apply` mówi
`corrupt patch at line 10086` i kernel umiera po minucie. Sprawdza to `tools/verify_offline.py`
(dlatego wyciąga patche z notebooka sam, a nie z pliku w repo).

### 2.7 `-f` jest już naprawione
`ops.py:136`, `:443`, `:469` mają dziś `submission.parquet`, a r069 poszedł z `-f submission.parquet`
i zwrócił rc=0. To zamknięte. (Wcześniejsza diagnoza: 12 prób ze ścieżką = 12×400,
2 z nazwą pliku = 2×0 — nadal aktualna jako wyjaśnienie 8 dni straty.)

---

## 3. Arytmetyka luki — dlaczego 45 to inna liga niż 26

Wynik to **procent ukończonej wagi** pomnożony przez efektywność ruchów, z capem 115 na poziom.
Policzone na tych samych 32 ukończonych poziomach z `r019`: **21 z 32 siedzi na capie 115**,
mediana wyniku poziomu to **115**, średnia **97,7**, a tylko 3 poziomy są poniżej 50.
Cała rezerwa „graj mniej ruchami” to więc ~1,7 pkt na grę (tyle dzieli 27,21 od 28,96).
Reszta luki to **głębokość**:

| scenariusz (na `r019`, smoke) | średnia | gdzie na LB (kalibracja −2,8…−6,7) |
|---|---|---|
| dziś (3,2 z 7,3 poziomu) | 27,21 | 26,25 — miejsce ~25 |
| ten sam zasięg, idealne ruchy | 28,96 | ~26 |
| **+1 poziom w każdej grze** | **44,2** | ~38–42 |
| **+2 poziomy** | **64,5** | ~58–61 |
| próg nagród 49,85 | — | potrzebne ~+1,6 poziomu |

(Przeliczone przeze mnie z formuły na tych samych 10 grach, nowy poziom wchodzi na cap 115.
c87 podaje 44,8 dla +1 — różnica 0,6 pkt, bez znaczenia dla wniosku; +2 wychodzi nam identycznie.)

Żeby dołożyć 1,6 poziomu na grę, trzeba **~2,5× więcej akcji** (718 vs 206 na pełne przejście).
Akcje kosztują tokeny: 174 tys. na grę przy ~900 tok/akcję. Więc albo 2,5× więcej tokenów
(nie ma skąd: 9 h × ~750 tok/s ÷ 110 gier), albo 2,5× mniej tokenów na akcję.

I tu jest twarda ściana: **autor tego harnessa, z tym samym modelem i tym samym kodem, ma
38,85**. To empiryczny sufit tej linii, nie moja ocena. Tufa (68,91) używa konfiguracji, której
w publicznym bundlu nie ma — inaczej rerun ich własnego notatnika nie dawałby 26.

Uczciwe widełki dla v9: **33–42**. 45+ wymaga, żeby `+1 poziom` przyszedł taniej, niż pokazuje
historia (np. speedup serwowania, którego nikt jeszcze nie zmierzył). Pieniądze (49,85) — nie.

---

## 4. Co robi pakiet v9 (i czego nie robi)

Robi trzy rzeczy, żadna nie jest „nowym algorytmem”:

1. **Naprawia metadanę** — bez tego c45 nie ma szans się uruchomić (§2.5).
2. **Daje pomiar w każdym runie** — `actions`, `actions_need`, `calls`, `actions/call`,
   `tok/action`, `tok/call`, `% wagi`, `score`, zapis do `v9_metrics.json`. Po smoke'ie
   wiadomo, czy problemem jest głębokość, czy przepustowość, i który profil ma sens dalej.
3. **Daje jeden przełącznik na dźwignię** (`PROFILE`): `c45` (wierny), `wide` (MAXREQ 14),
   `deep` (dyrektywa głębokich batchy — mimo kontrargumentu z §2.2, żeby dało się to
   *zmierzyć*, a nie oceniać).

Nie robi: replaya, pamięci między replikami, `game_weights`, nowych patchy behawioralnych,
zmian w prompcie poza jednym opcjonalnym prefiksem. Każda z tych rzeczy albo nie ma mechanizmu
(§2.3), albo została już zmierzona jako strata (v5 23,94 < v2 24,66 < v3 26,25).

---

## 5. Plan slotów (25.10 → 2.11), jedna zmiana na slot

| kiedy | co | koszt | bramka przed dalszym krokiem |
|---|---|---|---|
| **dziś** | `op: lb` — odczytaj wynik **57607527** | 0 | jeśli COMPLETE: to nowy punkt odniesienia |
| **dziś** | push v9 `PROFILE=c45` → smoke 10×48 min | 2,5 h | run COMPLETE **i** `mean score > 29,02` |
| **26.10** | submit v9 c45 (jeśli bramka przeszła) | 1 slot | — (to pierwszy prawdziwy pomiar linii szybkiej) |
| **27.10** | z meteringu: jeśli `tok/action` ~900 i `a/call` ~5 → `wide`; jeśli `a/call < 3` → `deep` | 2,5 h | jak wyżej |
| **28–30.10** | zwycięzca + `ARC3_SYSTEM_PROMPT_PREFIX` wg potrzeb; bez łączenia dwóch zmian | 1 slot/dzień | smoke > poprzedni |
| **31.10–1.11** | finalista **jako publiczny notebook** (CC0/MIT-0) | 1 slot | `is_private: false`, inaczej nagroda przepada |
| **2.11** | zapas; nic bez bramki | — | — |

Budżet GPU: 2,5 h smoke + 9 h rerun = 11,5 h na slot; przy 30 h/tydz. to **2 sloty na tydzień**,
czyli realnie 3–4 pełne pomiary do końca. Dlatego każdy slot musi odpowiadać na jedno pytanie.

---

## 6. Czego bym nie zrobił

- **Nie wysyłałbym `duck-v8` (replay)** — mechanizm nie występuje w scorecardzie (§2.3),
  a patch jest niezmierzony.
- **Nie podnosiłbym `MAXREQ` przed odczytem KV** — `r019`/c87: użycie KV 0,71 mediana,
  0,99 max przy 10 strumieniach; 14 może wywalić run (dlatego `wide` nie jest domyślne).
- **Nie ufałbym prognozom +7…+37 pkt** z tabel dźwigni (c87 sam je wycofał; zostało 3,18).
- **Nie oceniałbym kandydata po score z 10 gier** bez `depth budget` i `tok/action` — przy n=10
  dwa punkty to szum, a kalibracja smoke→LB to −2,8…−6,7.
- **Nie zmieniałbym dwóch rzeczy naraz.** Historia: v5 (world model) −0,68, v6 (nudge) −0,72,
  v2 (think-less) −1,59 — wszystkie „oczywiste ulepszenia” wyszły na minus.

---

## 7. Co jest potrzebne od Ciebie

1. `op: lb` (albo jedno kliknięcie w Submissions) — czy 57607527 ma już wynik. Bez tej liczby
   nie wiem, czy v5 to 26, czy 38, i czy w ogóle warto pushować v9.
2. Push `arc3-duck-v9.ipynb` + `kernel-metadata.json` do `petersharps/arc3-duck-v9`
   (request w §4 README).
3. Po smoke: `benchmark.json` albo `v9_metrics.json` tutaj — policzę bramkę i wskażę profil.

Ja nie mam dostępu do Kaggle i nie potrzebuję Twojego klucza API.
