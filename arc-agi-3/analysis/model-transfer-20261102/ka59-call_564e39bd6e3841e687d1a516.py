def step5(state,action):
    YOFF=frozenset([(0,3),(0,4),(0,5),(1,3),(1,4),(1,5),(2,3),(2,4),(2,5),(3,0),(3,1),(3,2),(3,3),(3,4),(3,5),(3,6),(3,7),(3,8),(4,0),(4,1),(4,2),(4,3),(4,4),(4,5),(4,6),(4,7),(4,8),(5,0),(5,1),(5,2),(5,3),(5,4),(5,5),(5,6),(5,7),(5,8),(6,3),(6,4),(6,5),(7,3),(7,4),(7,5),(8,3),(8,4),(8,5)])
    B3=frozenset([(i,j) for i in range(3) for j in range(3)])
    D={'UP':(-3,0),'DOWN':(3,0),'LEFT':(0,-3),'RIGHT':(0,3)}
    P=state['P']; sh=[B3,B3,YOFF]; pos=[state['b'][0],state['b'][1],state['y']]; s=state['sel']
    if isinstance(action,dict):
        if action.get('action')!='MOUSE': return None
        cell=(action['row'],action['col'])
        t=None
        for i in (0,1):
            if cell in cells5(B3,pos[i]): t=i
        if t is None or t==s: return None
        return {'P':P,'b':list(pos[:2]),'y':pos[2],'sel':t}
    d=D.get(action)
    if d is None: return None
    def cs(i,p): return frozenset((p[0]+a,p[1]+b) for a,b in sh[i])
    dest=(pos[s][0]+d[0],pos[s][1]+d[1]); dc=cs(s,dest)
    if not dc<=P: return None
    hit=None
    for i in range(3):
        if i==s: continue
        if dc & cs(i,pos[i]): hit=i
    if hit is None:
        np=list(pos); np[s]=dest
        return {'P':P,'b':[np[0],np[1]],'y':np[2],'sel':s}
    for k in range(5,22):
        lp=(pos[hit][0]+3*k*d[0],pos[hit][1]+3*k*d[1]); lc=cs(hit,lp)
        if not lc<=P: continue
        bad=False
        for i in range(3):
            if i==hit: continue
            occ = dc if i==s else cs(i,pos[i])
            if lc & occ: bad=True;break
        if bad: continue
        np=list(pos); np[s]=dest; np[hit]=lp
        return {'P':P,'b':[np[0],np[1]],'y':np[2],'sel':s}
    return None
import collections
acc=collections.Counter(); miss=[]
for t in transitions:
    if t.before_frame.level!=4: continue
    b=model_state5(t.before_frame); af=model_state5(t.after_frame)
    a=t.action
    pr=step5(b,a) if isinstance(a,str) else step5(b,a)
    if pr==af: acc['ok']+=1
    else:
        acc['bad']+=1
        if len(miss)<5: miss.append((t.after_frame.step,a,pr,af))
print(acc)
for m in miss: print(m)
