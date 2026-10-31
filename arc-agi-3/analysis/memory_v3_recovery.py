"""One bounded recovery hint after repeated long failures, on memory-v3.

Observed motivation: tn36 ran14 distinct61-action failed attempts. A hint is
not a solver and cannot establish that the hidden failure cause is a timer.
"""
from memory_v3 import source as base_source


def source():
    return base_source()+'''

_slm_recovery_original_prompt = _ta_slm.ToolAgent._build_user_prompt

def _slm_recovery_lengths(entries, level):
    attempts = []
    count = 0
    for entry in entries or []:
        frame_level = getattr(getattr(entry, "frame", None), "level", None)
        if frame_level != level:
            count = 0
            continue
        action = str(getattr(entry, "action", "") or "").strip()
        if action.upper().startswith("RESET"):
            if count:
                attempts.append(count)
            count = 0
        elif action:
            count += 1
    return attempts[-3:]

def _slm_recovery_prompt(self, *args, **kwargs):
    prompt = _slm_recovery_original_prompt(self, *args, **kwargs)
    try:
        frame = kwargs.get("current_frame")
        level = int(getattr(frame, "level", 0) or 0)
        key = (getattr(self, "_slm_v3_runtime_key", None), level)
        seen = getattr(self, "_slm_recovery_seen", set())
        if key in seen or not (self._last_step_summary or {}).get("game_over"):
            return prompt
        lengths = _slm_recovery_lengths(kwargs.get("history_entries"), level)
        if len(lengths) != 3 or min(lengths) < 30 or max(lengths)-min(lengths)>2:
            return prompt
        self._slm_recovery_seen = seen | {key}
        prompt += (
            "\\n\\nFAILURE AUDIT: Your last three failed attempts used "
            + ", ".join(map(str, lengths))
            + " actions. Similar lengths suggest an action budget, but verify the death-frame bar. "
            "Before another long attempt, identify the uncertain goal or control rule and test it "
            "with a short discriminating probe. Validate model_step/model_goal against recorded "
            "successes AND failures, then search for a shorter plan. A changed long route alone "
            "does not establish a new mechanic."
        )
        print(f"SLM_V3_RECOVERY level={level} lengths={lengths}", flush=True)
    except Exception as exc:
        print(f"SLM_V3_RECOVERY_ERROR {type(exc).__name__}", flush=True)
    return prompt

_ta_slm.ToolAgent._build_user_prompt = _slm_recovery_prompt
'''
