SHAPE = {(0, 2), (1, 1), (1, 3), (2, 0), (2, 4), (3, 1), (3, 2), (3, 3)}
SH = {(0, 2), (1, 1), (1, 3), (2, 0), (2, 4), (3, 1), (3, 2), (3, 3)}
SH2 = {(0, 2), (1, 1), (1, 3), (2, 0), (2, 4), (3, 1), (3, 2), (3, 3)}

def enc2(fr):
    blocks = []
    dots = []
    pts = []
    for n in fr.segmentation['nodes']:
        b = n['boundary']
        r0 = min((p[0] for p in b))
        c0 = min((p[1] for p in b))
        r1 = max((p[0] for p in b))
        c1 = max((p[1] for p in b))
        if r0 < 10:
            continue
        col = n['color']
        px = n['pixels']
        if col == 'S' and px == 1:
            dots.append((r0, c0))
        elif col == 'M' and px == 4:
            blocks.append((2, r0, c0))
        elif col == 'p' and px == 9:
            blocks.append((3, r0, c0))
        elif col == 'Y' and px == 16:
            blocks.append((4, r0, c0))
        elif col in ('P',) or (col == 'B' and px <= 4):
            for r, c in [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]:
                pts.append((r, c))
    ar = (min((p[0] for p in pts)), min((p[1] for p in pts))) if pts else None
    return (blocks, dots, ar)

def model_state(frame):
    b, d, a = enc2(frame)
    return {'b': sorted(b), 'd': sorted(d), 'a': a}

def desired(cen):
    return (round(cen[0] - 2), round(cen[1] - 2.0))

def cen_of(o):
    if o[0] == 1:
        return (o[1], o[2])
    off = {2: 0.5, 3: 1.0, 2: 1.5}[o[0]]
    return (o[1] + off, o[2] + off)

def arrow_step(ar, blocks, dots, moved):
    objs = [(sz, r, c) for sz, r, c in blocks] + [(1, r, c) for r, c in dots]
    if not objs:
        return ar

    def dl(o):
        dr = desired(cen_of(o))
        return (dr[0] - ar[0], dr[1] - ar[1])
    t = min(objs, key=lambda o: (max(abs(dl(o)[0]), abs(dl(o)[1])), o))
    dr, dc = dl(t)
    fast = moved is not None and moved == t
    k, lim = (2, 12) if fast else (1, 4)
    return (ar[0] + max(-lim, min(lim, k * dr)), ar[1] + max(-lim, min(lim, k * dc)))

def eats(ar, blocks, dots):
    cellsb = {}
    for sz, r, c in blocks:
        for i in range(sz):
            for j in range(sz):
                cellsb[r + i, c + j] = (2, r, c) if sz == 0 else (sz, r, c)
    eaten = []
    for i, j in SH2:
        p = (ar[0] + i, ar[1] + j)
        if p in cellsb:
            eaten.append(cellsb[p])
        for r, c in dots:
            if p == (r, c):
                eaten.append((1, r, c))
    return set(eaten)

def model_step(state, act):
    R = C = None
    if isinstance(act, dict):
        R, C = (act.get('row'), act.get('col'))
    if R is None:
        return None
    st = {'b': list(state['b']), 'd': list(state['d']), 'a': state['a']}
    moved = None
    hit = [(r, c) for r, c in st['d'] if (r, c) == (R, C)]
    if hit:
        r0, c0 = hit[0]
        part = min([d for d in st['d'] if d != hit[0]], key=lambda d: max(abs(d[0] - r0), abs(d[1] - c0)))
        if max(abs(part[0] - r0), abs(part[1] - c0)) <= 6:
            st['d'] = [d for d in st['d'] if d not in (hit[0], part)]
            nb = (2, R - 1, C - 1)
            st['b'].append(nb)
            moved = nb
    else:
        cand = [b for b in st['b'] if max(abs(b[1] - (R - 1)), abs(b[2] - (C - 1))) <= 6]
        if not cand:
            return None
        b = min(cand, key=lambda b: max(abs(b[1] - (R - 1)), abs(b[2] - (C - 1))))
        tr, tc = (R - 1, C - 1)
        nr = b[1] + max(-6, min(6, tr - b[1]))
        nc = b[2] + max(-6, min(6, tc - b[2]))
        if (nr, nc) == (b[1], b[2]):
            return None
        st['b'] = [x for x in st['b'] if x != b]
        nb = (b[0], nr, nc)
        st['b'].append(nb)
        moved = nb
        same = [x for x in st['b'] if x[0] == nb[0] and x != nb and (max(abs(x[1] - nb[1]), abs(x[2] - nb[2])) <= 7)]
        if same:
            st['b'] = [x for x in st['b'] if x not in (nb,) + tuple(same)]
            st['b'].append((nb[0] + 1, nb[1], nb[2]))
            moved = (nb[0] + 1, nb[1], nb[2])
    st['a'] = arrow_step(st['a'], st['b'], st['d'], moved)
    eated = eats(st['a'], st['b'], st['d'])
    if eated:
        st['b'] = [x for x in st['b'] if x not in [e for e in eated if e[0] > 1]]
        st['d'] = [d for d in st['d'] if (1, d[0], d[1]) not in eated]
    return st

def model_goal(state):
    return any((b[0] == 4 and 53 <= b[1] + 1.5 <= 61 and (1 <= b[2] + 1.5 <= 9) for b in state['b']))
