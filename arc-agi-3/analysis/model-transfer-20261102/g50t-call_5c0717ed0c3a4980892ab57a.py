def simrun(path, recs, strict=True):
    ADJ=maze(); START=(2,0); GOAL=(2,2)
    PAD={'R':(7,2),'Y':(2,4),'B':(4,5)}; HOME={'R':(4,2),'B':(7,5),'Y':(2,7)}; PUSH={'R':(5,2),'B':(6,5),'Y':(2,6)}
    latchY=False; overlaps=[]
    for t in range(1,len(path)):
        if path[t] not in ADJ.get(path[t-1],[]): return {'ok':False,'reason':'badmove t=%d'%t,'t':t}
        epos=[]
        for i,rec in enumerate(recs):
            p=rec[t-1] if t<=len(rec) else rec[-1]
            epos.append((i,p,t>=len(rec)))
        prev=path[t-1] if t>1 else START
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
                kind='parked' if pa else ('converge' if not any(q==prev for j,q,_ in epos if j==i) else 'together')
                overlaps.append((t,i,kind))
                if kind=='parked': return {'ok':False,'reason':'absorb E%d t=%d'%(i,t),'t':t}
                if strict and kind=='converge': return {'ok':False,'reason':'converge E%d t=%d'%(i,t),'t':t}
    return {'ok':path[-1]==GOAL,'reason':'end '+str(path[-1]),'overlaps':overlaps,'n':len(path)-1,'latchY':latchY}
recC=[(1,0),(2,0),(1,0),(0,0),(0,1),(0,2),(0,3),(0,4),(1,4),(2,4),(3,4),(4,4),(4,5)]
for m in range(0,5):
    for pk in ('shallow','deep'):
        base=buildD(m,pk,[])
        r=simrun(base,[recC],strict=True)
        print(m,pk,len(base)-1,r['ok'],r['reason'],r.get('overlaps'))
