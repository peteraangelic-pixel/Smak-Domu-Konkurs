"""Testy v6.8: KNOBS (rejestr, override z JSON) + CEM ewolucja.

CPU, bez LM Studio i bez sieci. Katalog `llm-agent` ma myślnik — alias `llmagent`.
"""

from __future__ import annotations

import io
import json
import sys
import contextlib
import types
import unittest
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parents[1]
_pkg = types.ModuleType("llmagent")
_pkg.__path__ = [str(PKG_DIR)]  # type: ignore[attr-defined]
sys.modules.setdefault("llmagent", _pkg)

from llmagent import knobs as kn  # noqa: E402
from llmagent import evolve_knobs as ek  # noqa: E402
from llmagent import llm_policy as lp  # noqa: E402


class KnobsRegistryTest(unittest.TestCase):
    def test_domyślne_wartości_obecne(self) -> None:
        for key in ("AUDIT_ACTIONS", "AUDIT_TOKENS", "TEMP_STUCK", "PROBE_MAX",
                    "NOOP_TRIGGER", "LESSONS_MAX", "QUEUE_MAX"):
            self.assertIn(key, kn.KNOBS)

    def test_override_częściowy_i_typy(self) -> None:
        backup = dict(kn.KNOBS)
        try:
            kn.apply_overrides(json.dumps({"AUDIT_ACTIONS": 55, "TEMP_STUCK": 0.85,
                                           "NIEZNANE": 1, "QUEUE_MAX": "złe"}))
            self.assertEqual(kn.KNOBS["AUDIT_ACTIONS"], 55)
            self.assertEqual(kn.KNOBS["TEMP_STUCK"], 0.85)
            self.assertEqual(kn.KNOBS["QUEUE_MAX"], backup["QUEUE_MAX"])  # zły typ odrzucony
        finally:
            kn.KNOBS.clear()
            kn.KNOBS.update(backup)

    def test_zły_json_nie_wywala(self) -> None:
        backup = dict(kn.KNOBS)
        try:
            buf = io.StringIO()
            with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(buf):
                kn.apply_overrides("{zły json")
                kn.apply_overrides("[1,2]")
            self.assertEqual(kn.KNOBS["AUDIT_ACTIONS"], backup["AUDIT_ACTIONS"])
        finally:
            kn.KNOBS.clear()
            kn.KNOBS.update(backup)


class KnobsWiringTest(unittest.TestCase):
    """Polityka czyta progi z KNOBS (test na eskalacji i kolejce)."""

    def _policy(self) -> lp.LLMPolicy:
        p = lp.LLMPolicy.__new__(lp.LLMPolicy)
        p.config = None
        p.client = types.SimpleNamespace(
            chat=lambda m, temperature=None: {"content": '{"action": "UP"}'},
            total_tokens=0)
        p.tracker = lp.StateTracker()
        p._messages = []
        p._action_queue = []
        p._actions_since_last_llm = 0
        p._max_actions_per_plan = int(kn.KNOBS["QUEUE_MAX"])
        p._last_level = 0
        p._game_notes = []
        p._actions_on_level = 0
        p._last_audit_at = 0
        p._probe_level = 0
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

    def _frame(self) -> lp.FrameInfo:
        return lp.FrameInfo(grid=((0, 0), (1, 0)), step=0, level=0,
                            state_name="PLAYING", levels_completed=0,
                            available_actions=["ACTION1", "ACTION6"])

    def test_ostre_zmniejszenie_progu_audytu_powoduje_wczesny_audyt(self) -> None:
        backup = dict(kn.KNOBS)
        try:
            kn.KNOBS["AUDIT_ACTIONS"] = 5
            kn.KNOBS["AUDIT_ACTIONS_REARM"] = 1
            p = self._policy()
            p._actions_on_level = 5
            audit = p._stuck_audit(self._frame())
            assert audit is not None
            self.assertIn("STRATEGY AUDIT", audit)
        finally:
            kn.KNOBS.clear()
            kn.KNOBS.update(backup)

    def test_escalate_from_1_daje_reset_w_pierwszym_audycie(self) -> None:
        backup = dict(kn.KNOBS)
        try:
            kn.KNOBS["AUDIT_ESCALATE_FROM"] = 1
            p = self._policy()
            p._actions_on_level = 40
            audit = p._stuck_audit(self._frame())
            assert audit is not None
            self.assertIn("STRATEGY RESET", audit)
        finally:
            kn.KNOBS.clear()
            kn.KNOBS.update(backup)


class CemTest(unittest.TestCase):
    def test_mutant_w_granicach(self) -> None:
        rng = __import__("random").Random(3)
        mean = {key: kn.KNOBS[key] for key in ek.EVOLVABLE}
        std = {key: (spec[1] - spec[0]) * 0.3 for key, spec in ek.EVOLVABLE.items()}
        for _ in range(50):
            child = ek.mutate(mean, std, rng)
            for key, (lo, hi) in ek.EVOLVABLE.items():
                self.assertGreaterEqual(child[key], lo)
                self.assertLessEqual(child[key], hi)

    def test_cem_znajduje_optimum_toy(self) -> None:
        best, value = ek.cem(ek.toy_fitness, generations=6, population=12,
                             seed=5, verbose=False)
        self.assertGreater(value, -1.0)  # optimum = 0.0 w (55, 0.85)
        self.assertAlmostEqual(best["AUDIT_ACTIONS"], 55, delta=6)
        self.assertAlmostEqual(best["TEMP_STUCK"], 0.85, delta=0.06)

    def test_cli_toy_end_to_end(self) -> None:
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "best.json"
            result = subprocess.run(
                [sys.executable, str(PKG_DIR / "evolve_knobs.py"),
                 "--gens", "3", "--pop", "6", "--out", str(out)],
                capture_output=True, text=True, cwd=str(PKG_DIR))
            self.assertEqual(result.returncode, 0, result.stderr[-400:])
            blob = json.loads(out.read_text())
            self.assertIn("AUDIT_ACTIONS", blob)


if __name__ == "__main__":
    unittest.main()
