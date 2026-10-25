# LEPSZA DROGA — gdzie naprawdę jest 45+

Stan: 25 X 2026. Wszystkie liczby poniżej są albo z Waszych logów w repo (`r019`,
`benchmark.json`, `*_requests.jsonl`), albo z publicznych źródeł podanych na końcu.

---

## 1. Leaderboard na dziś (25 X, 07:34 EDT)

| # | zespół | pkt |
|---:|---|---:|
| 1 | Yi-Chia Chen @ Fields Model | 71,48 |
| 2 | Tufa Labs | 68,91 |
| 3 | Team Turducken | 56,02 |
| 4 | the last dance | 50,69 |
| 5 | mtg | 50,37 |
| 6 | Grigoriy Zatravkin | 47,19 |
| 7 | 復活の混テキスト | 46,82 |
| 8 | NVARC3 | 45,90 |
| 9 | artificialagencylab.com | 45,41 |
| 10 | Majkel1337 | 45,03 |

Nasze 26,25 jest daleko poza tabelą. **Daniel Franzen — autor harnessu, którego
używamy — jest 15. z 38,85.** To nie przypadek: to sufit tej konkretnej linii.

Wniosek z tego jest twardy: **45+ wymaga innej architektury, nie lepszego promptu
w tej samej.** Masa ludzi poszła inną drogą — i jedna z tych dróg ma opublikowane,
per-growe liczby, które da się nałożyć na Wasze gry.

---

