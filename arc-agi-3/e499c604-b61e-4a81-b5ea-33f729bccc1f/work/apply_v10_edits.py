"""Apply the v10 (plan-commit) edits to a prepared harness tree.

Usage: python3 apply_v10_edits.py <tree-root>

The tree must already contain Franzen's patch plus 0001/0002/0004. Every anchor
is asserted, so a moved anchor fails loudly instead of silently doing nothing.
"""
import io
import shutil
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None
AGENT = ROOT / "ARC3-Inference/inference/agent/tool_agent.py"
PROMPTS = ROOT / "ARC3-Inference/inference/agent/prompts.py"
SANDBOX = ROOT / "ARC3-Inference/inference/agent/python_tool_sandbox.py"
MODULE_SRC = Path("work/harness_plan_commit.py")
MODULE_DST = ROOT / "ARC3-Inference/inference/utils/plan_commit.py"

AGENT_EDITS = [
    (
        "    WORLD_MODEL_TOOL_ADDENDUM,\n",
        "    WORLD_MODEL_TOOL_ADDENDUM,\n    PLAN_COMMIT_TOOL_ADDENDUM,\n    plan_escalation_prompt,\n",
    ),
    (
        "def _world_model_nudge() -> bool:\n"
        '    """ARC3_WORLD_MODEL_NUDGE (needs ARC3_WORLD_MODEL): a world-model status line in every turn."""\n'
        '    return _get_env_bool("ARC3_WORLD_MODEL", False) and _get_env_bool("ARC3_WORLD_MODEL_NUDGE", False)\n',
        "def _world_model_nudge() -> bool:\n"
        '    """ARC3_WORLD_MODEL_NUDGE (needs ARC3_WORLD_MODEL): a world-model status line in every turn."""\n'
        '    return _get_env_bool("ARC3_WORLD_MODEL", False) and _get_env_bool("ARC3_WORLD_MODEL_NUDGE", False)\n'
        "\n"
        "\n"
        "def _plan_commit_enabled() -> bool:\n"
        '    """ARC3_PLAN_COMMIT: expose commit()/frame_digest() and document them."""\n'
        '    return _get_env_bool("ARC3_PLAN_COMMIT", False)\n'
        "\n"
        "\n"
        "def _escalate_actions() -> int:\n"
        '    """ARC3_ESCALATE_ACTIONS: actions on one level before the escalation directive."""\n'
        '    return max(0, _get_env_int("ARC3_ESCALATE_ACTIONS", 0))\n',
    ),
    (
        '    "Use `print(...)` for compact output or assign final data to `result`."\n)\n',
        '    "Use `print(...)` for compact output or assign final data to `result`."\n)\n'
        "\n"
        "if _plan_commit_enabled():\n"
        "    _PYTHON_TOOL_DESCRIPTION += (\n"
        '        " Also available: `commit(plan)` plays a list of actions one step at a time and stops at "\n'
        '        "the first failed `expect={...}` (level, board_changed, step, digest, cells), returning "\n'
        '        "`mismatch` with the field that differed; `frame_digest()` returns the stable digest of a frame."\n'
        "    )\n",
    ),
    (
        "        prompt += WORLD_MODEL_TOOL_ADDENDUM\n",
        "        prompt += WORLD_MODEL_TOOL_ADDENDUM\n"
        "    if _plan_commit_enabled():\n"
        "        # commit()/frame_digest() live in the sandbox (inference/utils/plan_commit.py).\n"
        "        prompt += PLAN_COMMIT_TOOL_ADDENDUM\n",
    ),
    (
        '                lines.append(_stuck_audit_prompt(int(current_level or 1), spent))\n'
        '        return "\\n".join(lines)\n',
        '                lines.append(_stuck_audit_prompt(int(current_level or 1), spent))\n'
        "        escalate_every = _escalate_actions()\n"
        "        if escalate_every and _plan_commit_enabled():\n"
        "            on_level = max(0, int(action_num or 0) - int(self._actions_at_level_start or 0))\n"
        "            if on_level >= escalate_every * (self._arc3_escalations_on_level + 1):\n"
        "                self._arc3_escalations_on_level = on_level // escalate_every\n"
        "                lines.append(plan_escalation_prompt(int(current_level or 1), on_level))\n"
        '        return "\\n".join(lines)\n',
    ),
    (
        "        self._actions_at_level_start = 0\n",
        "        self._actions_at_level_start = 0\n        self._arc3_escalations_on_level = 0\n",
    ),
    (
        "            self._actions_at_level_start = _priority_action_count(summary)\n"
        "            self._tokens_at_level_start = self._session_generated_tokens\n",
        "            self._actions_at_level_start = _priority_action_count(summary)\n"
        "            self._tokens_at_level_start = self._session_generated_tokens\n"
        "            self._arc3_escalations_on_level = 0\n",
    ),
]

