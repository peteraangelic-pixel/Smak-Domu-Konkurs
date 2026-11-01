"""Exercise upstream scope boundaries without LLM or game oracle."""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT/'analysis/v3-levelscope-20261101'
sys.path.insert(0, str(LAB/'materialized/ARC3-Inference'))
os.environ.update(ARC3_PERSISTENT_FUNCTIONS='1',
                  ARC3_PERSISTENT_FUNCTIONS_SCOPE='levelup', ARC3_MEMORY_SECTIONS='off')
from inference.agent import tool_agent as ta

agent = ta.ToolAgent(model='verification-only', provider='lmstudio')
agent._ensure_session(LAB/'fixture-a/state.json')
agent._kept_functions = {'helper': 'def helper():\n    return 7'}
agent._last_step_summary = {'level': 1, 'level_transition': False}
agent._update_summarized_knowledge_from_step_summary()
assert agent._kept_functions
agent._last_step_summary = {'level': 2, 'level_transition': True}
agent._update_summarized_knowledge_from_step_summary()
assert not agent._kept_functions
assert 'cleared at this level transition' in agent._retained_function_context()
os.environ['ARC3_PERSISTENT_FUNCTIONS_SCOPE'] = 'game'
agent._kept_functions = {'helper': 'def helper():\n    return 7'}
agent._update_summarized_knowledge_from_step_summary()
assert agent._kept_functions
# Upstream session identity is the runtime directory, not the filename.
agent._ensure_session(LAB/'fixture-b/state.json')
assert not agent._kept_functions
manifest = json.loads((LAB/'materialized/source-manifest.json').read_text())
baseline = json.loads((ROOT/'analysis/v3-slim-20261101/materialized/source-manifest.json').read_text())
assert manifest['source_sha256'] == baseline['source_sha256']
report = {'retained_within_level': True, 'cleared_on_level_transition': True,
          'clear_notice_rendered': True, 'control_game_scope_keeps_helpers': True,
          'different_runtime_directory_clears_helpers': True,
          'inference_sources_identical': len(manifest['source_sha256']),
          'scope': 'Actual ToolAgent methods; no LLM-quality measurement',
          'fixture_correction': 'Initial check used two filenames in the same runtime directory; corrected to distinct game directories.'}
(LAB/'verification.json').write_text(json.dumps(report, indent=2), encoding='utf8')
print(json.dumps(report))
