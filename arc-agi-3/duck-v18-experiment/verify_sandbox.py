"""Exercise the packaged v18 planner through the shipped isolated sandbox."""
import ast
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types

D = Path(__file__).resolve().parent
notebook = json.loads((D / 'candidate/arc3-duck-v18.ipynb').read_text(encoding='utf8'))

with tempfile.TemporaryDirectory(prefix='arc18-verify-') as temp:
    root = Path(temp)
    source = root / 'ARC3-Inference'
    shutil.copytree(D.parent / 'kaggle/ops/results/r033-recon-bundle/bundle/src/ARC3-Inference', source)
    for index in range(6, 16):
        cell = ''.join(notebook['cells'][index]['source'])
        if index == 6:
            patches = [cell.split('\n', 1)[1]]
        else:
            patches = [node.value for node in ast.walk(ast.parse(cell))
                       if isinstance(node, ast.Constant) and isinstance(node.value, str)
                       and node.value.startswith(('diff --git', '--- a/'))]
        for patch in patches:
            subprocess.run(['git', 'apply', '--include=ARC3-Inference/*', '--whitespace=nowarn', '-'],
                           input=(patch.rstrip('\n') + '\n').encode(), cwd=root, check=True)

    for name in ('inference', 'inference.agent', 'inference.utils'):
        module = types.ModuleType(name)
        module.__path__ = [str(source.joinpath(*name.split('.')))]
        sys.modules[name] = module
    spec = importlib.util.spec_from_file_location(
        'inference.agent.python_tool_sandbox', source / 'inference/agent/python_tool_sandbox.py')
    sandbox = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sandbox)
    os.environ['ARC3_WORLD_MODEL'] = '1'
    # Windows caps command-line length. Preserve the shipped bootstrap bytes,
    # but launch them from a file for this local check. Kaggle uses Linux -c.
    if os.name == 'nt':
        original_popen = subprocess.Popen
        def windows_popen(args, **kwargs):
            bootstrap = Path(kwargs['cwd']) / 'bootstrap.py'
            bootstrap.write_text(args[-1], encoding='utf8')
            return original_popen(args[:3] + [str(bootstrap)], **kwargs)
        sandbox.subprocess.Popen = windows_popen
    print('World-model enabled:', sandbox._world_model_enabled())
    frame = {'ascii': '000\n010\n000', 'grid': [[0,0,0],[0,1,0],[0,0,0]],
             'shape': [3,3], 'level': 0, 'step': 0}
    state = {'current_frame': frame, 'history': [], 'valid_actions': ['MOUSE']}
    code = '''
def model_step(state, action):
    return 1 if isinstance(action, dict) and action.get("row") == 1 and action.get("col") == 1 else state
def model_goal(state):
    return state == 1
result = plan(start=0, max_nodes=100)
assert result["found"], result
assert result["actions"] == [{"action":"MOUSE", "row":1, "col":1}], result
explicit = plan(start=0, actions=[{"action":"MOUSE", "row":0, "col":0}], max_nodes=100)
assert not explicit["found"], explicit
print("default clicks and explicit override passed")
'''
    result = sandbox.run_sandboxed_python(
        code=code, timeout_seconds=10, initial_state=state,
        action_handler=lambda _: (_ for _ in ()).throw(AssertionError('unexpected live action')))
    print(json.dumps(result, indent=2))
    assert not result.get('error'), result
    assert 'default clicks and explicit override passed' in result.get('stdout', ''), result
    (D / 'sandbox-verification.json').write_text(json.dumps(result, indent=2), encoding='utf8')