PROMPTS_ADDITION = '''PLAN_COMMIT_TOOL_ADDENDUM = (
    "- `commit(plan)` plays a plan and checks it as it goes. A plan is a list of steps; each step "
    "is an action (`'UP'`, `{'action': 'MOUSE', 'row': r, 'col': c}`) or `{'action': ..., "
    "'expect': {...}}`. After every step the expectation is compared with the frame that actually "
    "came back, and the plan stops at the first disagreement with `mismatch` naming the field that "
    "failed. Expectations: `level` (int), `board_changed` (bool), `step` (int, absolute), `digest` "
    "(from `frame_digest()`), and `cells` ({'row,col': symbol} or [[row, col, symbol], ...]). It also "
    "stops on level completion, game over, run completion, or `max_actions` (default 40). "
    "Example: `commit(['LEFT', {'action': 'UP', 'expect': {'level': 2}}])`.\\n"
    "- A step you claim to understand should carry an expectation computed before it runs. A wrong "
    "rule then costs one action and hands back a diff, instead of spending the rest of the plan on a "
    "board that no longer matches the reasoning.\\n"
)


def plan_escalation_prompt(level: int, actions_spent: int) -> str:
    return (
        f"ESCALATION: {actions_spent} actions on level {level} without completing it. Stop probing "
        "by hand. In this turn: (1) state what the recorded transitions leave unexplained; (2) write "
        "the rule you believe as `model_state(frame)` and `model_step(state, action)`; (3) run "
        "`check_model()` and report the accuracy - below ~0.9 on this level it is not yet a model; "
        "(4) only then `plan()` inside it and `commit()` the result with an expectation on every "
        "step. If the level still resists, search the model for the nearest unseen board and test the "
        "single action that reaches it."
    )


STEP_VERIFICATION_ADDENDUM = ('''

SANDBOX_EDITS = [
    (
        "from inference.utils import world_model as _world_model_module",
        "from inference.utils import plan_commit as _plan_commit_module\n"
        "from inference.utils import world_model as _world_model_module",
    ),
    (
        "    __WORLD_MODEL_SOURCE__\n\n    __RETAINED_FUNCTIONS_SOURCE__",
        "    __WORLD_MODEL_SOURCE__\n\n    __PLAN_COMMIT_SOURCE__\n\n    __RETAINED_FUNCTIONS_SOURCE__",
    ),
    (
        '        runtime_globals["action"] = action\n        if initial.get("animation_enabled"):',
        '        runtime_globals["action"] = action\n'
        "\n"
        "        def commit(plan, stop_on_terminal=True, max_actions=40):\n"
        "            # Plays a plan step by step, halting on the first failed expectation.\n"
        "            return pc_play(\n"
        "                plan,\n"
        "                action,\n"
        '                lambda: runtime_globals.get("current_frame"),\n'
        "                max_actions=max_actions,\n"
        "                stop_on_terminal=bool(stop_on_terminal),\n"
        "            )\n"
        "\n"
        "        def frame_digest(frame=None):\n"
        "            # Stable across processes, so a digest can be written down and reused.\n"
        '            target = frame if frame is not None else runtime_globals.get("current_frame")\n'
        '            return pc_digest(str(getattr(target, "ascii", "") or ""))\n'
        "\n"
        '        if bool(initial.get("plan_commit_enabled")):\n'
        '            runtime_globals["commit"] = commit\n'
        '            runtime_globals["frame_digest"] = frame_digest\n'
        "\n"
        '        if initial.get("animation_enabled"):',
    ),
    (
        '.replace(\n    "__WORLD_MODEL_SOURCE__\\n", inspect.getsource(_world_model_module)\n)',
        '.replace(\n    "__WORLD_MODEL_SOURCE__\\n", inspect.getsource(_world_model_module)\n).replace(\n'
        '    "__PLAN_COMMIT_SOURCE__\\n", inspect.getsource(_plan_commit_module)\n)',
    ),
    (
        "def _world_model_enabled() -> bool:\n"
        '    """ARC3_WORLD_MODEL: expose check_model()/plan() and the per-snippet model check."""\n'
        '    return str(os.environ.get("ARC3_WORLD_MODEL", "")).strip().lower() in {"1", "true", "yes", "on"}',
        "def _world_model_enabled() -> bool:\n"
        '    """ARC3_WORLD_MODEL: expose check_model()/plan() and the per-snippet model check."""\n'
        '    return str(os.environ.get("ARC3_WORLD_MODEL", "")).strip().lower() in {"1", "true", "yes", "on"}\n'
        "\n"
        "\n"
        "def _plan_commit_enabled() -> bool:\n"
        '    """ARC3_PLAN_COMMIT: expose commit()/frame_digest() to the model."""\n'
        '    return str(os.environ.get("ARC3_PLAN_COMMIT", "")).strip().lower() in {"1", "true", "yes", "on"}',
    ),
    (
        '                "world_model_enabled": _world_model_enabled(),',
        '                "world_model_enabled": _world_model_enabled(),\n'
        '                "plan_commit_enabled": _plan_commit_enabled(),',
    ),
]


def apply(path, edits):
    text = io.open(path, encoding="utf-8").read()
    for index, (old, new) in enumerate(edits, start=1):
        count = text.count(old)
        if count != 1:
            print(f"{path.name}: edit {index} matched {count} times")
            return False
        text = text.replace(old, new, 1)
    io.open(path, "w", encoding="utf-8").write(text)
    print(f"{path.name}: {len(edits)} edits applied")
    return True


def main():
    if ROOT is None:
        print("usage: apply_v10_edits.py <tree-root>")
        return 2
    prompts = io.open(PROMPTS, encoding="utf-8").read()
    anchor = "STEP_VERIFICATION_ADDENDUM = ("
    if prompts.count(anchor) != 1:
        print("prompts.py: STEP_VERIFICATION_ADDENDUM anchor not unique")
        return 1
    io.open(PROMPTS, "w", encoding="utf-8").write(
        prompts.replace(anchor, PROMPTS_ADDITION, 1))
    print("prompts.py: addenda inserted")
    if not apply(AGENT, AGENT_EDITS):
        return 1
    if not apply(SANDBOX, SANDBOX_EDITS):
        return 1
    shutil.copyfile(MODULE_SRC, MODULE_DST)
    print(f"plan_commit.py: copied to {MODULE_DST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
