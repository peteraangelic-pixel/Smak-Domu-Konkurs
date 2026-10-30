# OCENA ARENY — duck-v13.3-arena (własny wariant, 30.10 2026 ~09:30 UTC)

**Werdykt: CERTYFIKOWANA przez Arenę (wszystkie checki własne, „ALL CHECKS PASSED").
Kandydat na slot 31.10 jako pomiar mechanizmu „wymuszenie batcha" — GO#1 na 30.10
pozostaje v13.2 (cererowanie: patrz koniec dokumentu). NIC do Kaggle bez GO usera.**

Lineage: v13.2 (Pokemon 6b10853, certyfikacja 75306840^) → **v13.3-arena** (nasz pakiet).
Autor zmian: Arena (ta sesja). Zmiany celowo MINIMALNE i każd z osobna kill-switchowalna,
bo slot 31.10 ma mierzyć JEDEN mechanizm naraz.

## Zmiany vs v13.2 (dokładnie 3 obszary)

### 1. `ARC3_OPENER_COMMIT_HINT=1` (env-only, zero nowych patchy promptowych)
- Mechanizm istnieje w harnessie: `inference/agent/tool_agent.py` `_opener_commit_hint()`
  (`_get_env_bool("ARC3_OPENER_COMMIT_HINT", False)` — domyślnie OFF; nic w drzewie tego
  nie nadpisuje — grep potwierdzony). Przy włączeniu dodaje do każdego świeżego openera
  linię: „When your evidence supports a choice, call `action(actions)` with the sequence
  it supports. Probe with a single action when you genuinely need to distinguish two
  possibilities; otherwise batch the route you have."
- **Pomiar upstreamu w docstringu** (Tufa lineage): sekwencje po resumption batchują
  6,73/6,91 akcji; świeże openery 5,43/3,91 — hint celowo asymetryczny (batch domyślny,
  probe dozwolony ale wymaga uzasadnienia). Nasza linia mierzy ~4,36 akcji/wywołanie
  (r019) — cel 6–9.
- Dlaczego to jest „to samo" co postulat c87 („wymuszenie batcha na 1. turze poziomu"):
  opener = świeża tura; dyrektywa eskalacyjna (v13.2, co 10 akcji) nie obejmuje pierwszych
  ~10 akcji poziomu, hint obejmuje KAŻDY opener w tym start poziomu.
- Wpina się w `ARC3_VARIANT["env"]` (kom. 1) → aplikowane przez `os.environ.update`
  w kom. 13 (ten sam kanał co ARC3_WINPATH/DEAD_SKIP). Czytane NA ŻYWO przy budowie
  prompta (bez cache konstrukcji agenta).
- Kill-switch: `"ARC3_OPENER_COMMIT_HINT": "0"` w komórce wariantu.

### 2. Patch 0007 (`duck-extra-05`): log zdarzeń win-path (observability)
- Nowy plik patcha: `patches/0007-arena-replay-log.patch` (blob 4113516→c788255, +43 linie
  na `ARC3-Inference/inference/framework/arc3_winpath.py`).
- `_log()` = jednolinijkowy stdout `[arc3-winpath] …` (flush), domyślnie ON,
  `ARC3_WINPATH_LOG=0` wycisza. **Nigdy na gorących ścieżkach** (per-iteracyjne
  early-returns ciche). Zdarzenia: session begin/end (z licznikami magazynu),
  playbook match, replay start (game/level/n), replay ok, replay abort + POWÓD
  (hash-mismatch@krok, action-unavailable, game-over, init-mismatch→broken, exhausted),
  record, dead-skip (game/passes_completed).
- Motywacja: audyt 7911 (replay = try/except bez logu; init-mismatch → broken CICHO)
  + c87 („wymagać linii logu o replay"; „ryzyko diagnostyki, nie wyniku"). Skutek
  operacyjny: z samego logu reruna 31.10 odczytamy, czy replay w ogóle strzelał,
  bez dumpów plików — domyka probe wartości pamięci.
- **Zmiana semantyki: ZERO** (log-only); potwierdzone 11/11 testami, w tym
  zachowanie liczników akcji bez zmian.

### 3. Porządki wersyjne
- Kom. 2: print `v13.3-arena profile=…` + komentarz kill-switchy. Kom. 1: name
  `v13-3-arena` + rejestracja extra-05/0007. Metadata: `arc3-duck-v13-3-arena`.
- NOWE narzędzie: `tools/build_v133_arena.py` (builder z jawnym lineage; źródło:
  certyfikowany notebook v13.2, nie base-v11 — najmniejszy możliwy delta-chain).
