"""Exercise the local JSON policy with real games and native LM Studio API.

This checks integration only. It does not run the v13.7/v18 Duck REPL agent.
"""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'llm-agent'))
import local_eval


if __name__ == '__main__':
    os.environ.update(LLM_API_STYLE='lmstudio_native', LLM_MODEL_ID='arc-lab-fast',
                      LLM_BASE_URL='http://127.0.0.1:1234/v1', LLM_ENABLE_THINKING='0',
                      LLM_CONTEXT_WINDOW='8192', LLM_MAX_OUTPUT='384', LLM_TEMPERATURE='0')
    rows = local_eval.evaluate({'control': {}}, ['ft09', 'ls20'],
                                games_dir=str(ROOT / 'games/environment_files'),
                                mode='real', max_actions=6, workers=1)
    report = {'scope': 'Local JSON policy integration only; not a Duck v13.7/v18 quality comparison',
              'games': rows, 'cpu_search_workers_in_separate_ablation': 16,
              'llm_request_parallelism': 1}
    (ROOT / 'analysis/native-policy-smoke-20261030.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps(report), flush=True)
