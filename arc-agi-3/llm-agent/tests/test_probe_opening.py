"""Testy v6.1: scripted probe opening (tape opening) + self-test w builderach.

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


def _frame(levels: int = 0, actions=None) -> lp.FrameInfo:
    return lp.FrameInfo(
        grid=((0, 0), (0, 0)),
        step=0,
        level=0,
        state_name="PLAYING",
        levels_completed=levels,
        available_actions=list(actions or ["ACTION1", "ACTION2", "ACTION3",
                                           "ACTION4", "ACTION5", "ACTION6"]),
    )


def _policy_stub(client_content: str = '{"action": "UP"}') -> lp.LLMPolicy:
    p = lp.LLMPolicy.__new__(lp.LLMPolicy)
    p.config = None
    p.client = types.SimpleNamespace(chat=lambda msgs: {"content": client_content}, total_tokens=0)
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
    return p


class ProbeActionsTest(unittest.TestCase):
    def test_tylko_kierunki_dostepne(self) -> None:
        probes = lp.LLMPolicy._probe_actions(_frame())
        self.assertEqual([p["name"] for p in probes],
                         ["ACTION1", "ACTION2", "ACTION3", "ACTION4"])

    def test_nigdy_confirm_klikani_reset(self) -> None:
        probes = lp.LLMPolicy._probe_actions(_frame())
        names = {p["name"] for p in probes}
        self.assertNotIn("ACTION6", names)
        self.assertNotIn("ACTION5", names)
        self.assertNotIn("RESET", names)

    def test_gra_bez_kierunkow_pusta_lista(self) -> None:
        probes = lp.LLMPolicy._probe_actions(_frame(actions=["ACTION5", "ACTION6"]))
        self.assertEqual(probes, [])


class ProbeOpeningIntegrationTest(unittest.TestCase):
    def test_start_gry_probe_przed_llm(self) -> None:
        p = _policy_stub()
        calls = []
        orig_chat = p.client.chat

        def spy(msgs):
            calls.append(1)
            return orig_chat(msgs)

        p.client.chat = spy
        first = p.choose_action(_frame())
        self.assertEqual(first["name"], "ACTION1")
        self.assertEqual(first["reasoning"].get("probe"), True)
        self.assertEqual(calls, [1] * 0)  # LLM jeszcze nie wołany
        self.assertEqual(len(p._action_queue), 3)

    def test_po_probach_llm_przejmuje(self) -> None:
        p = _policy_stub()
        for _ in range(4):
            p.choose_action(_frame())
        nxt = p.choose_action(_frame())
        self.assertIsNone(nxt["reasoning"].get("probe"))
        self.assertEqual(nxt["name"], "ACTION1")  # z odpowiedzi stuba

    def test_nowy_poziom_probe_ponownie(self) -> None:
        p = _policy_stub()
        p.choose_action(_frame(levels=0))
        # Ta sama tura bez zmiany poziomu: brak nowych prob (kolejka sie kurczy).
        p._probe_level = 0
        before = len(p._action_queue)
        p.choose_action(_frame(levels=0))
        self.assertEqual(len(p._action_queue), before - 1)
        # Zmiana poziomu: kolejka czyszczona i zapelniona probami od nowa.
        first = p.choose_action(_frame(levels=1))
        self.assertEqual(first["name"], "ACTION1")
        self.assertEqual(first["reasoning"].get("probe"), True)
        self.assertEqual([a["name"] for a in p._action_queue],
                         ["ACTION2", "ACTION3", "ACTION4"])

    def test_reset_game_czysci_probe_level(self) -> None:
        p = _policy_stub()
        p.choose_action(_frame())
        self.assertEqual(p._probe_level, 0)
        p.reset_game()
        self.assertIsNone(p._probe_level)


class BuilderSelfTestTest(unittest.TestCase):
    def test_h100_builder_ma_selftest(self) -> None:
        src = (Path(__file__).resolve().parents[1] / "build_notebook.py").read_text()
        for marker in ("ARC3_AGENT_SELFTEST_OK", "FIELD GUIDE",
                       "_probe_actions", "stale payload"):
            self.assertIn(marker, src)

    def test_t4_builder_ma_selftest_i_field_guide(self) -> None:
        src = (Path(__file__).resolve().parents[1] / "build_notebook_t4.py").read_text()
        for marker in ("ARC3_AGENT_SELFTEST_OK", "FIELD GUIDE",
                       "stale payload", "Deliberate LESS"):
            self.assertIn(marker, src)


if __name__ == "__main__":
    unittest.main()
