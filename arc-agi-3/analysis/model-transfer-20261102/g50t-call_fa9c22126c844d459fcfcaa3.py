def maze():
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
    return ADJ
def simrun(path, recs, strict=True):
    """path[0]=START. Returns dict(ok,reason,t,overlaps,n,latchY,bloblog)."""
    ADJ=maze(); START=(2,0); GOAL=(2,2)
    PAD={'R':(7,2),'Y':(2,4),'B':(4,5)}; HOME={'R':(4,2),'B':(7,5),'Y':(2,7)}; PUSH={'R':(5,2),'B':(6,5),'Y':(2,6)}
    latchY=False; overlaps=[]
    for t in range(1,len(path)):
        if path[t] not in ADJ.get(path[t-1],[]): return {'ok':False,'reason':'badmove t=%d'%t,'t':t}
        epos=[]
        for i,rec in enumerate(recs):
            p=rec[t-1] if t<=len(rec) else rec[-1]
            epos.append((i,p,t>=len(rec)))
        onpad={}
        for k in PAD:
            who=[]
            if path[t]==PAD[k]: who.append('P')
            for i,p,pa in epos:
                if p==PAD[k]: who.append('E%d'%i)
            onpad[k]=who
        blob={}
        for k in HOME:
            if onpad[k]: blob[k]=PUSH[k]
            elif k=='Y' and latchY: blob[k]=PUSH[k]
            else: blob[k]=HOME[k]
        if 'P' in onpad['Y']: latchY=True
        for k in HOME:
            if path[t]==blob[k]: return {'ok':False,'reason':'blocked %s t=%d'%(k,t),'t':t}
        for i,p,pa in epos:
            if p==path[t]:
                kind='parked' if pa else ('converge' if not (t>1 and any(q==path[t-1] for j,q,_ in epos if j==i)) else 'together')
                if kind in ('parked','converge') or strict:
                    overlaps.append((t,i,kind))
                if kind=='parked': return {'ok':False,'reason':'absorb E%d t=%d'%(i,t),'t':t}
                if strict and kind=='converge': return {'ok':False,'reason':'converge E%d t=%d'%(i,t),'t':t}
    return {'ok':path[-1]==GOAL,'reason':'end '+str(path[-1]),'overlaps':overlaps,'n':len(path)-1,'latchY':latchY}
recC=[(1,0),(2,0),(1,0),(0,0),(0,1),(0,2),(0,3),(0,4),(1,4),(2,4),(3,4),(4,4),(4,5)]
print('sanity: runC replay w/ recC only (echo_C self) len',len(recC))
print(simrun([ (2,0)]+recC, [recC], strict=False))
