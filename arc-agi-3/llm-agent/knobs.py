"""Rejestr KNOBS (v6.8) — ewoluowalna powierzchnia parametrów polityki.

Wzorzec z projektu Pokemon (c87f7a48): wszystkie magiczne liczby agenta w jednym
słowniku `PTCG_*` → ewolucja CEM po 26 pokrętłach (100 mutantów, 138 gier/mutant)
zdała +pkt tam, gdzie płytkie ML dało ±0. U nas analogicznie: ARC3_* knobs.

 nadpisanie: env `ARC3_KNOBS_JSON` = JSON z PODZBIOREM kluczy (reszta z domyślnych).
JSON jest czytany RAZ przy imporcie modułu; testy ustawiają wpisy wprost.
"""

from __future__ import annotations

import json
import os

KNOBS: dict[str, float] = {
    # audyt utknięcia — wyzwalacz akcyjny
    "AUDIT_ACTIONS": 40,            # próg akcji na poziomie
    "AUDIT_ACTIONS_REARM": 15,      # kolejny audyt po tylu akcjach
    # audyt utknięcia — wyzwalacz tokenowy
    "AUDIT_TOKENS": 50_000,         # próg tokenów na poziomie
    "AUDIT_TOKENS_REARM": 20_000,   # kolejny audyt po tylu tokenach
    "AUDIT_ESCALATE_FROM": 2,       # od tego numeru audytu dochodzi STRATEGY RESET
    # adaptacyjna temperatura
    "TEMP_BASE": 0.6,               # (kompatybilność z configiem; chat używa configu gdy None)
    "TEMP_FRESH": 0.7,              # świeży poziom (< FRESH_ACTIONS akcji)
    "TEMP_FRESH_ACTIONS": 5,
    "TEMP_STUCK": 0.9,              # po eskalacji (audyt >= AUDIT_ESCALATE_FROM)
    # probe opening
    "PROBE_MAX": 4,                 # maks. akcji-kierunków na start poziomu
    # batching
    "PROMPT_BATCH_MAX": 8,          # ile akcji planować w jednej odpowiedzi (prompt)
    "QUEUE_MAX": 15,                # re-plan po tylu akcjach z kolejki
    # pamięć
    "NOTES_MAX": 4,                 # notatki „notes" trzymane jednocześnie
    "LESSONS_MAX": 8,               # lekcje między grami w runie
    "LEVEL_NOTES_KEEP": 3,          # notatki rozwiązanych poziomów
    "LEVEL_NOTES_CHARS": 400,
    "GAME_OVERS_KEEP": 5,
    "GAME_OVERS_SHOW": 3,
    # no-op detector
    "NOOP_WINDOW": 10,
    "NOOP_MIN_SAMPLES": 6,
    "NOOP_TRIGGER": 3,
}


def apply_overrides(raw: str | None) -> None:
    """Nadpisz KNOBS z JSON (częściowy). Nieznane klucze pomijane z ostrzeżeniem."""
    if not raw:
        return
    try:
        blob = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        print(f"[KNOBS] ARC3_KNOBS_JSON nie jest poprawnym JSON — pomijam: {raw[:80]}")
        return
    if not isinstance(blob, dict):
        print("[KNOBS] ARC3_KNOBS_JSON nie jest obiektem — pomijam")
        return
    for key, value in blob.items():
        if key in KNOBS and isinstance(value, (int, float)) and not isinstance(value, bool):
            KNOBS[key] = type(KNOBS[key])(value)
        else:
            print(f"[KNOBS] pomijam nieznane/złe pole: {key}={value!r}")


# Snapshot domyślnych wartości (do resetu w workerach multiprocessing).
DEFAULTS: dict[str, float] = dict(KNOBS)


def reset_to_defaults() -> None:
    """Przywróć wartości domyślne (worker multiprocessing przed własnym nadpisaniem)."""
    KNOBS.clear()
    KNOBS.update(DEFAULTS)


apply_overrides(os.environ.get("ARC3_KNOBS_JSON"))
