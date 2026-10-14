"""Testy atrapy save-fazy notebooka (bez pandas, bez sieci, bez Kaggle).

Cel: atrapa zapisywana przez notebook w fazie „save” nie może przejść
walidacji zgłoszenia (check_submission.py).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_notebook  # noqa: E402
from check_submission import PLACEHOLDER_GAME_ID, validate_rows  # noqa: E402


class SaveRunnerPlaceholderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = build_notebook._competition_runner()

    def test_runner_zapisuje_atrapę_tylko_poza_rerunem(self) -> None:
        # Gałąź atrapy musi być w else, czyli dla KAGGLE_IS_COMPETITION_RERUN != true.
        self.assertIn("if is_competition_rerun:", self.runner)
        self.assertIn("else:", self.runner)
        self.assertIn("placeholder_0", self.runner)

    def test_atrapa_z_notebooka_jest_odrzucana_przez_walidator(self) -> None:
        # Ta sama struktura co w notebooku: row_id, game_id, end_of_game, score.
        self.assertIn(f'"{PLACEHOLDER_GAME_ID}"', self.runner)
        atrapa = [
            {
                "row_id": "placeholder_0",
                "game_id": PLACEHOLDER_GAME_ID,
                "end_of_game": True,
                "score": 0.0,
            }
        ]
        problems = validate_rows(atrapa)
        self.assertTrue(problems, "atrapa notebooka nie może przejść walidacji")


if __name__ == "__main__":
    unittest.main()
