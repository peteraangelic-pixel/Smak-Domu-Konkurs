import collections
m=map4(current_frame)
FL=set((r,c) for r in range(15) for c in range(15) if m[r][c]=='B')
PL={(12,3):'p',(1,4):'p',(6,8):'N',(6,14):'O'}
DR={'N':{(5,3),(5,4),(5,5)},'O':{(9,2),(9,3),(9,4)},'p':{(5,10),(5,11),(5,12),(9,10),(9,11),(9,12)}}
CELLS={}
for k,v in PL.items(): CELLS[k]=v
for c,cs in DR.items():
    for x in cs: CELLS[x]=('door',c)
def op_of(A,B): return set(PL[x] for x in (A,B) if x in PL)
def ok_cell(x,op):
    if x in FL or x in PL: return True
    d=CELLS.get(x)
    return bool(d) and d[0]=='door' and d[1] in op
def step_pair(A,B,act):
    da={'UP':(-1,0),'DOWN':(1,0),'LEFT':(0,1),'RIGHT':(0,-1)}[act]
    db={'UP':(-1,0),'DOWN':(1,0),'LEFT':(0,-1),'RIGHT':(0,1)}[act]
    op=op_of(A,B)
    ta=(A[0]+da[0],A[1]+da[1]); tb=(B[0]+db[0],B[1]+db[1])
    na= ta if ok_cell(ta,op) else A
    nb= tb if ok_cell(tb,op) else B
    op2=op_of(na,nb)
    # safety: no agent left inside a closed door
    for x in (na,nb):
        d=CELLS.get(x)
        if d and d[0]=='door' and d[1] not in op2: return None
    if na==A and nb==B: return None
    return na,nb
def jbf(A0,B0,maxd=60,nocross=True):
    start=(A0,B0); seen={start}; q=collections.deque([(start,[])])
    while q:
        (A,B),p=q.popleft()
        if A==B and A in FL: return p
        if len(p)>=maxd: continue
        for act in ['UP','DOWN','LEFT','RIGHT']:
            s=step_pair(A,B,act)
            if s is None: continue
            na,nb=s
            if nocross and not(na==nb) and na[1]>nb[1]: continue
            if s in seen: continue
            seen.add(s); q.append((s,p+[act]))
    return None
sol=jbf((6,5),(6,12))
print('len',len(sol) if sol else None); print(sol)
