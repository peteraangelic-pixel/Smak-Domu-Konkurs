def simok(path, recs, strict=True):
    r=simrun(path,recs,strict); return r
def searchE(recs, maxt=52):
    ADJ=maze(); START=(2,0); GOAL=(2,2)
    from collections import deque
    start=(START,0)
    q=deque([start]); par={start:None}
    best=None
    while q:
        (c,t)=q.popleft()
        if t>=maxt: continue
        for n in ADJ[c]:
            path=None
            # build path by walking parents
            seq=[]; node=(c,t)
            while node is not None:
                seq.append(node[0]); node=par[node]
            seq.reverse(); seq.append(n)
            r=simok(seq,recs,strict=True)
            if not r['ok'] and r.get('reason','').startswith(('converge','absorb','blocked','badmove')):
                continue
            st=(n,t+1)
            if st in par: continue
            par[st]=((c,t))
            if n==GOAL:
                out=[]; node=st
                while node is not None:
                    out.append(node[0]); node=par[node]
                out.reverse()
                return out
            q.append(st)
    return None
recC=[(1,0),(2,0),(1,0),(0,0),(0,1),(0,2),(0,3),(0,4),(1,4),(2,4),(3,4),(4,4),(4,5)]
for m in range(1,6):
    for pk in ('shallow','deep'):
        recD=buildD(m,pk,[])[1:]
        sol=searchE([recC,recD],maxt=46)
        print(m,pk,len(recD),'sol',None if not sol else len(sol)-1, sol if sol else '')
