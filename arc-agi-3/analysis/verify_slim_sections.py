"""Reproduce the actual upstream section renderer; not a notebook string search."""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'analysis/v3-slim-20261101/materialized/ARC3-Inference'))
from inference.agent import tool_agent as ta

agent = ta.ToolAgent(model='verification-only', provider='lmstudio')
agent._summarized_knowledge.update(world_model='Observed mechanics',
                                   current_plan='Test the next hypothesis',
                                   action_model='Action detail')
os.environ['ARC3_MEMORY_SECTIONS'] = 'off'
off = agent._summarized_knowledge_lines()
os.environ['ARC3_MEMORY_SECTIONS'] = 'slim'
slim = agent._summarized_knowledge_lines()
assert off == []
assert any('Observed mechanics' in line for line in slim)
assert any('Test the next hypothesis' in line for line in slim)
assert not any('Action detail' in line for line in slim)
print(json.dumps({'off_output': off, 'slim_output': slim,
                  'scope': 'Actual ToolAgent renderer with injected fixture; real LLM activation requires prompt logs.'}, indent=2))
