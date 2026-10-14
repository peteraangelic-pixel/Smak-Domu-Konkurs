"""Testy v6.4: LEVEL NOTES ekstrakcja + reinjekcja, GAME OVER history.

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


def _frame(levels: int = 0, state: str = "PLAYING") -> lp.FrameInfo:
    return lp.FrameInfo(
        grid=((0, 0), (0, 0)),
        step=3,
        level=0,
        state_name=state,
        levels_completed=levels,
        available_actions=["ACTION1", "ACTION2", "ACTION6"],
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


class LevelNotesExtractionTest(unittest.TestCase):
    def test_wyodrebnia_akapit_notatek(self) -> None:
        p = _policy()
        p._absorb_level_notes(
            "LEVEL 0 NOTES: Wagons must be collected in pattern order. "
            "Pink head pushes.\n\nNext I will explore."
        )
        self.assertIn("Wagons must be collected", p._level_notes[0])
        self.assertNotIn("Next I will explore", p._level_notes[0])

    def test_kilka_notatek_i_nadpisanie(self) -> None:
        p = _policy()
        p._absorb_level_notes("LEVEL 0 NOTES: aaa.\nLEVEL 1 NOTES: bbb.")
        self.assertEqual(p._level_notes[0], "aaa.")
        self.assertEqual(p._level_notes[1], "bbb.")
        p._absorb_level_notes("LEVEL 0 NOTES: nowa wersja.")
        self.assertEqual(p._level_notes[0], "nowa wersja.")

    def test_kafelek_trzyma_maks_trzy_poziomy(self) -> None:
        p = _policy()
        for lvl in range(5):
            p._absorb_level_notes(f"LEVEL {lvl} NOTES: notatka {lvl}.")
        self.assertEqual(sorted(p._level_notes), [2, 3, 4])

    def test_bez_notatek_cisza(self) -> None:
        p = _policy()
        p._absorb_level_notes("I think UP is best. {\"action\": \"UP\"}")
        self.assertEqual(p._level_notes, {})

    def test_notatki_sa_w_turze_uzytkownika(self) -> None:
        p = _policy()
        p._level_notes = {0: "collect wagons in order"}
        turn = p._build_user_turn(_frame())
        self.assertIn("Level notes (from solved levels):", turn)
        self.assertIn("collect wagons in order", turn)


class GameOverHistoryTest(unittest.TestCase):
    def test_zapis_i_wstrzykniecie(self) -> None:
        p = _policy()
        p.note_game_over(_frame(levels=0))
        p._actions_on_level = 17
        p.note_game_over(_frame(levels=0))
        self.assertEqual(len(p._game_overs), 2)
        turn = p._build_user_turn(_frame())
        self.assertIn("GAME OVER HISTORY", turn)
        self.assertIn("after 17 actions", turn)

    def test_limit_pieciu_najnowsze_wygrywaja(self) -> None:
        p = _policy()
        for i in range(7):
            p._actions_on_level = i
            p.note_game_over(_frame(levels=0))
        self.assertEqual(len(p._game_overs), 5)
        self.assertIn("after 6 actions", p._game_overs[-1])
        self.assertIn("after 2 actions", p._game_overs[0])

    def test_w_turze_tylko_ostatnie_trzy(self) -> None:
        p = _policy()
        for i in range(5):
            p._actions_on_level = i
            p.note_game_over(_frame(levels=0))
        turn = p._build_user_turn(_frame())
        self.assertNotIn("after 0 actions", turn)
        self.assertIn("after 4 actions", turn)

    def test_reset_game_czysci_historie(self) -> None:
        p = _policy()
        p.note_game_over(_frame())
        p._level_notes = {0: "x"}
        p.reset_game()
        self.assertEqual(p._game_overs, [])
        self.assertEqual(p._level_notes, {})


if __name__ == "__main__":
    unittest.main()
