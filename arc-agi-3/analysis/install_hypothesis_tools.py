"""Experimental Duck sandbox integration; call only in an isolated candidate."""
from pathlib import Path

GUIDANCE = '''
Hypothesis testing helpers are available. When two plausible rules imply different
outcomes, encode both as {'name': str, 'encode': frame_to_state, 'step': (state, action)_to_state}.
Use the SAME state schema for both; omit HUD/time and preserve gameplay state.
choose_probe(models, current_frame, candidate_actions) returns an action that
separates predictions, or None. Supply only valid actions and explicit observed
mouse targets. This ranks information, NOT safety or progress: inspect the proposed
action before executing action([probe['action']]). It never executes actions itself.
validate_hypotheses(models, [(tr.before_frame, tr.action, tr.after_frame), ...])
compares with real observed transitions. Normalize tr.action into your step function's
action schema. Never invent outcomes. Discard contradicted models; no evidence or
errors cannot validate a model. Use check_model with explicit functions for fuller
transition validation, then search a validated model. Retained helpers must be plain
defs with constants inside; do not expect a top-level models variable to persist.
'''


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


def install_agent(tool_agent, sandbox):
    """Expose the helpers in the actual Python tool specification, once."""
    install(sandbox)
    if getattr(tool_agent,'_hypothesis_guidance_installed',False):return
    tool_agent._PYTHON_TOOL_DESCRIPTION += '\n'+GUIDANCE
    tool_agent._hypothesis_guidance_installed=True