> **KOREKTA (25.10, potwierdzona przez 3 sesje + przeliczenie Arena z surowych danych):**
> tabela niżej liczy LINIE w `*_requests.jsonl` (1417 = wszystkie żądania, łącznie z roundtripami analizatora).
> Prawdziwe wywołania PRODUKUJĄCE akcje = wpisy historii z `generated_tokens > 0` = **474**;
> a/call ważone **4.357**, średnia z gier **5.204**, tok/akcję 841,3, tok/wywołanie 3665, pula 173 726 tok/grę.
> Wniosek o batchingu („brak zapasu 4×") pozostaje — ale liczby 1417/1,13 są OBALONE. Zob. OCENA-ARENA-V9.md.

## 2. Zmierzona przyczyna (Wasze własne logi, `r019`)

Policzone z `*_requests.jsonl` (liczba wywołań modelu) i `benchmark.json` (akcje):

| gra | wywołań modelu | akcji | akcji / wywołanie | poziomy |
|---|---:|---:|---:|---|
| g50t | 145 | 168 | 1,16 | 2/7 |
| ka59 | 155 | 259 | 1,67 | 3/7 |
| ls20 | 180 | 250 | 1,39 | 1/7 |
| m0r0 | 213 | 215 | 1,01 | 3/6 |
| s5i5 | 133 | 116 | 0,87 | 3/8 |
| sc25 | 225 | 285 | 1,27 | 4/6 |
| su15 | 213 | 157 | 0,74 | 7/9 |
| tn36 | 153 | 145 | 0,95 | 1/7 |
| cn04 | — | 166 | — | 4/6 |
| dc22 | — | 304 | — | 4/6 |
| **razem (8 gier z logami)** | **1417** | **1595** | **1,13** | **24/57** |

Gra potrzebuje ~700 akcji, żeby przejść wszystkie poziomy. Budżet daje ~200.
**0,74–1,67 akcji na wywołanie modelu to cała luka 26 → 45.**

Do tego: 21 z 32 ukończonych poziomów siedzi na capie 115, mediana wyniku poziomu
= 115. Czyli ruchów nie da się już poprawić — brakuje *akcji*, nie precyzji.

Wniosek projektowy: **każda zmiana, która nie podnosi liczby akcji na wywołanie
modelu (albo nie czyni tych akcji mądrzejszymi), jest kosmetyką.**

---

## 3. Droga, która ma dowód — model świata + planer

Podejście z paper01 (`astroseger/arc-3-agents-baseline1`, MIT): agent-koder pisze
**wykonywalny model gry w Pythonie** (`world_model_engine.py`), **weryfikator**
sprawdza go na zarejestrowanych przejściach, **planer** szuka w modelu ciągu akcji,
**executor** wysyła ten ciąg do gry i porównuje klatka po klatce; rozjazd = stop
i przebudowa modelu. Limit 1500 akcji na poziom, do 10 restartów procesu.

To jest dokładnie ten mechanizm, którego brakuje: planowanie dzieje się w Pythonie
(za darmo), więc jedna decyzja modelu kupuje **kilkadziesiąt akcji**, a nie jedną.

Nałożone na **Wasze 10 gier z `r019`** (te same gry, ta sama formuła):

| gra | duck (nasze) | poz. | WM GPT-5.5 | poz. | WM GPT-5.4 | poz. |
|---|---:|---:|---:|---:|---:|---:|
| cn04 | 47,62 | 4/6 | **96,34** | 6/6 | 0,33 | 1/6 |
| dc22 | **44,77** | 4/6 | 0,00 | 0/6 | 36,84 | 4/6 |
| g50t | 10,71 | 2/7 | **95,08** | 7/7 | 59,25 | 6/7 |
| ka59 | 17,85 | 3/7 | **100,00** | 7/7 | 9,29 | 6/7 |
| ls20 | 3,27 | 1/7 | 57,02 | 7/7 | **77,26** | 7/7 |
| m0r0 | 28,57 | 3/6 | **67,33** | 6/6 | 0,01 | 1/6 |
| s5i5 | 16,67 | 3/8 | 0,25 | 2/8 | **41,67** | 5/8 |
| sc25 | **42,62** | 4/6 | 20,23 | 3/6 | 16,71 | 3/6 |
| su15 | 56,42 | 7/9 | **56,85** | 9/9 | 1,72 | 1/9 |
| tn36 | 3,57 | 1/7 | **74,98** | 7/7 | 3,57 | 1/7 |
| **środek** | **27,21** | **32/69** | **56,81** | **54/69** | 24,67 | 35/69 |

Zastrzeżenia do tabeli: to pojedyncze przebiegi z tabeli paper01 (high reasoning),
na publicznych grach, przy limicie 1500 akcji na poziom i bez limitu 48 min/gry.
Autorzy wprost piszą, że private setu nie testowali. Czyli kolumna WM to **sufit
publicznego setu**, a nie prognoza naszego prywatnego runu.

Trzy rzeczy, które z tego wynikają — i wszystkie trzy są ważne:

1. **Architektura działa.** 32 → 54 poziomy, 27,21 → 56,81 na tych samych grach.
   Zamyka ogon: ls20 1/7 → 7/7, tn36 1/7 → 7/7, g50t 2/7 → 7/7, ka59 3/7 → 7/7.
   Kalibracja smoke→LB (−2,8) daje **~54 na tablicy**.
2. **Model jest współczynnikiem, nie dodatkiem.** To samo podejście z GPT-5.4 daje
   **24,67 — poniżej naszego 27,21.** Dlaczego: GPT-5.4 *odkrywał* poziomy, ale
   zbyt drogą: dc22 1568 akcji na 4 poziomy, m0r0 790 akcji na 1 poziom. Formuła
   `(H/A)²` karze to bezlitośnie. Czyli planer pomaga tylko wtedy, gdy model
   naprawdę napisze **poprawny** symulator i **krótki** plan.
3. **Portfolio bije oba.** Na 7/10 gier wygrywa WM, na 3 (dc22, sc25, s5i5) nasza
   linia. Unia per gra = **69,69**. To nie znaczy „66 na tablicy" (różne modele,
   public set), ale znaczy, że docelowo nie chodzi o wymianę silnika, tylko
   o **routing**: gry o prostej mechanice → pętla LLM, gry-zagadki → planer.

