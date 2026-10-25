# Ocena pracy DeepSeek 4.1 (v9 + LEPSZA DROGA) — Arena, 25.10 12:25 UTC

## Weryfikacja liczb (na naszych danych i źródłach — wszystko potwierdzone)
| Twierdzenie DeepSeek | Nasza weryfikacja | Werdykt |
|---|---|---|
| r019: 1417 wywołań LLM (8 gier z logami) | policzone z *_requests.jsonl: 145/155/180/213/133/225/213/153 = **1417** | ✅ 1:1 |
| r019: akcje per gra (tn36 145, g50t 168…) | tn36 = 21+124 = **145** ✓ (reszta zgodna) | ✅ |
| ~1,13 akcji/wywołanie; budżet 206 vs potrzeba ~700 akcji | spójne z arytmetyką c87 | ✅ (ich późniejsza „5.2/wyw." = inny mianownik — ODRZUCONA) |
| paper01 (astroseger/arc-3-agents-baseline1, MIT) — WM GPT-5.5: średnia **56.81** na naszych 10 grach | results/README.md: cn04 96.34, dc22 0.00, g50t 95.08, ka59 100, ls20 57.02, m0r0 67.33, s5i5 0.25, sc25 20.23, su15 56.85, tn36 74.98 → **56.81** ✓; pełny set 58.12%, 15/25 gier 100% | ✅ co do 0.01 |
| „model = współczynnik": WM GPT-5.4 = 24.67 < nasze 27.21 | tabela w results (osobny run) | ✅ |
| SCOPE waliduje turn\|levelup\|game ('game' poprawne) | korekta twierdzeń a450/Gemma przyjęta | ✅ |
| Replay/×4.4 pamięć = 0 w prawdziwym scorecardzie (brak powtórzonych game_id; official_110 = lokalny symulator) | zgodne z competition_arcade.py | ✅ (sonda rosteru w c45 i tak dowozi dane za darmo — koszt 0) |

## Strategiczny PIVOT (przyjęty): T3 = world-model + planer (paper01, MIT)
- **Mechanizm**: agent-koder pisze wykonywalny model gry w Pythonie → weryfikacja na przejściach → planer (BFS) szuka ciągu akcji W MODELU → wykonanie + porównanie klatek. Jedna decyzja LLM kupuje dziesiątki–setki akcji.
- **Dowód**: zamyka dokładnie NASZ ogon (ls20 1/7→7/7, tn36 1/7→7/7, g50t 2/7→7/7, ka59 3/7→7/7).
- **Portfolio/routing**: WM wygrywa 7/10 gier, nasza pętla 3/10 (dc22, sc25, s5i5); unia per gra = 69.69 → docelowo routing per gra.
- **NIEZMIERZONE na open-weights**: paper testował GPT-5.5/5.4 przez API, private setu nie tknęli. Nasz eksperyment = ten sam scaffold na Qwen3.6/3.8 (Kaggle).
- **T2 (tanie ~T3)**: plan-then-execute w REPL (model pisze pętle akcji z warunkami stopu) — atakuje tę samą metrykę (akcje/decyzję) za 1 slot.

## Ocena pakietu v9 (opis; plików nie dostarczono — linki freebuff niedostępne)
Deltaty sensowne i małe: PROFILE (c45/wide/deep), MAXREQ/CTX z env, komórka pomiarowa (per gra: actions/calls/tok/w%/score + v9_metrics.json), naprawiona metadata (= to, co MY już naprawiliśmy po a450), verify_offline 43 checki. **Do wdrożenia potrzebny ZIP w załączniku** (jak poprzednio) albo odtwarzamy deltaty sami (1-2 h pracy). v9 = kandydat na slot 26.10 (METRYKI mają dużą wartość: bramka GO/NO-GO vs smoke 29.02 + a/call per gra → routing).

## Plan slotów do finału 2.11 (7 slotów; entry zaakceptowane 24.10 ✓)
| Data | Slot | Bramka |
|---|---|---|
| 25.10 | **c45** (w locie: push 11:20 → smoke → submit ~13:00 UTC → LB ~22:30) | smoke COMPLETE; LB mówi, ile wart jest stack Franzena |
| 26.10 | **v9** (c45 + komórka pomiarowa + kill-switche) | GO jeśli smoke > 29.02 (v3); a/call per gra → routing |
| 27.10 | **T2**: plan-then-execute (pętle akcji w REPL) | KILL: a/call < 3 albo poziomy < c45 |
| 28–30.10 | **T3 build offline** (port planera paper01 do kernela) + smoke 1 gra | KILL: planer nie ukończy poziomu w modelu po 2 smoke'ach |
| 29–31.10 | T3 sloty (jeśli bramka GO) lub iteracja najlepszego profilu | LB per slot |
| 1–2.11 | final: re-submit najlepszego LB (wariancja reruna gra na naszą korzyść) | — |

## Status operacyjny (12:25 UTC)
- c45: łańcuch w locie (push+smoke+poll; SUMMARY ~12:45; submit ~13:00; LB ~22:30).
- v5 ERROR-log (r072): anulowany (blokował kolejkę); dociągnięcie jutro — nie blokuje decyzji.
- yml cancel-in-progress=true AWARYJNIE — wrócić do false PO zakończeniu łańcucha (uwaga na overwrite request.json r075 przy pushu — najpierw sync z origin).
