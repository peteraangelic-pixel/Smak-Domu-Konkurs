"""Testy v6.7: adaptacyjna temperatura + odporna ekstrakcja LEVEL NOTES.

CPU, bez LM Studio i bez sieci. Katalog `llm-agent` ma myślnik — alias `llmagent`.
"""

from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parents[1]
_pkg = types.ModuleType("llmagent")
_pkg.__path__ = [str(PKG_DIR)]  # type: ignore[attr-defined]
sys.modules.setdefault("llmagent", _pkg)

from llmagent import llm_policy as lp  # noqa: E402


def _frame(levels: int = 0) -> lp.FrameInfo:
    return lp.FrameInfo(
        grid=((0, 0), (1, 0)),
        step=0,
        level=0,
        state_name="PLAYING",
        levels_completed=levels,
        available_actions=["ACTION1", "ACTION2", "ACTION6"],
    )


class TemperatureRecorder:
    """Fałszywy klient: pamięta temperatury z wywołań."""

    def __init__(self, total_tokens: int = 0):
        self.total_tokens = total_tokens
        self.temps: list[float | None] = []

    def chat(self, messages, temperature=None):
        self.temps.append(temperature)
        return {"content": '{"action": "UP"}'}


def _policy(client: TemperatureRecorder | None = None) -> lp.LLMPolicy:
    p = lp.LLMPolicy.__new__(lp.LLMPolicy)
    p.config = None
    p.client = client or TemperatureRecorder()
    p.tracker = lp.StateTracker()
    p._messages = []
    p._action_queue = []
    p._actions_since_last_llm = 0
    p._max_actions_per_plan = 15
    p._last_level = 0
    p._game_notes = []
    p._actions_on_level = 0
    p._last_audit_at = 0
    p._probe_level = None
    p._noop_recent = []
    p._last_exec = None
    p._last_grid = None
    p._run_lessons = []
    p._level_start_tokens = 0
    p._audit_level_tokens = 0
    p._pending_notes = None
    p._level_notes = {}
    p._game_overs = []
    p._audits_on_level = 0
    p.value_gate = None
    return p


class AdaptiveTemperatureTest(unittest.TestCase):
    def test_nie_gleboko_utkniety_none_configu(self) -> None:
        rec = TemperatureRecorder()
        p = _policy(rec)
        p._actions_on_level = 20  # świeży nie jest, audytów brak
        p._probe_level = 0  # pomiń probe opening (testujemy temperaturę LLM)
        p.choose_action(_frame())
        self.assertEqual(rec.temps, [None])  # temperatura z configu

    def test_pierwsze_akcje_poziomu_goraczej(self) -> None:
        rec = TemperatureRecorder()
        p = _policy(rec)
        p._actions_on_level = 2
        p._probe_level = 0
        p.choose_action(_frame())
        self.assertEqual(rec.temps, [0.7])

    def test_po_dwóch_audytach_najgoraczej(self) -> None:
        rec = TemperatureRecorder()
        p = _policy(rec)
        p._actions_on_level = 42
        p._audits_on_level = 2
        p._probe_level = 0
        p.choose_action(_frame())
        self.assertEqual(rec.temps, [0.9])

    def test_reset_game_zeruje_audyty(self) -> None:
        p = _policy()
        p._audits_on_level = 3
        p.reset_game()
        self.assertEqual(p._audits_on_level, 0)

    def test_reset_pola_audytow_poziomu(self) -> None:
        p = _policy()
        p._audits_on_level = 1
        p._actions_on_level = 41
        p.choose_action(_frame(levels=1))  # rozwiązany poziom
        self.assertEqual(p._audits_on_level, 0)


class RobustNotesExtractionTest(unittest.TestCase):
    def test_z_reasoning_content(self) -> None:
        p = _policy()
        p._absorb_level_notes({
            "content": '{"action": "UP"}',
            "reasoning_content": "Level 0 NOTES: wagons in pattern order. Push pink head first.",
        })
        self.assertIn("wagons in pattern order", p._level_notes[0])

    def test_z_listy_czesci(self) -> None:
        p = _policy()
        p._absorb_level_notes({
            "content": [{"type": "text", "text": "Some preamble."},
                        {"type": "text", "text": "LEVEL 0 NOTES: gems are targets. X"}],
        })
        self.assertIn("gems are targets", p._level_notes[0])

    def test_krotka_notatka_odrzucona(self) -> None:
        p = _policy()
        p._absorb_level_notes("LEVEL 0 NOTES: ok.")
        self.assertEqual(p._level_notes, {})

    def test_backticki_i_poziom_ponad_sto(self) -> None:
        p = _policy()
        p._absorb_level_notes("LEVEL 0 NOTES: use `confirm` only after setup is ready.")
        self.assertIn("confirm", p._level_notes[0])
        p._absorb_level_notes("LEVEL 999 NOTES: this should be ignored entirely.")
        self.assertEqual(sorted(p._level_notes), [0])


if __name__ == "__main__":
    unittest.main()
