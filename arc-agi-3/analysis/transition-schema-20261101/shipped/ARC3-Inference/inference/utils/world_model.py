"""Executable world-model helpers for the analyzer Python tool.

The model writes three ordinary (retained) functions:
    model_state(frame)          -> compact description of the board (dict/tuple/list/set/...)
    model_step(state, action)   -> predicted next state, or None if the action is impossible
    model_goal(state)           -> True when the level is believed to be won (optional)

`wm_check` replays model_step(model_state(before), action) against recorded
transitions and reports where the model is wrong; `wm_plan` searches the model.

Stdlib-only and free of package imports: this source is also embedded verbatim
into the isolated Python runner (see python_tool_sandbox.py).
"""
import heapq
import re
import time
from collections import deque

WM_STATE_FN = "model_state"
WM_STEP_FN = "model_step"
WM_GOAL_FN = "model_goal"

_WM_MOUSE_RE = re.compile(
    r"^\s*MOUSE\s*\(\s*row\s*=\s*(-?\d+)\s*,\s*col\s*=\s*(-?\d+)\s*\)\s*$", re.I)
_WM_SKIP_ACTIONS = {"RESET"}


def wm_parse_action(display):
    """History action text -> the form the model passes to action():
    'UP' stays 'UP'; 'MOUSE(row=3, col=5)' -> {'action': 'MOUSE', 'row': 3, 'col': 5}."""
    if isinstance(display, dict):
        return dict(display)
    text = str(display or "").strip()
    match = _WM_MOUSE_RE.match(text)
    if match:
        return {"action": "MOUSE", "row": int(match.group(1)), "col": int(match.group(2))}
    return text


def wm_action_name(action):
    if isinstance(action, dict):
        return str(action.get("action", "")).upper()
    return str(action or "").strip().upper()


