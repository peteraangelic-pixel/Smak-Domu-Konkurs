"""Testy v6.9: goal-class detection (counter-picking) + VALUE_GATE + drabinka.

CPU, bez LM Studio i bez sieci. Katalog `llm-agent` ma myślnik — alias `llmagent`.
"""

from __future__ import annotations

import json
import sys
import types
import unittest
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parents[1]
_pkg = types.ModuleType("llmagent")
_pkg.__path__ = [str(PKG_DIR)]  # type: ignore[attr-defined]
sys.modules.setdefault("llmagent", _pkg)

from llmagent import knobs as kn  # noqa: E402
from llmagent import llm_policy as lp  # noqa: E402
from llmagent.goal_classifier import (  # noqa: E402
    GOAL_CLASSES,
    detect_goal_class,
    STRATEGY_HINTS,
)


def _grid(size: int = 20, marks: list[tuple[int, int, int]] | None = None):
    g = [[0] * size for _ in range(size)]
    for r, c, v in marks or []:
        g[r][c] = v
    return g


def _cover_grid() -> list[list[int]]:
    """12 rozproszonych izolowanych znaczników → COVER."""
    marks = [(2, 3), (3, 6), (5, 9), (7, 2), (8, 13), (10, 5),
             (11, 15), (13, 8), (14, 11), (15, 16), (16, 4), (17, 12)]
    return _grid(marks=[(r, c, 3) for r, c in marks])


def _copy_grid() -> list[list[int]]:
    """Wzorzec 10×10 (≥4 niezerowe) + kopia w wierszu 10 → COPY."""
    g = [[0] * 20 for _ in range(20)]
    for r in range(10):
        for c in range(10):
            v = 1 if (r + c) % 4 == 0 else (2 if (r * c) % 5 == 0 else 0)
            g[r][c] = v
            g[10 + r][c] = v
    return g


def _frame(grid, levels: int = 0) -> lp.FrameInfo:
    return lp.FrameInfo(
        grid=tuple(tuple(row) for row in grid),
        step=1,
        level=0,
        state_name="PLAYING",
        levels_completed=levels,
        available_actions=["ACTION1", "ACTION2", "ACTION3"],
    )


class Recorder:
    """Fałszywy klient: rejestruje wywołania chat."""

    def __init__(self):
        self.total_tokens = 42
        self.calls: list[tuple[list[dict], float | None]] = []

    def chat(self, messages, temperature=None):
        self.calls.append((messages, temperature))
        return {"content": '{"action": "UP"}'}


def _policy(client: Recorder | None = None) -> lp.LLMPolicy:
    p = lp.LLMPolicy.__new__(lp.LLMPolicy)
    p.config = None
    p.client = client or Recorder()
    p.tracker = lp.StateTracker()
    p._messages = []
    p._action_queue = []
    p._actions_since_last_llm = 0
    p._max_actions_per_plan = 15
    p._last_level = 0
    p._game_notes = []
    p._actions_on_level = 0
    p._last_audit_at = 0
    p._probe_level = 0  # pomijamy skryptowany probe opening
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
    p._goal_class = None
    return p


class ClassifierTest(unittest.TestCase):
    def test_pusta_plansza_unknown(self) -> None:
        self.assertEqual(detect_goal_class([[0] * 20 for _ in range(20)]), "UNKNOWN")

    def test_cover(self) -> None:
        self.assertEqual(detect_goal_class(_cover_grid()), "COVER")

    def test_copy(self) -> None:
        self.assertEqual(detect_goal_class(_copy_grid()), "COPY")

    def test_reduce(self) -> None:
        marks = [(r, c, 5) for r, c in
                 [(2, 2), (2, 8), (4, 5), (6, 12), (8, 3), (9, 16), (11, 7), (12, 14),
                  (14, 2), (15, 9), (16, 17), (17, 5), (3, 15), (5, 17), (7, 8),
                  (10, 10), (13, 4), (1, 11), (18, 13), (4, 10), (6, 1), (9, 6),
                  (12, 18), (15, 14), (17, 9), (1, 4), (8, 18), (11, 1), (14, 12), (16, 7)]]
        self.assertEqual(detect_goal_class(_grid(marks=marks)), "REDUCE")

    def test_burzliwe_rzadkie_plansze_nigdy_copy(self) -> None:
        """BUGFIX #3: zero-vs-zero nie może udawać wzorca (ich błąd → COPY)."""
        import random
        rng = random.Random(42)
        for _ in range(50):
            marks = [(rng.randrange(20), rng.randrange(20), rng.choice([1, 2, 3]))
                     for _ in range(rng.randint(3, 40))]
            self.assertNotEqual(detect_goal_class(_grid(marks=marks)), "COPY")

    def test_wynik_z_dozwolonego_zbioru(self) -> None:
        self.assertIn(detect_goal_class(_cover_grid()), GOAL_CLASSES)

    def test_hints_pokrywaja_klasy(self) -> None:
        for cls in GOAL_CLASSES:
            if cls not in ("UNKNOWN", "LOCAL_CONSTRAINTS"):
                self.assertIn(cls, STRATEGY_HINTS)
        self.assertIn("LOCAL_CONSTRAINTS", STRATEGY_HINTS)


