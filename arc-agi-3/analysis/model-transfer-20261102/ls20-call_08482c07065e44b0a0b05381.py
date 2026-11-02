print('box glyph (b)', p3c(current_frame,'b'), 'panel (O)', p3c(current_frame,'O'))
# executor
am={'U':'UP','D':'DOWN','L':'LEFT','R':'RIGHT'}
def step_dest(LAB,PASS,launch,pos,ch):
    dr,dc={'U':(-5,0),'D':(5,0),'L':(0,-5),'R':(0,5)}[ch]
    nxt=(pos[0]+dr,pos[1]+dc)
    if nxt not in LAB or LAB[nxt] not in PASS: return None
    return launch.get(nxt,nxt)
def run(path_str):
    global_pos=blockpos(current_frame)
    LAB,PASS=model_graph(current_frame)
    launch={(5,9):slide(LAB,PASS,5,9,0,5),(5,54):slide(LAB,PASS,5,54,5,0)}
    log=[]
    for ch in path_str:
        exp=step_dest(LAB,PASS,launch,global_pos,ch)
        r=action([am[ch]])
        nb=blockpos(current_frame)
        bar=sum(1 for c in current_frame.ascii.split('\n')[61] if c=='Y')
        log.append((ch,nb,bar))
        if nb!=exp: log.append(('MISMATCH exp',exp,'got',nb,'state',r['state'])); return log,nb
        global_pos=nb
        if r.get('level_completed') or r.get('game_over'): log.append(('END',r['state'])); return log,nb
    return log,global_pos
ADJ=adj_with_launch(*model_graph(current_frame)[:2],{(5,9):None})  # placeholder
LAB,PASS=model_graph(current_frame)
launch={(5,9):slide(LAB,PASS,5,9,0,5),(5,54):slide(LAB,PASS,5,54,5,0)}
ADJ=adj_with_launch(LAB,PASS,launch)
p=nodes_path(ADJ,(45,9),(15,34))
seq=''.join(mv(x,y) for x,y in zip(p,p[1:]))
print('path S->YA',len(p)-1,seq)
log,pos=run(seq)
for e in log: print(e)
