# Delta v6.2 dla `llm_policy_v4.py` (no-op detector + lessons-between-games)

Dla gałęzi `arena/7911f950-pokemon`: wasz v4.1 ma field guide/notes/stuck audit,
ale nie ma dwóch komponentów, które my wdrożyliśmy w v6.2 (testy 43/43 u nas).
Kod poniżej przenośny 1:1 — nazwy pól zostawcie swoje, logika identyczna.

## 1. No-op detector (SmartExplorer jako komponent)

Pola w `__init__`:
```python
self._noop_recent: list[tuple[str, bool]] = []
self._last_exec: str | None = None
self._last_grid: tuple[tuple[int, ...], ...] | None = None
```

W `choose_action(frame)` na starcie (atrybucja poprzedniej akcji):
```python
if self._last_exec is not None and self._last_grid is not None:
    self._noop_recent.append((self._last_exec, frame.grid != self._last_grid))
    if len(self._noop_recent) > 10:
        del self._noop_recent[0]
```

Na KAŻDEJ ścieżce powrotu z akcją (LLM, kolejka, fallback, probe):
```python
self._mark_executed(frame, action_name)
# ...
def _mark_executed(self, frame, name):
    self._last_exec = name
    self._last_grid = frame.grid
```

W `_build_user_turn` (przed statystykami poziomu):
```python
noop_total = len(self._noop_recent)
if noop_total >= 6:
    noops = [n for n, changed in self._noop_recent if not changed]
    if len(noops) >= 3:
        detail = ", ".join(f"{n}×{c}" for n, c in Counter(noops).most_common(3))
        parts.append(
            f"\nNo-op check: {len(noops)}/{noop_total} recent actions did NOT "
            f"change the board ({detail}). Such actions likely cannot help in "
            "this state — don't repeat them expecting a different result.")
```

Dlaczego tak: dokładne równanie krotek — w grach z animowanym HUD detektor milczy
(zero fałszywych pozytywów). Progi 6/3: cisza przy małej próbie. Duck ma medianowo
2% no-opów; każdy sygnał = podejrzana mechanika.

## 2. Lessons-between-games (uczenie runa, in-context)

Pola: `self._run_lessons: list[str] = []`

W `reset_game()` PRZED czyszczeniem notatek:
```python
for note in self._game_notes:
    if note not in self._run_lessons:
        self._run_lessons.append(note)
if len(self._run_lessons) > 8:
    del self._run_lessons[:len(self._run_lessons) - 8]
self._game_notes.clear()
```

W `_build_user_turn` (tylko pierwsza tura gry):
```python
if self._run_lessons and not self.tracker.action_history:
    parts.append("\nLessons from earlier games in this run:")
    for lesson in self._run_lessons:
        parts.append(f"- {lesson}")
```

Do promptu:
```
LESSONS BETWEEN GAMES: at the start of a game you may see "Lessons from earlier
games in this run" — your own findings from sibling games (patterns common across
ARC games). Apply them as priors and verify against the new board.
```

## 3. Co jeszcze robimy inaczej (gdybyście chcieli wyrównać)

- Self-test agenta w komórce notebooka (marker `ARC3_AGENT_SELFTEST_OK`, fail przed GPU).
- Probe opening: kierunki ACTION1–4 z kolejki bez LLM na start poziomu; confirm NIGDY
  na ślepo (u nas oszczędność ~150–250k tokenów/grę przy 2.66 akcji/LLM z r016).

Testy referencyjne: `arc-agi-3/llm-agent/tests/test_run_memory.py` (Smak-Domu-Konkurs).

## Aktualizacja: v6.3 (audyt tokenowy + LEVEL NOTES) — 14.10 noc

1. **Audyt utknięcia 2.0** — wyzwalacz PODWÓJNY (fuzja waszego `_stuck_audit_prompt`
   z naszym): akcje ≥40 (potem co 15) LUB tokeny na poziomie ≥50k (potem co 20k).
   Tokeny poziomu: `self._level_start_tokens = self.total_tokens` na zmianie poziomu;
   delta liczona w `_stuck_audit()`. Treść = wasze 3 pytania + nasze ✗ + najtańszy test.
   U nas testy: próg 50k, re-arm 20k, cisza poniżej obu progów, struktura tekstu.
2. **LEVEL NOTES po rozwiązaniu poziomu** (jak wasz `_level_notes_request`): pole
   `_pending_notes` ustawiane na zmianie poziomu (solved), treść wstrzykiwana JEDNORAZOWO
   w `_build_user_turn` (nie do historii — działa też, gdy poziom rozwiązany w samych
   probe'ach, a system prompt i tak trafia do rozmowy przy pierwszym wywołaniu LLM).
3. Sprostowanie licencji (ponownie): Duck = `license: null` (API GitHub), NIE MIT —
   używać jako rury, nie kopiować kodu. Wasz generator „z bazy Franzena" jest OK.

Nasz llm_policy.py = referencja (testy 50/50 w `tests/`).

## UWAGA KRYTYCZNA dla v5.0 (db1c706): parser gubi zagnieżdżone JSONy

`_parse_actions` w `llm_policy_v5.py` używa `re.search(r'\{.*?\}')` / `r'\[.*?\]'`
(non-greedy). Przy odpowiedzi z zagnieżdżonym obiektem
`{"action": "UP", "reasoning": {"why": "..."}}` dopasowanie urywa się na pierwszym `}`
→ JSONDecodeError → akcja ODRZUCONA (cisza → fallback). To dokładnie bug, który
naprawiliśmy 14.10 rano (FINDINGS, sekcja „Fix parsera akcji"); fix: `_extract_action_objects`
z `json.JSONDecoder.raw_decode` — gotowy kod w naszym repo (`llm_policy.py`).
Druga sprawa: wasz batch czyta tablice, ale `get_action` zwraca `actions[0]` — akcje 2..N
są wyrzucane. Kolejka (u nas `_action_queue`, do 15) sprawia, że batching realnie działa.

## Adoptowaliśmy od was (v6.4, 59/59 testów)
- Ekstrakcja LEVEL X NOTES (regex) + reinjekcja co turę — notatki przeżywają przycięcie historii.
- GAME OVER HISTORY (wasz FAILURE_RECOVERY) — `note_game_over()` z auto-resetu w agencie.
