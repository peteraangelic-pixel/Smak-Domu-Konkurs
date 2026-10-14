"""Testy v6.3: audyt na tokenach LUB akcjach + notatki z ukończonego poziomu.

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
        grid=((0, 0), (0, 0)),
        step=0,
        level=0,
        state_name="PLAYING",
        levels_completed=levels,
        available_actions=["ACTION1", "ACTION2", "ACTION3", "ACTION4", "ACTION6"],
    )


def _policy(content='{"action": "UP"}', total_tokens: int = 0) -> lp.LLMPolicy:
    p = lp.LLMPolicy.__new__(lp.LLMPolicy)
    p.config = None
    p.client = types.SimpleNamespace(chat=lambda msgs: {"content": content},
                                     total_tokens=total_tokens)
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
    p._level_start_tokens = total_tokens
    p._audit_level_tokens = 0
    p._pending_notes = None
    p._level_notes = {}
    p._game_overs = []
    return p


class TokenAuditTest(unittest.TestCase):
    def test_audit_od_tokenow_przed_prog_akcji(self) -> None:
        p = _policy(total_tokens=0)
        p._actions_on_level = 5  # akcje poniżej progu 40
        p.client.total_tokens = 55_000
        audit = p._stuck_audit()
        assert audit is not None
        self.assertIn("STRATEGY AUDIT", audit)
        self.assertIn("~55k tokens", audit)
        # re-arm do +20k tokenów
        self.assertIsNone(p._stuck_audit())

    def test_poziom_tokenow_resetuje_sie_na_zmianie(self) -> None:
        p = _policy(total_tokens=0)
        p.client.total_tokens = 30_000
        p.choose_action(_frame(levels=1))  # zmiana poziomu (solved)
        self.assertEqual(p._level_start_tokens, 30_000)
        self.assertIsNone(p._stuck_audit())

    def test_cisza_ponizej_obu_progow(self) -> None:
        p = _policy(total_tokens=0)
        p._actions_on_level = 39
        p.client.total_tokens = 49_999
        self.assertIsNone(p._stuck_audit())

    def test_audit_zawiera_trzy_czeci_i_falsyfikacje(self) -> None:
        p = _policy(total_tokens=0)
        p._actions_on_level = 40
        audit = p._stuck_audit()
        assert audit is not None
        for marker in ("FALSIFIED", "NOT yet tried", "differs from your assumption",
                       "cheapest"):
            self.assertIn(marker, audit)


class LevelCompletionNotesTest(unittest.TestCase):
    def test_poziom_wygrany_zadaje_notatki_w_turze(self) -> None:
        p = _policy()
        p._last_level = 0
        p._messages = [{"role": "system", "content": "s"}]
        p.choose_action(_frame(levels=1))  # poziom 0 właśnie rozwiązany
        turn = p._build_user_turn(_frame(levels=1))
        self.assertIn("LEVEL 0 NOTES:", turn)
        self.assertIn("max 4 short sentences", turn)
        # żądanie jednorazowe
        turn2 = p._build_user_turn(_frame(levels=1))
        self.assertNotIn("LEVEL 0 NOTES:", turn2)

    def test_bez_rozwiazania_brak_zadania(self) -> None:
        p = _policy()
        p._last_level = 2
        p._messages = [{"role": "system", "content": "s"}]
        p.choose_action(_frame(levels=1))  # levels spadły — nie solved
        self.assertIsNone(p._pending_notes)

    def test_reset_game_czysci_pending(self) -> None:
        p = _policy()
        p._pending_notes = 3
        p.reset_game()
        self.assertIsNone(p._pending_notes)


if __name__ == "__main__":
    unittest.main()
