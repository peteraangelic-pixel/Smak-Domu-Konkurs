"""Testy parsowania odpowiedzi LLM (CPU, bez LM Studio, bez sieci).

Katalog `llm-agent` ma myślnik, więc pakiet ładujemy pod aliasem `llmagent`.
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

AVAILABLE = ["ACTION1", "ACTION2", "ACTION3", "ACTION4", "ACTION6"]


def _frame() -> lp.FrameInfo:
    return lp.FrameInfo(
        grid=((0, 0), (0, 0)),
        step=0,
        level=0,
        state_name="PLAYING",
        levels_completed=0,
        available_actions=list(AVAILABLE),
    )


class ParseResponseTest(unittest.TestCase):
    def setUp(self) -> None:
        # Nie wywołujemy __init__ (nie tworzy klienta LLM).
        self.policy = lp.LLMPolicy.__new__(lp.LLMPolicy)
        self.frame = _frame()

    def parse(self, text: str) -> list[dict]:
        return self.policy._parse_response(text, self.frame)

    def test_prosty_json_w_bloku_kodu(self) -> None:
        actions = self.parse('```json\n{"action": "UP"}\n```')
        self.assertEqual([a["name"] for a in actions], ["ACTION1"])

    def test_zagniezdzony_reasoning_nie_gubi_akcji(self) -> None:
        # Stary regex zatrzymywał się na pierwszym "}" i odrzucał tę akcję.
        text = '```json\n{"action": "UP", "reasoning": {"why": "exit is up"}}\n```'
        actions = self.parse(text)
        self.assertEqual([a["name"] for a in actions], ["ACTION1"])
        self.assertIn("exit is up", str(actions[0]["reasoning"]))

    def test_kilka_akcji_batch(self) -> None:
        text = (
            '{"action": "UP"}\n'
            'then {"action": "LEFT", "reasoning": {"a": {"b": 1}}}\n'
            '{"action": "DOWN"}'
        )
        names = [a["name"] for a in self.parse(text)]
        self.assertEqual(names, ["ACTION1", "ACTION3", "ACTION2"])

    def test_bez_json_fallback_tekstowy(self) -> None:
        actions = self.parse("I think we should go RIGHT now.")
        self.assertEqual([a["name"] for a in actions], ["ACTION4"])

    def test_niedozwolona_akcja_jest_pomijana(self) -> None:
        self.assertEqual(self.parse('{"action": "TELEPORT"}'), [])

    def test_uszkodzony_json_nie_wywala_parsera(self) -> None:
        # Brak słów kierunkowych w tekście: fallback tekstowy nic nie znajdzie.
        self.assertEqual(self.parse('{"action": "XYZ", "reasoning": {'), [])


class ExtractActionObjectsTest(unittest.TestCase):
    def test_pomija_obiekty_bez_action(self) -> None:
        objs = lp._extract_action_objects('{"x": 1} {"action": "UP"}')
        self.assertEqual(objs, [{"action": "UP"}])

    def test_zagniezdzone_klamry(self) -> None:
        objs = lp._extract_action_objects('{"action": "UP", "r": {"k": {"n": 2}}}')
        self.assertEqual(len(objs), 1)
        self.assertEqual(objs[0]["r"]["k"]["n"], 2)


if __name__ == "__main__":
    unittest.main()
