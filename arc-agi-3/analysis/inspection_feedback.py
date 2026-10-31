"""Experimental feedback after different inspections without a game action.

Unlike the old exact-code guard, this counts actual tool outcomes. It retains
every tool result and never blocks code or chooses an engine action.
"""
from dataclasses import replace


def install(agent_class, interval=3):
    original=agent_class._run_python_tool
    def run(self,*args,**kwargs):
        result=original(self,*args,**kwargs)
        count=0 if result.step_executed else getattr(self,'_inspection_idle_count',0)+1
        self._inspection_idle_count=count
        if count and count%interval==0:
            self._inspection_feedback_count=getattr(self,'_inspection_feedback_count',0)+1
            text=(f'\nEXPERIMENT FEEDBACK: {count} consecutive Python calls executed no game action. '
                  'Different crops of an unchanged board do not test a causal hypothesis. '
                  'State the uncertainty that matters and the expected effect of one legal probe. '
                  'Continue computing only if it can change that choice; otherwise perform the probe '
                  'and compare the returned observation with the prediction.')
            return replace(result,content=result.content+text)
        return result
    agent_class._run_python_tool=run
