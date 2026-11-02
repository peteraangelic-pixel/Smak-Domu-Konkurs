m=map4(current_frame)
FLOOR=set((r,c) for r in range(15) for c in range(15) if m[r][c]=='B')
KEYS={(1,4):'p',(6,8):'N',(6,14):'O'}
DOORS={'N':{(5,3),(5,4),(5,5)},'O':{(9,2),(9,3),(9,4)},'p':{(5,10),(5,11),(5,12),(9,10),(9,11),(9,12)}}
def passable(cell,opened,uncoll):
    return cell in FLOOR or any(cell in DOORS[c] for c in opened) or cell in uncoll
def predict(A,B,op,act):
    da={'UP':(-1,0),'DOWN':(1,0),'LEFT':(0,1),'RIGHT':(0,-1)}[act]
    db={'UP':(-1,0),'DOWN':(1,0),'LEFT':(0,-1),'RIGHT':(0,1)}[act]
    uncoll=frozenset(k for k in KEYS if KEYS[k] not in op)
    ta=(A[0]+da[0],A[1]+da[1]); tb=(B[0]+db[0],B[1]+db[1])
    na= ta if passable(ta,op,uncoll) else A
    nb= tb if passable(tb,op,uncoll) else B
    op2=set(op)
    for x in (na,nb):
        if x in uncoll: op2.add(KEYS[x])
    return na,nb,frozenset(op2)
sol=['UP','UP','UP','UP','UP','UP','LEFT','UP','LEFT','LEFT','RIGHT','RIGHT','RIGHT','RIGHT','RIGHT','UP','RIGHT','UP','UP','UP','UP','LEFT','LEFT','UP','LEFT','UP','LEFT','LEFT','LEFT']
A,B=(12,3),(13,11); op=frozenset(['p'])
for i,act in enumerate(sol):
    A,B,op=predict(A,B,op,act)
    print(i,act,A,B,sorted(op))
