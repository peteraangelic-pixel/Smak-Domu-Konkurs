"""Solved-level memory experiment on exact v3; no scheduler/budget changes.

Attribution: lalalia9/vickyfym, adapted from rellik13/sirikilohit (CC-BY4.0).
Builds on local lalalia_compat, adding turn-cap eviction coverage and telemetry.
"""
from lalalia_compat import source as original_source


def source():
    return original_source()+'''

# Codex v3 experiment: count actual eviction events, including persistent
# turn-cap pruning that does not reduce messages in the token trimmer.
_slm_v3_original_evicted = _ta_slm.ToolAgent._note_history_evicted
_slm_v3_original_persistent = _ta_slm.ToolAgent._persistent_history_messages
_slm_v3_original_before = _slm_before_turn
_slm_v3_original_ensure = _ta_slm.ToolAgent._ensure_session

def _slm_v3_ensure(self, state_path):
    key = str(Path(state_path).resolve())
    changed = getattr(self, "_slm_v3_runtime_key", None) != key
    _slm_v3_original_ensure(self, state_path)
    if changed:
        old = getattr(self, "_slm_block_text", "")
        if old:
            self._system_prompt = self._system_prompt.replace(old, "").rstrip()
        self._slm_levels = []
        self._slm_block_text = ""
        self._slm_v3_evictions = 0
        self._slm_v3_runtime_key = key
        self._last_step_summary = None

def _slm_v3_evicted(self):
    _slm_v3_original_evicted(self)
    self._slm_v3_evictions = getattr(self, "_slm_v3_evictions", 0) + 1

def _slm_v3_persistent(self, messages, *args, **kwargs):
    before = getattr(self, "_slm_v3_evictions", 0)
    result = _slm_v3_original_persistent(self, messages, *args, **kwargs)
    if getattr(self, "_slm_v3_evictions", 0) > before:
        try:
            _slm_refresh_system_prompt(self)
        except Exception as exc:
            print(f"SLM_V3_REFRESH_ERROR {type(exc).__name__}", flush=True)
    return result

def _slm_v3_before(self, state_path):
    self._ensure_session(Path(state_path))
    before = len(getattr(self, "_slm_levels", []))
    _slm_v3_original_before(self, state_path)
    after = len(getattr(self, "_slm_levels", []))
    if after > before:
        print(f"SLM_V3_CAPTURE levels={after} current={(self._last_step_summary or {}).get('level')}", flush=True)

_slm_before_turn = _slm_v3_before
_ta_slm.ToolAgent._note_history_evicted = _slm_v3_evicted
_ta_slm.ToolAgent._persistent_history_messages = _slm_v3_persistent
_ta_slm.ToolAgent._ensure_session = _slm_v3_ensure
'''
