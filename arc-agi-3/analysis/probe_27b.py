"""Record real model identity and OpenAI tool-call behavior before Duck tests."""
import json
from pathlib import Path
import time
import requests

root = Path(__file__).resolve().parent
models = requests.get('http://127.0.0.1:1234/api/v1/models', timeout=20).json()
start = time.monotonic()
response = requests.post('http://127.0.0.1:1234/v1/chat/completions', timeout=180, json={
    'model': 'arc-lab-27b', 'messages': [{'role': 'user', 'content': 'Call python with code print(6*7). Do not explain.'}],
    'tools': [{'type': 'function', 'function': {'name': 'python', 'description': 'Run Python code',
                'parameters': {'type': 'object', 'properties': {'code': {'type': 'string'}}, 'required': ['code']}}}],
    'tool_choice': 'required',
    'max_tokens': 256, 'temperature': 0, 'reasoning_effort': 'none', 'stream': False,
})
record = {'http_status': response.status_code, 'seconds': time.monotonic() - start,
          'models': models, 'response': response.json()}
(root / 'model27-probe.json').write_text(json.dumps(record, indent=2), encoding='utf8')
print(json.dumps({k: v for k, v in record.items() if k != 'models'}), flush=True)
