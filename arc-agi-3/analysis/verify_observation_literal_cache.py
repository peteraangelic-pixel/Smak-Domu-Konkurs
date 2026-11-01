"""Boundary tests for the unintegrated scratch-cache prototype."""
from observation_literal_cache import ObservationLiteralCache

c=ObservationLiteralCache()
value={'BLK':{'R':[(1,2),(3,4)]},'RING':{(2,3)},'huge':'x'*100000,'fn':lambda:0,'current_frame':'provided'}
r=c.capture(value,observation_token='game-a/level1/step4/framehash',excluded=['current_frame'])
assert set(r['retained'])=={'BLK','RING'}
restored=c.restore(observation_token=c.token);assert restored=={k:value[k] for k in ('BLK','RING')}
restored['BLK']['R'].append((9,9));assert len(c.restore(observation_token=c.token)['BLK']['R'])==2
assert c.restore(observation_token='game-a/level1/step5/framehash')=={}
c.capture({'x':3},observation_token='same');c.clear();assert c.restore(observation_token='same')=={}
c.capture({'x':3},observation_token='game-a');assert c.restore(observation_token='game-b')=={}
class Dangerous:
    def __repr__(self):raise AssertionError('must not invoke repr')
r=c.capture({'bad':Dangerous(),'nan':float('nan'),'text':'__import__("os")'},observation_token='safe')
assert r['retained']==['text']
assert c.restore(observation_token='safe')['text']=='__import__("os")'
print('8 scratch-cache boundary checks passed; no sandbox integration or quality claim')
