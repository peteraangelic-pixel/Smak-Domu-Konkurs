"""Experimental prompt hook: validate an already-written simulator, once/level.

No new tools or automatic execution of inferred models. A name match is only
a request to inspect a helper, never a claim that its signature is compatible.
"""
import ast
import re


def install(agent_class):
    if getattr(agent_class,'_validation_nudge_installed',False):return
    original=agent_class._build_user_prompt
    def build(self,*args,**kwargs):
        prompt=original(self,*args,**kwargs)
        candidates=[]
        for source in getattr(self,'_kept_functions',{}).values():
            try:
                defs=[n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)]
                for fn in defs:
                    if re.search(r'(step|sim|slide|apply_move)',fn.name,re.I) and len(fn.args.args)>=2:
                        candidates.append(fn.name)
            except SyntaxError:continue
        frame=kwargs.get('current_frame')
        level=getattr(frame,'level',None)
        if level is None:return prompt
        key=(str(getattr(self,'_session_runtime_dir','')),level)
        if not candidates or getattr(self,'_last_validation_nudge',None)==key:return prompt
        self._last_validation_nudge=key
        return prompt+'\n\nMODEL_VALIDATION_REQUEST: You already wrote possible simulator helpers: '+', '.join(sorted(set(candidates))[:4])+'. Before trusting another plan, compare a concrete prediction with a recorded transition on this level. If compatible, adapt your existing helpers and call check_model(state_fn=your_frame_encoder, step_fn=your_state_action_step, limit=3). Print its compact result and repair mismatches before further search. Function names alone do not establish compatibility. Do not invent observations; if the helper is not a simulator, continue with the actual evidence.'
    agent_class._build_user_prompt=build
    agent_class._validation_nudge_installed=True
