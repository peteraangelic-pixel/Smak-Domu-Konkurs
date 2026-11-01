"""Codec limits; sandbox integration is verified separately."""
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
c.capture({'v'+str(i):i for i in range(100)},observation_token='names')
assert len(c.restore(observation_token='names'))==64
c.capture({'v'+str(i):'\U0001f600'*16000 for i in range(4)},observation_token='bytes')
assert len(c.payload.encode('utf8'))<=65536
cyclic=[];cyclic.append(cyclic)
r=c.capture({'cycle':cyclic,'surrogate':'\ud800','big':1<<4097,'okay':17},observation_token='limits')
assert r['retained']==['okay']
print('Scratch-cache codec boundaries passed, including UTF-8 bytes, 64 names, cyclic values and unsupported types; no LLM quality claim')
