"""Expectation-carrying plan execution for the analyzer Python tool.

The model commits a *plan*, not an action: a list of actions where each step may
carry what it expects the board to show afterwards. ``pc_play`` issues the steps
one at a time, verifies each expectation against the frame that actually came
back, and halts the plan at the first disagreement. A wrong world model then
costs one action and returns a diff, instead of spending the rest of the plan on
a board that no longer matches the reasoning behind it.

Stdlib-free and dependency-free: this source is embedded verbatim into the
isolated Python runner (see python_tool_sandbox.py), so it may not import
anything and may only use builtins the sandbox exposes.
"""

PLAN_TERMINAL_KEYS = ("run_complete", "game_over", "level_completed", "done")


def pc_digest(text):
    """Process-independent 64-bit FNV-1a digest of a frame's ASCII text."""
    value = 0xCBF29CE484222325
    for char in str(text or ""):
        value ^= ord(char)
        value = (value * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return "%016x" % value


def pc_cell(frame_ascii, row, col):
    """One color symbol at (row, col), or None when the coordinates miss."""
    lines = str(frame_ascii or "").split("\n")
    try:
        row = int(row)
        col = int(col)
    except (TypeError, ValueError):
        return None
    if row < 0 or col < 0 or row >= len(lines):
        return None
    line = lines[row]
    if col >= len(line):
        return None
    return line[col]


def pc_observe(frame, result=None):
    """The facts a plan step is allowed to predict."""
    payload = result if isinstance(result, dict) else {}
    frame_ascii = str(getattr(frame, "ascii", "") or "")
    level = payload.get("level")
    if level is None:
        level = getattr(frame, "level", None)
    return {
        "level": level,
        "step": getattr(frame, "step", None),
        "board_changed": bool(payload.get("board_changed")),
        "digest": pc_digest(frame_ascii),
    }


def pc_normalize_step(item):
    """Plan item -> (action dict, expectation dict).

    Accepted forms: ``"UP"``, ``{"action": "MOUSE", "row": 3, "col": 4}`` and
    either of those plus ``expect={...}``.
    """
    if isinstance(item, str):
        name = item.strip()
        if not name:
            raise ValueError("plan step is an empty action name")
        return {"action": name}, {}
    if isinstance(item, dict):
        step = dict(item)
        expect = step.pop("expect", None) or {}
        if not isinstance(expect, dict):
            raise TypeError("expect must be a dict, e.g. expect={'level': 2}")
        action = {}
        if "action" in step:
            action["action"] = str(step.get("action")).strip()
        if not action.get("action"):
            raise ValueError("plan step is missing an `action` field")
        name = action["action"].upper()
        if name == "MOUSE" and ("x" in step or "y" in step):
            raise ValueError("MOUSE takes integer row and col fields, not x/y")
        if "row" in step:
            action["row"] = step.get("row")
        if "col" in step:
            action["col"] = step.get("col")
        return action, expect
    raise TypeError("plan steps must be strings or dicts")


def pc_check(expect, observed, frame_ascii=""):
    """Every way ``observed`` fails ``expect``; empty list means it held."""
    if not expect:
        return []
    bad = []
    for key in ("level", "step", "digest"):
        if key in expect:
            want = expect.get(key)
            got = observed.get(key) if isinstance(observed, dict) else None
            if str(want) != str(got):
                bad.append({"field": key, "want": want, "got": got})
    if "board_changed" in expect:
        want = bool(expect.get("board_changed"))
        got = bool((observed or {}).get("board_changed"))
        if want != got:
            bad.append({"field": "board_changed", "want": want, "got": got})
    cells = expect.get("cells")
    if cells:
        label = [("cells", "want a {'row,col': symbol} map or [[row, col, symbol], ...]")]
        if isinstance(cells, dict):
            pairs = list(cells.items())
        elif isinstance(cells, (list, tuple)):
            pairs = list(cells)
        else:
            pairs = []
            bad.append({"field": "cells", "want": label[0][1], "got": type(cells).__name__})
        for item in pairs:
            if isinstance(item, (list, tuple)) and len(item) == 3:
                row, col, want = item
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                where, want = item
                if not isinstance(where, str) or "," not in where:
                    continue
                row, col = where.split(",", 1)
            else:
                continue
            got = pc_cell(frame_ascii, row, col)
            if str(got) != str(want):
                bad.append({"field": "cell(%s,%s)" % (str(row).strip(), str(col).strip()),
                            "want": want, "got": got})
    return bad


def pc_play(plan, action_fn, frame_fn, max_actions=40, stop_on_terminal=True,
            steps_shown=12):
    """Play ``plan`` one step at a time, checking expectations as they come back.

    ``action_fn`` takes one normalized action dict and returns the engine's
    action result; ``frame_fn`` returns the frame after it. Execution stops on
    the first failed expectation, on a terminal action result, when the plan
    ends, or at ``max_actions`` - so a runaway plan cannot decide the level on
    its own.
    """
    try:
        steps = list(plan or [])
    except TypeError:
        raise TypeError("commit(plan) expects a list of steps")
    limit = max(1, int(max_actions))
    executed = 0
    checked = 0
    trace = []
    mismatch = None
    terminal = None
    stop_reason = "complete"
    level = None
    board_changed = False
    digest = None

    for index, item in enumerate(steps, start=1):
        if executed >= limit:
            stop_reason = "max_actions"
            break
        if len(steps) > limit:
            steps = steps[:limit]
        action, expect = pc_normalize_step(item)
        result = action_fn(action)
        executed += 1
        try:
            frame = frame_fn()
        except Exception:  # noqa: BLE001 - a stale frame must not lose the step
            frame = None
        observed = pc_observe(frame, result)
        level = observed["level"]
        board_changed = observed["board_changed"]
        digest = observed["digest"]
        if len(trace) < steps_shown:
            trace.append({
                "i": index,
                "action": str(action.get("action", "")),
                "level": level,
                "changed": board_changed,
                "digest": digest[:8],
            })
        if expect:
            checked += 1
            failed = pc_check(expect, observed, str(getattr(frame, "ascii", "") or ""))
            if failed:
                mismatch = {"step": index, "action": action, "failed": failed[:6],
                            "level": level, "digest": digest[:8]}
                stop_reason = "mismatch"
                break
        if stop_on_terminal and isinstance(result, dict):
            for key in PLAN_TERMINAL_KEYS:
                if result.get(key):
                    terminal = {"reason": key, "step": index, "level": level}
                    stop_reason = key
                    break
            if terminal is not None:
                break

    report = {
        "executed": executed,
        "requested": len(steps),
        "stop_reason": stop_reason,
        "level": level,
        "board_changed": board_changed,
        "digest": digest[:8] if isinstance(digest, str) else digest,
        "expectations_checked": checked,
        "steps": trace,
    }
    if len(steps) > len(trace) or executed > len(trace):
        report["steps_omitted"] = max(0, executed - len(trace))
    if mismatch is not None:
        report["mismatch"] = mismatch
        report["advice"] = ("the model of this level is wrong at this step: read the "
                            "failed fields, fix the rule, and re-commit")
    if terminal is not None:
        report["terminal"] = terminal
    return report
