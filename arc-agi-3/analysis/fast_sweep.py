"""Separate fast-clone backend; preserve the running sweep2 implementation."""
import importlib.util
from pathlib import Path
import sys
import copy
import hashlib
import inspect
import json
from types import SimpleNamespace
from fast_state_clone import clone

_approved=set()
_counts={'fast':0,'fallback':0}
def safe_clone(state):
    if type(state) in _approved:
        try:
            result=clone(state);_counts['fast']+=1;return result
        except Exception:
            # Later levels can introduce unsupported callable state.
            pass
    _counts['fallback']+=1
    return copy.deepcopy(state)

_path=Path(__file__).with_name('sweep2.py')
_spec=importlib.util.spec_from_file_location('arc3_fast_sweep_implementation',_path)
_module=importlib.util.module_from_spec(_spec)
sys.modules[_spec.name]=_module
_spec.loader.exec_module(_module)
# Replace this module's reference only, never copy.deepcopy process-wide.
_module.copy=SimpleNamespace(deepcopy=safe_clone)


def load_game(path,cls):
    spec=importlib.util.spec_from_file_location('arc3_fast_game_'+cls.lower(),path)
    mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod
    spec.loader.exec_module(mod)
    game=getattr(mod,cls)()
    certificate=Path(__file__).with_name('fast-clone-certificate-20261101.json')
    if certificate.exists():
        import arcengine
        cert=json.loads(certificate.read_text(encoding='utf8'))
        engine=Path(inspect.getfile(arcengine)).parent
        engine_matches=all(hashlib.sha256((engine/name).read_bytes()).hexdigest()==sha for name,sha in cert['engine_sha256'].items())
        source_hash=hashlib.sha256(Path(path).read_bytes()).hexdigest()
        if engine_matches and source_hash in cert['approved_source_hashes']:_approved.add(type(game))
    return game


_module.load_game=load_game
def play_game(job):
    _counts.update(fast=0,fallback=0)
    result=_module.play_game(job)
    result['clone_calls']=dict(_counts)
    return result
search_level=_module.search_level
