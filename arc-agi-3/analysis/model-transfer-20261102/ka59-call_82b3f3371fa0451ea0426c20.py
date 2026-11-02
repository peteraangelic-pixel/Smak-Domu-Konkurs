import re as _re
def step5b(state,action):
    YOFF=frozenset([(0,3),(0,4),(0,5),(1,3),(1,4),(1,5),(2,3),(2,4),(2,5),(3,0),(3,1),(3,2),(3,3),(3,4),(3,5),(3,6),(3,7),(3,8),(4,0),(4,1),(4,2),(4,3),(4,4),(4,5),(4,6),(4,7),(4,8),(5,0),(5,1),(5,2),(5,3),(5,4),(5,5),(5,6),(5,7),(5,8),(6,3),(6,4),(6,5),(7,3),(7,4),(7,5),(8,3),(8,4),(8,5)])
    B3=frozenset([(i,j) for i in range(3) for j in range(3)])
    D={'UP':(-3,0),'DOWN':(3,0),'LEFT':(0,-3),'RIGHT':(0,3)}
    P=state['P']; sh=[B3,B3,YOFF]; pos=[tuple(state['b'][0]),tuple(state['b'][1]),tuple(state['y'])]; s=state['sel']
    def cs(i,p): return frozenset((p[0]+a,p[1]+b) for a,b in sh[i])
    d=D.get(action)
    dest=(pos[s][0]+d[0],pos[s][1]+d[1]); dc=cs(s,dest)
    hit=None
    for i in range(3):
        if i==s: continue
        ov=dc & cs(i,pos[i])
        print('  i',i,'ovl',len(ov))
        if ov: hit=i
    print('dest',dest,'dc<=P',dc<=P,'hit',hit)
    return hit
H=[h for h in history if h.frame.level==4]
b=None
for i in range(1,len(H)):
    if H[i].frame.step==131: b=model_state5(H[i-1].frame)
step5b(b,'UP')
