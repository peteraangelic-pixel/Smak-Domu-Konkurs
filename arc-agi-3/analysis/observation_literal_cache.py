"""Prototype bounded scratch-variable cache for ONE unchanged observation.

No functions, modules, objects, eval or pickle. Not installed in a candidate.
The host must clear BEFORE every action attempt and change the observation
token on any frame/step/level/game change. This is program scratch space, not
solved-level memory or a model-written factual summary.
"""
import json
import math


def encode(value, budget, depth=0):
    if depth>12:raise ValueError('depth limit')
    budget[0]-=1
    if budget[0]<0:raise ValueError('item limit')
    t=type(value)
    if t is type(None):return ['none',None]
    if t is bool:return ['bool',value]
    if t is int:
        if value.bit_length()>4096:raise ValueError('integer limit')
        return ['int',value]
    if t is float:
        if not math.isfinite(value):raise ValueError('nonfinite value')
        return ['float',value]
    if t is str:
        if len(value)>16384:raise ValueError('string limit')
        return ['str',value]
    if t in (list,tuple,set,frozenset):
        return [{list:'list',tuple:'tuple',set:'set',frozenset:'frozenset'}[t],
                [encode(v,budget,depth+1) for v in value]]
    if t is dict:
        return ['dict',[[encode(k,budget,depth+1),encode(v,budget,depth+1)] for k,v in value.items()]]
    raise ValueError('unsupported type')


def decode(node):
    tag,value=node
    if tag in ('none','bool','int','float','str'):return value
    if tag=='dict':return {decode(k):decode(v) for k,v in value}
    values=[decode(v) for v in value]
    return {'list':list,'tuple':tuple,'set':set,'frozenset':frozenset}[tag](values)


class ObservationLiteralCache:
    def __init__(self):self.clear()

    def clear(self):self.token=None;self.payload='{}'

    def capture(self,namespace,*,observation_token,excluded=()):
        data={};skipped=[];excluded=set(excluded)
        for name,value in namespace.items():
            if not isinstance(name,str) or not name.isidentifier() or name.startswith('_') or name in excluded:continue
            if len(data)>=64:skipped.append(name);continue
            try:
                candidate=dict(data);candidate[name]=encode(value,[4096])
                text=json.dumps(candidate,ensure_ascii=False)
                if len(text.encode('utf8'))>65536:raise ValueError('byte limit')
                data=candidate
            except (ValueError,TypeError,OverflowError,UnicodeError):skipped.append(name)
        self.token=observation_token;self.payload=json.dumps(data,ensure_ascii=False)
        return {'retained':list(data),'skipped':skipped}

    def restore(self,*,observation_token):
        if observation_token!=self.token:
            self.clear();return {}
        return {name:decode(value) for name,value in json.loads(self.payload).items()}
