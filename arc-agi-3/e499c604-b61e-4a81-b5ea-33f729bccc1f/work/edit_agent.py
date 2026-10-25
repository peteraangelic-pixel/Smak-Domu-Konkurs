import io
import sys

AGENT = "work/c45base/ARC3-Inference/inference/agent/tool_agent.py"

EDITS = [
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


def main() -> int:
    with io.open(AGENT, encoding="utf-8") as handle:
        text = handle.read()
    for index, (old, new) in enumerate(EDITS, start=1):
        count = text.count(old)
        if count != 1:
            print(f"EDIT {index}: expected 1 match, found {count}")
            return 1
        text = text.replace(old, new, 1)
    with io.open(AGENT, "w", encoding="utf-8") as handle:
        handle.write(text)
    print(f"applied {len(EDITS)} edits")
    return 0


if __name__ == "__main__":
    sys.exit(main())
