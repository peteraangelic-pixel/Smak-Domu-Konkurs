"""Isolated audit hardening experiment; original notebook remains unchanged."""
import os
from template_gated_transfer import TemplateTransfer
from template_hook import install as install_base


class GuardedTemplateTransfer(TemplateTransfer):
    def __init__(self,*args,max_actions_per_level=32,**kwargs):
        if max_actions_per_level<1:raise ValueError('Positive action cap required')
        super().__init__(*args,**kwargs)
        self.max_actions_per_level=max_actions_per_level
        self.level_actions=0
        self.cap_hits=0

    def act(self,grid,available,level):
        if self.level!=level:
            self.level_actions=0
            if self.level is not None and level<self.level:self.learned=None
        if self.level_actions>=self.max_actions_per_level:
            self.cap_hits+=1
            return None
        action=super().act(grid,available,level)
        if action is not None:self.level_actions+=1
        return action


def install(ta,controller_class=GuardedTemplateTransfer):
    original=ta.ToolAgent.analyze
    if getattr(original,'_arc3_guarded_template',False):return
    install_base(ta,controller_class)
    enabled=ta.ToolAgent.analyze
    def analyze(self,*args,**kwargs):
        if os.environ.get('ARC3_TEMPLATE_ENABLED','1')=='0':
            return original(self,*args,**kwargs)
        return enabled(self,*args,**kwargs)
    analyze._arc3_guarded_template=True
    ta.ToolAgent.analyze=analyze
