"""Protocol checks: preserve history and reject false reasoning-off responses."""
import io
import json
from pathlib import Path
import sys
import types
from unittest.mock import patch

import pytest

pkg = types.ModuleType('llmagent')
pkg.__path__ = [str(Path(__file__).resolve().parents[1])]
sys.modules.setdefault('llmagent', pkg)
from llmagent.llm_policy import LLMClient, LLMConfig


def client():
    return LLMClient(LLMConfig(base_url='http://127.0.0.1:1234/v1', model_id='lab',
                               api_style='lmstudio_native', enable_thinking=False))


def response(content='{"action":"UP"}', reasoning=0):
    return io.BytesIO(json.dumps({'output': [{'type': 'message', 'content': content}],
                                 'stats': {'input_tokens': 10, 'total_output_tokens': 5,
                                           'reasoning_output_tokens': reasoning}}).encode())


def test_native_payload_preserves_role_transcript_and_usage():
    c = client()
    conversation = [{'role': 'system', 'content': 'Solve'}, {'role': 'user', 'content': 'first'},
                    {'role': 'assistant', 'content': 'prior'}, {'role': 'user', 'content': 'next'}]
    with patch('urllib.request.urlopen', return_value=response()) as call:
        result = c.chat(conversation, temperature=0.1)
    request = call.call_args.args[0]
    payload = json.loads(request.data)
    assert request.full_url == 'http://127.0.0.1:1234/api/v1/chat'
    assert json.loads(payload['input']) == conversation[1:]
    assert payload['reasoning'] == 'off' and payload['store'] is False
    assert payload['temperature'] == 0.1
    assert result['content'] == '{"action":"UP"}'
    assert (c.total_calls, c.total_tokens, c.reasoning_tokens, c.failed_calls) == (1, 15, 0, 0)


@pytest.mark.parametrize('content,reasoning', [('', 0), ('ok', 4)])
def test_native_rejects_unusable_or_ignored_reasoning_setting(content, reasoning):
    c = client()
    with patch('urllib.request.urlopen', return_value=response(content, reasoning)):
        with pytest.raises(RuntimeError):
            c.chat([{'role': 'user', 'content': 'hello'}])
    assert c.failed_calls == 1


def test_native_does_not_silently_drop_images():
    with pytest.raises(ValueError, match='text messages'):
        client().chat([{'role': 'user', 'content': [{'type': 'image_url'}]}])
