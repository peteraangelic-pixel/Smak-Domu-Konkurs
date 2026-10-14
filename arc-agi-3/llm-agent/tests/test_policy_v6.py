"""Testy v6: notatki gry, audyt utknięcia, licznik akcji na poziomie, prompt.

CPU, bez LM Studio i bez sieci. Katalog `llm-agent` ma myślnik, więc pakiet
ładujemy pod aliasem `llmagent`.
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


def _policy() -> lp.LLMPolicy:
    p = lp.LLMPolicy.__new__(lp.LLMPolicy)
    p.tracker = lp.StateTracker()
    p.client = types.SimpleNamespace(total_tokens=0)
    p._messages = []
    p._action_queue = []
    p._actions_since_last_llm = 0
    p._last_level = 0
    p._game_notes = []
    p._actions_on_level = 0
    p._last_audit_at = 0
    p._noop_recent = []
    p._last_exec = None
    p._last_grid = None
    p._run_lessons = []
    p._level_start_tokens = 0
    p._audit_level_tokens = 0
    p._pending_notes = None
    return p


class NotesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = _policy()

    def test_notes_trafiaja_do_pamieci_i_znika_z_akcji(self) -> None:
        actions = [{"name": "ACTION1", "reasoning": {},
                    "notes": "GOAL: cover all dotted targets"}]
        self.p._absorb_notes(actions)
        self.assertEqual(self.p._game_notes, ["GOAL: cover all dotted targets"])
        self.assertNotIn("notes", actions[0])

    def test_duplikat_notatki_nie_dubluje_sie(self) -> None:
        self.p._absorb_notes([{"name": "ACTION1", "notes": "GOAL: X"}])
        self.p._absorb_notes([{"name": "ACTION1", "notes": "GOAL: X"}])
        self.assertEqual(self.p._game_notes, ["GOAL: X"])

    def test_trzyma_maks_cztery_notatki(self) -> None:
        for i in range(6):
            self.p._absorb_notes([{"name": "ACTION1", "notes": f"n{i}"}])
        self.assertEqual(self.p._game_notes, ["n2", "n3", "n4", "n5"])

    def test_reset_game_czysci_notatki(self) -> None:
        self.p._absorb_notes([{"name": "ACTION1", "notes": "GOAL: X"}])
        self.p._actions_on_level = 12
        self.p.reset_game()
        self.assertEqual(self.p._game_notes, [])
        self.assertEqual(self.p._actions_on_level, 0)
        self.assertEqual(self.p._last_audit_at, 0)

    def test_notatki_sa_w_turze_uzytkownika(self) -> None:
        self.p._game_notes = ["GOAL: all boxes in zone"]
        turn = self.p._build_user_turn(_frame())
        self.assertIn("Your game notes", turn)
        self.assertIn("all boxes in zone", turn)


def _frame() -> lp.FrameInfo:
    return lp.FrameInfo(
        grid=((0, 0), (0, 0)),
        step=0,
        level=0,
        state_name="PLAYING",
        levels_completed=0,
        available_actions=["ACTION1", "ACTION6"],
    )


class StuckAuditTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = _policy()

    def test_ponizej_progu_cisza(self) -> None:
        self.p._actions_on_level = 39
        self.assertIsNone(self.p._stuck_audit())

    def test_na_progu_audit_i_rearm(self) -> None:
        self.p._actions_on_level = 40
        first = self.p._stuck_audit()
        assert first is not None
        self.assertIn("STRATEGY AUDIT", first)
        self.assertIsNone(self.p._stuck_audit())  # re-arm: 45 - 40 < 15
        self.p._actions_on_level = 55
        second = self.p._stuck_audit()
        assert second is not None
        self.assertIn("55 actions", second)

    def test_licznik_na_turze_uzytkownika(self) -> None:
        self.p._actions_on_level = 7
        turn = self.p._build_user_turn(_frame())
        self.assertIn("Actions on this level: 7", turn)


class PromptV6Test(unittest.TestCase):
    def test_field_guide_w_prompcie(self) -> None:
        for marker in ('"ALL of something"', "PATTERN", "CONFIRM action",
                       "never a win", "GOAL PERSISTENCE", "STUCK PROTOCOL"):
            self.assertIn(marker, lp.SYSTEM_PROMPT)

    def test_format_notes_w_prompcie(self) -> None:
        self.assertIn('"notes"', lp.SYSTEM_PROMPT)
        self.assertIn("Deliberate LESS", lp.SYSTEM_PROMPT)


if __name__ == "__main__":
    unittest.main()
