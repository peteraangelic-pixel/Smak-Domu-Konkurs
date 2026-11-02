def model_state5(frame):
    P=build_pass(frame); g=grid(frame)
    cs=[(r,c) for r in range(63) for c in range(64) if g[r][c] in 'NW']
    cl=comps2(cs)
    cl.sort(key=lambda L:(min(x[0] for x in L),min(x[1] for x in L)))
    wd=[(r,c) for r in range(63) for c in range(64) if g[r][c]=='W']
    sel=0
    for i,L in enumerate(cl):
        if wd and wd[0] in L: sel=i
    b=[(min(x[0] for x in L),min(x[1] for x in L)) for L in cl]
    ys=[(r,c) for r in range(63) for c in range(64) if g[r][c]=='Y']
    y=(min(r for r,c in ys),min(c for r,c in ys))
    return {'P':P,'b':b,'y':y,'sel':sel}
import collections
acc=collections.Counter(); miss=[]
H=[h for h in history if h.frame.level==4]
for i in range(1,len(H)):
    try:
        b=model_state5(H[i-1].frame); af=model_state5(H[i].frame)
    except Exception: acc['skip']+=1; continue
    pr=step5(b,H[i].action); exp=b if pr is None else pr
    if sd(exp)==sd(af): acc['ok']+=1
    else:
        acc['bad']+=1
        if len(miss)<6: miss.append((H[i].frame.step,H[i].action,sd(exp),sd(af)))
print('n',len(H),'acc',dict(acc))
for m in miss: print(m)