def wm_freeze(value):
    """Hashable, order-insensitive-for-sets canonical form of a state."""
    if isinstance(value, dict):
        items = [(wm_freeze(k), wm_freeze(v)) for k, v in value.items()]
        try:
            items.sort()
        except TypeError:
            items.sort(key=repr)
        return ("__dict__", tuple(items))
    if isinstance(value, (list, tuple)):
        return tuple(wm_freeze(v) for v in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(wm_freeze(v) for v in value)
    try:
        hash(value)
        return value
    except TypeError:
        return repr(value)


def wm_short(value, limit=120):
    text = repr(value)
    return text if len(text) <= limit else text[: limit - 3] + "..."


def wm_state_diff(predicted, actual, limit=6):
    """Compact description of how a predicted state differs from the observed one."""
    if isinstance(predicted, dict) and isinstance(actual, dict):
        out = {}
        for key in list(predicted) + [k for k in actual if k not in predicted]:
            if key not in actual:
                out[str(key)] = {"predicted": wm_short(predicted[key], 80), "actual": "<missing>"}
            elif key not in predicted:
                out[str(key)] = {"predicted": "<missing>", "actual": wm_short(actual[key], 80)}
            elif wm_freeze(predicted[key]) != wm_freeze(actual[key]):
                sub = wm_state_diff(predicted[key], actual[key], limit=3)
                out[str(key)] = sub
            if len(out) >= limit:
                out["..."] = "more fields differ"
                break
        return out
    if isinstance(predicted, (set, frozenset)) and isinstance(actual, (set, frozenset)):
        fp = {wm_freeze(v): v for v in predicted}
        fa = {wm_freeze(v): v for v in actual}
        return {
            "only_predicted": wm_short(sorted((fp[k] for k in fp.keys() - fa.keys()), key=repr)[:limit], 100),
            "only_actual": wm_short(sorted((fa[k] for k in fa.keys() - fp.keys()), key=repr)[:limit], 100),
        }
    if (isinstance(predicted, (list, tuple)) and isinstance(actual, (list, tuple))
            and len(predicted) == len(actual) and len(predicted) > 1):
        out = {}
        for index, (p, a) in enumerate(zip(predicted, actual)):
            if wm_freeze(p) != wm_freeze(a):
                out["[%d]" % index] = {"predicted": wm_short(p, 80), "actual": wm_short(a, 80)}
                if len(out) >= limit:
                    out["..."] = "more items differ"
                    break
        return out
    return {"predicted": wm_short(predicted), "actual": wm_short(actual)}


def _wm_exc(exc):
    return "%s: %s" % (exc.__class__.__name__, str(exc)[:160])


def wm_check(transitions, state_fn, step_fn, goal_fn=None, *, level=None, start=0,
             limit=3, budget_s=8.0, newest_first=False):
    """Replay the model on recorded transitions.

    transitions: objects with .action, .before_frame, .after_frame, .result.
    level: only transitions that START on this level (None = all levels).
    start: ignore transitions before this index.
    newest_first: walk backwards, so a time-budget cut keeps the most recent evidence.
    """
    t0 = time.monotonic()
    cache = {}

    def state_of(frame):
        key = id(frame)
        if key not in cache:
            cache[key] = (frame, state_fn(frame))  # keep frame alive so id() stays unique
        return cache[key][1]

    checked = correct = 0
    wins = wins_hit = false_wins = 0
    skipped = {"reset": 0, "game_over": 0, "other_level": 0, "no_frame": 0}
    errors = 0
    first_error = None
    mismatches = []
    by_action = {}
    partial = False
    order = range(max(0, int(start)), len(transitions))
    if newest_first:
        order = reversed(order)
    index = None
    for index in order:
        if time.monotonic() - t0 > budget_s:
            partial = True
            break
        tr = transitions[index]
        before, after = getattr(tr, "before_frame", None), getattr(tr, "after_frame", None)
        if before is None or after is None:
            skipped["no_frame"] += 1
            continue
        action = wm_parse_action(getattr(tr, "action", ""))
        name = wm_action_name(action)
        if name in _WM_SKIP_ACTIONS:
            skipped["reset"] += 1
            continue
        if level is not None and getattr(before, "level", None) != level:
            skipped["other_level"] += 1
            continue
        result = getattr(tr, "result", None) or {}
        won = bool(result.get("level_completed") or result.get("done") or result.get("run_complete")
                   or getattr(after, "level", 0) > getattr(before, "level", 0))
        if result.get("game_over") and not won:
            skipped["game_over"] += 1
            continue
        try:
            predicted = step_fn(state_of(before), action)
        except Exception as exc:  # noqa: BLE001 - model code
            errors += 1
            first_error = first_error or {"t": index, "action": wm_short(action, 60), "error": _wm_exc(exc)}
            continue
        if won:
            wins += 1
            if goal_fn is not None and predicted is not None:
                try:
                    if goal_fn(predicted):
                        wins_hit += 1
                except Exception as exc:  # noqa: BLE001
                    errors += 1
                    first_error = first_error or {"t": index, "action": wm_short(action, 60), "error": _wm_exc(exc)}
            continue
        try:
            actual = state_of(after)
        except Exception as exc:  # noqa: BLE001
            errors += 1
            first_error = first_error or {"t": index, "action": wm_short(action, 60), "error": _wm_exc(exc)}
            continue
        checked += 1
        stats = by_action.setdefault(name, [0, 0])
        stats[1] += 1
        if predicted is None:
            # None = "impossible / no effect": counts as correct when nothing changed
            ok = wm_freeze(actual) == wm_freeze(state_of(before))
            shown_pred = "<None: no change>"
        else:
            ok = wm_freeze(predicted) == wm_freeze(actual)
            shown_pred = predicted
        if ok:
            correct += 1
            stats[0] += 1
        elif len(mismatches) < limit:
            mismatches.append({
                "t": index,
                "action": action,
                "diff": (wm_state_diff(shown_pred, actual) if predicted is not None
                         else {"predicted": shown_pred, "changed": wm_state_diff(state_of(before), actual)}),
            })
        if goal_fn is not None:
            try:
                if goal_fn(actual):
                    false_wins += 1
            except Exception as exc:  # noqa: BLE001
                errors += 1
                first_error = first_error or {"t": index, "action": wm_short(action, 60), "error": _wm_exc(exc)}
    report = {
        "checked": checked,
        "correct": correct,
        "accuracy": round(correct / checked, 3) if checked else None,
        "by_action": {k: "%d/%d" % (v[0], v[1]) for k, v in sorted(by_action.items())},
        "mismatches": mismatches,
    }
    if errors:
        report["errors"] = errors
        report["first_error"] = first_error
    if goal_fn is not None:
        report["goal"] = {
            "level_wins_seen": wins,
            "wins_predicted": wins_hit,
            "false_wins": false_wins,
        }
    report["skipped"] = {k: v for k, v in skipped.items() if v}
    if partial:
        report["partial"] = "time budget reached at transition %s (%s)" % (
            index, "older ones unchecked" if newest_first else "newer ones unchecked")
    return report


def wm_default_actions(valid_actions):
    out = []
    for item in valid_actions or []:
        name = str(item).strip()
        if name.upper() in {"RESET", "UNDO", "MOUSE", "CLICK"} or not name:
            continue
        out.append(name)
    return out


def wm_plan(start, step_fn, goal_fn, actions, *, max_nodes=100000, heuristic=None,
            max_depth=None, budget_s=10.0):
    """BFS (or best-first on g + heuristic) over the model. Returns a dict with
    `found`, `actions` (ready for action(...)), `length`, `expanded`."""
    t0 = time.monotonic()
    actions = list(actions or [])
    if not actions:
        return {"found": False, "reason": "no actions to search (pass actions=[...])"}
    errors = 0
    first_error = None
    start_key = wm_freeze(start)
    try:
        if goal_fn(start):
            return {"found": True, "actions": [], "length": 0, "expanded": 0,
                    "note": "goal already true in the start state"}
    except Exception as exc:  # noqa: BLE001
        return {"found": False, "reason": "model_goal raised " + _wm_exc(exc)}
    parents = {start_key: None}
    counter = 0
    best = None
    if heuristic is None:
        frontier = deque([(start, start_key, 0)])
        pop = frontier.popleft
        push = frontier.append
    else:
        frontier = []
        try:
            h0 = float(heuristic(start))
        except Exception as exc:  # noqa: BLE001
            return {"found": False, "reason": "heuristic raised " + _wm_exc(exc)}
        heap_push = heapq.heappush
        heap_pop = heapq.heappop
        heap_push(frontier, (h0, 0, 0, start, start_key))
        best = (h0, start_key)

        def pop():
            _, _, depth, state, key = heap_pop(frontier)
            return state, key, depth

        def push(item):
            nonlocal counter
            state, key, depth, h = item
            counter += 1
            heap_push(frontier, (depth + h, counter, depth, state, key))
    expanded = 0
    reason = "exhausted"
    while frontier:
        if expanded >= max_nodes:
            reason = "max_nodes"
            break
        if (expanded & 255) == 0 and time.monotonic() - t0 > budget_s:
            reason = "time_budget"
            break
        state, key, depth = pop()
        expanded += 1
        if max_depth is not None and depth >= max_depth:
            continue
        for action in actions:
            try:
                nxt = step_fn(state, action)
            except Exception as exc:  # noqa: BLE001
                errors += 1
                first_error = first_error or {"action": wm_short(action, 60), "error": _wm_exc(exc)}
                continue
            if nxt is None:
                continue
            nkey = wm_freeze(nxt)
            if nkey in parents:
                continue
            parents[nkey] = (key, action)
            try:
                done = goal_fn(nxt)
            except Exception as exc:  # noqa: BLE001
                errors += 1
                first_error = first_error or {"action": wm_short(action, 60), "error": _wm_exc(exc)}
                done = False
            if done:
                path = _wm_path(parents, nkey)
                out = {"found": True, "actions": path, "length": len(path), "expanded": expanded,
                       "seconds": round(time.monotonic() - t0, 2)}
                if errors:
                    out["errors"] = errors
                    out["first_error"] = first_error
                return out
            if heuristic is None:
                push((nxt, nkey, depth + 1))
            else:
                try:
                    h = float(heuristic(nxt))
                except Exception as exc:  # noqa: BLE001
                    errors += 1
                    first_error = first_error or {"action": wm_short(action, 60), "error": _wm_exc(exc)}
                    continue
                if h < best[0]:
                    best = (h, nkey)
                push((nxt, nkey, depth + 1, h))
    out = {"found": False, "reason": reason, "expanded": expanded, "distinct_states": len(parents),
           "seconds": round(time.monotonic() - t0, 2)}
    if best is not None and best[1] != start_key:
        partial = _wm_path(parents, best[1])
        out["best_partial"] = {"heuristic": best[0], "actions": partial, "length": len(partial)}
    if errors:
        out["errors"] = errors
        out["first_error"] = first_error
    return out


def _wm_path(parents, key):
    path = []
    while parents.get(key) is not None:
        key, action = parents[key]
        path.append(action)
    path.reverse()
    return path
