"""Compare paired ARC benchmark.json runs without pooling unlike game rosters."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


def load_run(path: Path):
    data = path.read_bytes()
    rows = json.loads(data)["game_runs"]
    occurrences = Counter()
    games = {}
    for row in rows:
        game_id = row["game_id"]
        occurrence = occurrences[game_id]
        occurrences[game_id] += 1
        key = (game_id, occurrence)
        completed = int(row.get("levels_completed", 0))
        baselines = row.get("base_actions_per_level")
        if not baselines:
            raise ValueError(f"{key}: missing baselines, cannot verify scoring")
        actions = row.get("actions_per_level", [])
        if completed > len(baselines) or completed > len(actions) or completed < 0:
            raise ValueError(f"{key}: inconsistent completion count")
        if any(a <= 0 for a in actions[:completed]):
            raise ValueError(f"{key}: completed level has no positive action count")
        total_weight = sum(range(1, len(baselines) + 1))
        efficiency = sum(
            (index + 1) * min(115.0, 100 * (baselines[index] / actions[index]) ** 2)
            for index in range(completed)
        ) / total_weight
        coverage = 100 * sum(range(1, completed + 1)) / total_weight
        score = min(efficiency, coverage)
        stored = row.get("final_score")
        if stored is not None and abs(score - stored) > 0.001:
            raise ValueError(f"{key}: computed score {score} differs from stored {stored}")
        games[key] = {"baselines": baselines, "completed": completed, "score": score}
    if not games:
        raise ValueError("Empty benchmark")
    return games, hashlib.sha256(data).hexdigest()


def compare(control: Path, candidate: Path):
    left, left_hash = load_run(control)
    right, right_hash = load_run(candidate)
    if left.keys() != right.keys():
        raise ValueError("Game rosters differ. Run both variants on the same pinned public corpus.")
    pairs = []
    for key in left:
        a, b = left[key], right[key]
        if a["baselines"] != b["baselines"]:
            raise ValueError(f"{key}: baseline/level definitions differ")
        pairs.append({
            "game_id": key[0], "occurrence": key[1],
            "control_completed": a["completed"], "candidate_completed": b["completed"],
            "delta_completed": b["completed"] - a["completed"],
            "delta_score": b["score"] - a["score"],
        })
    return {
        "control_sha256": left_hash, "candidate_sha256": right_hash,
        "same_file": left_hash == right_hash, "games": len(pairs),
        "control_mean": sum(r["score"] for r in left.values()) / len(left),
        "candidate_mean": sum(r["score"] for r in right.values()) / len(right),
        "delta_completed": sum(r["delta_completed"] for r in pairs),
        "pairs": pairs,
        "qualification": "Game IDs and baselines match. Model, seed, runtime and game-source hashes must also match in the experiment manifest.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("control", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    print(json.dumps(compare(args.control, args.candidate), indent=2))
