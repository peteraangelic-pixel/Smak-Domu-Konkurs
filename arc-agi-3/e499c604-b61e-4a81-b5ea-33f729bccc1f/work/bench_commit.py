"""Measure commit() overhead inside the real sandbox with a realistic history."""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.getcwd(), "ARC3-Inference"))
os.environ["ARC3_PLAN_COMMIT"] = "1"

from inference.agent.python_tool_sandbox import run_sandboxed_python  # noqa: E402

ROWS, COLS = 64, 64


def frame_ascii(row):
    lines = []
    for r in range(ROWS):
        line = ["W"] * COLS
        line[1] = "R"
        lines.append("".join(line))
    lines[row] = lines[row][:1] + "R" + lines[row][2:]
    return "\n".join(lines)


def frame_payload(row, step, level=1):
    return {
        "ascii": frame_ascii(row),
        "step": step,
        "level": level,
        "shape": [ROWS, COLS],
        "grid": [[0] * COLS for _ in range(ROWS)],
    }


def state(row, step, history_entries):
    history = [
        {"action": "UP", "frame": frame_payload(row, i + 1), "result": {}}
        for i in range(history_entries)
    ]
    return {
        "current_frame": frame_payload(row, step),
        "history": history,
        "valid_actions": ["UP", "DOWN"],
        "last_action_result": {},
    }


def run(history_entries, actions):
    row = {"value": 32}
    step = {"value": history_entries}

    def handler(action_list, stale_after=None):
        result = None
        for action in action_list:
            step["value"] += 1
            if str(action.get("action", "")).upper() == "UP":
                row["value"] = max(0, row["value"] - 1)
            else:
                row["value"] = min(ROWS - 1, row["value"] + 1)
            result = {
                "executed": True,
                "level": 1,
                "step": step["value"],
                "board_changed": True,
                "level_completed": False,
                "game_over": False,
                "run_complete": False,
                "done": False,
            }
        return {
            "action_result": result or {"executed": False},
            "state": state(row["value"], step["value"], history_entries),
        }

    code = f"result = commit({['UP'] * actions!r})\n"
    started = time.monotonic()
    out = run_sandboxed_python(
        code=code,
        timeout_seconds=120,
        initial_state=state(row["value"], step["value"], history_entries),
        action_handler=handler,
    )
    elapsed = time.monotonic() - started
    assert not out.get("error"), out.get("error")
    return elapsed, out["result"]["executed"]


if __name__ == "__main__":
    for entries in (0, 50, 200, 400):
        elapsed, executed = run(entries, 20)
        print(
            f"history={entries:4d}  actions={executed:2d}  wall={elapsed:6.2f}s"
            f"  per_action={elapsed / max(1, executed) * 1000:6.1f}ms"
        )
