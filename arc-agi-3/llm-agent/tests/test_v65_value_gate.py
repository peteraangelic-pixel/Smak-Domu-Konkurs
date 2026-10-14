"""Testy v6.5: value gate (cechy, OFF bez wag, predykcja) + eskalacja audytu + trener.

CPU, bez LM Studio i bez sieci. Katalog `llm-agent` ma myślnik — alias `llmagent`.
"""

from __future__ import annotations

import json
import sys
import tempfile
import types
import unittest
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parents[1]
_pkg = types.ModuleType("llmagent")
_pkg.__path__ = [str(PKG_DIR)]  # type: ignore[attr-defined]
sys.modules.setdefault("llmagent", _pkg)

from llmagent import llm_policy as lp  # noqa: E402
from llmagent.value_gate import FEATURES, ValueGate, extract_features  # noqa: E402


def _frame(grid=None, levels: int = 0, step: int = 0) -> lp.FrameInfo:
    return lp.FrameInfo(
        grid=grid or ((0, 0), (1, 0)),
        step=step,
        level=0,
        state_name="PLAYING",
        levels_completed=levels,
        available_actions=["ACTION1", "ACTION2", "ACTION6"],
    )


def _policy(total_tokens: int = 0) -> lp.LLMPolicy:
    p = lp.LLMPolicy.__new__(lp.LLMPolicy)
    p.config = None
    p.client = types.SimpleNamespace(chat=lambda m: {"content": '{"action": "UP"}'},
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
    p._audits_on_level = 0
    p.value_gate = None
    return p


class FeaturesTest(unittest.TestCase):
    def test_cechy_w_zakresie_i_kolejnosci(self) -> None:
        p = _policy()
        p._noop_recent = [("ACTION1", False)] * 10
        p._actions_on_level = 50
        feats = extract_features(p, _frame())
        self.assertEqual(len(feats), len(FEATURES))
        for value in feats:
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 1.0)
        # gęstość: 1 z 4 pól niezerowe
        self.assertAlmostEqual(feats[FEATURES.index("density")], 0.25)
        # noop_ratio = 1.0 przy samych no-opach
        self.assertAlmostEqual(feats[FEATURES.index("noop_ratio")], 1.0)

    def test_obiekty_z_segmentacji(self) -> None:
        p = _policy()
        feats = extract_features(p, _frame())
        self.assertGreater(feats[FEATURES.index("objects")], 0.0)


class ValueGateOffTest(unittest.TestCase):
    def test_brat_sciezki_none(self) -> None:
        self.assertIsNone(ValueGate.load(None))
        self.assertIsNone(ValueGate.load(""))
        self.assertIsNone(ValueGate.load("/nie/ma/takiego.json"))

    def test_uszkodzony_json_none(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            fh.write("{nie jest jsonem")
            path = fh.name
        self.assertIsNone(ValueGate.load(path))

    def test_policy_bez_env_ma_gate_off(self) -> None:
        p = lp.LLMPolicy.__new__(lp.LLMPolicy)  # bez __init__: getattr fallback
        self.assertIsNone(getattr(p, "value_gate", None))
        # audyt działa jak dotąd (cisza poniżej progów)
        p2 = _policy()
        p2._actions_on_level = 5
        self.assertIsNone(p2._stuck_audit(_frame()))


class ValueGateOnTest(unittest.TestCase):
    def _weights_file(self, tmp: str, value_bias: float = 0.0) -> str:
        # maleńka sieć: 12 -> 2 -> 1, deterministyczna
        W0 = [[0.1] * 12 for _ in range(2)]
        b0 = [0.0, 0.0]
        W1 = [[0.2, -0.1], [0.0, 0.3]]
        b1 = [0.0, 0.0]
        W2 = [[0.5], [-0.5]]
        b2 = [value_bias]
        path = Path(tmp) / "w.json"
        path.write_text(json.dumps({
            "features": FEATURES,
            "thresholds": {"low": 0.3, "high": 0.7},
            "weights": {"W0": W0, "b0": b0, "W1": W1, "b1": b1, "W2": W2, "b2": b2},
        }), encoding="utf-8")
        return str(path)

    def test_ladowanie_i_predykcja_deteministyczna(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gate = ValueGate.load(self._weights_file(tmp))
            assert gate is not None and gate.ok
            p = _policy()
            v1 = gate.value(p, _frame())
            v2 = gate.value(p, _frame())
            assert v1 is not None
            self.assertAlmostEqual(v1, v2)
            self.assertGreaterEqual(v1, 0.0)
            self.assertLessEqual(v1, 1.0)

    def test_audyt_strzela_gdy_gate_ocenia_nisko(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gate = ValueGate.load(self._weights_file(tmp, value_bias=-8.0))
            assert gate is not None
            p = _policy()
            p.value_gate = gate
            audit = p._stuck_audit(_frame())
            assert audit is not None
            self.assertIn("STRATEGY AUDIT", audit)
            self.assertIn("learned state-value", audit)

    def test_eskalacja_na_drugim_audycie(self) -> None:
        p = _policy()
        p._actions_on_level = 40
        first = p._stuck_audit(_frame())
        assert first is not None
        self.assertNotIn("STRATEGY RESET", first)
        p._actions_on_level = 55
        second = p._stuck_audit(_frame())
        assert second is not None
        self.assertIn("STRATEGY RESET", second)
        self.assertIn("#2", second)


class TrainerTest(unittest.TestCase):
    def test_split_per_gra(self) -> None:
        from llmagent import train_value_model as tvm
        games = ["g1"] * 4 + ["g2"] * 4 + ["g3"] * 4 + ["g4"] * 4
        tr, va = tvm.game_split(games, holdout=0.5)
        self.assertEqual(len(tr & va), 0)
        self.assertEqual(len(tr) + len(va), 4)

    def test_trening_na_syntetycznych_rozdzielnych(self) -> None:
        from llmagent import train_value_model as tvm
        rng = __import__("random").Random(5)
        xs, ys = [], []
        for i in range(40):  # gra "dobra": wysokie gęstość i kolor
            xs.append([1.0, 0.9] + [rng.random() * 0.1 for _ in range(10)])
            ys.append(1)
        for i in range(40):  # gra "zła": niskie
            xs.append([0.0, 0.1] + [rng.random() * 0.1 for _ in range(10)])
            ys.append(0)
        w = tvm.train(xs, ys, epochs=60, lr=0.2)
        acc = tvm.accuracy(xs, ys, w)
        self.assertGreater(acc, 0.9)

    def test_cli_end_to_end(self) -> None:
        import csv as _csv
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "dane.csv"
            with path.open("w", newline="") as fh:
                writer = _csv.writer(fh)
                writer.writerow(["game_id", "label", *FEATURES])
                for g, label, base in (("a", 1, 0.9), ("b", 0, 0.1)):
                    for _ in range(30):
                        row = [g, label] + [base for _ in FEATURES]
                        writer.writerow(row)
            out = Path(tmp) / "w.json"
            result = subprocess.run(
                [sys.executable, str(PKG_DIR / "train_value_model.py"), str(path),
                 "--out", str(out), "--epochs", "40", "--lr", "0.3"],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr[-400:])
            blob = json.loads(out.read_text())
            self.assertEqual(blob["features"], FEATURES)
            self.assertIn("val_acc", blob["meta"])


if __name__ == "__main__":
    unittest.main()
