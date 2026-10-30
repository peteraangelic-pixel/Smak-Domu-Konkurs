"""Adapt lalalia9's public solved-level hook to our existing level notes.

Source: vickyfym/arc-agi-3-lalalia-final, cell17, adapted there from
rellik13/sirikilohit (M85, CC-BY4.0). Retain their attribution and source.
Only the memory hook is installed; notebook runtime/budget edits are excluded.
"""
from pathlib import Path


def source(compatible=True):
    text = Path(__file__).with_name('lalalia-memory-cell.txt').read_text(encoding='utf8')
    text = text.split('\nbm.solver.max_runtime_s_per_game', 1)[0]
    if compatible:
        # Base ARC3_LEVEL_NOTES rewrites the system prompt AFTER _note_history_evicted.
        # Pin the memory only after all base trimming/notes work is complete.
        start = text.index('def _slm_note_evicted(self):')
        end = text.index('\n\n_ta_slm.ToolAgent.analyze', start)
        text = text[:start] + '''def _slm_note_evicted(self):
    _slm_original_evicted(self)


def _slm_trim(self, messages, *args, **kwargs):
    result = _slm_original_trim(self, messages, *args, **kwargs)
    if len(result) < len(messages) and result and result[0].get("role") == "system":
        _slm_refresh_system_prompt(self)
        result = [{**result[0], "content": self._system_prompt}, *result[1:]]
    return result
''' + text[end:]
        text = text.replace('if block == getattr(self, "_slm_block_text", ""):',
            'if block == getattr(self, "_slm_block_text", "") and block in self._system_prompt:')
    return text


def install(compatible=True):
    text = source(compatible)
    namespace = {}
    exec(compile(text, 'lalalia-memory-compatible.py' if compatible else 'lalalia-memory-original.py', 'exec'), namespace)
    return namespace
