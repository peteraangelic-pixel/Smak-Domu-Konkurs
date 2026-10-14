"""Testy v6.2: no-op detector + lessons-between-games (pamięć poziomu runa).

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


def _frame(grid, levels=0):
    return lp.FrameInfo(
        grid=grid,
        step=0,
        level=0,
        state_name="PLAYING",
        levels_completed=levels,
        available_actions=["ACTION1", "ACTION2", "ACTION3", "ACTION4", "ACTION6"],
    )


G_A = ((0, 0), (0, 0))
G_B = ((0, 1), (0, 0))


def _policy(content='{"action": "UP"}') -> lp.LLMPolicy:
    p = lp.LLMPolicy.__new__(lp.LLMPolicy)
    p.config = None
    p.client = types.SimpleNamespace(chat=lambda msgs: {"content": content}, total_tokens=0)
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
    return p


class NoopDetectorTest(unittest.TestCase):
    def test_akcja_bez_zmiany_planszy_jest_liczona(self) -> None:
        p = _policy()
        p.choose_action(_frame(G_A))          # wykonuje ACTION1 na G_A
        p.choose_action(_frame(G_A))          # plansza ta sama -> no-op
        self.assertEqual(p._noop_recent, [("ACTION1", False)])

    def test_zmiana_planszy_nie_jest_no_opem(self) -> None:
        p = _policy()
        p.choose_action(_frame(G_A))
        p.choose_action(_frame(G_B))          # plansza się zmieniła
        self.assertEqual(p._noop_recent, [("ACTION1", True)])

    def test_akcje_z_kolejki_tez_sa_liczone(self) -> None:
        p = _policy(content='{"action": "UP"}\n{"action": "DOWN"}')
        p.choose_action(_frame(G_A))          # UP wykonywany, DOWN do kolejki
        p.choose_action(_frame(G_A))          # DOWN z kolejki, plansza bez zmian
        p.choose_action(_frame(G_A))          # atrybucja DOWN nastepuje teraz
        self.assertEqual([n for n, _ in p._noop_recent], ["ACTION1", "ACTION2"])

    def test_okno_maks_dziesiec_wpisow(self) -> None:
        p = _policy()
        for i in range(15):
            p.choose_action(_frame(G_A if i % 2 else G_B))
        self.assertLessEqual(len(p._noop_recent), 10)

    def test_iniekcja_do_tury_przy_trzech_noopach(self) -> None:
        p = _policy()
        for _ in range(7):
            p.choose_action(_frame(G_A))      # wszystkie no-op
        turn = p._build_user_turn(_frame(G_A))
        self.assertIn("No-op check", turn)
        self.assertIn("did NOT change the board", turn)

    def test_cisza_przy_malo_prob_lub_malo_noopow(self) -> None:
        p = _policy()
        for _ in range(3):
            p.choose_action(_frame(G_A))
        self.assertNotIn("No-op check", p._build_user_turn(_frame(G_A)))
        p2 = _policy()
        p2._noop_recent = [("ACTION1", True)] * 6
        self.assertNotIn("No-op check", p2._build_user_turn(_frame(G_A)))


class LessonsBetweenGamesTest(unittest.TestCase):
    def test_reset_game_zbiera_notatki_do_lekcji(self) -> None:
        p = _policy()
        p._game_notes = ["GOAL: cover all dotted targets",
                         "✗ pushing boxes does nothing"]
        p.reset_game()
        self.assertEqual(p._game_notes, [])
        self.assertEqual(p._run_lessons, ["GOAL: cover all dotted targets",
                                          "✗ pushing boxes does nothing"])

    def test_lekcje_przezywaja_reset_i_sa_deduplikowane(self) -> None:
        p = _policy()
        p._game_notes = ["GOAL: X"]
        p.reset_game()
        p._game_notes = ["GOAL: X", "GOAL: Y"]   # duplikat + nowa
        p.reset_game()
        self.assertEqual(p._run_lessons, ["GOAL: X", "GOAL: Y"])

    def test_limit_osmiu_lekcji_najnowsze_wygrewaja(self) -> None:
        p = _policy()
        for i in range(12):
            p._game_notes = [f"lesson {i}"]
            p.reset_game()
        self.assertEqual(len(p._run_lessons), 8)
        self.assertEqual(p._run_lessons[-1], "lesson 11")
        self.assertEqual(p._run_lessons[0], "lesson 4")

    def test_lekcje_w_pierwszej_turze_nowej_gry(self) -> None:
        p = _policy()
        p._game_notes = ["GOAL: X"]
        p.reset_game()
        turn = p._build_user_turn(_frame(G_A))
        self.assertIn("Lessons from earlier games in this run", turn)
        self.assertIn("GOAL: X", turn)

    def test_lekcje_nie_powtarzaja_sie_pozniej_w_grze(self) -> None:
        p = _policy()
        p._run_lessons = ["GOAL: X"]
        p.choose_action(_frame(G_A))           # pierwsza akcja gry
        turn = p._build_user_turn(_frame(G_A))
        self.assertNotIn("Lessons from earlier games", turn)

    def test_prompt_tlumaczy_lekcje(self) -> None:
        self.assertIn("LESSONS BETWEEN GAMES", lp.SYSTEM_PROMPT)


if __name__ == "__main__":
    unittest.main()
