"""Testy transcript_stats: parsowanie, zgodnosc Pool vs sekwencyjnie, benchmark.

CPU, bez sieci. Uzywa multiprocessing (fork), dlatego worker jest na poziomie modulu.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import transcript_stats as ts  # noqa: E402


class ParseTranscriptTest(unittest.TestCase):
    def test_kroki_akcje_myslenie(self) -> None:
        text = (
            "--- analysis_step=1 | action=1 | 09:00:01 | tool-agent ---\n"
            "Planuje droge w lewo, sporo rozwazan tutaj.\n"
            "--- analysis_step=2 | action=3 | 09:00:05 | tool-agent ---\n"
            "Krotko.\n"
            "--- analysis_step=3 | action=RESET | 09:00:09 | tool-agent ---\n"
            "Koniec.\n"
        )
        stats = ts.parse_transcript(text)
        self.assertEqual(stats["steps"], 3)
        self.assertEqual(stats["max_step_no"], 3)
        self.assertEqual(stats["actions"], {"1": 1, "3": 1, "RESET": 1})
        self.assertEqual(stats["total_actions"], 3)
        self.assertGreater(stats["think_chars"], 0)
        self.assertEqual(stats["chars_per_step"], round(stats["think_chars"] / 3))

    def test_pusty_transkrypt(self) -> None:
        stats = ts.parse_transcript("")
        self.assertEqual(stats["steps"], 0)
        self.assertEqual(stats["chars_per_step"], 0)


class ParseEventsTest(unittest.TestCase):
    def test_plansze_i_powtorzenia(self) -> None:
        b1 = {"board": [[0, 1], [1, 0]]}
        b2 = {"board": [[1, 0], [0, 1]]}
        text = "\n".join(
            [
                '{"board": [[0, 1], [1, 0]]}',
                '{"board": [[0, 1], [1, 0]]}',
                '{"board": [[1, 0], [0, 1]]}',
                "not json at all",
            ]
        )
        stats = ts.parse_events(text)
        self.assertEqual(stats["boards"], 3)
        self.assertEqual(stats["unique_boards"], 2)
        self.assertEqual(stats["max_consecutive_repeat"], 1)
        self.assertEqual(stats["diversity"], round(2 / 3, 3))


class PoolVsSequentialTest(unittest.TestCase):
    def test_pool_zwraca_identycznie_jak_sekwencyjnie(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for i in range(6):
                p = Path(tmp) / f"t{i}.txt"
                p.write_text(ts._synth_transcript(i, steps=40), encoding="utf-8")
                paths.append(p)
            seq = ts.analyze_paths(paths, workers=1)
            par = ts.analyze_paths(paths, workers=2)
            self.assertEqual(seq, par)
            self.assertEqual(len(par), 6)


class BenchmarkSmokeTest(unittest.TestCase):
    def test_benchmark_dziala_i_wyniki_identyczne(self) -> None:
        out = ts.benchmark(n_files=4)
        self.assertIn("wyniki identyczne", out)


if __name__ == "__main__":
    unittest.main()
