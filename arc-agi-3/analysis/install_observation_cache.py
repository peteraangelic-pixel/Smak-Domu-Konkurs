"""Experimental same-observation cache integration; not a submitted candidate."""
from contextvars import ContextVar
import hashlib
import inspect
import json
from pathlib import Path
from observation_literal_cache import ObservationLiteralCache,decode


def install(tool_agent,sandbox):
    if getattr(tool_agent,'_observation_cache_installed',False):return
    source=Path(__file__).with_name('observation_literal_cache.py').read_text(encoding='utf8')
    bootstrap=sandbox._SANDBOX_BOOTSTRAP
    anchor='HOST_STDOUT = sys.stdout'
    assert bootstrap.count(anchor)==1
    bootstrap=bootstrap.replace(anchor,source+'\n'+anchor)
    anchor='    _available_names = set(runtime_globals) | set(runtime_globals["__builtins__"])'
    assert bootstrap.count(anchor)==1
    restore='''
    _literal_action_attempted = [False]
    _literal_excluded = set(_available_names) | {'result'}
    for _name, _node in (initial.get('state', {}).get('_literal_variables') or {}).items():
        if _name.isidentifier() and not _name.startswith('_') and _name not in _literal_excluded:
            runtime_globals[_name] = decode(_node)
    def _collect_literal_payload():
        if _literal_action_attempted[0]:
            return {'literal_payload': '{}'}
        _cache = ObservationLiteralCache()
        _cache.capture(runtime_globals, observation_token='child', excluded=_literal_excluded)
        return {'literal_payload': _cache.payload}
'''
    bootstrap=bootstrap.replace(anchor,anchor+'\n'+restore)
    anchor='    def action(actions):'
    assert bootstrap.count(anchor)==1
    bootstrap=bootstrap.replace(anchor,anchor+'\n        _literal_action_attempted[0] = True')
    anchor='                **_collect_retention_payload(),'
    assert bootstrap.count(anchor)==2
    bootstrap=bootstrap.replace(anchor,anchor+'\n                **_collect_literal_payload(),')
    compile(bootstrap,'<literal-cache-bootstrap>','exec');sandbox._SANDBOX_BOOTSTRAP=bootstrap
    # Preserve one extra bounded response field through the real host runner.
    host=inspect.getsource(sandbox.run_sandboxed_python)
    anchor='"keepable_functions": list(message.get("keepable_functions") or []),'
    assert host.count(anchor)==1
    host=host.replace(anchor,anchor+'\n                    "literal_payload": message.get("literal_payload", "{}"),')
    exec(compile(host,'<literal-cache-host>','exec'),vars(sandbox))
    raw_run=sandbox.run_sandboxed_python
    active=ContextVar('observation_cache_agent',default=None)
    original_tool=tool_agent.ToolAgent._run_python_tool
    def tool(self,state_path,arguments):
        token=active.set((self,str(Path(state_path).resolve())))
        try:return original_tool(self,state_path,arguments)
        finally:active.reset(token)
    def run(**kwargs):
        context=active.get()
        if context is None:return raw_run(**kwargs)
        agent,path=context
        cache=getattr(agent,'_observation_literal_cache',None)
        if cache is None:cache=agent._observation_literal_cache=ObservationLiteralCache()
        state=dict(kwargs['initial_state'])
        token=(path,hashlib.sha256(json.dumps(state,sort_keys=True).encode()).hexdigest())
        restored=cache.restore(observation_token=token)
        # Re-encode locally captured literals before sending to the child.
        from observation_literal_cache import encode
        state['_literal_variables']={k:encode(v,[4096]) for k,v in restored.items()}
        kwargs['initial_state']=state
        action_handler=kwargs['action_handler'];attempted=[False]
        def action(*args,**kw):
            attempted[0]=True;cache.clear()  # BEFORE any action, including refusal/failure.
            return action_handler(*args,**kw)
        kwargs['action_handler']=action
        result=raw_run(**kwargs)
        if attempted[0] or result.get('error'):
            cache.clear()
        else:
            try:
                payload=result.pop('literal_payload','{}')
                if not isinstance(payload,str) or len(payload.encode())>65536:raise ValueError('cache limit')
                data={k:decode(v) for k,v in json.loads(payload).items()}
                cache.capture(data,observation_token=token)
            except Exception:cache.clear()
        result.pop('literal_payload',None)
        if restored:
            result['stdout']=str(result.get('stdout') or '')+'\nOBSERVATION_CACHE restored='+str(len(restored))+'\n'
        return result
    tool_agent.run_sandboxed_python=run
    tool_agent.ToolAgent._run_python_tool=tool
    tool_agent._observation_cache_installed=True
