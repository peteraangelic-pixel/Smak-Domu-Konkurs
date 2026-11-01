"""Separate fast-clone backend; preserve the running sweep2 implementation."""
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
from fast_state_clone import clone

_path=Path(__file__).with_name('sweep2.py')
_spec=importlib.util.spec_from_file_location('arc3_fast_sweep_implementation',_path)
_module=importlib.util.module_from_spec(_spec)
sys.modules[_spec.name]=_module
_spec.loader.exec_module(_module)
# Replace this module's reference only, never copy.deepcopy process-wide.
_module.copy=SimpleNamespace(deepcopy=clone)


def load_game(path,cls):
    spec=importlib.util.spec_from_file_location('arc3_fast_game_'+cls.lower(),path)
    mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod
    spec.loader.exec_module(mod)
    return getattr(mod,cls)()


_module.load_game=load_game
play_game=_module.play_game
search_level=_module.search_level
