m=map4(current_frame)
FLOOR=set((r,c) for r in range(15) for c in range(15) if m[r][c]=='B')
KEYS={(1,4):'p',(6,8):'N',(6,14):'O'}
DOORS={'N':{(5,3),(5,4),(5,5)},'O':{(9,2),(9,3),(9,4)},'p':{(5,10),(5,11),(5,12),(9,10),(9,11),(9,12)}}
def passable2(cell,opened,uncoll): return cell in FLOOR or any(cell in DOORS[c] for c in opened) or cell in uncoll
def predict2(A,B,op,act):
    da={'UP':(-1,0),'DOWN':(1,0),'LEFT':(0,1),'RIGHT':(0,-1)}[act]
    db={'UP':(-1,0),'DOWN':(1,0),'LEFT':(0,-1),'RIGHT':(0,1)}[act]
    uncoll=frozenset(k for k in KEYS if KEYS[k] not in op)
    ta=(A[0]+da[0],A[1]+da[1]); tb=(B[0]+db[0],B[1]+db[1])
    na= ta if passable2(ta,op,uncoll) else A
    nb= tb if passable2(tb,op,uncoll) else B
    op2=set(op)
    for x in (na,nb):
        if x in uncoll: op2.add(KEYS[x])
    return na,nb,frozenset(op2)
sol=['UP','UP','UP','UP','UP','UP','LEFT','UP','LEFT','LEFT','RIGHT','RIGHT','RIGHT','RIGHT','RIGHT','UP','RIGHT','UP','UP','UP','UP','LEFT','LEFT','UP','LEFT','UP','LEFT','LEFT','LEFT']
A,B=(12,3),(13,11); op=frozenset(['p']); bad=0
for i,act in enumerate(sol):
    A,B,op=predict2(A,B,op,act)
    try: r=action([act])
    except Exception as e: print('HALT at',i,type(e).__name__); bad=1; break
    got=sorted(ags4(current_frame)); exp=sorted([A,B])
    if r.get('level_completed'): print(i,act,'LEVEL COMPLETED'); bad=2; break
    if r.get('game_over'): print(i,act,'GAME OVER'); bad=3; break
    if got!=exp: print('MISMATCH',i,act,'exp',exp,'got',got); bad=1; break
if bad==0: print('finished plan, agents',ags4(current_frame))