- `tools/verify_v13.py` pakietu: 7 patchy, 36 komórek, nowe checki (opener hint,
  extra-05, wersja), **naprawiony znany bug środowiskowy** (krok winpath nadpisywał
  PYTHONPATH gubiąc arcengine — teraz PYTHONPATH jest zachowany; FAIL z 30.10 07:57
  był tym samym korzeniem).

## Weryfikacja (wszystko samodzielnie, 30.10)

1. **7/7 patchy** na czystym bundle r033, kolejność komórek jak w notebooku
   (harness-changes → extra-00..04 → extra-05); `verify_v13.py --bundle … --tests`
   → **ALL CHECKS PASSED** (lista 30 checków OK, m.in. opener hint w wariancie,
   extra-05 zarejestrowany, playbook embedded == playbook.json, przełącznik
   PLAN_COMMIT w obie strony, 36 komórek, 21 komórek kodu się kompiluje).
2. **12/12 plan-commit + 11/11 winpath** na spatchowanym drzewie
   (arcengine 0.9.3 z /tmp/ae). 3 nowe testy: log przy sukcesie replayu
   (`replay start/ok`), init-mismatch (`-> broken` + powód), tryb cichy
   (`ARC3_WINPATH_LOG=0` → puste stdout, zachowanie bez zmian).
3. standalone `src/arc3_winpath.py` == spatchowany moduł **bajt-w-bajt** (cmp).
4. **Playbook bajtowo identyczny z v13.2** (cmp) + revalidacja **14/14 na żywym
   silniku** (arcengine 0.9.3 / arc_agi 0.9.9).
5. **Cell-diff vs v13.2**: różnią się WYŁĄCZNIE kom. 1 i 2 + wstawiony writer
   (nowa kom. 12); komórki 11..34 → 12..35 przesunięte 1:1 BEZ zmian treści;
   **serving: stara kom. 21 == nowa 22** (parity z c45 przenosi się tranzytywnie);
   test_plan_commit.py bajtowo identyczny.

## Ryzyka i mitygacje

| ryzyko | waga | mitygacja |
|---|---|---|
| model batchuje gorzej niż pojedyncze kroki (hint zmienia statystykę tur) | średnie | zmierzony upstream efekt kierunkowy (+); kill-switch env; osobny slot 31.10 (nie ryzykuje GO#1); metr: akcje/wywołanie w meteringu |
| interakcja hint+eskalacja (dwa naciski naraz) | niskie | oba teksty są komplementarne (batch via action(actions), commit(plan) w eskalacji); testy plan-commit 12/12 |
| log kłóci się z czymś w parserach Kaggle | znikome | zwykły stdout, prefix `[arc3-winpath]`, kilka-kilkanaście linii/gra |
| patch 0007 psuje replay | znikome | log-only; 11/11 testów na spatchowanym drzewie; standalone==patched bajt |

## Decyzja slotowa (propozycja; decyduje user GO)

- **30.10: v13.2 AS-SHIPPED** (GO#1, certyfikowana wcześniej) — baseline eskalacji co 10.
- **31.10: v13.3-arena** — pomiar mechanizmu: metering akcje/wywołanie (cel ≥6 z ~4,36)
  + logi `[arc3-winpath]` (czy replay żył) + score.
- 1.11: lepszy mechanizm ×2 (draw); 2.11: select best (sprawdzić w rules liczbę
  punktowanych submisji).
- Alternatywa agresywna: 30.10 od razu v13.3-arena — NIE rekomenduję: jedno wy_settings
  na slot; najpierw baseline v13.2 pozwoli policzyć wkład hinta z meteringu.

## Czego NIE zrobiłem (i dlaczego)

- Własny patch „twardego wymuszenia commit(plan)" (odrzucanie tur 1-akcyjnych na poziomie
  harnessu): dotykamy pętli decyzyjnej solvera = ryzyko klasy concurrency-120; hint
  + eskalacja pokrywają cel taniej. Kandydat na przyszłość po pomiarze 31.10.
- Skrócenie ścieżek playbooka: EV ≈ 0 na ukrytym rosterze (retrakcja §15), kosmetyka.
- Zmiany serwingu/promptów systemowych: ostrzeżenie c87 (−7…−8 bez pomiaru KV).
- Trim historii (ARC3_HISTORY_ASSISTANT_TURNS 150→np. 48): env-only i kuszące (−30% tok/akcję
  → +40% akcji/grę przy tym samym silniku), ALE niezmierzone i godzi w pamięć gry —
  zostaje jako PRZYGOTOWANA OPCJA na 1.11 (jedna linia env), nie doklejana do v13.3.
