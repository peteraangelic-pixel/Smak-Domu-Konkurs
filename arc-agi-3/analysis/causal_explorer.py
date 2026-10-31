"""Observation-only action policy: no engine/source/ID/solution-path access.

NumPy uses compiled array kernels. Search here means learning observed edges
of a live game; it never clones or steps an internal engine in the policy.
"""
from collections import Counter
import hashlib
import numpy as np


def observation_key(grid):
    a=np.asarray(grid,dtype=np.uint8)
    # Border HUD bars should not make unchanged puzzle states appear novel.
    interior=a[1:-2,1:-1] if min(a.shape)>8 else a
    return hashlib.blake2b(interior.tobytes(),digest_size=12).digest()


class CausalExplorer:
    def __init__(self, responsive=True, repeat_limit=8):
        self.responsive=responsive
        self.repeat_limit=repeat_limit
        self.last_key=None
        self.last_action=None
        self.level=None
        self.visits=Counter()
        self.attempts=Counter()
        self.noops=Counter()
        self.edges={}
        self.preferred=None
        self.repeat=0
        self.turn=0

    def act(self,grid,available,level):
        a=np.asarray(grid,dtype=np.uint8)
        key=observation_key(a)
        changed=self.last_key is not None and key!=self.last_key
        if self.level!=level:
            if self.level is not None and self.last_action:
                self.preferred=self.last_action
            self.level=level
            self.visits.clear();self.attempts.clear();self.noops.clear();self.edges.clear()
            self.last_key=None;self.repeat=0
        elif self.last_action is not None:
            self.edges[(self.last_key,self.last_action)]=key
            if not changed:self.noops[self.last_action]+=1
        self.visits[key]+=1
        h,w=a.shape
        actions=[(int(x),0,0) for x in available if int(x) not in (0,6,7)]
        if 6 in available:
            # Probe broad spatial hypotheses, then refine the resolution.
            coords=[]
            for stride in (16,8,4):
                coords.extend((6,x,y) for y in range(stride//2,h,stride) for x in range(stride//2,w,stride))
            actions.extend(dict.fromkeys(coords))
        if not actions:raise ValueError('No supported legal controls')
        if self.preferred in actions and self.last_key is None:
            action=self.preferred
        elif self.responsive and changed and self.last_action in actions and self.last_action[0]==6 and self.repeat<self.repeat_limit and self.visits[key]==1:
            action=self.last_action;self.repeat+=1
        else:
            def rank(action):
                count=self.attempts[(key,action)]
                target=self.edges.get((key,action))
                return (count>0,self.visits[target] if target is not None else 0,
                        self.noops[action],count,actions.index(action))
            if self.responsive:
                action=min(actions,key=rank)
            else:
                action=actions[self.turn%len(actions)]
            self.repeat=0
        self.turn+=1
        self.attempts[(key,action)]+=1
        self.last_key=key;self.last_action=action
        return action