class GoalClassInjectionTest(unittest.TestCase):
    def tearDown(self) -> None:
        kn.reset_to_defaults()

    def test_detekcja_i_wstrzykniecie_do_system_prompta(self) -> None:
        rec = Recorder()
        p = _policy(rec)
        p.choose_action(_frame(_cover_grid()))
        self.assertEqual(p._goal_class, "COVER")
        self.assertEqual(rec.calls[0][0][0]["role"], "system")
        sys_text = rec.calls[0][0][0]["content"]
        self.assertIn("RUNTIME GOAL-CLASS DETECTION", sys_text)
        self.assertIn("COVER", sys_text)
        self.assertIn(STRATEGY_HINTS["COVER"][:20], sys_text)

    def test_unknown_czeka_na_pozniejsza_plansze(self) -> None:
        p = _policy()
        p.choose_action(_frame(_grid()))          # pusta → UNKNOWN, bez decyzji
        self.assertIsNone(p._goal_class)
        p.choose_action(_frame(_cover_grid()))    # kolejna klatka → COVER
        self.assertEqual(p._goal_class, "COVER")

    def test_knob_off_prompt_identyczny_z_v68(self) -> None:
        kn.apply_overrides(json.dumps({"GOAL_CLASS": 0}))
        rec = Recorder()
        p = _policy(rec)
        p.choose_action(_frame(_cover_grid()))
        self.assertIsNone(getattr(p, "_goal_class", None))
        self.assertEqual(rec.calls[0][0][0]["content"], lp.SYSTEM_PROMPT)

    def test_reset_game_czysci_klase(self) -> None:
        p = _policy()
        p._goal_class = "COVER"
        p.reset_game()
        self.assertIsNone(p._goal_class)

    def test_audit_drabinka_z_klasa(self) -> None:
        p = _policy()
        p._actions_on_level = 50   # >= AUDIT_ACTIONS(40) i rearm 15
        p._audits_on_level = 1     # → audits = 2 >= AUDIT_ESCALATE_FROM
        p._goal_class = "COVER"
        audit = p._stuck_audit(_frame(_cover_grid()))
        self.assertIsNotNone(audit)
        assert audit is not None
        self.assertIn("STRATEGY RESET", audit)
        self.assertIn("Goal-class ladder", audit)
        self.assertIn("DIFFERENT", audit)
        self.assertIn("COVER", audit)

    def test_audit_drabinka_bez_klasy(self) -> None:
        p = _policy()
        p._actions_on_level = 50
        p._audits_on_level = 1
        audit = p._stuck_audit(_frame(_cover_grid()))
        assert audit is not None
        self.assertIn("name the class", audit)


class ValueGateTest(unittest.TestCase):
    def tearDown(self) -> None:
        kn.reset_to_defaults()

    def test_domyslnie_off(self) -> None:
        rec = Recorder()
        p = _policy(rec)
        p.choose_action(_frame(_cover_grid()))
        user_text = rec.calls[0][0][1]["content"]
        self.assertNotIn("Deterministic value estimate", user_text)

    def test_on_linia_w_prompcie(self) -> None:
        kn.apply_overrides(json.dumps({"VALUE_GATE": 1}))
        rec = Recorder()
        p = _policy(rec)
        p.choose_action(_frame(_cover_grid()))
        user_text = rec.calls[0][0][1]["content"]
        self.assertIn("Deterministic value estimate", user_text)

    def test_deterministycznosc(self) -> None:
        kn.apply_overrides(json.dumps({"VALUE_GATE": 1}))
        p = _policy()
        f = _frame(_cover_grid())
        v1 = p._deterministic_value(f)
        v2 = p._deterministic_value(f)
        self.assertEqual(f"{v1:.4f}", f"{v2:.4f}")
        self.assertGreaterEqual(v1, 0.0)
        self.assertLessEqual(v1, 1.0)

    def test_petla_obniza_wartosc(self) -> None:
        kn.apply_overrides(json.dumps({"VALUE_GATE": 1}))
        p = _policy()
        f = _frame(_cover_grid())
        v_clean = p._deterministic_value(f)
        for name in ("ACTION1", "ACTION1", "ACTION1", "ACTION1"):
            p.tracker.record(p.tracker.state_signatures[0] if p.tracker.state_signatures else "s", name)
        p.tracker.record("same", "ACTION1")
        p.tracker.record("same", "ACTION1")
        v_looped = p._deterministic_value(f)
        self.assertLess(v_looped, v_clean)


if __name__ == "__main__":
    unittest.main()
