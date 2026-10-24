# Weryfikacja między-sesyjnych opinii (24.10) — co potwierdzone, co obalone, co przyjęte

## POTWIERDZONE DZIAŁANIEM
| Teza | Źródło | Dowód |
|---|---|---|
| **400 = `-f` ścieżka repo zamiast nazwy pliku** | DeepSeek 4.1 | ops.py:459; 12×ścieżka=12×400 vs 2×nazwa=2×rc=0; **r069: submit v5 `-f submission.parquet` → rc=0, ref 57607527** |
| Guard kwoty martwy (soft_end nadpisywany) | DeepSeek 4.1 | kom.14: nasz guard @3641 < `soft_end=None` @3872 < ich finalny @4004 < bm.run @4219 → smoke 2h12m zamiast 40 min; FIX: cap re-applied po nadpisaniu |
| 400 nie pali slotu | my (empiria) | 3×400 dziś, slot dalej wolny przed r069 |

## OBALONE / WYCOFANE (REJESTR)
- **`game_weights` realokuje budżet** — MIT (a450+DeepSeek): tylko agregacja diagnostyki (benchmark.py ~38–52). Dźwignia #1 z PLAN-GENIUS nie istnieje.
- **Pin dockera blokuje API-submit** — nasza hipoteza; prawdziwą przyczyną było `-f`.
- **Replay = +45–50% → 45** — efektywność H/A już ~0.95 (17/27 poziomów na capie 115); replay podnosi efektywność, nie sufit → realnie ≤ +1.5. Warto rośnie przy n_passes>1 / po śmierciach (ONLY_RESET_LEVELS=true: reset cofa tylko bieżący poziom — werdykt Smak potwierdzony w game_api.py:221).
- „Deadline 26.10 = koniec" — entry ACCEPTED; **finał = 2.11** → 9 dni = pętla pomiarowa. Nagrody = MIEJSCA (Top Score $75K/$40K/$15K/$10K/$5K/$5K), nie próg 40 (to była 5. pozycja starego snapshotu).
- „Workflow gubi token" — redundantna linia (Arena verdict): $GITHUB_ENV wchodzi do env kolejnych kroków.

## PRZYJĘTE (dźwignie na 25.10+)
1. **Pamięć między replikami** (c87 log + Arena): official_110 = 25 mechanik × ~4.4 replik; ARC3_PERSISTENT_FUNCTIONS_SCOPE='game' + MEMORY_SECTIONS='off' = wiedza ginie między replikami → SCOPE='run' = ×4.4 budżetu/mechanikę (915 vs 685 akcji na clearing). Test: 5 linii logu (hash segmentacji 1. ramki + game_id) w najbliższym smoke.
2. **MAXREQ 10→16** = +45% puli (ekstrapolacja c87; walczy o KV z #1 — po nim).
3. **Głębokość na cn04/su15** (0.3–0.5× baseline), nie ogon (ls20/tn36 = wiedza, nie punkty).
4. **Offline-search playbook c87 = zmierzone +3.18 LB** — podłoga/warm-start.
5. **LB anchor do odświeżenia** (r070) — stare 40.97 = 5. miejsce z 10.10.
6. Open-source (CC0/MIT-0) wymagany przed nagrodą — nasze kernele is_private → otworzymy przy prize-eligibility (kod Tufy i tak MIT).

## PODZIĘKOWANIA (konkretne)
DeepSeek 4.1 — bug `-f` (kosztował nas 8 dni); c87f7a48 — FAKTY-I-POMIARY, arytmetyka budżetu, uczciwe korekty własnych obietnic; a450b00f — audyty + pakiet duck-v8 (replay, 10/10 testów, 2 bugi złapane własnym testem integracyjnym); Gemma c4eeb067 — wzór scoringu per poziom i decyzje/min; Gemma 6d081d52 — kalibracja oczekiwań i rozdzielenie deadline'ów.
