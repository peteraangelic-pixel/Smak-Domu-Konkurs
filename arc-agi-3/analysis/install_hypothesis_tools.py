"""Experimental Duck sandbox integration; call only in an isolated candidate."""
from pathlib import Path


def install(sandbox):
    if getattr(sandbox, '_hypothesis_tools_installed', False):return
    source=Path(__file__).with_name('hypothesis_probes.py').read_text(encoding='utf8')
    anchor='HOST_STDOUT = sys.stdout'
    exports='        runtime_globals["plan"] = plan'
    bootstrap=sandbox._SANDBOX_BOOTSTRAP
    assert bootstrap.count(anchor)==1 and bootstrap.count(exports)==1
    bootstrap=bootstrap.replace(anchor,source+'\n'+anchor)
    bootstrap=bootstrap.replace(exports,exports+'\n        runtime_globals["choose_probe"] = choose_probe\n        runtime_globals["validate_hypotheses"] = validate')
    compile(bootstrap,'<hypothesis-bootstrap>','exec')
    sandbox._SANDBOX_BOOTSTRAP=bootstrap
    sandbox._hypothesis_tools_installed=True
