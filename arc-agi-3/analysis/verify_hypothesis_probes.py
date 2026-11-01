"""Synthetic infrastructure checks, not ARC completions or a policy benchmark."""
from hypothesis_probes import choose_probe,validate

encode=lambda frame:frame['position']
wall={'name':'wall','encode':encode,'step':lambda s,a:min(2,s+1) if a=='RIGHT' else max(0,s-1)}
wrap={'name':'wrap','encode':encode,'step':lambda s,a:(s+1)%3 if a=='RIGHT' else (s-1)%3}
frame={'position':2}
assert choose_probe([wall,wrap],frame,['LEFT','RIGHT'])['action']=='RIGHT'
evidence=[(frame,'RIGHT',{'position':0})]
reports=validate([wall,wrap],evidence)
assert not reports[0]['validated'] and reports[1]['validated']
assert choose_probe([wrap],frame,['RIGHT']) is None
assert choose_probe([wall,wall],frame,['LEFT','RIGHT']) is None
assert not any(r['validated'] for r in validate([wall,wrap],[]))
broken={'name':'broken','encode':encode,'step':lambda s,a:1/0}
assert choose_probe([wall,broken],frame,['LEFT','RIGHT']) is None
assert validate([broken],evidence)[0]['errors']==1
assert choose_probe([wall,wrap],frame,['RIGHT'],costs=[0]) is None
print('8 synthetic checks passed; no engine/LLM or quality claim')
