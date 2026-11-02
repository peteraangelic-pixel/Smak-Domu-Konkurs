ADJ={
(0,0):[(0,1),(1,0)],(0,1):[(0,0),(0,2)],(0,2):[(0,1),(0,3)],(0,3):[(0,2),(0,4)],
(0,4):[(0,3),(0,5),(1,4)],(0,5):[(0,4),(0,6)],(0,6):[(0,5),(0,7)],(0,7):[(0,6),(1,7)],
(1,0):[(0,0),(2,0)],(1,4):[(0,4),(2,4)],(1,7):[(0,7),(2,7)],
(2,0):[(1,0)],(2,2):[(3,2)],(2,4):[(1,4),(3,4)],(2,7):[(1,7),(3,7)],
(3,2):[(2,2),(4,2)],(3,4):[(2,4),(4,4)],(3,7):[(2,7),(4,7)],
(4,0):[(4,1),(5,0)],(4,1):[(4,0),(4,2)],(4,2):[(3,2),(4,1)],(4,4):[(3,4),(4,5)],
(4,5):[(4,4)],(4,7):[(3,7),(5,7)],(5,0):[(4,0),(6,0)],(5,7):[(4,7),(6,7)],
(6,0):[(5,0),(7,0)],(6,7):[(5,7),(7,7)],(7,0):[(6,0),(7,1)],(7,1):[(7,0),(7,2)],
(7,2):[(7,1),(7,3)],(7,3):[(7,2),(7,4)],(7,4):[(7,3),(7,5)],(7,5):[(7,4),(7,6)],
(7,6):[(7,5),(7,7)],(7,7):[(6,7),(7,6)]}
START=(2,0);GOAL=(2,2)
PAD={'R':(7,2),'Y':(2,4),'B':(4,5)}   # R=red1, B=red2(pad), Y=yellow
HOME={'R':(4,2),'B':(7,5),'Y':(2,7)}
PUSH={'R':(5,2),'B':(6,5),'Y':(2,6)}
def sim(moves, recs, verbose=False):
    """moves: list of direction-free target cells (my positions t=1..n). recs: list of recordings (lists of cells).
       Returns dict with ok, reason, overlaps, goal."""
    pos=START; path=[START]+list(moves); overlaps=[]; latchY=False
    for t in range(1,len(path)):
        # validate move
        if path[t] not in ADJ.get(path[t-1],[]): return {'ok':False,'reason':'bad move t=%d'%t,'t':t}
        # echo positions at tick t
        epos=[]
        for i,rec in enumerate(recs):
            p=rec[t-1] if t<=len(rec) else rec[-1]
            parked = t>=len(rec)
            epos.append((i,p,parked))
        # who occupies pads this tick (player + echoes)
        occ={}
        for k,pk in ['R','Y','B']:
            who=[]
            if path[t]==PAD[pk]: who.append('P')
            for i,p,pa in epos:
                if p==PAD[pk]: who.append('E%d'%i)
            occ[pk]=who
        # blobs
        blob={}
        for k in HOME:
            if occ[k]: blob[k]=PUSH[k]
            elif k=='Y' and latchY: blob[k]=PUSH[k]
            else: blob[k]=HOME[k]
        if 'P' in occ['Y']: latchY=True
        if path[t] in blob.values(): return {'ok':False,'reason':'blocked by blob %s at t=%d'%(k,t),'t':t,'cell':path[t]}
        # overlap check
        for i,p,pa in epos:
            if p==path[t]:
                same_prev = (t>1 and any(p2==path[t-1] for j,p2,q in epos if j==i))
                overlaps.append((t,i,'parked' if pa else ('with' if same_prev else 'converge')))
        # blocked by parked echo (absorb)
        for i,p,pa in epos:
            if pa and p==path[t]:
                return {'ok':False,'reason':'absorb echo%d at t=%d'%(i,t),'t':t}
    return {'ok':path[-1]==GOAL,'goal':path[-1]==GOAL,'reason':'reached '+str(path[-1]),'overlaps':overlaps,'n':len(path)-1,'latchY':latchY}
import json
open('/dev/null','w') if False else None
print('sim defined')
print(sim([(1,0),(0,0)],[],verbose=True))
