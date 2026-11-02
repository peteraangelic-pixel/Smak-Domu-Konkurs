def build_pass(f):
    g=grid(f); P=set()
    for r in range(59):
        for c in range(64):
            if g[r][c] in 'wc': P.add((r,c))
    return frozenset(P)
YOFF=frozenset([(0,3),(0,4),(0,5),(1,3),(1,4),(1,5),(2,3),(2,4),(2,5),(3,0),(3,1),(3,2),(3,3),(3,4),(3,5),(3,6),(3,7),(3,8),(4,0),(4,1),(4,2),(4,3),(4,4),(4,5),(4,6),(4,7),(4,8),(5,0),(5,1),(5,2),(5,3),(5,4),(5,5),(5,6),(5,7),(5,8),(6,3),(6,4),(6,5),(7,3),(7,4),(7,5),(8,3),(8,4),(8,5)])
B3=frozenset([(i,j) for i in range(3) for j in range(3)])
D={'UP':(-3,0),'DOWN':(3,0),'LEFT':(0,-3),'RIGHT':(0,3)}
def cells5(sh,p): return frozenset((p[0]+a,p[1]+b) for a,b in sh)
def parse5(f):
    g=grid(f)
    def one(pred):
        cs=[(r,c) for r in range(63) for c in range(64) if pred(g[r][c])]
        cl=comps2(cs); cl.sort(key=lambda L:(min(a for a,b in L),min(b for a,b in L)))
        out=[]
        for L in cl:
            r0=min(a for a,b in L);c0=min(b for a,b in L)
            out.append((r0,c0,len(L)))
        return out
    ns=[x for x in one(lambda ch: ch in 'NW')]
    ys=[x for x in one(lambda ch: ch=='Y')]
    return ns,ys
def model_state5(frame):
    P=build_pass(frame)
    ns,ys=parse5(frame)
    return {'P':P,'b':[ns[0][:2],ns[1][:2]],'y':ys[0][:2],'sel':0}
def step5(state,action):
    P=state['P']
    if isinstance(action,dict):
        return state
    d=D.get(action)
    if d is None: return None
    sh=[B3,B3,YOFF]; pos=[state['b'][0],state['b'][1],state['y']]; s=state['sel']
    dest=(pos[s][0]+d[0],pos[s][1]+d[1])
    dc=cells5(sh[s],dest)
    if not dc<=P: return None
    hit=None
    for i in range(3):
        if i==s: continue
        if dc & cells5(sh[i],pos[i]): hit=i
    if hit is None:
        np=list(pos); np[s]=dest
        return {'P':P,'b':[np[0],np[1]],'y':np[2],'sel':s}
    # launch hit
    for k in range(5,22):
        lp=(pos[hit][0]+3*k*d[0],pos[hit][1]+3*k*d[1])
        lc=cells5(sh[hit],lp)
        if not lc<=P: continue
        bad=False
        for i in range(3):
            if i in (hit,): continue
            occ = dc if i==s else cells5(sh[i],pos[i])
            if lc & occ: bad=True;break
        if bad: continue
        np=list(pos); np[s]=dest; np[hit]=lp
        return {'P':P,'b':[np[0],np[1]],'y':np[2],'sel':s}
    return None
def model_goal5(state):
    return state['y']==(8,35) and set(state['b'])=={(29,50),(53,38)}
s5=model_state5(current_frame)
print('state',s5['b'],s5['y'],'goal',model_goal5(s5))
# validate on the level's transitions
import collections
acc=collections.Counter(); miss=[]
for t in transitions:
    if t.before_frame.level!=4: continue
    try:
        b=model_state5(t.before_frame)
    except Exception as e:
        miss.append(('parse',t.step,str(e))); continue
    a=t.action if isinstance(t.action,str) else t.action
    try:
        pr=step5(b,a) if isinstance(a,str) else b
    except Exception as e:
        miss.append(('err',t.step,str(e))); continue
    try: af=model_state5(t.after_frame)
    except Exception as e: af=None
    if pr==af: acc['ok']+=1
    else:
        acc['bad']+=1
        if len(miss)<4: miss.append((t.step,a,pr,af))
print(acc)
for m in miss: print(m)
