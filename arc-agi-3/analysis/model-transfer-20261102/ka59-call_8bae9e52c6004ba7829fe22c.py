def step5(state,action):
    YOFF=frozenset([(0,3),(0,4),(0,5),(1,3),(1,4),(1,5),(2,3),(2,4),(2,5),(3,0),(3,1),(3,2),(3,3),(3,4),(3,5),(3,6),(3,7),(3,8),(4,0),(4,1),(4,2),(4,3),(4,4),(4,5),(4,6),(4,7),(4,8),(5,0),(5,1),(5,2),(5,3),(5,4),(5,5),(5,6),(5,7),(5,8),(6,3),(6,4),(6,5),(7,3),(7,4),(7,5),(8,3),(8,4),(8,5)])
    B3=frozenset([(i,j) for i in range(3) for j in range(3)])
    D={'UP':(-3,0),'DOWN':(3,0),'LEFT':(0,-3),'RIGHT':(0,3)}
    P=state['P']; sh=[B3,B3,YOFF]; pos=[tuple(state['b'][0]),tuple(state['b'][1]),tuple(state['y'])]; s=state['sel']
    act=action
    if isinstance(act,str) and act.startswith('MOUSE'):
        import re
        m=re.search(r'row=(\d+),\s*col=(\d+)',act)
        act={'action':'MOUSE','row':int(m.group(1)),'col':int(m.group(2))} if m else None
    if isinstance(act,dict):
        if act.get('action')!='MOUSE': return None
        cell=(act['row'],act['col']); t=None
        for i in (0,1):
            if cell in frozenset((pos[i][0]+a,pos[i][1]+b) for a in range(3) for b in range(3)): t=i
        if t is None or t==s: return None
        return {'P':P,'b':[pos[0],pos[1]],'y':pos[2],'sel':t}
    d=D.get(act)
    if d is None: return None
    def cs(i,p): return frozenset((p[0]+a,p[1]+b) for a,b in sh[i])
    dest=(pos[s][0]+d[0],pos[s][1]+d[1]); dc=cs(s,dest)
    hit=None
    for i in range(3):
        if i==s: continue
        if dc & cs(i,pos[i]): hit=i
    if hit is None:
        if not dc<=P: return None
        np=list(pos); np[s]=dest
        return {'P':P,'b':[np[0],np[1]],'y':np[2],'sel':s}
    for k in range(5,22):
        lp=(pos[hit][0]+3*k*d[0],pos[hit][1]+3*k*d[1]); lc=cs(hit,lp)
        if not lc<=P: continue
        bad=False
        for i in range(3):
            if i==hit: continue
            occ = cs(s,pos[s]) if i==s else cs(i,pos[i])
            if lc & occ: bad=True;break
        if bad: continue
        np=list(pos); np[hit]=lp
        return {'P':P,'b':[np[0],np[1]],'y':np[2],'sel':s}
    return None
import collections
acc=collections.Counter(); miss=[]
H=[h for h in history if h.frame.level==4]
for i in range(1,len(H)):
    try:
        b=model_state5(H[i-1].frame); af=model_state5(H[i].frame)
        pr=step5(b,H[i].action); exp=b if pr is None else pr
        e=sd(exp); a=sd(af)
    except Exception as ex:
        acc['skip']+=1; continue
    if e==a: acc['ok']+=1
    else:
        acc['bad']+=1
        if len(miss)<6: miss.append((H[i].frame.step,H[i].action,e,a))
print('n',len(H),'acc',dict(acc))
for m in miss: print(m)