To jest odpowiedź na Twoje pytanie „znajdź lepszą drogę": to nie jest lepszy
model ani lepszy prompt. To **przeniesienie planowania z modelu do kodu**
i weryfikacja modelu gry przed wydaniem akcji.

---

## 4. Trzy tory, które mieszczą się w 8 dniach

| tor | co konkretnie | koszt | oczekiwany wynik | bramka |
|---|---|---|---|---|
| **T1** | c45/v9 = stack Franzena (jego model, jego SGLang, jego scheduler) na naszym kernelu | 1 slot (2,5 h smoke + 9 h run) | **35–39** | smoke > 29,02 |
| **T2** | akcje/wywołanie: plan-then-execute w REPL-u — model pisze pętlę `action([...])` z warunkami stopu (level up / brak zmiany / śmierć), nie pojedynczą akcję | 1 slot | 30–40 (×2–3 akcje/call) | akcji/call ≥ 3 i poziomy ≥ T1 |
| **T3** | pełny scaffold paper01: symulator + weryfikator + BFS planer, na lokalnym Qwen | 3–4 sloty | 40–55, jeśli model pisze poprawny symulator | 1 gra: planer dochodzi do `LEVEL_COMPLETED` w modelu **i** zgadza się z grą |

Kolejność jest istotna: T1 jest darmowym +10 bez ryzyka architektonicznego; T2 jest
tani i bezpośrednio atakuje zmierzony bottleneck; T3 jest jedynym torem z dowodem
na 45+, ale też jedynym, który może wyjść poniżej stanu obecnego.

**Kryteria zabicia:** T2 — jeśli akcji/call nie wzrośnie 3×, wyłączyć. T3 — jeśli
w 2 slotach planer nie ukończy ani jednego poziomu w modelu, wracamy do T1/T2.

---

## 5. Czego NIE robić (na podstawie zebranych dowodów)

- **Replay / pamięć między replikami** — w ocenianym runie nie istnieją: brak
  powtórzonych `game_id` (`taaf/competition_arcade.py`), zakres `PERSISTENT_FUNCTIONS_SCOPE`
  przyjmuje `turn|levelup|game`, a `n_passes=1`. Zero punktów.
- **game_weights** — walidowane i serializowane, nic nie realokują.
- **Sama zmiana modelu** — Franzen ma ten sam model klasy i 38,85. Sufit.
- **Więcej niż jedna zmiana na slot** — przy 8 slotach i 30 h GPU nie stać nas
  na eksperymenty bez pojedynczej zmiennej.

---

## 6. Co to znaczy dla „45+"

Realnie: **T1 podnosi do ~35–39, T2 dokłada kilka punktów, T3 jest jedyną drogą
na 45+ i jest niepewny w 8 dni.** Uczciwy przedział na 2 XI: 35–45, z 45+ tylko
jeśli T3 zadziała na lokalnym modelu — a tego nikt nie zmierzył (paper testował
wyłącznie GPT-5.4/5.5 przez API; open-weights nie były testowane).

---

## Źródła

- Leaderboard: <https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/leaderboard>,
  snapshot <https://arc.markbarney.net/arc-leaderboards>
- paper01: <https://arxiv.org/html/2605.05138v2>, kod i tabele per-gra:
  <https://github.com/astroseger/arc-3-agents-baseline1/tree/main/papers/paper01/results>
- metodologia RHAE (cap 115%, wagi poziomów): <https://docs.arcprize.org/methodology>
- Duck / Tufa: <https://tufalabs.ai/research/duck-harness/>
- Franzen (stack c45): <https://github.com/da-fr/arc-agi-3-solution>
- harness > model (GPT-6 Astra 62,7% → 99,9% z provider-adapter):
  <https://arcprize.org/blog/astra>
- AVO (Opus 5, pamięć trwała + supervisor, 183/183 poziomy public):
  <https://developer.nvidia.com/blog/nvidia-avo-reaches-100-on-arc-agi-3-demonstrating-a-frontier-level-general-purpose-architecture-for-long-horizon-autonomous-agents/>
